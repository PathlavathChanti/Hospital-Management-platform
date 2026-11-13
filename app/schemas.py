from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import enum


class UserRole(str, enum.Enum):
    patient = "patient"
    receptionist = "receptionist"
    admin = "admin"


class AppointmentStatus(str, enum.Enum):
    confirmed = "CONFIRMED"
    cancelled = "CANCELLED"


# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Doctors ---
class DoctorOut(BaseModel):
    id: int
    name: str
    specialty: Optional[str] = None
    model_config = {"from_attributes": True}


class SlotOut(BaseModel):
    slot_start: datetime
    slot_end: datetime
    is_booked: bool


# --- Appointments ---
class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    slot_start: datetime
    slot_end: datetime


class AppointmentPatch(BaseModel):
    slot_start: datetime
    slot_end: datetime


class AppointmentOut(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    slot_start: datetime
    slot_end: datetime
    status: AppointmentStatus
    created_at: datetime
    model_config = {"from_attributes": True}
