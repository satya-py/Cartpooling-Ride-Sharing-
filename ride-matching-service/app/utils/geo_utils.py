"""
Pure geographic math helpers used by the ROUTE COMPATIBILITY stage
(i.e. the precise calculations that run only on the small candidate
set produced by the geohash stage — never on the whole rides table).
"""

from __future__ import annotations
import math
from typing import List, Tuple

Point = Tuple[float, float]  # (lat, lon)

EARTH_RADIUS_KM = 6371.0088


def haversine_km(p1: Point, p2: Point) -> float:
    """Great-circle distance between two lat/lon points, in km."""
    lat1, lon1 = p1
    lat2, lon2 = p2
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def interpolate_points(start: Point, end: Point, interval_m: float) -> List[Point]:
    """
    Produce evenly spaced points along the straight line between start
    and end, roughly `interval_m` meters apart.

    NOTE: This is the FALLBACK route representation used when no real
    routing/mapping provider is wired in. If a real polyline is
    available (e.g. from Google/Mapbox Directions, or your existing
    ETA/route module), prefer sampling THAT polyline instead — see
    RouteProvider in route_compatibility_service.py, which is the
    single place to swap this out.
    """
    total_km = haversine_km(start, end)
    if total_km == 0:
        return [start]

    interval_km = interval_m / 1000.0
    steps = max(1, math.ceil(total_km / interval_km))

    points = []
    for i in range(steps + 1):
        t = i / steps
        lat = start[0] + (end[0] - start[0]) * t
        lon = start[1] + (end[1] - start[1]) * t
        points.append((lat, lon))
    return points


def point_to_segment_distance_km(point: Point, seg_start: Point, seg_end: Point) -> float:
    """
    Approximate distance from `point` to the line segment (seg_start,
    seg_end) in km. Uses an equirectangular flat-plane approximation,
    which is accurate enough at carpool distances (<50km) and far
    cheaper than doing this on a sphere for every candidate/segment
    pair.
    """
    lat0 = math.radians((seg_start[0] + seg_end[0]) / 2)

    def to_xy(p: Point) -> Tuple[float, float]:
        x = math.radians(p[1]) * math.cos(lat0) * EARTH_RADIUS_KM
        y = math.radians(p[0]) * EARTH_RADIUS_KM
        return x, y

    px, py = to_xy(point)
    ax, ay = to_xy(seg_start)
    bx, by = to_xy(seg_end)

    dx, dy = bx - ax, by - ay
    seg_len_sq = dx * dx + dy * dy

    if seg_len_sq == 0:
        return math.hypot(px - ax, py - ay)

    t = ((px - ax) * dx + (py - ay) * dy) / seg_len_sq
    t = max(0.0, min(1.0, t))

    closest_x = ax + t * dx
    closest_y = ay + t * dy
    return math.hypot(px - closest_x, py - closest_y)


def point_to_route_distance_km(point: Point, route: List[Point]) -> float:
    """Minimum distance from `point` to any segment of a polyline route."""
    if len(route) == 1:
        return haversine_km(point, route[0])

    best = math.inf
    for i in range(len(route) - 1):
        d = point_to_segment_distance_km(point, route[i], route[i + 1])
        best = min(best, d)
    return best


def route_length_km(route: List[Point]) -> float:
    """Total length of a polyline route in km."""
    return sum(haversine_km(route[i], route[i + 1]) for i in range(len(route) - 1))
