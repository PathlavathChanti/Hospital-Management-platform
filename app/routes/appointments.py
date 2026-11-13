from datetime import datetime, time, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db import get_db
from app import models, schemas
from app.auth import get_current_user
from app.audit import log_audit

router = APIRouter()


def _validate_slot(slot_start: datetime, slot_end: datetime) -> None:
    """Enforce business rules on slot timing."""
    # Strip timezone for comparison if present
    st = slot_start.replace(tzinfo=None) if slot_start.tzinfo else slot_start
    et = slot_end.replace(tzinfo=None) if slot_end.tzinfo else slot_end
    now = datetime.utcnow()

    if st <= now:
        raise HTTPException(status_code=422, detail="Slot must be in the future")
    if st.minute % 30 != 0 or st.second != 0:
        raise HTTPException(status_code=422, detail="slot_start must align to a 30-minute boundary")
    if et.minute % 30 != 0 or et.second != 0:
        raise HTTPException(status_code=422, detail="slot_end must align to a 30-minute boundary")
    if et != st + timedelta(minutes=30):
        raise HTTPException(status_code=422, detail="Slot must be exactly 30 minutes")
    if not (time(9, 0) <= st.time() < time(17, 0)):
        raise HTTPException(status_code=422, detail="slot_start must be between 09:00 and 16:30")
    if not (time(9, 30) <= et.time() <= time(17, 0)):
        raise HTTPException(status_code=422, detail="slot_end must be between 09:30 and 17:00")


def _check_patient_permission(user: models.User, patient_id: int) -> None:
    """Patients may only act on their own records."""
    if user.role == models.UserRole.patient and user.patient_id != patient_id:
        raise HTTPException(status_code=403, detail="Patients may only manage their own appointments")


@router.post("/", response_model=schemas.AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Book a new appointment."""
    # Validate doctor exists
    doctor = db.query(models.Doctor).filter(models.Doctor.id == payload.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Validate patient exists
    patient = db.query(models.Patient).filter(models.Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Role check
    _check_patient_permission(current_user, payload.patient_id)

    # Slot validation
    _validate_slot(payload.slot_start, payload.slot_end)

    appt = models.Appointment(
        doctor_id=payload.doctor_id,
        patient_id=payload.patient_id,
        slot_start=payload.slot_start,
        slot_end=payload.slot_end,
        status=models.AppointmentStatus.confirmed,
    )
    db.add(appt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Doctor already booked for this slot")
    db.refresh(appt)

    log_audit(db, current_user.id, "create", "appointment", appt.id,
             {"doctor_id": payload.doctor_id, "patient_id": payload.patient_id})
    return appt


@router.get("/", response_model=List[schemas.AppointmentOut])
def list_appointments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Patient sees own appointments; staff sees all."""
    q = db.query(models.Appointment)
    if current_user.role == models.UserRole.patient:
        q = q.filter(models.Appointment.patient_id == current_user.patient_id)
    return q.all()


@router.patch("/{appt_id}", response_model=schemas.AppointmentOut)
def reschedule_appointment(
    appt_id: int,
    payload: schemas.AppointmentPatch,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Reschedule an existing appointment to a new slot."""
    appt = db.query(models.Appointment).filter(models.Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    _check_patient_permission(current_user, appt.patient_id)
    _validate_slot(payload.slot_start, payload.slot_end)

    # Cancel the old slot, create fresh to leverage the unique index
    appt.status = models.AppointmentStatus.cancelled
    db.flush()

    new_appt = models.Appointment(
        doctor_id=appt.doctor_id,
        patient_id=appt.patient_id,
        slot_start=payload.slot_start,
        slot_end=payload.slot_end,
        status=models.AppointmentStatus.confirmed,
    )
    db.add(new_appt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Doctor already booked for the new slot")
    db.refresh(new_appt)

    log_audit(db, current_user.id, "reschedule", "appointment", new_appt.id,
             {"old_id": appt_id, "new_start": str(payload.slot_start)})
    return new_appt


@router.delete("/{appt_id}", response_model=schemas.AppointmentOut)
def cancel_appointment(
    appt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Cancel an appointment (soft-delete: set status to CANCELLED)."""
    appt = db.query(models.Appointment).filter(models.Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    _check_patient_permission(current_user, appt.patient_id)

    if appt.status == models.AppointmentStatus.cancelled:
        raise HTTPException(status_code=422, detail="Appointment already cancelled")

    appt.status = models.AppointmentStatus.cancelled
    db.commit()
    db.refresh(appt)

    log_audit(db, current_user.id, "cancel", "appointment", appt.id, {"status": "CANCELLED"})
    return appt
