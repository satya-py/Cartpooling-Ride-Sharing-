"""
SpatialIndexService

Sole responsibility: turn a passenger's pickup/destination points into
the set of geohash cells that must be searched, and answer "which
rides have route cells intersecting these cells?" via the RideStore's
cell index.

This is STEP 7-9 of the matching pipeline. It never computes distance
— it only narrows the search space. Precise compatibility is decided
later by RouteCompatibilityService.
"""

from __future__ import annotations
from typing import List, Set, Tuple

from app.config import config
from app.utils import geohash_utils
from app.data.loader import RideStore

Point = Tuple[float, float]


class SpatialIndexService:
    def __init__(self, store: RideStore, precision: int = config.GEOHASH_PRECISION):
        self.store = store
        self.precision = precision

    def cells_for_point(self, point: Point) -> List[str]:
        """Target geohash cell + 8 neighbors for a single point.

        Searching neighbors too is what prevents false negatives for
        passengers sitting near a cell boundary.
        """
        cell = geohash_utils.encode(*point, precision=self.precision)
        return geohash_utils.cells_with_neighbors(cell)

    def candidate_ride_ids(self, pickup: Point, destination: Point) -> Set[str]:
        """
        Union of rides whose route touches cells near EITHER the
        passenger's pickup OR their destination.

        We search both ends because a ride could be a great match on
        pickup proximity but wrong on destination (or vice versa) —
        hard filters / scoring downstream will reject bad matches;
        here we just want to avoid missing legitimate candidates.
        """
        pickup_cells = self.cells_for_point(pickup)
        dest_cells = self.cells_for_point(destination)
        all_cells = list(set(pickup_cells) | set(dest_cells))
        return self.store.all_ride_ids_in_cells(all_cells)
