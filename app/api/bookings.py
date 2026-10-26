from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Consultation, AvailabilitySlot, User
from app.schemas.schemas import BookingCreate, ConsultationResponse
from app.core.security import get_current_user
from app.services.booking_service import create_booking
from app.services.audit_service import record_audit

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("", response_model=ConsultationResponse, status_code=status.HTTP_201_CREATED)
def book_appointment(
    booking_in: BookingCreate,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else None
    return create_booking(
        db=db,
        patient_id=current_user.id,
        doctor_id=booking_in.doctor_id,
        slot_id=booking_in.slot_id,
        notes=booking_in.notes,
        idempotency_key=idempotency_key,
        client_ip=client_ip
    )


@router.get("", response_model=List[ConsultationResponse])
def list_my_bookings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "patient":
        return db.query(Consultation).filter(Consultation.patient_id == current_user.id).all()
    if current_user.role == "doctor" and current_user.doctor_profile:
        return db.query(Consultation).filter(Consultation.doctor_id == current_user.doctor_profile.id).all()
    return db.query(Consultation).all()


@router.get("/{booking_id}", response_model=ConsultationResponse)
def get_booking(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    consultation = db.query(Consultation).filter(Consultation.id == booking_id).first()
    if not consultation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    is_patient = consultation.patient_id == current_user.id
    is_doctor = current_user.doctor_profile and consultation.doctor_id == current_user.doctor_profile.id
    is_admin = current_user.role == "admin"

    if not (is_patient or is_doctor or is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return consultation


@router.patch("/{booking_id}/cancel", response_model=ConsultationResponse)
def cancel_booking(
    booking_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    consultation = db.query(Consultation).filter(Consultation.id == booking_id).first()
    if not consultation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    is_patient = consultation.patient_id == current_user.id
    is_doctor = current_user.doctor_profile and consultation.doctor_id == current_user.doctor_profile.id
    is_admin = current_user.role == "admin"

    if not (is_patient or is_doctor or is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if consultation.status == "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel a completed consultation")

    consultation.status = "cancelled"
    slot = db.query(AvailabilitySlot).filter(AvailabilitySlot.id == consultation.slot_id).first()
    if slot:
        slot.is_booked = False

    db.commit()
    db.refresh(consultation)

    record_audit(
        db=db,
        action="CANCEL_BOOKING",
        resource=f"consultation:{consultation.id}",
        actor_id=current_user.id,
        details=f"Cancelled by {current_user.role}",
        ip_address=request.client.host if request.client else None
    )

    return consultation
