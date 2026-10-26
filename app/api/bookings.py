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
    consultation = create_booking(
        db=db,
        patient_id=current_user.id,
        doctor_id=booking_in.doctor_id,
        slot_id=booking_in.slot_id,
        notes=booking_in.notes,
        idempotency_key=idempotency_key,
        client_ip=client_ip
    )
    return consultation

@router.get("", response_model=List[ConsultationResponse])
def get_user_bookings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "patient":
        consultations = db.query(Consultation).filter(Consultation.patient_id == current_user.id).all()
    elif current_user.role == "doctor":
        consultations = db.query(Consultation).join(User, Consultation.doctor_id == current_user.doctor_profile.id).all() if current_user.doctor_profile else []
    else:
        consultations = db.query(Consultation).all()
    return consultations

@router.get("/{booking_id}", response_model=ConsultationResponse)
def get_booking_by_id(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    consultation = db.query(Consultation).filter(Consultation.id == booking_id).first()
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    is_patient = consultation.patient_id == current_user.id
    is_doctor = current_user.doctor_profile and consultation.doctor_id == current_user.doctor_profile.id
    is_admin = current_user.role == "admin"

    if not (is_patient or is_doctor or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this booking"
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    is_patient = consultation.patient_id == current_user.id
    is_doctor = current_user.doctor_profile and consultation.doctor_id == current_user.doctor_profile.id
    is_admin = current_user.role == "admin"

    if not (is_patient or is_doctor or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to cancel this booking"
        )

    if consultation.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completed consultations cannot be cancelled"
        )

    consultation.status = "cancelled"
    slot = db.query(AvailabilitySlot).filter(AvailabilitySlot.id == consultation.slot_id).first()
    if slot:
        slot.is_booked = False

    db.commit()
    db.refresh(consultation)

    client_ip = request.client.host if request.client else None
    record_audit(
        db=db,
        action="CANCEL_BOOKING",
        resource=f"consultation:{consultation.id}",
        actor_id=current_user.id,
        details=f"Booking cancelled by {current_user.role}",
        ip_address=client_ip
    )

    return consultation
