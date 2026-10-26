from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Consultation, Prescription, User
from app.schemas.schemas import PrescriptionCreate, PrescriptionResponse
from app.core.security import get_current_user
from app.services.audit_service import record_audit

router = APIRouter(prefix="/consultations", tags=["Prescriptions"])

@router.post("/{consultation_id}/prescriptions", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
def create_prescription(
    consultation_id: str,
    rx_in: PrescriptionCreate,
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
            detail="Only the attending doctor can create prescriptions for this consultation"
        )

    if consultation.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot issue a prescription for a cancelled consultation"
        )

    existing_rx = db.query(Prescription).filter(Prescription.consultation_id == consultation_id).first()
    if existing_rx:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A prescription has already been issued for this consultation"
        )

    prescription = Prescription(
        consultation_id=consultation_id,
        diagnosis=rx_in.diagnosis,
        medicines=rx_in.medicines,
        instructions=rx_in.instructions
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)

    client_ip = request.client.host if request.client else None
    record_audit(
        db=db,
        action="ISSUE_PRESCRIPTION",
        resource=f"prescription:{prescription.id}",
        actor_id=current_user.id,
        details=f"Prescription created for consultation {consultation_id}",
        ip_address=client_ip
    )

    return prescription

@router.get("/{consultation_id}/prescriptions", response_model=PrescriptionResponse)
def get_prescription(
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
            detail="You are not authorized to view this prescription"
        )

    prescription = db.query(Prescription).filter(Prescription.consultation_id == consultation_id).first()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No prescription found for this consultation"
        )

    return prescription
