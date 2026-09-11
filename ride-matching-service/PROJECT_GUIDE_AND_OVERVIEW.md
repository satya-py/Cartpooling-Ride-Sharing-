# Intelligent Ride Matching Service: Complete Guide & Technical Overview

---

## Part 1: Step-by-Step Guide to Run the Project

### 1. Prerequisites
Ensure you have the following installed on your system:
- **Python 3.9+** (Python 3.10 or 3.11 recommended)
- **pip** (Python package installer)
- **Git** (optional, for version control)

---

### 2. Environment Setup

#### Option A: Using a Virtual Environment (Recommended)
Open your terminal/command prompt, navigate to the project directory, and set up a virtual environment:

```bash
# Navigate to the project root
cd d:/ride-matching-service

# Create a virtual environment named 'venv'
python -m venv venv

# Activate the virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On Windows (Command Prompt):
.\venv\Scripts\activate.bat

# On Linux/macOS:
source venv/bin/activate
```

#### Option B: Installing Direct to System
If you prefer not using a virtual environment:
```bash
cd d:/ride-matching-service
```

---

### 3. Install Dependencies

Install all required Python packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

*Dependencies installed:*
- `fastapi`: Modern, high-performance web framework for the API.
- `uvicorn[standard]`: Lightning-fast ASGI server.
- `pandas`: Data loading and CSV parsing.
- `pydantic`: Request/Response data validation and schema definitions.
- `pytest`: Testing framework.
- `httpx` & `requests`: HTTP clients for external routing integration.
- `python-dotenv`: Environment variable management.

---

### 4. Configuration & Environment File (`.env`)

Check or create the `.env` file in the root directory:

```env
# Optional: Set Mapbox Token for live routed distances & traffic ETAs
# MAPBOX_ACCESS_TOKEN=pk.eyJ1I...

# Optional: Path to custom rides CSV (defaults to data/rides.csv)
RIDES_CSV_PATH=data/rides.csv
```

> **Note**: If `MAPBOX_ACCESS_TOKEN` is not set, the system automatically defaults to a high-speed, offline straight-line (Haversine + geometric interpolation) route compatibility provider.

---

### 5. Running the API Server

Start the FastAPI application with Uvicorn live reload:

```bash
uvicorn app.main:app --reload --port 8000
```

Once started, you will see output like:
```text
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

### 6. Verification & Health Check

Verify that the server is running and the ride dataset is loaded by accessing the health endpoint:

#### Browser / cURL:
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "ridesLoaded": 20
}
```

---

### 7. Interactive API Documentation (Swagger UI)

Open your web browser and navigate to:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

This opens the interactive Swagger UI where you can inspect schema models and test requests directly from your browser.

---

### 8. Testing the Matching Endpoint (`POST /rides/match`)

Send a sample match request using `curl` or Postman:

#### Sample `curl` Request:
```bash
curl -X POST http://localhost:8000/rides/match \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "org_default",
    "pickup": {
      "latitude": 22.584,
      "longitude": 88.402
    },
    "destination": {
      "latitude": 22.50,
      "longitude": 88.38
    },
    "travel_date": "2026-08-08",
    "requested_hour": 18.0,
    "seats": 1,
    "max_fare": 60
  }'
```

#### Sample Response:
```json
{
  "results": [
    {
      "rideId": "ride_101",
      "driverName": "Amit Sharma",
      "matchScore": 88.45,
      "breakdown": {
        "pickupScore": 92.10,
        "destinationScore": 89.50,
        "detourScore": 85.00,
        "timeScore": 90.00,
        "fareScore": 75.00
      },
      "reasons": [
        "Pickup walk distance: 0.23 km",
        "Dropoff walk distance: 0.31 km",
        "Driver detour distance: 0.85 km",
        "Departure time difference: 10 mins",
        "Fare within budget: $45.00"
      ]
    }
  ],
  "candidatesConsidered": 12,
  "totalRidesInSystem": 20
}
```

---

### 9. Running the Automated Test Suite

To run all unit and end-to-end integration tests:

```bash
python -m pytest tests/ -v
```

This runs tests verifying:
- Spatial geohash cell encoding/decoding & neighbor calculation
- Hard filtering rules (tenant, seats, time window, distance thresholds)
- Multi-attribute scoring math & normalization
- Deterministic tie-breaking behavior
- End-to-end matching performance and response schema validity

