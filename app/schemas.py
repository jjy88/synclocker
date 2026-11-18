from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(pattern=EMAIL_PATTERN, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class RegisterResponse(BaseModel):
    user_id: str
    email: str


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class SessionOut(BaseModel):
    session_id: str
    location_id: str
    name: str
    starts_at: datetime
    ends_at: datetime
    price_cents: int


class LockerAvailability(BaseModel):
    locker_id: str
    size: Literal["small", "medium", "large"]
    available: bool


class AvailabilityResponse(BaseModel):
    session_id: str
    lockers: list[LockerAvailability]


class HoldRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    size: Literal["small", "medium", "large"]


class HoldResponse(BaseModel):
    hold_id: str
    locker_id: str
    status: Literal["HELD", "EXPIRED", "CONVERTED", "RELEASED"]
    expires_at: datetime


class ReservationOut(BaseModel):
    reservation_id: str
    session_id: str
    locker_id: str
    status: Literal["CONFIRMED", "CANCELLED"]
    created_at: datetime
