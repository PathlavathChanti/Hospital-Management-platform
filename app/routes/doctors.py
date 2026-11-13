from datetime import datetime, time, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[schemas.DoctorOut])
def list_doctors(db: Session = Depends(get_db)):
    """Return all doctors."""
    return db.query(models.Doctor).all()


def _generate_daily_slots(date_obj: datetime) -> list[datetime]:
    """Generate 30-min slots from 09:00 to 17:00 for a given date."""
    slots: list[datetime] = []
    current = datetime.combine(date_obj.date(), time(9, 0))
    end = datetime.combine(date_obj.date(), time(17, 0))
    while current < end:
        slots.append(current)
        current += timedelta(minutes=30)
    return slots


@router.get("/{doctor_id}/slots", response_model=List[schemas.SlotOut])
def get_doctor_slots(
    doctor_id: int,
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return 30-min slots for a doctor on a given date, marking booked ones."""
    # Validate date format
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid date format. Use YYYY-MM-DD.",
        )

    # Validate doctor exists
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    slot_starts = _generate_daily_slots(target_date)

    # Fetch confirmed appointments for this doctor on this date
    day_start = slot_starts[0]
    day_end = slot_starts[-1] + timedelta(minutes=30)
    confirmed = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.doctor_id == doctor_id,
            models.Appointment.status == models.AppointmentStatus.confirmed,
            models.Appointment.slot_start >= day_start,
            models.Appointment.slot_start < day_end,
        )
        .all()
    )
    booked_set = {a.slot_start.replace(tzinfo=None) for a in confirmed}

    return [
        schemas.SlotOut(
            slot_start=s,
            slot_end=s + timedelta(minutes=30),
            is_booked=(s in booked_set),
        )
        for s in slot_starts
    ]
