"""
Tests for API endpoints, Driver Accept/Reject workflow, and SQLite database persistence.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["ridesLoaded"] > 0


def test_auth_login_and_register():
    login_resp = client.post("/api/auth/login", json={"email": "admin@org.com", "password": "admin123"})
    assert login_resp.status_code == 200
    admin_user = login_resp.json()
    assert admin_user["role"] == "admin"
    assert admin_user["name"] == "Admin User"

    unique_email = f"testemp_{uuid.uuid4().hex[:6]}@org.com"
    reg_resp = client.post("/api/auth/register", json={
        "name": "Test Employee",
        "email": unique_email,
        "password": "pass123",
        "phone": "+91 9999999999",
        "department": "Engineering",
        "manager": "Lead",
        "office_location": "Building A"
    })
    assert reg_resp.status_code == 200
    emp_user = reg_resp.json()
    assert emp_user["email"] == unique_email
    assert emp_user["wallet_balance"] == 500.0


def test_vehicle_registration():
    login_resp = client.post("/api/auth/login", json={"email": "amit@org.com", "password": "user123"})
    user_id = login_resp.json()["id"]

    reg_no = f"WB-99-{uuid.uuid4().hex[:4].upper()}"
    veh_resp = client.post(f"/api/vehicles?user_id={user_id}", json={
        "model": "Honda City",
        "registration_number": reg_no,
        "seating_capacity": 4
    })
    assert veh_resp.status_code == 200
    veh = veh_resp.json()
    assert veh["registration_number"] == reg_no


def test_ride_creation_and_driver_accept_reject_workflow():
    # 1. Driver Amit creates a ride with 1 seat
    driver_resp = client.post("/api/auth/login", json={"email": "amit@org.com", "password": "user123"})
    driver_id = driver_resp.json()["id"]

    create_resp = client.post(f"/api/rides?user_id={driver_id}", json={
        "pickup_name": "New Town Clock Tower",
        "pickup_lat": 22.585,
        "pickup_lon": 88.450,
        "drop_name": "Park Street Kolkata",
        "drop_lat": 22.550,
        "drop_lon": 88.350,
        "travel_date": "2026-08-10",
        "departure_hour": 18.0,
        "available_seats": 1,
        "fare_per_seat": 60.0
    })
    assert create_resp.status_code == 200
    ride_id = create_resp.json()["id"]

    # 2. Passenger Chanchal sends a booking request
    pass_resp = client.post("/api/auth/login", json={"email": "chanchal@org.com", "password": "user123"})
    passenger_id = pass_resp.json()["id"]

    book_resp = client.post(f"/api/rides/{ride_id}/book?user_id={passenger_id}", json={
        "seats_booked": 1,
        "pickup_name": "New Town",
        "drop_name": "Park Street"
    })
    assert book_resp.status_code == 200
    booking_id = book_resp.json()["id"]
    assert book_resp.json()["status"] == "requested"

    # 3. Test Duplicate Request Prevention
    dup_resp = client.post(f"/api/rides/{ride_id}/book?user_id={passenger_id}", json={
        "seats_booked": 1,
        "pickup_name": "New Town",
        "drop_name": "Park Street"
    })
    assert dup_resp.status_code == 400
    assert "duplicate request prevented" in dup_resp.json()["detail"].lower()

    # 4. Test Authorization Enforcement: Non-driver trying to accept
    unauth_resp = client.post(f"/api/bookings/{booking_id}/accept?driver_id={passenger_id}")
    assert unauth_resp.status_code == 403
    assert "authorization denied" in unauth_resp.json()["detail"].lower()

    # 5. Driver Amit accepts booking -> available seats updated after acceptance
    accept_resp = client.post(f"/api/bookings/{booking_id}/accept?driver_id={driver_id}")
    assert accept_resp.status_code == 200
    assert accept_resp.json()["status"] == "accepted"

    # Verify ride available_seats updated to 0
    ride_detail = client.get(f"/api/rides/{ride_id}").json()
    assert ride_detail["available_seats"] == 0

    # 6. Test Overbooking Prevention for second passenger
    pass2_email = f"pass2_{uuid.uuid4().hex[:6]}@org.com"
    reg2 = client.post("/api/auth/register", json={
        "name": "Priya", "email": pass2_email, "password": "pass", "phone": "123",
        "department": "IT", "manager": "M", "office_location": "O"
    }).json()
    
    overbook_resp = client.post(f"/api/rides/{ride_id}/book?user_id={reg2['id']}", json={
        "seats_booked": 1, "pickup_name": "P", "drop_name": "D"
    })
    assert overbook_resp.status_code == 400
    assert "overbooking prevented" in overbook_resp.json()["detail"].lower()

    # 7. Test Show Riders API
    riders_resp = client.get(f"/api/rides/{ride_id}/riders")
    assert riders_resp.status_code == 200
    riders = riders_resp.json()
    assert len(riders) == 1
    assert riders[0]["passenger_name"] == "Chanchal Ghosh"


def test_wallet_recharge():
    pass_resp = client.post("/api/auth/login", json={"email": "chanchal@org.com", "password": "user123"})
    user_id = pass_resp.json()["id"]

    initial_bal = client.get(f"/api/wallet?user_id={user_id}").json()["wallet_balance"]
    recharge_resp = client.post(f"/api/wallet/recharge?user_id={user_id}", json={"amount": 200.0})
    assert recharge_resp.status_code == 200
    assert recharge_resp.json()["wallet_balance"] == initial_bal + 200.0


def test_admin_endpoints():
    emps_resp = client.get("/api/admin/employees")
    assert emps_resp.status_code == 200

    vehs_resp = client.get("/api/admin/vehicles")
    assert vehs_resp.status_code == 200

    settings_resp = client.get("/api/admin/settings")
    assert settings_resp.status_code == 200


def test_reports_endpoint():
    reports_resp = client.get("/api/reports")
    assert reports_resp.status_code == 200
    data = reports_resp.json()
    assert "summary" in data
    assert data["summary"]["total_trips"] > 0
