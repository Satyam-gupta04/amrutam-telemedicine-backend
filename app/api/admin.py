from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import User, Doctor, Consultation, Payment, AuditLog
from app.schemas.schemas import UserResponse, AnalyticsSummary, AuditLogResponse
from app.core.security import require_roles

router = APIRouter(prefix="/admin", tags=["Admin & Compliance"])

@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/analytics", response_model=AnalyticsSummary)
def get_platform_analytics(
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_patients = db.query(func.count(User.id)).filter(User.role == "patient").scalar() or 0
    total_doctors = db.query(func.count(Doctor.id)).scalar() or 0
    total_consultations = db.query(func.count(Consultation.id)).scalar() or 0
    completed_consultations = db.query(func.count(Consultation.id)).filter(Consultation.status == "completed").scalar() or 0
    cancelled_consultations = db.query(func.count(Consultation.id)).filter(Consultation.status == "cancelled").scalar() or 0
    total_revenue = db.query(func.sum(Payment.amount)).filter(Payment.status == "completed").scalar() or 0.0

    return AnalyticsSummary(
        total_users=total_users,
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_consultations=total_consultations,
        completed_consultations=completed_consultations,
        cancelled_consultations=cancelled_consultations,
        total_revenue=float(total_revenue)
    )

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_trail(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs
