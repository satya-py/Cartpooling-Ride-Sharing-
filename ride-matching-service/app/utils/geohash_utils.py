"""
Self-contained Geohash implementation.

Kept dependency-free on purpose (hackathon environments often have
restricted network/pip access) — this is the standard base32 geohash
algorithm used by geohash.org / most geohash libraries, so hashes
produced here are interoperable with any other geohash tool.

Geohash is used ONLY for:
  - spatial indexing (bucketing rides into cells)
  - candidate retrieval (narrowing millions of rides to a small set)
  - reducing search space before expensive route/distance math

It is deliberately NEVER used as the final distance/compatibility
metric — see route_compatibility_service.py for that.
"""

from __future__ import annotations
from typing import List, Tuple

_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"
_BASE32_MAP = {c: i for i, c in enumerate(_BASE32)}


def encode(latitude: float, longitude: float, precision: int = 6) -> str:
    """Encode a lat/lon pair into a base32 geohash string."""
    lat_range = [-90.0, 90.0]
    lon_range = [-180.0, 180.0]
    geohash_chars: List[str] = []
    bit = 0
    ch = 0
    even = True  # geohash interleaves longitude first

    while len(geohash_chars) < precision:
        if even:
            mid = (lon_range[0] + lon_range[1]) / 2
            if longitude >= mid:
                ch |= 1 << (4 - bit)
                lon_range[0] = mid
            else:
                lon_range[1] = mid
        else:
            mid = (lat_range[0] + lat_range[1]) / 2
            if latitude >= mid:
                ch |= 1 << (4 - bit)
                lat_range[0] = mid
            else:
                lat_range[1] = mid

        even = not even
        if bit < 4:
            bit += 1
        else:
            geohash_chars.append(_BASE32[ch])
            bit = 0
            ch = 0

    return "".join(geohash_chars)


def decode_bbox(geohash: str) -> Tuple[float, float, float, float]:
    """Decode a geohash into (min_lat, max_lat, min_lon, max_lon)."""
    lat_range = [-90.0, 90.0]
    lon_range = [-180.0, 180.0]
    even = True

    for char in geohash:
        cd = _BASE32_MAP[char]
        for mask in (16, 8, 4, 2, 1):
            bit = 1 if cd & mask else 0
            if even:
                mid = (lon_range[0] + lon_range[1]) / 2
                if bit:
                    lon_range[0] = mid
                else:
                    lon_range[1] = mid
            else:
                mid = (lat_range[0] + lat_range[1]) / 2
                if bit:
                    lat_range[0] = mid
                else:
                    lat_range[1] = mid
            even = not even

    return lat_range[0], lat_range[1], lon_range[0], lon_range[1]


def decode(geohash: str) -> Tuple[float, float]:
    """Decode a geohash into its center (lat, lon)."""
    min_lat, max_lat, min_lon, max_lon = decode_bbox(geohash)
    return (min_lat + max_lat) / 2, (min_lon + max_lon) / 2


def _adjacent(geohash: str, direction: str) -> str:
    """Compute the neighboring geohash in one of: n, s, e, w."""
    neighbor_map = {
        "n": ["p0r21436x8zb9dcf5h7kjnmqesgutwvy", "bc01fg45238967deuvhjyznpkmstqrwx"],
        "s": ["14365h7k9dcfesgujnmqp0r2twvyx8zb", "238967debc01fg45kmstqrwxuvhjyznp"],
        "e": ["bc01fg45238967deuvhjyznpkmstqrwx", "p0r21436x8zb9dcf5h7kjnmqesgutwvy"],
        "w": ["238967debc01fg45kmstqrwxuvhjyznp", "14365h7k9dcfesgujnmqp0r2twvyx8zb"],
    }
    border_map = {
        "n": ["prxz", "bcfguvyz"],
        "s": ["028b", "0145hjnp"],
        "e": ["bcfguvyz", "prxz"],
        "w": ["0145hjnp", "028b"],
    }

    geohash = geohash.lower()
    last_char = geohash[-1]
    parent = geohash[:-1]
    parity = len(geohash) % 2

    if last_char in border_map[direction][parity] and parent:
        parent = _adjacent(parent, direction)

    idx = neighbor_map[direction][parity].index(last_char)
    return parent + _BASE32[idx]


def neighbors(geohash: str) -> List[str]:
    """Return the 8 surrounding geohash cells (N, NE, E, SE, S, SW, W, NW)."""
    n = _adjacent(geohash, "n")
    s = _adjacent(geohash, "s")
    e = _adjacent(geohash, "e")
    w = _adjacent(geohash, "w")
    ne = _adjacent(n, "e")
    nw = _adjacent(n, "w")
    se = _adjacent(s, "e")
    sw = _adjacent(s, "w")
    return [n, ne, e, se, s, sw, w, nw]


def cells_with_neighbors(geohash: str) -> List[str]:
    """Target cell + its 8 neighbors (9 cells total).

    We always search this full 3x3 block rather than just the target
    cell, because a passenger sitting near a cell boundary would
    otherwise miss valid rides whose route only technically falls in
    the adjacent cell.
    """
    return [geohash] + neighbors(geohash)
