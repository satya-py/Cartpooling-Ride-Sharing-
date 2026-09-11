"""
Central configuration for the Intelligent Ride Matching module.

Every tunable threshold lives here so the matching pipeline can be
tuned per-deployment (urban vs rural, tenant-specific policy, etc.)
without touching business logic.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MatchingConfig:
    # ---- Geohash strategy ----
    # Precision 6 => ~1.2km x 0.6km cells. Good default for urban/suburban
    # carpooling. Bump to 7 for very dense cities, drop to 5 for rural/highway
    # commute corridors where rides are sparse and routes are long.
    GEOHASH_PRECISION: int = 6

    # Distance (meters) between sampled points when converting a route
    # polyline into a set of geohash cells. Smaller = more accurate route
    # coverage but bigger index. 300-500m is a good balance for city driving.
    ROUTE_SAMPLE_INTERVAL_M: float = 400.0

    # ---- Hard filters ----
    MAX_TIME_DIFFERENCE_HOURS: float = 1.0
    MAX_PICKUP_ROUTE_DISTANCE_KM: float = 1.5
    MAX_DROPOFF_ROUTE_DISTANCE_KM: float = 2.0
    MAX_DETOUR_DISTANCE_KM: float = 3.0

    # ---- Candidate reduction ----
    # Hard ceiling on how many candidates get expensive precise scoring.
    # Protects the service from pathological "everyone matches" queries.
    MAX_CANDIDATES: int = 100

    # Of those (up to) MAX_CANDIDATES geohash-filtered candidates, only
    # this many get scored with the real routing provider (e.g. Mapbox).
    # The rest are pre-ranked for free using straight-line distance
    # first (RideMatchingService._cheap_prefilter), so a passenger
    # search never triggers more than this many external API calls —
    # directly implementing the "minimize routing API calls" requirement.
    MAX_CANDIDATES_FOR_PRECISE_ROUTING: int = 20

    # ---- Result size ----
    TOP_N_RESULTS: int = 10

    # ---- Scoring weights (must sum to 1.0) ----
    WEIGHT_PICKUP: float = 0.30
    WEIGHT_DESTINATION: float = 0.25
    WEIGHT_DETOUR: float = 0.20
    WEIGHT_TIME: float = 0.15
    WEIGHT_FARE: float = 0.10

    # Neutral score applied to the fare component when the passenger
    # supplies no budget preference (keeps fare from unfairly punishing
    # or rewarding rides when there's no signal).
    NEUTRAL_FARE_SCORE: float = 70.0


config = MatchingConfig()

assert abs(
    config.WEIGHT_PICKUP
    + config.WEIGHT_DESTINATION
    + config.WEIGHT_DETOUR
    + config.WEIGHT_TIME
    + config.WEIGHT_FARE
    - 1.0
) < 1e-9, "Scoring weights must sum to 1.0"
