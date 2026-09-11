"""
Ride data model + loader.

In a real project this file is the thing you REPLACE with your actual
ORM model / repository (e.g. SQLAlchemy Ride model, or your existing
Mongo/Postgres access layer). Everything downstream (spatial index,
candidate service, scoring) only depends on the `Ride` dataclass
below, not on how it was loaded — so swapping CSV -> real DB later is
a one-file change.

At publish time (ride creation), each ride's route is sampled into a
deduplicated set of geohash cells (`route_geohashes`). This is what
makes candidate retrieval possible without ever comparing every ride
to the passenger — see spatial_index_service.py.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple
import os
import pandas as pd

from app.config import config
from app.utils import geohash_utils, geo_utils

Point = Tuple[float, float]


@dataclass
class Ride:
    ride_id: str
    driver_name: str
    org_id: str
    travel_date: str
    status: str  # "active" | "cancelled" | "completed" ...
    pickup: Point
    drop: Point
    departure_hour: float
    available_seats: int
    fare_per_seat: float

    # Derived / spatial fields, computed once at publish time
    pickup_geohash: str = field(init=False)
    drop_geohash: str = field(init=False)
    route_points: List[Point] = field(init=False)
    route_geohashes: Set[str] = field(init=False)
    route_length_km: float = field(init=False)

    def __post_init__(self):
        precision = config.GEOHASH_PRECISION
        self.pickup_geohash = geohash_utils.encode(*self.pickup, precision=precision)
        self.drop_geohash = geohash_utils.encode(*self.drop, precision=precision)

        # Route geometry: swap `interpolate_points` for a real polyline
        # from your mapping provider / existing route module if available.
        self.route_points = geo_utils.interpolate_points(
            self.pickup, self.drop, config.ROUTE_SAMPLE_INTERVAL_M
        )
        self.route_geohashes = {
            geohash_utils.encode(lat, lon, precision=precision)
            for lat, lon in self.route_points
        }
        self.route_length_km = geo_utils.route_length_km(self.route_points)


class RideStore:
    """In-memory ride store + geohash cell -> ride_id index.
    Keeps synchronised with SQLite database for fast O(cells) spatial candidate matching.
    """

    def __init__(self):
        self.rides: dict[str, Ride] = {}
        self.cell_index: dict[str, Set[str]] = {}

    def add_ride(self, ride: Ride) -> None:
        self.rides[ride.ride_id] = ride
        for cell in ride.route_geohashes:
            self.cell_index.setdefault(cell, set()).add(ride.ride_id)

    def update_ride_seats(self, ride_id: str, new_seats: int) -> None:
        if ride_id in self.rides:
            self.rides[ride_id].available_seats = new_seats

    def update_ride_status(self, ride_id: str, status: str) -> None:
        if ride_id in self.rides:
            self.rides[ride_id].status = status

    def get(self, ride_id: str) -> Optional[Ride]:
        return self.rides.get(ride_id)

    def all_ride_ids_in_cells(self, cells: List[str]) -> Set[str]:
        result: Set[str] = set()
        for cell in cells:
            result |= self.cell_index.get(cell, set())
        return result

    def __len__(self) -> int:
        return len(self.rides)


def load_rides_from_db() -> RideStore:
    """Load all rides from SQLite database into RideStore."""
    from app.db.database import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rides")
    rows = cursor.fetchall()
    conn.close()

    store = RideStore()
    for row in rows:
        ride = Ride(
            ride_id=str(row["id"]),
            driver_name=str(row["driver_name"]),
            org_id=str(row["org_id"]),
            travel_date=str(row["travel_date"]),
            status=str(row["status"]),
            pickup=(float(row["pickup_lat"]), float(row["pickup_lon"])),
            drop=(float(row["drop_lat"]), float(row["drop_lon"])),
            departure_hour=float(row["departure_hour"]),
            available_seats=int(row["available_seats"]),
            fare_per_seat=float(row["fare_per_seat"]),
        )
        store.add_ride(ride)
    return store


def load_rides_from_csv(
    csv_path: str,
    default_org_id: str = os.environ.get("DEFAULT_ORG_ID", "ORG_KOL_001"),
    default_travel_date: str = os.environ.get("DEFAULT_TRAVEL_DATE", "2026-08-10"),
    default_status: str = "active",
) -> RideStore:
    """Load rides from CSV format into RideStore."""
    df = pd.read_csv(csv_path)
    store = RideStore()

    for _, row in df.iterrows():
        ride = Ride(
            ride_id=str(row["ride_id"]),
            driver_name=str(row["driver_name"]),
            org_id=str(row.get("org_id", default_org_id)),
            travel_date=str(row.get("travel_date", default_travel_date)),
            status=str(row.get("status", default_status)),
            pickup=(float(row["pickup_lat"]), float(row["pickup_lon"])),
            drop=(float(row["drop_lat"]), float(row["drop_lon"])),
            departure_hour=float(row["departure_hour"]),
            available_seats=int(row["available_seats"]),
            fare_per_seat=float(row["fare_per_seat"]),
        )
        store.add_ride(ride)

    return store

