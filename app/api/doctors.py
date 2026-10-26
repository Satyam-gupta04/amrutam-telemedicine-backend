from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Doctor, AvailabilitySlot, User, Profile
from app.schemas.schemas import (
    DoctorResponse,
    DoctorCreate,
    SlotCreate,
    SlotResponse
)
from app.core.security import get_current_user, require_roles

router = APIRouter(prefix="/doctors", tags=["Doctors & Availability"])

@router.get("", response_model=List[DoctorResponse])
def search_doctors(
    specialization: Optional[str] = Query(None),
    min_experience: Optional[int] = Query(None, ge=0),
    max_fee: Optional[float] = Query(None, ge=0),
    name: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Doctor).join(User).join(Profile)

    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
    if min_experience is not None:
        query = query.filter(Doctor.experience_years >= min_experience)
    if max_fee is not None:
        query = query.filter(Doctor.consultation_fee <= max_fee)
    if name:
        query = query.filter(Profile.full_name.ilike(f"%{name}%"))

    doctors = query.all()
    results = []
    for doc in doctors:
        results.append(
            DoctorResponse(
                id=doc.id,
                user_id=doc.user_id,
                full_name=doc.user.profile.full_name if doc.user and doc.user.profile else "Doctor",
                email=doc.user.email if doc.user else "",
                specialization=doc.specialization,
                experience_years=doc.experience_years,
                consultation_fee=doc.consultation_fee,
                bio=doc.bio,
                rating=doc.rating
            )
        )
    return results

@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_doctor_by_id(doctor_id: str, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    return DoctorResponse(
        id=doctor.id,
        user_id=doctor.user_id,
        full_name=doctor.user.profile.full_name if doctor.user and doctor.user.profile else "Doctor",
        email=doctor.user.email if doctor.user else "",
        specialization=doctor.specialization,
        experience_years=doctor.experience_years,
        consultation_fee=doctor.consultation_fee,
        bio=doctor.bio,
        rating=doctor.rating
    )

@router.put("/profile/me", response_model=DoctorResponse)
def update_doctor_profile(
    doc_in: DoctorCreate,
    current_user: User = Depends(require_roles(["doctor"])),
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        doctor = Doctor(user_id=current_user.id)
        db.add(doctor)

    doctor.specialization = doc_in.specialization
    doctor.experience_years = doc_in.experience_years
    doctor.consultation_fee = doc_in.consultation_fee
    doctor.bio = doc_in.bio

    db.commit()
    db.refresh(doctor)

    return DoctorResponse(
        id=doctor.id,
        user_id=doctor.user_id,
        full_name=current_user.profile.full_name if current_user.profile else "Doctor",
        email=current_user.email,
        specialization=doctor.specialization,
        experience_years=doctor.experience_years,
        consultation_fee=doctor.consultation_fee,
        bio=doctor.bio,
        rating=doctor.rating
    )

@router.post("/{doctor_id}/slots", response_model=SlotResponse, status_code=status.HTTP_201_CREATED)
def create_slot(
    doctor_id: str,
    slot_in: SlotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )

    if current_user.role != "admin" and doctor.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are only allowed to manage your own availability slots"
        )

    if slot_in.start_time >= slot_in.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot start time must be before end time"
        )

    existing = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.doctor_id == doctor_id,
        AvailabilitySlot.start_time == slot_in.start_time
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A slot already exists at this start time"
        )

    slot = AvailabilitySlot(
        doctor_id=doctor_id,
        start_time=slot_in.start_time,
        end_time=slot_in.end_time,
        is_booked=False
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot

@router.get("/{doctor_id}/slots", response_model=List[SlotResponse])
def get_doctor_slots(
    doctor_id: str,
    available_only: bool = True,
    db: Session = Depends(get_db)
):
    query = db.query(AvailabilitySlot).filter(AvailabilitySlot.doctor_id == doctor_id)
    if available_only:
        query = query.filter(AvailabilitySlot.is_booked == False)
    slots = query.order_by(AvailabilitySlot.start_time.asc()).all()
    return slots
