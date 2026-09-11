# Intelligent Ride Matching Service

Implements the ranking pipeline from the problem statement:

```
Passenger Search
  → Hard Filters
  → Geohash Candidate Retrieval
  → Candidate Reduction
  → Precise Route/Distance Calculations
  → Match Score
  → Ranking
  → Top N Results
```

## Folder structure

```
ride-matching-service/
├── app/
│   ├── main.py                          # FastAPI app, POST /rides/match
│   ├── config.py                        # ALL tunable thresholds live here
│   ├── models/
│   │   └── schemas.py                   # API request/response (Pydantic)
│   ├── data/
│   │   └── loader.py                    # Ride model + CSV loader + RideStore (swap for real DB later)
│   ├── services/
│   │   ├── spatial_index_service.py     # SpatialIndexService  (geohash cell lookup only)
│   │   ├── ride_candidate_service.py    # RideCandidateService (hard filters + candidate cap)
│   │   ├── route_compatibility_service.py  # RouteCompatibilityService (precise distances/detour)
│   │   ├── match_scoring_service.py     # MatchScoringService  (pure scoring functions)
│   │   └── ride_matching_service.py     # RideMatchingService  (orchestrator + ranking/tie-break)
│   └── utils/
│       ├── geohash_utils.py             # dependency-free geohash encode/decode/neighbors
│       └── geo_utils.py                 # haversine, interpolation, point-to-route distance
├── tests/
│   ├── conftest.py                      # 12-ride synthetic fixture (edge cases baked in)
│   ├── test_spatial_index.py
│   ├── test_candidate_retrieval.py
│   ├── test_scoring.py
│   └── test_matching_e2e.py
├── data/
│   └── rides.csv                        # sample data — REPLACE with your 20k-row file
└── requirements.txt
```

## Why this structure (for the architecture writeup)

- **`utils/`** — pure math, zero dependencies on the rest of the app. Fully unit-testable in isolation.
- **`data/loader.py`** — the ONLY file that knows about CSV/pandas. Swap this for a real
  SQLAlchemy/Mongo repository later; `Ride` and `RideStore`'s public interface stay the same,
  so nothing above it needs to change.
- **`spatial_index_service.py`** — does ONLY geohash cell math. Never computes real distance.
  This is what makes candidate retrieval O(cells) instead of O(all rides).
- **`ride_candidate_service.py`** — the only place allowed to "touch" many rides. Applies
  tenant/date/status/seats/time hard filters, then caps the result at `MAX_CANDIDATES`.
- **`route_compatibility_service.py`** — the only place doing expensive precise math (point-to-route
  distance, detour), and it only ever runs on the small candidate set. This is also the single
  integration point for your existing ETA/route-prediction module — implement the `RouteProvider`
  protocol and pass it into `RideMatchingService`.
- **`match_scoring_service.py`** — pure functions, no I/O. Easiest file to unit test exhaustively.
- **`ride_matching_service.py`** — orchestrates everything + deterministic tie-breaking. This is
  the only service `main.py` talks to.

## Setup

```bash
cd ride-matching-service
pip install -r requirements.txt --break-system-packages   # or use a venv

# replace data/rides.csv with your full 20,000-row CSV (same column names)
uvicorn app.main:app --reload --port 8000
```

## Try it

```bash
curl -X POST http://localhost:8000/rides/match \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "org_default",
    "pickup": {"latitude": 22.584, "longitude": 88.402},
    "destination": {"latitude": 22.50, "longitude": 88.38},
    "travel_date": "2026-08-08",
    "requested_hour": 18.0,
    "seats": 1,
    "max_fare": 60
  }'
```

## Run tests

```bash
python -m pytest tests/ -v
```

37 tests covering geohash correctness, boundary cases, tenant isolation, seat/status/date/time
hard filters, scoring math, weighted final score, empty results, zero-length routes, and
deterministic tie-breaking.

## Plugging in your existing ETA/route module

You mentioned you've already built ETA-mean prediction + drop→pickup routing. Wire it in at
**one place**: `app/services/route_compatibility_service.py`. Implement a class matching the
`RouteProvider` protocol:

```python
class MyRealRouteProvider:
    def get_route_points(self, ride: Ride) -> list[tuple[float, float]]:
        return my_eta_module.get_route(ride.pickup, ride.drop)   # real polyline

    def estimate_route_distance_km(self, points) -> float:
        return my_eta_module.route_distance(points)
```

Then in `main.py`:

```python
route_service = RouteCompatibilityService(route_provider=MyRealRouteProvider())
matching_service = RideMatchingService(store, route_service=route_service)
```

Everything else (geohash indexing, filters, scoring, ranking, API) is unaffected — the fallback
straight-line provider is only used until this is wired in.

## Why Geohash is only used for candidate retrieval, not final distance

Geohash cells are rectangular and their "closeness" doesn't equal real-world distance —
two points can share a geohash prefix and still be kilometers apart across a cell boundary
(handled here by searching the 8 neighbor cells too), or be geographically close but fall in
different cells. So geohash is used purely to shrink "20,000 rides" down to "~dozens of rides
whose route passes near this area" cheaply (dictionary lookup, no math). Once that small set
exists, real haversine/point-to-route/detour math (in `route_compatibility_service.py`) decides
the actual score — this two-stage design is what makes the service scale to millions of rides
without scanning the table or calling a routing API per-ride.

## Benchmark (synthetic 20,000-ride dataset)

Loading 20k rides + building the route-geohash index: ~6s (one-time, at data-load/publish time).
A single `/rides/match` query against those 20,000 rides: **~11ms**, narrowed to exactly
`MAX_CANDIDATES=100` candidates via geohash lookup before any precise math runs — never a full
table scan.
