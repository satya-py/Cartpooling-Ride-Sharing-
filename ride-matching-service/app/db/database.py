"""
SQLite Database Layer for Carpooling Platform.

Manages tables for users, vehicles, rides, bookings, saved places, and company settings.
Handles initialization, seeding from CSV/defaults, and persistence across server restarts.
"""

import os
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join("data", "carpooling.db"))


def get_db_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(csv_path: str = os.path.join("data", "rides.csv")):
    """Initialize SQLite database tables and seed initial data if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        phone TEXT,
        role TEXT NOT NULL DEFAULT 'employee',
        department TEXT,
        manager TEXT,
        office_location TEXT,
        platform_access TEXT NOT NULL DEFAULT 'active',
        wallet_balance REAL NOT NULL DEFAULT 500.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Vehicles table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicles (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        driver_name TEXT NOT NULL,
        model TEXT NOT NULL,
        registration_number TEXT UNIQUE NOT NULL,
        seating_capacity INTEGER NOT NULL DEFAULT 4,
        status TEXT NOT NULL DEFAULT 'approved',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)

    # 3. Rides table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rides (
        id TEXT PRIMARY KEY,
        driver_id TEXT NOT NULL,
        driver_name TEXT NOT NULL,
        vehicle_id TEXT,
        org_id TEXT NOT NULL DEFAULT 'ORG_KOL_001',
        pickup_name TEXT NOT NULL,
        pickup_lat REAL NOT NULL,
        pickup_lon REAL NOT NULL,
        drop_name TEXT NOT NULL,
        drop_lat REAL NOT NULL,
        drop_lon REAL NOT NULL,
        travel_date TEXT NOT NULL,
        departure_hour REAL NOT NULL,
        available_seats INTEGER NOT NULL,
        fare_per_seat REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. Bookings / Trips table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id TEXT PRIMARY KEY,
        ride_id TEXT NOT NULL,
        passenger_id TEXT NOT NULL,
        passenger_name TEXT NOT NULL,
        seats_booked INTEGER NOT NULL DEFAULT 1,
        status TEXT NOT NULL DEFAULT 'booked',
        pickup_name TEXT NOT NULL,
        drop_name TEXT NOT NULL,
        total_fare REAL NOT NULL,
        payment_method TEXT DEFAULT 'wallet',
        payment_status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ride_id) REFERENCES rides(id),
        FOREIGN KEY (passenger_id) REFERENCES users(id)
    );
    """)

    # 5. Saved Places table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_places (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        address TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)

    # 6. Company Settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company_settings (
        org_id TEXT PRIMARY KEY,
        company_name TEXT NOT NULL,
        registered_office TEXT NOT NULL,
        industry TEXT NOT NULL,
        admin_contact TEXT NOT NULL,
        fuel_cost_per_liter REAL NOT NULL DEFAULT 102.50,
        travel_cost_per_km REAL NOT NULL DEFAULT 12.00,
        default_policy TEXT NOT NULL DEFAULT 'Standard Enterprise Carpooling Policy'
    );
    """)

    conn.commit()

    # Seed Default Data if users table is empty
    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()["count"] == 0:
        _seed_default_users(cursor)

    cursor.execute("SELECT COUNT(*) as count FROM company_settings")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("""
        INSERT INTO company_settings (org_id, company_name, registered_office, industry, admin_contact, fuel_cost_per_liter, travel_cost_per_km, default_policy)
        VALUES ('ORG_KOL_001', 'Acme Corp Kolkata', 'Sector V, Salt Lake, Kolkata', 'Technology', 'admin@acmecorp.com', 102.50, 12.00, 'Employees are encouraged to share rides for commutes > 3km.')
        """)

    # Seed Rides from CSV if rides table is empty
    cursor.execute("SELECT COUNT(*) as count FROM rides")
    if cursor.fetchone()["count"] == 0 and os.path.exists(csv_path):
        _seed_rides_from_csv(cursor, csv_path)

    conn.commit()
    conn.close()


def _seed_default_users(cursor: sqlite3.Cursor):
    """Seed initial default admin and employee accounts."""
    users_data = [
        ("USR_ADMIN_01", "Admin User", "admin@org.com", "admin123", "+91 9876543210", "admin", "Operations", "CEO", "Kolkata HQ", "active", 1000.0),
        ("USR_EMP_01", "Amit Sharma", "amit@org.com", "user123", "+91 9876543211", "employee", "Engineering", "Rakesh Singh", "Kolkata Tech Park", "active", 500.0),
        ("USR_EMP_02", "Chanchal Ghosh", "chanchal@org.com", "user123", "+91 9876543212", "employee", "Product", "Suman Ray", "Kolkata Sector V", "active", 450.0),
        ("USR_EMP_03", "Priya Nair", "priya@org.com", "user123", "+91 9876543213", "employee", "HR", "A. Das", "Smart City Center", "active", 600.0),
    ]

    for u in users_data:
        cursor.execute("""
        INSERT INTO users (id, name, email, password_hash, phone, role, department, manager, office_location, platform_access, wallet_balance)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, u)

    vehicles_data = [
        ("VEH_01", "USR_EMP_01", "Amit Sharma", "Honda City", "WB-02-AB-1234", 4, "approved"),
        ("VEH_02", "USR_EMP_02", "Chanchal Ghosh", "Hyundai i20", "WB-06-CD-5678", 3, "approved"),
        ("VEH_03", "USR_EMP_03", "Priya Nair", "Maruti Swift", "WB-12-EF-9012", 4, "approved"),
    ]

    for v in vehicles_data:
        cursor.execute("""
        INSERT INTO vehicles (id, user_id, driver_name, model, registration_number, seating_capacity, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, v)

    places_data = [
        ("PLC_01", "USR_EMP_01", "Home", "New Town Action Area 1, Kolkata", 22.584, 88.402),
        ("PLC_02", "USR_EMP_01", "Office", "Sector V, Salt Lake, Kolkata", 22.570, 88.435),
        ("PLC_03", "USR_EMP_02", "Home", "Salt Lake Gate 1, Kolkata", 22.590, 88.410),
    ]

    for p in places_data:
        cursor.execute("""
        INSERT INTO saved_places (id, user_id, name, address, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?)
        """, p)


def _seed_rides_from_csv(cursor: sqlite3.Cursor, csv_path: str):
    """Seed rides table from the CSV file."""
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        ride_id = str(row["ride_id"])
        driver_name = str(row["driver_name"])
        pickup_lat = float(row["pickup_lat"])
        pickup_lon = float(row["pickup_lon"])
        drop_lat = float(row["drop_lat"])
        drop_lon = float(row["drop_lon"])
        departure_hour = float(row["departure_hour"])
        seats = int(row["available_seats"])
        fare = float(row["fare_per_seat"])

        cursor.execute("""
        INSERT INTO rides (
            id, driver_id, driver_name, vehicle_id, org_id,
            pickup_name, pickup_lat, pickup_lon,
            drop_name, drop_lat, drop_lon,
            travel_date, departure_hour, available_seats, fare_per_seat, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ride_id,
            "USR_EMP_01" if driver_name == "Amit Sharma" else "USR_EMP_02",
            driver_name,
            "VEH_01",
            "ORG_KOL_001",
            f"Pickup Point ({pickup_lat:.3f}, {pickup_lon:.3f})",
            pickup_lat,
            pickup_lon,
            f"Destination ({drop_lat:.3f}, {drop_lon:.3f})",
            drop_lat,
            drop_lon,
            "2026-08-10",
            departure_hour,
            seats,
            fare,
            "active"
        ))
