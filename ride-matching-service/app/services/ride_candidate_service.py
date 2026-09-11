"""
RideCandidateService

STEP 2-10 of the pipeline:
  tenant filter -> date filter -> status filter -> seat filter ->
  time-window filter -> geohash candidate retrieval -> false-positive
  trim -> capped candidate list.

This is the ONLY place that is allowed to look at "many" rides. It
narrows thousands/millions of rides down to at most MAX_CANDIDATES
before anything expensive happens.
"""

from __future__ import annotations
from typing import List

from app.config import config
from app.data.loader import Ride, RideStore
from app.models.schemas import MatchRequest
from app.services.spatial_index_service import SpatialIndexService
from app.utils import geo_utils


class RideCandidateService:
    def __init__(self, store: RideStore, spatial_index: SpatialIndexService):
        self.store = store
        self.spatial_index = spatial_index

    def _passes_hard_filters(self, ride: Ride, req: MatchRequest) -> bool:
        if ride.org_id != req.org_id:
            return False
        if ride.travel_date != req.travel_date:
            return False
        if ride.status != "active":
            return False
        if ride.available_seats < req.seats:
            return False
        if abs(ride.departure_hour - req.requested_hour) > config.MAX_TIME_DIFFERENCE_HOURS:
            return False
        return True

    def get_candidates(self, req: MatchRequest) -> List[Ride]:
        pickup = (req.pickup.latitude, req.pickup.longitude)
        destination = (req.destination.latitude, req.destination.longitude)

        # STEP 7-9: geohash-based spatial narrowing (cheap, index lookup only)
        spatial_candidate_ids = self.spatial_index.candidate_ride_ids(pickup, destination)

        # STEP 2-6: hard filters, applied only to the already-narrowed set
        candidates: List[Ride] = []
        for ride_id in spatial_candidate_ids:
            ride = self.store.get(ride_id)
            if ride is None:
                continue
            if self._passes_hard_filters(ride, req):
                candidates.append(ride)

        # STEP 10 + safety cap: Pre-sort candidates by spatial proximity (pickup + destination)
        # so that when capping to MAX_CANDIDATES, the most promising rides are kept
        # rather than being truncated arbitrarily by set iteration order.
        def rough_distance(ride: Ride) -> float:
            pickup_d = geo_utils.point_to_route_distance_km(pickup, ride.route_points)
            dest_d = geo_utils.point_to_route_distance_km(destination, ride.route_points)
            return pickup_d + dest_d

        candidates.sort(key=rough_distance)
        return candidates[: config.MAX_CANDIDATES]