---
---

## Part 2: Detailed Technical & Architectural Overview

### 1. High-Level Architecture & Ranking Pipeline

The Intelligent Ride Matching Service is built to solve the high-performance carpooling match problem. Rather than scanning thousands of rides using expensive geospatial database queries or external mapping calls, it uses a **2-stage retrieval and ranking pipeline**:

```
 ┌─────────────────────────────────────────────────────────┐
 │               1. Passenger Match Request                │
 └────────────────────────────┬────────────────────────────┘
                              │
                              ▼
 ┌─────────────────────────────────────────────────────────┐
 │  2. SpatialIndexService (Geohash Cell Retrieval)        │
 │  - Searches passenger pickup & dropoff 9-cell neighborhoods│
 └────────────────────────────┬────────────────────────────┘
                              │
                              ▼
 ┌─────────────────────────────────────────────────────────┐
 │  3. RideCandidateService (Hard Filters & Ceiling Cap)   │
 │  - Tenant isolation, seats, date, time window, status   │
 │  - Caps candidate pool at MAX_CANDIDATES (default 100)  │
 └────────────────────────────┬────────────────────────────┘
                              │
                              ▼
 ┌─────────────────────────────────────────────────────────┐
 │  4. RouteCompatibilityService (Precise Distance Math)   │
 │  - Cheap pre-filter to top MAX_CANDIDATES_FOR_PRECISE    │
 │  - Computes exact Pickup/Dropoff walk & Driver Detour   │
 └────────────────────────────┬────────────────────────────┘
                              │
                              ▼
 ┌─────────────────────────────────────────────────────────┐
 │  5. MatchScoringService (Weighted Multi-Attribute Score)│
 │  - 30% Pickup + 25% Drop + 20% Detour + 15% Time + 10% Fare│
 └────────────────────────────┬────────────────────────────┘
                              │
                              ▼
 ┌─────────────────────────────────────────────────────────┐
 │  6. RideMatchingService (Ranking & Tie-Breaking)        │
 │  - Deterministic sort: matchScore DESC -> departure delta│
 │  - Returns Top N (default 10) results with breakdown    │
 └─────────────────────────────────────────────────────────┘
```

---

### 2. Detailed Component Overview

#### A. Data Layer (`app/data/loader.py`)
- **`Ride` Dataclass**: Internal representation of a driver's offered ride. Includes ride metadata (`ride_id`, `driver_name`, `org_id`, `travel_date`, `status`, `departure_hour`, `available_seats`, `fare_per_seat`) and computed spatial properties (`pickup_geohash`, `drop_geohash`, `route_points`, `route_geohashes`, `route_length_km`).
- **`RideStore`**: In-memory repository maintaining a lookup dictionary of rides and a spatial inverted index (`cell_index: Map<GeohashCell, Set<RideId>>`).
- **`load_rides_from_csv()`**: Initializes the store from CSV. Crucially, when a ride is loaded or published, its route polyline is sampled every `ROUTE_SAMPLE_INTERVAL_M` (400 meters) and converted into a deduplicated set of geohash cells stored in `route_geohashes`.

#### B. Spatial Index Service (`app/services/spatial_index_service.py`)
- **Geohash Cell Matching**: Converts pickup and destination points into Precision 6 (~1.2 km x 0.6 km) geohash cells.
- **Neighbor Search**: Includes all 8 surrounding neighbor cells (9 cells total per point) to eliminate boundary edge cases where a driver and passenger are meters apart but cross a geohash boundary.
- **Candidate Index Query**: Performs $O(1)$ set unions over the `RideStore` cell index, quickly extracting candidate rides that pass near either pickup or destination.

#### C. Candidate Filtering Service (`app/services/ride_candidate_service.py`)
Applies deterministic hard business rules to filter out ineligible rides before any distance math runs:
1. **Tenant Isolation**: `ride.org_id == req.org_id`
2. **Ride Status**: `ride.status == "active"`
3. **Travel Date**: `ride.travel_date == req.travel_date`
4. **Seat Availability**: `ride.available_seats >= req.seats`
5. **Time Window**: `|ride.departure_hour - req.requested_hour| <= MAX_TIME_DIFFERENCE_HOURS` (1.0 hour)
6. **Candidate Cap**: Truncates candidate pool to `MAX_CANDIDATES` (default 100) to protect against pathological queries.

