from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Consultation, Payment, User
from app.schemas.schemas import PaymentResponse
from app.core.security import get_current_user
from app.services.audit_service import record_audit

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.get("/{consultation_id}", response_model=PaymentResponse)
def get_payment_details(
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
            detail="Access forbidden"
        )

    payment = db.query(Payment).filter(Payment.consultation_id == consultation_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found"
        )

    return payment

@router.post("/{consultation_id}/confirm", response_model=PaymentResponse)
def confirm_payment(
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

    payment = db.query(Payment).filter(Payment.consultation_id == consultation_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found"
        )

    payment.status = "completed"
    db.commit()
    db.refresh(payment)

    client_ip = request.client.host if request.client else None
    record_audit(
        db=db,
        action="CONFIRM_PAYMENT",
        resource=f"payment:{payment.id}",
        actor_id=current_user.id,
        details=f"Payment marked completed for consultation {consultation_id}",
        ip_address=client_ip
    )

    return payment
