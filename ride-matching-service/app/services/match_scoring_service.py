"""
MatchScoringService

STEP 14-16 of the pipeline: convert precise distances/time
differences into normalized 0-100 sub-scores, then combine them into
the weighted Match Score.

Pure functions only — no I/O, no DB, easy to unit test in isolation
(see tests/test_scoring.py).
"""

from __future__ import annotations
from typing import Dict, List, Optional

from app.config import config
from app.data.loader import Ride


def pickup_score(distance_km: float) -> float:
    if distance_km <= 0:
        return 100.0
    score = 100.0 - (distance_km / config.MAX_PICKUP_ROUTE_DISTANCE_KM) * 100.0
    return round(max(0.0, min(100.0, score)), 2)


def destination_score(distance_km: float) -> float:
    if distance_km <= 0:
        return 100.0
    score = 100.0 - (distance_km / config.MAX_DROPOFF_ROUTE_DISTANCE_KM) * 100.0
    return round(max(0.0, min(100.0, score)), 2)


def detour_score(detour_km: float) -> float:
    if detour_km <= 0:
        return 100.0
    score = 100.0 - (detour_km / config.MAX_DETOUR_DISTANCE_KM) * 100.0
    return round(max(0.0, min(100.0, score)), 2)


def time_score(passenger_hour: float, driver_hour: float) -> float:
    diff = abs(passenger_hour - driver_hour)
    if diff <= 0:
        return 100.0
    score = 100.0 - (diff / config.MAX_TIME_DIFFERENCE_HOURS) * 100.0
    return round(max(0.0, min(100.0, score)), 2)


def fare_score(fare: float, max_budget: Optional[float]) -> float:
    if max_budget is None:
        return config.NEUTRAL_FARE_SCORE
    if fare <= max_budget:
        return 100.0
    overage_pct = (fare - max_budget) / max_budget
    score = 100.0 - overage_pct * 200.0  # steep penalty for exceeding budget
    return round(max(0.0, score), 2)


def weighted_final_score(scores: Dict[str, float]) -> float:
    final = (
        scores["pickup"] * config.WEIGHT_PICKUP
        + scores["destination"] * config.WEIGHT_DESTINATION
        + scores["detour"] * config.WEIGHT_DETOUR
        + scores["time"] * config.WEIGHT_TIME
        + scores["fare"] * config.WEIGHT_FARE
    )
    return round(max(0.0, min(100.0, final)), 2)


def build_reasons(
    scores: Dict[str, float],
    pickup_km: float,
    dest_km: float,
    detour_km: float,
    time_diff_hours: float,
    ride: Ride,
) -> List[str]:
    """Human-readable explanation for why a ride scored the way it did."""
    reasons: List[str] = []

    if scores["pickup"] >= 90:
        reasons.append(f"Pickup is {pickup_km:.2f} km from the driver's route")
    elif scores["pickup"] >= 60:
        reasons.append(f"Pickup is a moderate {pickup_km:.2f} km from the route")

    if scores["destination"] >= 90:
        reasons.append("Destination is directly along the driver's route")
    elif scores["destination"] >= 60:
        reasons.append(f"Destination is {dest_km:.2f} km from the route")

    if scores["detour"] >= 90:
        reasons.append(f"Estimated detour is only {detour_km:.2f} km")
    elif scores["detour"] < 50:
        reasons.append(f"Detour of {detour_km:.2f} km is significant")

    if scores["time"] >= 90:
        reasons.append(f"Departure is {time_diff_hours * 60:.0f} minutes from requested time")

    if scores["fare"] >= 90:
        reasons.append(f"Fare (₹{ride.fare_per_seat:.0f}) fits within your budget")
    elif scores["fare"] < 50:
        reasons.append(f"Fare (₹{ride.fare_per_seat:.0f}) is above your budget")

    return reasons
