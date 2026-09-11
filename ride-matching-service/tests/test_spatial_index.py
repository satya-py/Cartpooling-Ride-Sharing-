from app.utils import geohash_utils
from app.services.spatial_index_service import SpatialIndexService


def test_encode_is_deterministic():
    h1 = geohash_utils.encode(22.5726, 88.3639, precision=6)
    h2 = geohash_utils.encode(22.5726, 88.3639, precision=6)
    assert h1 == h2
    assert len(h1) == 6


def test_neighbors_returns_8_cells():
    center = geohash_utils.encode(22.5726, 88.3639, precision=6)
    n = geohash_utils.neighbors(center)
    assert len(n) == 8
    assert center not in n  # neighbors excludes self
    assert len(set(n)) == 8  # all distinct


def test_cells_with_neighbors_includes_self():
    center = geohash_utils.encode(22.5726, 88.3639, precision=6)
    cells = geohash_utils.cells_with_neighbors(center)
    assert center in cells
    assert len(cells) == 9


def test_boundary_point_neighbors_are_adjacent_cells():
    # A point just barely on one side of a cell boundary should still
    # have its true neighboring cell included in the search set.
    lat, lon = 22.6, 88.4
    h = geohash_utils.encode(lat, lon, precision=6)
    min_lat, max_lat, min_lon, max_lon = geohash_utils.decode_bbox(h)

    # nudge just across the eastern boundary into the neighbor cell
    nudged_lon = max_lon + 0.0001
    neighbor_hash = geohash_utils.encode(lat, nudged_lon, precision=6)

    cells = geohash_utils.cells_with_neighbors(h)
    assert neighbor_hash in cells


def test_spatial_index_finds_candidates_near_pickup(sample_store):
    idx = SpatialIndexService(sample_store)
    candidates = idx.candidate_ride_ids((22.5726, 88.3639), (22.60, 88.45))
    # Rides clustered around Kolkata should be found; the far-away
    # ride (R007) should not be.
    assert "R001" in candidates
    assert "R007" not in candidates


def test_spatial_index_empty_area_returns_empty(sample_store):
    idx = SpatialIndexService(sample_store)
    candidates = idx.candidate_ride_ids((0.0, 0.0), (0.1, 0.1))
    assert candidates == set()
