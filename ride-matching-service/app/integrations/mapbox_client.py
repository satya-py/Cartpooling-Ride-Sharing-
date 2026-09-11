"""
Mapbox Directions API client (driving-traffic profile).

This is the ONLY file in the project that talks to Mapbox. Adapted
from the user's original ETA script — same auth, same endpoint, same
depart_at-for-live-traffic trick — extended with two things the
matching engine needs:

  1. Optional route GEOMETRY (not just ETA numbers), so
     RouteCompatibilityService can measure how close a passenger's
     pickup/destination is to the actual road path, not a straight
     line.
  2. In-process CACHING, because the matching pipeline may ask for
     the same ride's route many times (once per passenger query) and
     the problem statement explicitly requires minimizing external
     routing API calls.
"""

import os
from datetime import datetime, timezone
from functools import lru_cache
from typing import List, Optional, Tuple

import requests
from dotenv import load_dotenv

load_dotenv()

MAPBOX_ACCESS_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")
MAPBOX_DIRECTIONS_URL = "https://api.mapbox.com/directions/v5/mapbox/driving-traffic"

Point = Tuple[float, float]  # (lat, lon)


def mapbox_configured() -> bool:
    """Whether a Mapbox token is available. Used by main.py to decide
    whether to wire up MapboxRouteProvider or fall back to the
    straight-line DefaultRouteProvider."""
    return bool(MAPBOX_ACCESS_TOKEN)


def _get_current_departure_time() -> str:
    """Current UTC time in ISO-8601, e.g. 2026-08-08T09:10:20Z.
    Sent as depart_at so Mapbox uses live + historical traffic."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return now.isoformat().replace("+00:00", "Z")


def _coords_to_url_param(points: List[Point]) -> str:
    # Mapbox wants "lon,lat;lon,lat;..."
    return ";".join(f"{lon},{lat}" for lat, lon in points)


RouteResult = dict


@lru_cache(maxsize=4096)
def _fetch_route_cached(
    rounded_points: Tuple[Tuple[float, float], ...], want_geometry: bool
) -> Optional[RouteResult]:
    """
    The actual HTTP call, wrapped in lru_cache so the same
    (waypoints, want_geometry) request never hits the network twice
    in a process's lifetime. `rounded_points` are rounded to 6
    decimal places (~11cm precision) purely so floating point noise
    doesn't defeat the cache.
    """
    if not MAPBOX_ACCESS_TOKEN:
        raise RuntimeError("MAPBOX_ACCESS_TOKEN is not set. Add it to your .env file.")

    coordinates = _coords_to_url_param(list(rounded_points))
    url = f"{MAPBOX_DIRECTIONS_URL}/{coordinates}"

    params = {
        "access_token": MAPBOX_ACCESS_TOKEN,
        "alternatives": "false",
        "overview": "full" if want_geometry else "false",
        "steps": "false",
        "depart_at": _get_current_departure_time(),
    }
    if want_geometry:
        params["geometries"] = "geojson"

    response = requests.get(url, params=params, timeout=20)

    if response.status_code != 200:
        try:
            err = response.json()
        except Exception:
            err = response.text
        raise RuntimeError(f"Mapbox HTTP {response.status_code}: {err}")

    data = response.json()

    if data.get("code") != "Ok":
        # Some waypoint combinations are unroutable (e.g. ferry-only,
        # disconnected road network). Callers fall back to straight-line
        # math instead of crashing the whole match request.
        if data.get("code") == "NoRoute" or not data.get("routes"):
            return None
        raise RuntimeError(f"Mapbox routing error: {data}")

    route = data["routes"][0]
    distance_km = route.get("distance", 0) / 1000
    duration_min = route.get("duration", 0) / 60
    typical_s = route.get("duration_typical")
    typical_min = typical_s / 60 if typical_s is not None else None

    geometry_points: Optional[List[Point]] = None
    if want_geometry:
        coords = route["geometry"]["coordinates"]  # [[lon, lat], ...]
        geometry_points = [(lat, lon) for lon, lat in coords]

    return {
        "distance_km": round(distance_km, 3),
        "duration_min": round(duration_min, 2),
        "typical_duration_min": round(typical_min, 2) if typical_min is not None else None,
        "geometry_points": geometry_points,
    }


def get_route(points: List[Point], want_geometry: bool = False) -> Optional[RouteResult]:
    """
    Public entrypoint.

    `points`: ordered list of (lat, lon) waypoints.
      - 2 points  -> a simple pickup->drop route (used to get the
        driver's own route, distance, and ETA)
      - 4 points  -> driver_pickup -> passenger_pickup ->
        passenger_drop -> driver_drop (used to measure real detour)

    Returns:
        {
          "distance_km": float,
          "duration_min": float,                # live-traffic ETA
          "typical_duration_min": float | None,  # historical baseline
          "geometry_points": list[(lat, lon)] | None,
        }
    """
    rounded = tuple((round(lat, 6), round(lon, 6)) for lat, lon in points)
    return _fetch_route_cached(rounded, want_geometry)
