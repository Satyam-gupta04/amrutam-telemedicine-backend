from typing import Optional
from sqlalchemy.orm import Session
from app.models.models import AuditLog

def record_audit(
    db: Session,
    action: str,
    resource: str,
    actor_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    log_entry = AuditLog(
        actor_id=actor_id,
        action=action,
        resource=resource,
        details=details,
        ip_address=ip_address
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