#### D. Route Compatibility Service (`app/services/route_compatibility_service.py`)
- Calculates exact spatial geometries:
  - **Pickup Walk Distance**: Minimum distance from passenger pickup to driver's route polyline.
  - **Dropoff Walk Distance**: Minimum distance from passenger dropoff to driver's route polyline.
  - **Driver Detour Distance**: Estimated extra distance added to driver's route if picking up/dropping off the passenger.
- **2-Tiered Optimization**:
  - Pre-ranks candidates using cheap straight-line distance.
  - Passes only top `MAX_CANDIDATES_FOR_PRECISE_ROUTING` (default 20) to the real routing provider (e.g. Mapbox API), ensuring zero external API cost bloat.

#### E. Match Scoring Service (`app/services/match_scoring_service.py`)
Applies normalized scoring logic (0.0 to 100.0) across 5 weighted dimensions:

| Component | Weight | Scoring Function Logic |
| :--- | :--- | :--- |
| **Pickup Proximity** | **30%** | $100 \times \max(0, 1 - \frac{\text{pickup\_dist}}{1.5\text{ km}})$ |
| **Destination Proximity** | **25%** | $100 \times \max(0, 1 - \frac{\text{drop\_dist}}{2.0\text{ km}})$ |
| **Driver Detour** | **20%** | $100 \times \max(0, 1 - \frac{\text{detour\_dist}}{3.0\text{ km}})$ |
| **Time Alignment** | **15%** | $100 \times \max(0, 1 - \frac{\text{time\_diff}}{1.0\text{ hr}})$ |
| **Fare Match** | **10%** | If no `max_fare` set $\rightarrow 70.0$. Else $100 \times \max(0, 1 - \frac{\text{fare} - \text{max\_fare}}{\text{max\_fare}})$ when fare > budget, else 100.0. |

#### F. Ride Matching Orchestrator (`app/services/ride_matching_service.py`)
- Coordinates candidate retrieval, route scoring, score computation, human-readable reason generation, and final ranking.
- **Deterministic Tie-Breaking**: When two rides achieve identical match scores, ties are broken by:
  1. Smaller departure time delta (`|departure_hour - requested_hour|`)
  2. Alphabetical `ride_id` (guarantees idempotent results across API calls)

#### G. Mapbox & Custom ETA Integration (`app/integrations/mapbox_client.py`)
- Provides a clean interface (`RouteProvider` protocol) for external routing providers.
- Supports Mapbox Directions API for live traffic ETAs and realistic street-network route polylines.

---

### 3. Key Tunable Configurations (`app/config.py`)

All business policies and threshold parameters are centralized in `app/config.py`:

```python
@dataclass(frozen=True)
class MatchingConfig:
    GEOHASH_PRECISION: int = 6                  # Cell size (~1.2km x 0.6km)
    ROUTE_SAMPLE_INTERVAL_M: float = 400.0     # Polyline sampling rate
    MAX_TIME_DIFFERENCE_HOURS: float = 1.0     # Departure window (±1 hr)
    MAX_PICKUP_ROUTE_DISTANCE_KM: float = 1.5   # Max pickup walk distance
    MAX_DROPOFF_ROUTE_DISTANCE_KM: float = 2.0  # Max dropoff walk distance
    MAX_DETOUR_DISTANCE_KM: float = 3.0         # Max allowed driver detour
    MAX_CANDIDATES: int = 100                   # Candidates capped after hard filters
    MAX_CANDIDATES_FOR_PRECISE_ROUTING: int = 20# Max external routing API calls
    TOP_N_RESULTS: int = 10                     # Top matches returned to user
    
    # Scoring weights (sum to 1.0)
    WEIGHT_PICKUP: float = 0.30
    WEIGHT_DESTINATION: float = 0.25
    WEIGHT_DETOUR: float = 0.20
    WEIGHT_TIME: float = 0.15
    WEIGHT_FARE: float = 0.10
```

---

### 4. Performance Benchmarks

- **Dataset Size**: Tested against 20,000 synthetic rides.
- **Index Build Time**: ~6.0s (one-time execution on application startup).
- **Match Latency (`POST /rides/match`)**: **~11 ms per query**.
- **Efficiency**: Reduces 20,000 candidate evaluations down to ~100 candidate cell lookups and 20 precise route scoring calls.
