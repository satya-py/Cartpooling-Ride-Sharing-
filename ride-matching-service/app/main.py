"""
FastAPI Enterprise Carpooling Application.

Provides authentication, ride matching (geohash spatial indexing), ride publishing,
booking requests, driver accept/reject workflow, live tracking support, payment & wallet, admin controls, and reporting.
"""

from __future__ import annotations
import os
import uuid
import sqlite3
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Header, status
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import init_db, get_db_connection
from app.data.loader import load_rides_from_db, Ride
from app.models.schemas import (
    MatchRequest, MatchResponse,
    LoginRequest, RegisterRequest, UserResponse,
    VehicleCreate, VehicleResponse,
    RideCreate, RideDetailResponse,
    BookingCreate, BookingResponse, PaymentRequest,
    WalletRechargeRequest, SavedPlaceCreate,
    EmployeeAccessUpdate, VehicleStatusUpdate, CompanySettingsUpdate
)
from app.services.ride_matching_service import RideMatchingService
from app.services.route_compatibility_service import RouteCompatibilityService, MapboxRouteProvider
from app.integrations import mapbox_client

app = FastAPI(
    title="Enterprise Carpooling & Intelligent Ride Matching Platform",
    version="2.1.0",
    description="Full-stack Enterprise Carpooling API with spatial index matching, driver accept/reject workflow, persistence, wallet & admin controls."
)

# Enable CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database and load rides into RideStore at server startup
init_db()
store = load_rides_from_db()

if mapbox_client.mapbox_configured():
    route_service = RouteCompatibilityService(route_provider=MapboxRouteProvider())
else:
    route_service = RouteCompatibilityService()

matching_service = RideMatchingService(store, route_service=route_service)


# -----------------------------------------------------------------------------
# System & Health Check
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "ridesLoaded": len(store),
        "database": "connected (SQLite carpooling.db)"
    }


# -----------------------------------------------------------------------------
# Intelligent Ride Matching Endpoint (Core Algorithm)
# -----------------------------------------------------------------------------
@app.post("/rides/match", response_model=MatchResponse)
def match_rides(req: MatchRequest):
    if req.seats < 1:
        raise HTTPException(status_code=400, detail="Seats requested must be >= 1")
    return matching_service.match(req)


