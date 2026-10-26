from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import User, Doctor, Consultation, Payment, AuditLog
from app.schemas.schemas import UserResponse, AnalyticsSummary, AuditLogResponse
from app.core.security import require_roles

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    return db.query(User).offset(skip).limit(limit).all()


@router.get("/analytics", response_model=AnalyticsSummary)
def get_analytics(current_user: User = Depends(require_roles(["admin"])), db: Session = Depends(get_db)):
    return AnalyticsSummary(
        total_users=db.query(func.count(User.id)).scalar() or 0,
        total_patients=db.query(func.count(User.id)).filter(User.role == "patient").scalar() or 0,
        total_doctors=db.query(func.count(Doctor.id)).scalar() or 0,
        total_consultations=db.query(func.count(Consultation.id)).scalar() or 0,
        completed_consultations=db.query(func.count(Consultation.id)).filter(Consultation.status == "completed").scalar() or 0,
        cancelled_consultations=db.query(func.count(Consultation.id)).filter(Consultation.status == "cancelled").scalar() or 0,
        total_revenue=float(db.query(func.sum(Payment.amount)).filter(Payment.status == "completed").scalar() or 0.0),
    )


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
