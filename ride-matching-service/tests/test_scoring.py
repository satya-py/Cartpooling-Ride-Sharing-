from app.services import match_scoring_service as scoring


def test_pickup_score_perfect_on_route():
    assert scoring.pickup_score(0.0) == 100.0


def test_pickup_score_decreases_with_distance():
    near = scoring.pickup_score(0.3)
    far = scoring.pickup_score(1.4)
    assert near > far


def test_pickup_score_clamped_at_zero_beyond_max():
    assert scoring.pickup_score(10.0) == 0.0


def test_destination_score_perfect_on_route():
    assert scoring.destination_score(0.0) == 100.0


def test_detour_score_zero_detour_is_perfect():
    assert scoring.detour_score(0.0) == 100.0


def test_detour_score_large_detour_clamped_zero():
    assert scoring.detour_score(100.0) == 0.0


def test_time_score_exact_match():
    assert scoring.time_score(10.0, 10.0) == 100.0


def test_time_score_outside_window_clamped_zero():
    assert scoring.time_score(10.0, 15.0) == 0.0


def test_fare_score_no_budget_is_neutral():
    assert scoring.fare_score(500.0, None) == 70.0


def test_fare_score_within_budget_is_perfect():
    assert scoring.fare_score(80.0, 100.0) == 100.0


def test_fare_score_far_above_budget_is_low():
    score = scoring.fare_score(500.0, 100.0)
    assert score < 20.0


def test_weighted_final_score_uses_configured_weights():
    scores = {"pickup": 100, "destination": 100, "detour": 100, "time": 100, "fare": 100}
    assert scoring.weighted_final_score(scores) == 100.0

    scores_zero = {"pickup": 0, "destination": 0, "detour": 0, "time": 0, "fare": 0}
    assert scoring.weighted_final_score(scores_zero) == 0.0


def test_weighted_final_score_is_clamped_0_to_100():
    scores = {"pickup": 100, "destination": 100, "detour": 100, "time": 100, "fare": 100}
    result = scoring.weighted_final_score(scores)
    assert 0.0 <= result <= 100.0