# -----------------------------------------------------------------------------
# Authentication Endpoints
# -----------------------------------------------------------------------------
@app.post("/api/auth/register", response_model=UserResponse)
def register(req: RegisterRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE email = ?", (req.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="User with this email already exists.")
    
    user_id = f"USR_{uuid.uuid4().hex[:8].upper()}"
    cursor.execute("""
    INSERT INTO users (id, name, email, password_hash, phone, role, department, manager, office_location, platform_access, wallet_balance)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 500.0)
    """, (user_id, req.name, req.email, req.password, req.phone, req.role, req.department, req.manager, req.office_location))
    
    conn.commit()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    return dict(user)


@app.post("/api/auth/login", response_model=UserResponse)
def login(req: LoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? AND password_hash = ?", (req.email, req.password))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if user["platform_access"] != "active":
        raise HTTPException(status_code=403, detail="Platform access has been revoked by Company Administrator.")
    
    return dict(user)


@app.get("/api/auth/me", response_model=UserResponse)
def get_current_user(user_id: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return dict(user)


# -----------------------------------------------------------------------------
# Vehicle Management Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/vehicles", response_model=List[VehicleResponse])
def get_user_vehicles(user_id: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicles WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/vehicles", response_model=VehicleResponse)
def register_vehicle(req: VehicleCreate, user_id: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")
    
    veh_id = f"VEH_{uuid.uuid4().hex[:6].upper()}"
    cursor.execute("""
    INSERT INTO vehicles (id, user_id, driver_name, model, registration_number, seating_capacity, status)
    VALUES (?, ?, ?, ?, ?, ?, 'approved')
    """, (veh_id, user_id, user["name"], req.model, req.registration_number, req.seating_capacity))
    
    conn.commit()
    cursor.execute("SELECT * FROM vehicles WHERE id = ?", (veh_id,))
    veh = cursor.fetchone()
    conn.close()
    return dict(veh)


# -----------------------------------------------------------------------------
# Ride Publishing & Management Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/rides", response_model=List[RideDetailResponse])
def list_rides(status_filter: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if status_filter:
        cursor.execute("SELECT * FROM rides WHERE status = ? ORDER BY created_at DESC", (status_filter,))
    else:
        cursor.execute("SELECT * FROM rides ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/rides/{ride_id}", response_model=RideDetailResponse)
def get_ride(ride_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rides WHERE id = ?", (ride_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Ride not found.")
    return dict(row)


@app.post("/api/rides", response_model=RideDetailResponse)
def create_ride(req: RideCreate, user_id: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")
    
    # Check that driver has at least one approved vehicle
    cursor.execute("SELECT id FROM vehicles WHERE user_id = ? AND status = 'approved'", (user_id,))
    veh = cursor.fetchone()
    if not veh and not req.vehicle_id:
        conn.close()
        raise HTTPException(status_code=400, detail="You must register an approved vehicle before publishing a ride.")
    
    vehicle_id = req.vehicle_id or (veh["id"] if veh else None)
    ride_id = f"R{uuid.uuid4().hex[:6].upper()}"
    
    cursor.execute("""
    INSERT INTO rides (
        id, driver_id, driver_name, vehicle_id, org_id,
        pickup_name, pickup_lat, pickup_lon,
        drop_name, drop_lat, drop_lon,
        travel_date, departure_hour, available_seats, fare_per_seat, status
    ) VALUES (?, ?, ?, ?, 'ORG_KOL_001', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
    """, (
        ride_id, user_id, user["name"], vehicle_id,
        req.pickup_name, req.pickup_lat, req.pickup_lon,
        req.drop_name, req.drop_lat, req.drop_lon,
        req.travel_date, req.departure_hour, req.available_seats, req.fare_per_seat
    ))
    conn.commit()
    
    # Index new ride dynamically into in-memory RideStore
    new_ride_obj = Ride(
        ride_id=ride_id,
        driver_name=user["name"],
        org_id="ORG_KOL_001",
        travel_date=req.travel_date,
        status="active",
        pickup=(req.pickup_lat, req.pickup_lon),
        drop=(req.drop_lat, req.drop_lon),
        departure_hour=req.departure_hour,
        available_seats=req.available_seats,
        fare_per_seat=req.fare_per_seat
    )
    store.add_ride(new_ride_obj)
    
    cursor.execute("SELECT * FROM rides WHERE id = ?", (ride_id,))
    ride_row = cursor.fetchone()
    conn.close()
    return dict(ride_row)


@app.get("/api/rides/{ride_id}/riders")
def show_riders(ride_id: str):
    """Show all riders (accepted or requested) for a specific ride."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT b.id as booking_id, b.passenger_id, b.passenger_name, b.seats_booked, b.status, b.pickup_name, b.drop_name, b.total_fare, b.created_at
    FROM bookings b
    WHERE b.ride_id = ?
    ORDER BY b.created_at DESC
    """, (ride_id,))
    riders = cursor.fetchall()
    conn.close()
    return [dict(r) for r in riders]


# -----------------------------------------------------------------------------
# Booking / Trip Endpoints (With Accept / Reject & Overbooking Prevention)
# -----------------------------------------------------------------------------
@app.post("/api/rides/{ride_id}/book", response_model=BookingResponse)
def book_ride(ride_id: str, req: BookingCreate, user_id: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM rides WHERE id = ?", (ride_id,))
    ride = cursor.fetchone()
    if not ride:
        conn.close()
        raise HTTPException(status_code=404, detail="Ride not found.")
    
    if ride["driver_id"] == user_id:
        conn.close()
        raise HTTPException(status_code=400, detail="Driver cannot book their own offered ride.")

    if ride["status"] != "active":
        conn.close()
        raise HTTPException(status_code=400, detail=f"Ride is not active (status: {ride['status']}).")
    
    # 1. Prevent Duplicate Requests
    cursor.execute("""
    SELECT id FROM bookings WHERE ride_id = ? AND passenger_id = ? AND status IN ('requested', 'accepted', 'booked', 'started')
    """, (ride_id, user_id))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Duplicate request prevented: You already have a pending or active booking for this ride.")

    # 2. Check Available Seats
    if ride["available_seats"] < req.seats_booked:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Overbooking prevented: Only {ride['available_seats']} seat(s) available.")
    
    cursor.execute("SELECT name FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Passenger user not found.")
    
    booking_id = f"BK_{uuid.uuid4().hex[:6].upper()}"
    total_fare = ride["fare_per_seat"] * req.seats_booked
    
    # Create booking request in 'requested' status (Pending Driver Approval)
    cursor.execute("""
    INSERT INTO bookings (id, ride_id, passenger_id, passenger_name, seats_booked, status, pickup_name, drop_name, total_fare, payment_method, payment_status)
    VALUES (?, ?, ?, ?, ?, 'requested', ?, ?, ?, 'wallet', 'pending')
    """, (booking_id, ride_id, user_id, user["name"], req.seats_booked, req.pickup_name, req.drop_name, total_fare))
    
    conn.commit()
    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    booking = cursor.fetchone()
    conn.close()
    return dict(booking)


@app.post("/api/bookings/{booking_id}/accept", response_model=BookingResponse)
def accept_booking(booking_id: str, driver_id: str = Query(...)):
    """Driver accepts a passenger's ride request. Updates seats upon acceptance."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT b.*, r.driver_id, r.available_seats, r.id as ride_id
    FROM bookings b
    JOIN rides r ON b.ride_id = r.id
    WHERE b.id = ?
    """, (booking_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Booking request not found.")
    
    # Authorization Enforcement: Only the ride's driver can accept
    if row["driver_id"] != driver_id:
        conn.close()
        raise HTTPException(status_code=403, detail="Authorization denied: Only the driver can accept ride requests.")
    
    if row["status"] == "accepted" or row["status"] == "booked":
        conn.close()
        raise HTTPException(status_code=400, detail="Booking is already accepted.")

    # Overbooking Prevention Check
    seats_needed = row["seats_booked"]
    current_seats = row["available_seats"]
    if current_seats < seats_needed:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Overbooking prevented: Only {current_seats} seats remain.")

    # Update seats after acceptance
    new_seats = current_seats - seats_needed
    cursor.execute("UPDATE rides SET available_seats = ? WHERE id = ?", (new_seats, row["ride_id"]))
    cursor.execute("UPDATE bookings SET status = 'accepted' WHERE id = ?", (booking_id,))
    conn.commit()

    # Update in-memory spatial store
    store.update_ride_seats(row["ride_id"], new_seats)

    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    updated_booking = cursor.fetchone()
    conn.close()
    return dict(updated_booking)


@app.post("/api/bookings/{booking_id}/reject", response_model=BookingResponse)
def reject_booking(booking_id: str, driver_id: str = Query(...)):
    """Driver rejects a passenger's ride request."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT b.*, r.driver_id
    FROM bookings b
    JOIN rides r ON b.ride_id = r.id
    WHERE b.id = ?
    """, (booking_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Booking request not found.")
    
    # Authorization Enforcement
    if row["driver_id"] != driver_id:
        conn.close()
        raise HTTPException(status_code=403, detail="Authorization denied: Only the driver can reject ride requests.")
    
    cursor.execute("UPDATE bookings SET status = 'rejected' WHERE id = ?", (booking_id,))
    conn.commit()

    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    updated_booking = cursor.fetchone()
    conn.close()
    return dict(updated_booking)


@app.get("/api/trips", response_model=List[BookingResponse])
def get_user_trips(user_id: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT b.* FROM bookings b
    JOIN rides r ON b.ride_id = r.id
    WHERE b.passenger_id = ? OR r.driver_id = ?
    ORDER BY b.created_at DESC
    """, (user_id, user_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/trips/{booking_id}", response_model=BookingResponse)
def get_trip_detail(booking_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    booking = cursor.fetchone()
    conn.close()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    return dict(booking)


@app.patch("/api/trips/{booking_id}/status")
def update_trip_status(booking_id: str, new_status: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", (new_status, booking_id))
    conn.commit()
    
    cursor.execute("SELECT ride_id FROM bookings WHERE id = ?", (booking_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE rides SET status = ? WHERE id = ?", (new_status, row["ride_id"]))
        conn.commit()
        store.update_ride_status(row["ride_id"], new_status)
        
    conn.close()
    return {"status": "success", "booking_id": booking_id, "new_status": new_status}


@app.post("/api/trips/{booking_id}/pay")
def pay_trip(booking_id: str, req: PaymentRequest, user_id: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    booking = cursor.fetchone()
    if not booking:
        conn.close()
        raise HTTPException(status_code=404, detail="Booking not found.")
    
    total_fare = booking["total_fare"]
    
    if req.payment_method == "wallet":
        cursor.execute("SELECT wallet_balance FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user or user["wallet_balance"] < total_fare:
            conn.close()
            raise HTTPException(status_code=400, detail="Insufficient wallet balance. Please recharge your wallet.")
        
        # Deduct wallet balance
        new_balance = user["wallet_balance"] - total_fare
        cursor.execute("UPDATE users SET wallet_balance = ? WHERE id = ?", (new_balance, user_id))
        
    cursor.execute("""
    UPDATE bookings SET payment_method = ?, payment_status = 'completed', status = 'completed' WHERE id = ?
    """, (req.payment_method, booking_id))
    
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Payment of ₹{total_fare:.2f} completed via {req.payment_method.upper()}."}


# -----------------------------------------------------------------------------
# Wallet & Saved Places Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/wallet")
def get_wallet(user_id: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT wallet_balance FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"user_id": user_id, "wallet_balance": user["wallet_balance"]}


@app.post("/api/wallet/recharge")
def recharge_wallet(req: WalletRechargeRequest, user_id: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT wallet_balance FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")
    
    new_balance = user["wallet_balance"] + req.amount
    cursor.execute("UPDATE users SET wallet_balance = ? WHERE id = ?", (new_balance, user_id))
    conn.commit()
    conn.close()
    return {"status": "success", "wallet_balance": new_balance}


@app.get("/api/saved-places")
def get_saved_places(user_id: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM saved_places WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/saved-places")
def add_saved_place(req: SavedPlaceCreate, user_id: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    place_id = f"PLC_{uuid.uuid4().hex[:6].upper()}"
    cursor.execute("""
    INSERT INTO saved_places (id, user_id, name, address, latitude, longitude)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (place_id, user_id, req.name, req.address, req.latitude, req.longitude))
    conn.commit()
    conn.close()
    return {"status": "success", "place_id": place_id}


# -----------------------------------------------------------------------------
# Company Administration Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/admin/employees")
def get_all_employees():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone, role, department, manager, office_location, platform_access FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.patch("/api/admin/employees/{user_id}")
def update_employee_access(user_id: str, req: EmployeeAccessUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET platform_access = ? WHERE id = ?", (req.platform_access, user_id))
    conn.commit()
    conn.close()
    return {"status": "success", "user_id": user_id, "platform_access": req.platform_access}


@app.get("/api/admin/vehicles")
def get_all_admin_vehicles():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicles")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.patch("/api/admin/vehicles/{vehicle_id}")
def update_vehicle_status(vehicle_id: str, req: VehicleStatusUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE vehicles SET status = ? WHERE id = ?", (req.status, vehicle_id))
    conn.commit()
    conn.close()
    return {"status": "success", "vehicle_id": vehicle_id, "status": req.status}


@app.get("/api/admin/settings")
def get_company_settings(org_id: str = "ORG_KOL_001"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM company_settings WHERE org_id = ?", (org_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {
            "org_id": org_id,
            "company_name": "Acme Corp Kolkata",
            "registered_office": "Sector V, Salt Lake, Kolkata",
            "industry": "Technology",
            "admin_contact": "admin@acmecorp.com",
            "fuel_cost_per_liter": 102.50,
            "travel_cost_per_km": 12.00,
            "default_policy": "Standard Enterprise Carpooling Policy"
        }
    return dict(row)


@app.post("/api/admin/settings")
def update_company_settings(req: CompanySettingsUpdate, org_id: str = "ORG_KOL_001"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO company_settings (org_id, company_name, registered_office, industry, admin_contact, fuel_cost_per_liter, travel_cost_per_km, default_policy)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(org_id) DO UPDATE SET
        company_name=excluded.company_name,
        registered_office=excluded.registered_office,
        industry=excluded.industry,
        admin_contact=excluded.admin_contact,
        fuel_cost_per_liter=excluded.fuel_cost_per_liter,
        travel_cost_per_km=excluded.travel_cost_per_km,
        default_policy=excluded.default_policy
    """, (org_id, req.company_name, req.registered_office, req.industry, req.admin_contact, req.fuel_cost_per_liter, req.travel_cost_per_km, req.default_policy))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Company settings updated."}


# -----------------------------------------------------------------------------
# Reports & Analytics Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/reports")
def get_reports():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM bookings WHERE status IN ('completed', 'accepted', 'booked')")
    total_trips = cursor.fetchone()["count"] or 18
    
    cursor.execute("SELECT COUNT(*) as count FROM rides")
    total_rides = cursor.fetchone()["count"] or 20
    
    total_distance = total_trips * 14.5
    fuel_saved = round(total_distance / 12.5, 1)
    co2_reduction = round(fuel_saved * 2.31, 1)
    total_savings = round(total_distance * 8.5, 2)
    
    conn.close()
    return {
        "summary": {
            "total_trips": total_trips,
            "total_rides_offered": total_rides,
            "total_distance_km": round(total_distance, 1),
            "fuel_saved_liters": fuel_saved,
            "co2_reduction_kg": co2_reduction,
            "total_cost_savings": total_savings,
            "avg_cost_per_km": 12.00
        },
        "fuel_efficiency_trend": [
            {"month": "May", "km_per_liter": 11.2},
            {"month": "Jun", "km_per_liter": 12.0},
            {"month": "Jul", "km_per_liter": 12.5},
            {"month": "Aug", "km_per_liter": 13.1}
        ],
        "emission_reduction_by_dept": [
            {"department": "Engineering", "co2_saved_kg": 142.5},
            {"department": "Product", "co2_saved_kg": 98.0},
            {"department": "Operations", "co2_saved_kg": 75.2},
            {"department": "HR", "co2_saved_kg": 45.8}
        ]
    }
