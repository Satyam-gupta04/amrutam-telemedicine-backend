from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Consultation, Payment, User
from app.schemas.schemas import PaymentResponse
from app.core.security import get_current_user
from app.services.audit_service import record_audit

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/{consultation_id}", response_model=PaymentResponse)
def get_payment(consultation_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Consultation not found")

    is_patient = c.patient_id == current_user.id
    is_doctor = current_user.doctor_profile and c.doctor_id == current_user.doctor_profile.id
    if not (is_patient or is_doctor or current_user.role == "admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    payment = db.query(Payment).filter(Payment.consultation_id == consultation_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("/{consultation_id}/confirm", response_model=PaymentResponse)
def confirm_payment(consultation_id: str, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Consultation not found")

    payment = db.query(Payment).filter(Payment.consultation_id == consultation_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment.status = "completed"
    db.commit()
    db.refresh(payment)

    record_audit(db, "CONFIRM_PAYMENT", f"payment:{payment.id}", actor_id=current_user.id, ip_address=request.client.host if request.client else None)
    return payment
