"""
RideMatchingService

Top-level orchestrator implementing the full pipeline:

Passenger Search
  -> Hard Filters
  -> Geohash Candidate Retrieval          (RideCandidateService + SpatialIndexService)
  -> Precise Route/Distance Calculations  (RouteCompatibilityService)
  -> Match Score                          (MatchScoringService)
  -> Ranking + Tie-Breaking
  -> Top N Results

This is the only service the API layer talks to.
"""

from __future__ import annotations
from typing import List, Tuple

from app.config import config
from app.data.loader import Ride, RideStore
from app.models.schemas import MatchRequest, MatchResponse, RideMatchResult, ScoreBreakdown
from app.services.spatial_index_service import SpatialIndexService
from app.services.ride_candidate_service import RideCandidateService
from app.services.route_compatibility_service import RouteCompatibilityService, DefaultRouteProvider
from app.services import match_scoring_service as scoring
from app.utils import geo_utils


class RideMatchingService:
    def __init__(
        self,
        store: RideStore,
        spatial_index: SpatialIndexService | None = None,
        candidate_service: RideCandidateService | None = None,
        route_service: RouteCompatibilityService | None = None,
    ):
        self.store = store
        self.spatial_index = spatial_index or SpatialIndexService(store)
        self.candidate_service = candidate_service or RideCandidateService(
            store, self.spatial_index
        )
        self.route_service = route_service or RouteCompatibilityService()

    def _score_ride(self, ride: Ride, req: MatchRequest) -> RideMatchResult:
        passenger_pickup = (req.pickup.latitude, req.pickup.longitude)
        passenger_dest = (req.destination.latitude, req.destination.longitude)

        pickup_km = self.route_service.pickup_distance_km(ride, passenger_pickup)
        dest_km = self.route_service.destination_distance_km(ride, passenger_dest)
        detour_km = self.route_service.estimate_detour_km(
            ride, passenger_pickup, passenger_dest
        )
        time_diff = abs(ride.departure_hour - req.requested_hour)

        scores = {
            "pickup": scoring.pickup_score(pickup_km),
            "destination": scoring.destination_score(dest_km),
            "detour": scoring.detour_score(detour_km),
            "time": scoring.time_score(req.requested_hour, ride.departure_hour),
            "fare": scoring.fare_score(ride.fare_per_seat, req.max_fare),
        }
        final_score = scoring.weighted_final_score(scores)
        reasons = scoring.build_reasons(scores, pickup_km, dest_km, detour_km, time_diff, ride)

        return RideMatchResult(
            rideId=ride.ride_id,
            driverName=ride.driver_name,
            matchScore=final_score,
            breakdown=ScoreBreakdown(
                pickupScore=scores["pickup"],
                destinationScore=scores["destination"],
                detourScore=scores["detour"],
                timeScore=scores["time"],
                fareScore=scores["fare"],
            ),
            reasons=reasons,
        ), detour_km, time_diff

    def _cheap_prefilter(self, candidates: List[Ride], req: MatchRequest) -> List[Ride]:
        """
        Rough, FREE (no external API call) pre-ranking using
        straight-line pickup distance, so that an expensive/real
        routing provider (e.g. MapboxRouteProvider) only ever gets
        called for a small, already-promising subset of candidates —
        never for every geohash-filtered ride.

        This is the "cheaper local/geographic calculation" the
        architecture spec asks for before touching a routing API.
        """
        if len(candidates) <= config.MAX_CANDIDATES_FOR_PRECISE_ROUTING:
            return candidates

        passenger_pickup = (req.pickup.latitude, req.pickup.longitude)
        default_route_provider = DefaultRouteProvider()

        def rough_pickup_distance(ride: Ride) -> float:
            route = default_route_provider.get_route_points(ride)
            return geo_utils.point_to_route_distance_km(passenger_pickup, route)

        ranked = sorted(candidates, key=rough_pickup_distance)
        return ranked[: config.MAX_CANDIDATES_FOR_PRECISE_ROUTING]

    def _rank(
        self, scored: List[Tuple[RideMatchResult, float, float]]
    ) -> List[RideMatchResult]:
        """
        Deterministic ranking with tie-breaking:
          1. higher match score
          2. lower detour
          3. smaller time difference
          4. lower fare
          5. stable ride id (never random)
        """

        def sort_key(item: Tuple[RideMatchResult, float, float]):
            result, detour_km, time_diff = item
            ride = self.store.get(result.rideId)
            fare = ride.fare_per_seat if ride else 0.0
            return (-result.matchScore, detour_km, time_diff, fare, result.rideId)

        scored_sorted = sorted(scored, key=sort_key)
        return [item[0] for item in scored_sorted[: config.TOP_N_RESULTS]]

    def match(self, req: MatchRequest) -> MatchResponse:
        candidates = self.candidate_service.get_candidates(req)
        candidates = self._cheap_prefilter(candidates, req)
        scored = [self._score_ride(ride, req) for ride in candidates]
        top_results = self._rank(scored)

        return MatchResponse(
            results=top_results,
            candidatesConsidered=len(candidates),
            totalRidesInSystem=len(self.store),
        )
