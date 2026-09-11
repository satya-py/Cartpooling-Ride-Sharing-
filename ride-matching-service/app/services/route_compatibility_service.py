"""
RouteCompatibilityService

STEP 11-13 of the pipeline: precise geographic calculations, run ONLY
on the small candidate set returned by RideCandidateService (never on
the whole table, never Haversine-against-everything).

This is the single integration point for your existing route/ETA
module. Swap `DefaultRouteProvider` for a class that calls your real
mapping/ETA service — every other file in this project is unaffected
because they only depend on the `RouteProvider` interface below.
"""

from __future__ import annotations
from typing import List, Protocol, Tuple

from app.data.loader import Ride
from app.utils import geo_utils
from app.integrations import mapbox_client

Point = Tuple[float, float]


class RouteProvider(Protocol):
    """Interface your existing route/ETA module should implement."""

    def get_route_points(self, ride: Ride) -> List[Point]:
        """Return the polyline (list of lat/lon points) for a ride."""
        ...

    def estimate_route_distance_km(self, points: List[Point]) -> float:
        """Total distance of a route/waypoint sequence, in km."""
        ...


class DefaultRouteProvider:
    """
    Fallback provider using straight-line interpolation.

    Replace this with an adapter around your already-implemented
    route/ETA-mean prediction module — it likely already exposes
    something like `get_route(pickup, drop) -> polyline` and
    `estimate_eta(points) -> minutes`. Wire those in here and every
    scoring computation below upgrades automatically to use real
    road-network geometry instead of straight lines.
    """

    def get_route_points(self, ride: Ride) -> List[Point]:
        return ride.route_points

    def estimate_route_distance_km(self, points: List[Point]) -> float:
        return geo_utils.route_length_km(points)


class MapboxRouteProvider:
    """
    Real routing via Mapbox Directions (driving-traffic profile) —
    adapted from the user's existing ETA script (app/integrations/mapbox_client.py).

    Implements the RouteProvider protocol (get_route_points /
    estimate_route_distance_km) so it's a drop-in replacement for
    DefaultRouteProvider, PLUS an extra `estimate_detour` method that
    RouteCompatibilityService prefers automatically when present (see
    `estimate_detour_km` below) — it computes detour using real roads
    and live traffic instead of a straight-line guess.
    """

    def __init__(self):
        if not mapbox_client.mapbox_configured():
            raise RuntimeError(
                "MapboxRouteProvider requires MAPBOX_ACCESS_TOKEN to be set "
                "(see .env.example)."
            )

    def get_route_points(self, ride: Ride) -> List[Point]:
        """Real road geometry for the driver's pickup->drop leg.
        Cached by mapbox_client, so repeat calls for the same ride
        across different passenger queries cost zero extra API calls."""
        result = mapbox_client.get_route([ride.pickup, ride.drop], want_geometry=True)
        if result is None:
            return ride.route_points
        points = result["geometry_points"]
        return points if points else [ride.pickup, ride.drop]

    def estimate_route_distance_km(self, points: List[Point]) -> float:
        # Only used if something calls this directly on raw points;
        # normal scoring goes through get_route_distance_duration()
        # below, which returns Mapbox's own exact distance instead of
        # re-summing polyline segments.
        return geo_utils.route_length_km(points)

    def get_route_distance_duration(self, ride: Ride) -> Tuple[float, float]:
        """Exact (distance_km, duration_min) for the driver's own
        pickup->drop leg, with live traffic. Cached per ride."""
        result = mapbox_client.get_route([ride.pickup, ride.drop], want_geometry=False)
        if result is None:
            return ride.route_length_km, 0.0
        return result["distance_km"], result["duration_min"]

    def estimate_detour(
        self, ride: Ride, passenger_pickup: Point, passenger_destination: Point
    ) -> Tuple[float, float] | None:
        """
        Real routed detour: how much extra distance/time the driver
        needs versus their normal route, computed by asking Mapbox for
        the route THROUGH the passenger's pickup and destination and
        comparing it against the driver's base route — both with live
        traffic. This is what STEP 13 of the pipeline should use
        whenever a real routing provider is available, since a
        straight-line estimate can be badly wrong wherever roads
        aren't straight (rivers, one-ways, highways with few exits).

        Returns (detour_distance_km, detour_time_min).
        """
        base_distance_km, base_duration_min = self.get_route_distance_duration(ride)

        waypoints = [ride.pickup, passenger_pickup, passenger_destination, ride.drop]
        with_passenger = mapbox_client.get_route(waypoints, want_geometry=False)
        if with_passenger is None:
            return None

        detour_km = max(0.0, with_passenger["distance_km"] - base_distance_km)
        detour_min = max(0.0, with_passenger["duration_min"] - base_duration_min)
        return detour_km, detour_min


def _straight_line_detour_km(
    ride: Ride, passenger_pickup: Point, passenger_destination: Point
) -> float:
    """Fallback detour when Mapbox cannot route the waypoint sequence."""
    with_passenger_points = [ride.pickup, passenger_pickup, passenger_destination, ride.drop]
    with_passenger_distance = sum(
        geo_utils.haversine_km(with_passenger_points[i], with_passenger_points[i + 1])
        for i in range(len(with_passenger_points) - 1)
    )
    return max(0.0, with_passenger_distance - ride.route_length_km)


class RouteCompatibilityService:
    def __init__(self, route_provider: RouteProvider | None = None):
        self.route_provider = route_provider or DefaultRouteProvider()

    def pickup_distance_km(self, ride: Ride, passenger_pickup: Point) -> float:
        """STEP 11: how far is the passenger's pickup from the driver's route."""
        route = self.route_provider.get_route_points(ride)
        return geo_utils.point_to_route_distance_km(passenger_pickup, route)

    def destination_distance_km(self, ride: Ride, passenger_destination: Point) -> float:
        """STEP 12: how far is the passenger's destination from the driver's route."""
        route = self.route_provider.get_route_points(ride)
        return geo_utils.point_to_route_distance_km(passenger_destination, route)

    def estimate_detour_km(
        self, ride: Ride, passenger_pickup: Point, passenger_destination: Point
    ) -> float:
        """
        STEP 13: additional distance the driver must travel to serve
        this passenger, i.e.:

            detour = dist(pickup -> p_pickup -> p_dest -> drop) - dist(pickup -> drop)

        This is intentionally NOT the same as pickup_distance_km — a
        passenger can be geographically close to the route (small
        point-to-route distance) yet still force a large detour if
        serving them requires leaving the route and re-joining it
        further along.

        If the active route_provider exposes `estimate_detour` (e.g.
        MapboxRouteProvider), that real, traffic-aware routed detour
        is used instead of the straight-line approximation below.
        """
        if hasattr(self.route_provider, "estimate_detour"):
            routed = self.route_provider.estimate_detour(
                ride, passenger_pickup, passenger_destination
            )
            if routed is not None:
                detour_km, _detour_min = routed
                return detour_km

        return _straight_line_detour_km(ride, passenger_pickup, passenger_destination)
