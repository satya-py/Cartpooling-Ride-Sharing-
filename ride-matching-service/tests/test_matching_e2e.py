from app.models.schemas import MatchRequest, LatLon


def test_best_ride_appears_first(matching_service, base_request):
    response = matching_service.match(base_request)
    assert len(response.results) > 0
    top = response.results[0]
    # Best match should be one of the tight-cluster, on-time, in-budget rides
    assert top.rideId in {"R001", "R002", "R006", "R010"}
    # Sorted descending by score
    scores = [r.matchScore for r in response.results]
    assert scores == sorted(scores, reverse=True)


def test_expensive_ride_scores_lower_than_similar_cheap_ride(matching_service, base_request):
    response = matching_service.match(base_request)
    by_id = {r.rideId: r for r in response.results}
    if "R006" in by_id and "R001" in by_id:
        # R006 is geographically near-identical to R001/R010 but far
        # over budget (fare=500 vs max_fare=120) -> should rank lower.
        assert by_id["R006"].matchScore < by_id["R001"].matchScore


def test_sold_out_ride_never_appears(matching_service, base_request):
    response = matching_service.match(base_request)
    ids = {r.rideId for r in response.results}
    assert "R005" not in ids


def test_wrong_tenant_never_appears(matching_service, base_request):
    response = matching_service.match(base_request)
    ids = {r.rideId for r in response.results}
    assert "R009" not in ids


def test_cancelled_ride_never_appears(matching_service, base_request):
    response = matching_service.match(base_request)
    ids = {r.rideId for r in response.results}
    assert "R008" not in ids


def test_empty_results_when_no_rides_match(matching_service):
    req = MatchRequest(
        org_id="org1",
        pickup=LatLon(latitude=-10.0, longitude=-10.0),  # nowhere near any ride
        destination=LatLon(latitude=-10.1, longitude=-10.1),
        travel_date="2026-08-08",
        requested_hour=10.0,
        seats=1,
    )
    response = matching_service.match(req)
    assert response.results == []
    assert response.candidatesConsidered == 0


def test_budget_not_provided_uses_neutral_fare_score(matching_service):
    req = MatchRequest(
        org_id="org1",
        pickup=LatLon(latitude=22.5726, longitude=88.3639),
        destination=LatLon(latitude=22.60, longitude=88.45),
        travel_date="2026-08-08",
        requested_hour=10.0,
        seats=1,
        max_fare=None,
    )
    response = matching_service.match(req)
    for result in response.results:
        assert result.breakdown.fareScore == 70.0  # NEUTRAL_FARE_SCORE


def test_response_includes_score_breakdown_and_reasons(matching_service, base_request):
    response = matching_service.match(base_request)
    for result in response.results:
        assert 0 <= result.matchScore <= 100
        assert result.breakdown is not None
        assert isinstance(result.reasons, list)


def test_zero_length_route_does_not_crash(matching_service):
    # R012 has identical pickup/drop (edge case: driver going nowhere)
    req = MatchRequest(
        org_id="org1",
        pickup=LatLon(latitude=22.5726, longitude=88.3639),
        destination=LatLon(latitude=22.5726, longitude=88.3639),
        travel_date="2026-08-08",
        requested_hour=10.0,
        seats=1,
    )
    response = matching_service.match(req)  # should not raise
    assert isinstance(response.results, list)


def test_tie_breaking_is_deterministic(matching_service, base_request):
    r1 = matching_service.match(base_request)
    r2 = matching_service.match(base_request)
    ids1 = [r.rideId for r in r1.results]
    ids2 = [r.rideId for r in r2.results]
    assert ids1 == ids2  # same input -> same order, every time
