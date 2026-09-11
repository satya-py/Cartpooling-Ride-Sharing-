"""
Tests for the Mapbox integration.

These NEVER hit the real network — mapbox_client.get_route is mocked
so the logic (caching pattern, detour math, fallback behavior) is
verified in isolation. Run these normally with `pytest`; no
MAPBOX_ACCESS_TOKEN or internet access is required.
"""

from unittest.mock import patch
import pytest

from app.data.loader import Ride
from app.services.route_compatibility_service import (
    RouteCompatibilityService,
    MapboxRouteProvider,
    DefaultRouteProvider,
)


def _make_ride() -> Ride:
    return Ride(
        ride_id="RM1",
        driver_name="D",
        org_id="org1",
        travel_date="2026-08-08",
        status="active",
        pickup=(22.58, 88.40),
        drop=(22.50, 88.38),
        departure_hour=10.0,
        available_seats=2,
        fare_per_seat=100.0,
    )


@patch("app.services.route_compatibility_service.mapbox_client.mapbox_configured", return_value=True)
def test_mapbox_provider_requires_token_when_not_configured(mock_configured):
    mock_configured.return_value = False
    with pytest.raises(RuntimeError):
        MapboxRouteProvider()


@patch("app.services.route_compatibility_service.mapbox_client.mapbox_configured", return_value=True)
@patch("app.services.route_compatibility_service.mapbox_client.get_route")
def test_mapbox_provider_uses_real_route_geometry(mock_get_route, _mock_configured):
    mock_get_route.return_value = {
        "distance_km": 5.0,
        "duration_min": 12.0,
        "typical_duration_min": 10.0,
        "geometry_points": [(22.58, 88.40), (22.55, 88.39), (22.50, 88.38)],
    }

    provider = MapboxRouteProvider()
    ride = _make_ride()
    points = provider.get_route_points(ride)

    assert points == [(22.58, 88.40), (22.55, 88.39), (22.50, 88.38)]
    mock_get_route.assert_called_once_with([ride.pickup, ride.drop], want_geometry=True)


@patch("app.services.route_compatibility_service.mapbox_client.mapbox_configured", return_value=True)
@patch("app.services.route_compatibility_service.mapbox_client.get_route")
def test_mapbox_provider_falls_back_to_straight_line_if_geometry_missing(mock_get_route, _mock_configured):
    # Some Mapbox responses could theoretically omit geometry; make
    # sure we never crash and never return an empty route.
    mock_get_route.return_value = {
        "distance_km": 5.0,
        "duration_min": 12.0,
        "typical_duration_min": None,
        "geometry_points": None,
    }

    provider = MapboxRouteProvider()
    ride = _make_ride()
    points = provider.get_route_points(ride)

    assert points == [ride.pickup, ride.drop]


@patch("app.services.route_compatibility_service.mapbox_client.mapbox_configured", return_value=True)
@patch("app.services.route_compatibility_service.mapbox_client.get_route")
def test_mapbox_provider_computes_real_detour(mock_get_route, _mock_configured):
    # First call = base route (pickup->drop). Second call = with-passenger route.
    mock_get_route.side_effect = [
        {"distance_km": 10.0, "duration_min": 20.0, "typical_duration_min": 18.0, "geometry_points": None},
        {"distance_km": 13.5, "duration_min": 27.0, "typical_duration_min": None, "geometry_points": None},
    ]

    provider = MapboxRouteProvider()
    ride = _make_ride()
    detour_km, detour_min = provider.estimate_detour(ride, (22.57, 88.39), (22.52, 88.385))

    assert detour_km == pytest.approx(3.5)
    assert detour_min == pytest.approx(7.0)
    assert mock_get_route.call_count == 2


@patch("app.services.route_compatibility_service.mapbox_client.mapbox_configured", return_value=True)
@patch("app.services.route_compatibility_service.mapbox_client.get_route")
def test_mapbox_provider_detour_never_negative(mock_get_route, _mock_configured):
    # If the "with passenger" route is somehow reported shorter than
    # base (shouldn't normally happen, but traffic timing noise could
    # cause it) detour must clamp to 0, not go negative.
    mock_get_route.side_effect = [
        {"distance_km": 10.0, "duration_min": 20.0, "typical_duration_min": 18.0, "geometry_points": None},
        {"distance_km": 9.0, "duration_min": 19.0, "typical_duration_min": None, "geometry_points": None},
    ]

    provider = MapboxRouteProvider()
    ride = _make_ride()
    detour_km, detour_min = provider.estimate_detour(ride, (22.57, 88.39), (22.52, 88.385))

    assert detour_km == 0.0
    assert detour_min == 0.0


@patch("app.services.route_compatibility_service.mapbox_client.mapbox_configured", return_value=True)
@patch("app.services.route_compatibility_service.mapbox_client.get_route")
def test_route_compatibility_service_prefers_mapbox_detour_when_available(mock_get_route, _mock_configured):
    mock_get_route.side_effect = [
        {"distance_km": 10.0, "duration_min": 20.0, "typical_duration_min": 18.0, "geometry_points": None},
        {"distance_km": 11.0, "duration_min": 22.0, "typical_duration_min": None, "geometry_points": None},
    ]

    provider = MapboxRouteProvider()
    svc = RouteCompatibilityService(route_provider=provider)
    ride = _make_ride()
    detour_km = svc.estimate_detour_km(ride, (22.57, 88.39), (22.52, 88.385))

    assert detour_km == pytest.approx(1.0)


def test_route_compatibility_service_uses_straight_line_fallback_without_mapbox():
    # No mocking needed here — DefaultRouteProvider never calls Mapbox,
    # so it must keep working standalone (offline / no API key case).
    svc = RouteCompatibilityService(route_provider=DefaultRouteProvider())
    ride = _make_ride()
    detour_km = svc.estimate_detour_km(ride, (22.57, 88.39), (22.52, 88.385))

    assert isinstance(detour_km, float)
    assert detour_km >= 0.0
