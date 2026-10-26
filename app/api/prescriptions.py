from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Consultation, Prescription, User
from app.schemas.schemas import PrescriptionCreate, PrescriptionResponse
from app.core.security import get_current_user
from app.services.audit_service import record_audit

router = APIRouter(prefix="/consultations", tags=["Prescriptions"])


@router.post("/{consultation_id}/prescriptions", response_model=PrescriptionResponse, status_code=201)
def create_prescription(
    consultation_id: str,
    rx_in: PrescriptionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    c = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Consultation not found")

    is_doctor = current_user.doctor_profile and c.doctor_id == current_user.doctor_profile.id
    if not (is_doctor or current_user.role == "admin"):
        raise HTTPException(status_code=403, detail="Only the attending doctor can write prescriptions")

    if c.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot prescribe for a cancelled consultation")

    if db.query(Prescription).filter(Prescription.consultation_id == consultation_id).first():
        raise HTTPException(status_code=400, detail="A prescription already exists for this consultation")

    rx = Prescription(consultation_id=consultation_id, diagnosis=rx_in.diagnosis, medicines=rx_in.medicines, instructions=rx_in.instructions)
    db.add(rx)
    db.commit()
    db.refresh(rx)

    record_audit(db, "ISSUE_PRESCRIPTION", f"prescription:{rx.id}", actor_id=current_user.id, ip_address=request.client.host if request.client else None)
    return rx


@router.get("/{consultation_id}/prescriptions", response_model=PrescriptionResponse)
def get_prescription(consultation_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Consultation not found")

    is_patient = c.patient_id == current_user.id
    is_doctor = current_user.doctor_profile and c.doctor_id == current_user.doctor_profile.id
    if not (is_patient or is_doctor or current_user.role == "admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    rx = db.query(Prescription).filter(Prescription.consultation_id == consultation_id).first()
    if not rx:
        raise HTTPException(status_code=404, detail="No prescription found")
    return rx
