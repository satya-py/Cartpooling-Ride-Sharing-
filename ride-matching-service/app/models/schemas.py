"""
API-facing request/response models.

Contains schemas for Ride Matching, User Authentication, Vehicle Management,
Ride Publishing, Bookings, Wallet Transactions, Admin Portal, and Reports.
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class LatLon(BaseModel):
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "latitude": 22.584,
                "longitude": 88.402
            }
        }
    )


class MatchRequest(BaseModel):
    org_id: str = Field("ORG_KOL_001", description="Tenant/organization id — hard filter")
    pickup: LatLon
    destination: LatLon
    travel_date: str = Field("2026-08-10", description="YYYY-MM-DD")
    requested_hour: float = Field(18.0, description="24h hour, e.g. 18.5 = 18:30")
    seats: int = Field(1, ge=1, description="Number of seats requested")
    max_fare: Optional[float] = Field(60.0, description="Optional maximum fare per seat")


class ScoreBreakdown(BaseModel):
    pickupScore: float
    destinationScore: float
    detourScore: float
    timeScore: float
    fareScore: float


class RideMatchResult(BaseModel):
    rideId: str
    driverName: str
    matchScore: float
    breakdown: ScoreBreakdown
    reasons: List[str]


class MatchResponse(BaseModel):
    results: List[RideMatchResult]
    candidatesConsidered: int
    totalRidesInSystem: int


# Authentication Schemas
class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    phone: str
    role: str = Field("employee", description="employee or admin")
    department: Optional[str] = "Engineering"
    manager: Optional[str] = "Manager"
    office_location: Optional[str] = "Kolkata HQ"


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str]
    role: str
    department: Optional[str]
    manager: Optional[str]
    office_location: Optional[str]
    platform_access: str
    wallet_balance: float


# Vehicle Schemas
class VehicleCreate(BaseModel):
    model: str
    registration_number: str
    seating_capacity: int = Field(4, ge=1)


class VehicleResponse(BaseModel):
    id: str
    user_id: str
    driver_name: str
    model: str
    registration_number: str
    seating_capacity: int
    status: str


# Ride Publishing Schemas
class RideCreate(BaseModel):
    pickup_name: str
    pickup_lat: float
    pickup_lon: float
    drop_name: str
    drop_lat: float
    drop_lon: float
    travel_date: str
    departure_hour: float
    available_seats: int = Field(3, ge=1)
    fare_per_seat: float = Field(50.0, ge=0)
    vehicle_id: Optional[str] = None


class RideDetailResponse(BaseModel):
    id: str
    driver_id: str
    driver_name: str
    vehicle_id: Optional[str]
    org_id: str
    pickup_name: str
    pickup_lat: float
    pickup_lon: float
    drop_name: str
    drop_lat: float
    drop_lon: float
    travel_date: str
    departure_hour: float
    available_seats: int
    fare_per_seat: float
    status: str


# Booking / Trip Schemas
class BookingCreate(BaseModel):
    seats_booked: int = Field(1, ge=1)
    pickup_name: str
    drop_name: str


class BookingResponse(BaseModel):
    id: str
    ride_id: str
    passenger_id: str
    passenger_name: str
    seats_booked: int
    status: str
    pickup_name: str
    drop_name: str
    total_fare: float
    payment_method: str
    payment_status: str
    created_at: str


class PaymentRequest(BaseModel):
    payment_method: str = Field("wallet", description="cash, card, upi, or wallet")


class WalletRechargeRequest(BaseModel):
    amount: float = Field(..., gt=0)


class SavedPlaceCreate(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float


class EmployeeAccessUpdate(BaseModel):
    platform_access: str = Field(..., description="active or revoked")


class VehicleStatusUpdate(BaseModel):
    status: str = Field(..., description="approved or inactive")


class CompanySettingsUpdate(BaseModel):
    company_name: str
    registered_office: str
    industry: str
    admin_contact: str
    fuel_cost_per_liter: float
    travel_cost_per_km: float
    default_policy: str
