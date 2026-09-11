import pytest
from app.data.loader import Ride, RideStore
from app.services.spatial_index_service import SpatialIndexService
from app.services.ride_candidate_service import RideCandidateService
from app.services.route_compatibility_service import RouteCompatibilityService
from app.services.ride_matching_service import RideMatchingService
from app.models.schemas import MatchRequest, LatLon


def _make_ride(**overrides) -> Ride:
    defaults = dict(
        ride_id="R0",
        driver_name="Test Driver",
        org_id="org1",
        travel_date="2026-08-08",
        status="active",
        pickup=(22.5726, 88.3639),   # Kolkata-ish
        drop=(22.6, 88.45),
        departure_hour=10.0,
        available_seats=2,
        fare_per_seat=100.0,
    )
    defaults.update(overrides)
    return Ride(**defaults)


@pytest.fixture
def sample_store() -> RideStore:
    """
    10+ rides covering: different routes, departure times, seat
    availability, fares, an inactive/cancelled ride, and a
    different-organization ride (tenant isolation check).
    """
    store = RideStore()

    rides = [
        _make_ride(ride_id="R001", pickup=(22.5726, 88.3639), drop=(22.60, 88.45),
                   departure_hour=10.0, available_seats=3, fare_per_seat=100.0),
        _make_ride(ride_id="R002", pickup=(22.58, 88.37), drop=(22.61, 88.46),
                   departure_hour=10.25, available_seats=1, fare_per_seat=90.0),
        _make_ride(ride_id="R003", pickup=(22.50, 88.30), drop=(22.55, 88.33),
                   departure_hour=9.0, available_seats=4, fare_per_seat=60.0),
        _make_ride(ride_id="R004", pickup=(22.65, 88.40), drop=(22.70, 88.42),
                   departure_hour=18.0, available_seats=2, fare_per_seat=150.0),
        _make_ride(ride_id="R005", pickup=(22.573, 88.365), drop=(22.605, 88.452),
                   departure_hour=10.1, available_seats=0, fare_per_seat=95.0),  # sold out
        _make_ride(ride_id="R006", pickup=(22.572, 88.363), drop=(22.599, 88.449),
                   departure_hour=10.05, available_seats=2, fare_per_seat=500.0),  # expensive
        _make_ride(ride_id="R007", pickup=(22.90, 88.90), drop=(23.0, 89.0),
                   departure_hour=10.0, available_seats=3, fare_per_seat=80.0),  # far away
        _make_ride(ride_id="R008", pickup=(22.5726, 88.3639), drop=(22.60, 88.45),
                   departure_hour=10.0, available_seats=2, fare_per_seat=100.0,
                   status="cancelled"),  # inactive
        _make_ride(ride_id="R009", pickup=(22.5726, 88.3639), drop=(22.60, 88.45),
                   departure_hour=10.0, available_seats=2, fare_per_seat=100.0,
                   org_id="org2"),  # different tenant
        _make_ride(ride_id="R010", pickup=(22.575, 88.366), drop=(22.602, 88.451),
                   departure_hour=10.02, available_seats=3, fare_per_seat=98.0),
        _make_ride(ride_id="R011", pickup=(22.574, 88.364), drop=(22.601, 88.450),
                   departure_hour=13.5, available_seats=2, fare_per_seat=100.0),  # outside time window
        _make_ride(ride_id="R012", pickup=(22.5726, 88.3639), drop=(22.5726, 88.3639),
                   departure_hour=10.0, available_seats=1, fare_per_seat=50.0),  # zero-length route
    ]

    for r in rides:
        store.add_ride(r)

    return store


@pytest.fixture
def matching_service(sample_store) -> RideMatchingService:
    spatial_index = SpatialIndexService(sample_store)
    candidate_service = RideCandidateService(sample_store, spatial_index)
    route_service = RouteCompatibilityService()
    return RideMatchingService(sample_store, spatial_index, candidate_service, route_service)


@pytest.fixture
def base_request() -> MatchRequest:
    return MatchRequest(
        org_id="org1",
        pickup=LatLon(latitude=22.5726, longitude=88.3639),
        destination=LatLon(latitude=22.60, longitude=88.45),
        travel_date="2026-08-08",
        requested_hour=10.0,
        seats=1,
        max_fare=120.0,
    )
