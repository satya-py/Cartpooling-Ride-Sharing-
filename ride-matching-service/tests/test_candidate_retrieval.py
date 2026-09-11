from app.services.spatial_index_service import SpatialIndexService
from app.services.ride_candidate_service import RideCandidateService
from app.models.schemas import MatchRequest, LatLon


def _candidates_for(sample_store, **overrides):
    idx = SpatialIndexService(sample_store)
    svc = RideCandidateService(sample_store, idx)
    req_kwargs = dict(
        org_id="org1",
        pickup=LatLon(latitude=22.5726, longitude=88.3639),
        destination=LatLon(latitude=22.60, longitude=88.45),
        travel_date="2026-08-08",
        requested_hour=10.0,
        seats=1,
        max_fare=None,
    )
    req_kwargs.update(overrides)
    req = MatchRequest(**req_kwargs)
    return svc.get_candidates(req)


def test_tenant_isolation(sample_store):
    candidates = _candidates_for(sample_store)
    ids = {r.ride_id for r in candidates}
    assert "R009" not in ids  # belongs to org2


def test_cancelled_ride_excluded(sample_store):
    candidates = _candidates_for(sample_store)
    ids = {r.ride_id for r in candidates}
    assert "R008" not in ids  # status=cancelled


def test_sold_out_ride_excluded(sample_store):
    candidates = _candidates_for(sample_store, seats=1)
    ids = {r.ride_id for r in candidates}
    assert "R005" not in ids  # available_seats=0


def test_seat_count_hard_filter(sample_store):
    candidates = _candidates_for(sample_store, seats=5)
    # No ride in the fixture has 5 seats available
    assert candidates == []


def test_departure_time_outside_window_excluded(sample_store):
    candidates = _candidates_for(sample_store, requested_hour=10.0)
    ids = {r.ride_id for r in candidates}
    assert "R011" not in ids  # departure_hour=13.5, > 1h window


def test_far_away_ride_never_reaches_candidates(sample_store):
    candidates = _candidates_for(sample_store)
    ids = {r.ride_id for r in candidates}
    assert "R007" not in ids


def test_only_one_candidate(sample_store):
    # Search near R003's route specifically (22.50,88.30 -> 22.55,88.33)
    # with a seat requirement only R003 satisfies in that area.
    candidates = _candidates_for(
        sample_store,
        pickup=LatLon(latitude=22.50, longitude=88.30),
        destination=LatLon(latitude=22.55, longitude=88.33),
        seats=4,
    )
    ids = {r.ride_id for r in candidates}
    assert ids == {"R003"}


def test_no_candidates_wrong_date(sample_store):
    candidates = _candidates_for(sample_store, travel_date="2099-01-01")
    assert candidates == []
