from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Consultation, User
from app.schemas.schemas import ConsultationResponse
from app.core.security import get_current_user
from app.services.audit_service import record_audit

router = APIRouter(prefix="/consultations", tags=["Consultations"])


def get_consultation_or_404(consultation_id: str, db: Session) -> Consultation:
    c = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Consultation not found")
    return c


def check_doctor_or_admin(consultation: Consultation, current_user: User):
    is_doctor = current_user.doctor_profile and consultation.doctor_id == current_user.doctor_profile.id
    if not (is_doctor or current_user.role == "admin"):
        raise HTTPException(status_code=403, detail="Only the assigned doctor or admin can do this")


def check_access(consultation: Consultation, current_user: User):
    is_patient = consultation.patient_id == current_user.id
    is_doctor = current_user.doctor_profile and consultation.doctor_id == current_user.doctor_profile.id
    if not (is_patient or is_doctor or current_user.role == "admin"):
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/{consultation_id}", response_model=ConsultationResponse)
def get_consultation(consultation_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = get_consultation_or_404(consultation_id, db)
    check_access(c, current_user)
    return c


@router.post("/{consultation_id}/start", response_model=ConsultationResponse)
def start_consultation(consultation_id: str, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = get_consultation_or_404(consultation_id, db)
    check_doctor_or_admin(c, current_user)
    if c.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot start a cancelled consultation")
    c.status = "in_progress"
    db.commit()
    db.refresh(c)
    record_audit(db, "START_CONSULTATION", f"consultation:{c.id}", actor_id=current_user.id, ip_address=request.client.host if request.client else None)
    return c


@router.post("/{consultation_id}/complete", response_model=ConsultationResponse)
def complete_consultation(consultation_id: str, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = get_consultation_or_404(consultation_id, db)
    check_doctor_or_admin(c, current_user)
    if c.status not in ("booked", "in_progress"):
        raise HTTPException(status_code=400, detail="Only booked or in_progress consultations can be completed")
    c.status = "completed"
    db.commit()
    db.refresh(c)
    record_audit(db, "COMPLETE_CONSULTATION", f"consultation:{c.id}", actor_id=current_user.id, ip_address=request.client.host if request.client else None)
    return c
