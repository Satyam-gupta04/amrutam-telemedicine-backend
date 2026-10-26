import json
import hashlib
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.models import (
    AvailabilitySlot,
    Doctor,
    Consultation,
    Payment,
    IdempotencyRecord
)
from app.services.audit_service import record_audit

def create_booking(
    db: Session,
    patient_id: str,
    doctor_id: str,
    slot_id: str,
    notes: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    client_ip: Optional[str] = None
) -> Consultation:
    request_payload_str = f"{patient_id}:{doctor_id}:{slot_id}:{notes or ''}"
    request_hash = hashlib.sha256(request_payload_str.encode("utf-8")).hexdigest()

    if idempotency_key:
        existing_record = db.query(IdempotencyRecord).filter(IdempotencyRecord.key == idempotency_key).first()
        if existing_record:
            if existing_record.request_hash != request_hash:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Idempotency key was reused with a different request payload"
                )
            cached_data = json.loads(existing_record.response_body)
            existing_consultation = db.query(Consultation).filter(Consultation.id == cached_data.get("id")).first()
            if existing_consultation:
                return existing_consultation

    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )

    try:
        try:
            slot = db.query(AvailabilitySlot).filter(AvailabilitySlot.id == slot_id).with_for_update().first()
        except Exception:
            slot = db.query(AvailabilitySlot).filter(AvailabilitySlot.id == slot_id).first()

        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Availability slot not found"
            )

        if slot.doctor_id != doctor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slot does not belong to the requested doctor"
            )

        if slot.is_booked:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Selected slot is already booked"
            )

        slot.is_booked = True

        consultation = Consultation(
            patient_id=patient_id,
            doctor_id=doctor_id,
            slot_id=slot_id,
            status="booked",
            notes=notes,
            meet_link=f"https://telemed.amrutam.co.in/room/{uuid.uuid4().hex[:12]}"
        )
        db.add(consultation)
        db.flush()

        payment = Payment(
            consultation_id=consultation.id,
            amount=doctor.consultation_fee,
            currency="INR",
            status="pending",
            transaction_ref=f"TXN-{uuid.uuid4().hex[:10].upper()}"
        )
        db.add(payment)

        if idempotency_key:
            response_payload = {
                "id": consultation.id,
                "patient_id": consultation.patient_id,
                "doctor_id": consultation.doctor_id,
                "slot_id": consultation.slot_id,
                "status": consultation.status,
                "meet_link": consultation.meet_link
            }
            idempotency_entry = IdempotencyRecord(
                key=idempotency_key,
                request_hash=request_hash,
                response_code=201,
                response_body=json.dumps(response_payload)
            )
            db.add(idempotency_entry)

        db.commit()
        db.refresh(consultation)

        record_audit(
            db=db,
            actor_id=patient_id,
            action="CREATE_BOOKING",
            resource=f"consultation:{consultation.id}",
            details=f"Booked slot {slot_id} with doctor {doctor_id}",
            ip_address=client_ip
        )

        return consultation

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Concurrency conflict: Slot was just booked by another user"
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to book consultation: {str(e)}"
        )
