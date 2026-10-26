from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Consultation, User
from app.schemas.schemas import ConsultationResponse, ConsultationStatusUpdate
from app.core.security import get_current_user
from app.services.audit_service import record_audit

router = APIRouter(prefix="/consultations", tags=["Consultation Lifecycle"])

@router.get("/{consultation_id}", response_model=ConsultationResponse)
def get_consultation(
    consultation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found"
        )

    is_patient = consultation.patient_id == current_user.id
    is_doctor = current_user.doctor_profile and consultation.doctor_id == current_user.doctor_profile.id
    is_admin = current_user.role == "admin"

    if not (is_patient or is_doctor or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this consultation"
        )

    return consultation

@router.post("/{consultation_id}/start", response_model=ConsultationResponse)
def start_consultation(
    consultation_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found"
        )

    is_doctor = current_user.doctor_profile and consultation.doctor_id == current_user.doctor_profile.id
    is_admin = current_user.role == "admin"

    if not (is_doctor or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned doctor or admin can start the consultation"
        )

    if consultation.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start a cancelled consultation"
        )

    consultation.status = "in_progress"
    db.commit()
    db.refresh(consultation)

    client_ip = request.client.host if request.client else None
    record_audit(
        db=db,
        action="START_CONSULTATION",
        resource=f"consultation:{consultation.id}",
        actor_id=current_user.id,
        details="Consultation status changed to in_progress",
        ip_address=client_ip
    )

    return consultation

@router.post("/{consultation_id}/complete", response_model=ConsultationResponse)
def complete_consultation(
    consultation_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found"
        )

    is_doctor = current_user.doctor_profile and consultation.doctor_id == current_user.doctor_profile.id
    is_admin = current_user.role == "admin"

    if not (is_doctor or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned doctor or admin can complete the consultation"
        )

    consultation.status = "completed"
    db.commit()
    db.refresh(consultation)

    client_ip = request.client.host if request.client else None
    record_audit(
        db=db,
        action="COMPLETE_CONSULTATION",
        resource=f"consultation:{consultation.id}",
        actor_id=current_user.id,
        details="Consultation status changed to completed",
        ip_address=client_ip
    )

    return consultation
