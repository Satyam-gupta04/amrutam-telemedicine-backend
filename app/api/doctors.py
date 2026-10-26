from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Doctor, AvailabilitySlot, User, Profile
from app.schemas.schemas import DoctorResponse, DoctorCreate, SlotCreate, SlotResponse
from app.core.security import get_current_user, require_roles

router = APIRouter(prefix="/doctors", tags=["Doctors"])


def build_doctor_response(doctor: Doctor) -> DoctorResponse:
    full_name = doctor.user.profile.full_name if doctor.user and doctor.user.profile else "Doctor"
    email = doctor.user.email if doctor.user else ""
    return DoctorResponse(
        id=doctor.id,
        user_id=doctor.user_id,
        full_name=full_name,
        email=email,
        specialization=doctor.specialization,
        experience_years=doctor.experience_years,
        consultation_fee=doctor.consultation_fee,
        bio=doctor.bio,
        rating=doctor.rating
    )


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
    return [build_doctor_response(d) for d in query.all()]


@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_doctor(doctor_id: str, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return build_doctor_response(doctor)


@router.put("/profile/me", response_model=DoctorResponse)
def update_my_doctor_profile(
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
    return build_doctor_response(doctor)


@router.post("/{doctor_id}/slots", response_model=SlotResponse, status_code=201)
def create_slot(
    doctor_id: str,
    slot_in: SlotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if current_user.role != "admin" and doctor.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only manage your own slots")
    if slot_in.start_time >= slot_in.end_time:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")
    if db.query(AvailabilitySlot).filter(AvailabilitySlot.doctor_id == doctor_id, AvailabilitySlot.start_time == slot_in.start_time).first():
        raise HTTPException(status_code=400, detail="A slot already exists at this time")

    slot = AvailabilitySlot(doctor_id=doctor_id, start_time=slot_in.start_time, end_time=slot_in.end_time, is_booked=False)
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
    return query.order_by(AvailabilitySlot.start_time.asc()).all()
