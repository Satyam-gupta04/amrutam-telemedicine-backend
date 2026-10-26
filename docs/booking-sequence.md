# Booking Flow Sequence Diagram

The diagram below details the sequence of events during appointment booking, illustrating concurrency control, database row locking, idempotency record checking, and audit logging.

```mermaid
sequenceDiagram
    autonumber
    actor Patient as Patient (App/Browser)
    participant ALB as Load Balancer
    participant API as FastAPI Backend
    participant Redis as Redis Cache
    participant DB as PostgreSQL Primary
    participant Audit as Audit Service

    Patient->>ALB: POST /api/v1/bookings<br/>Header: Idempotency-Key: IDEMP-XYZ<br/>Body: {doctor_id, slot_id, notes}
    ALB->>API: Forward Request + Client IP

    API->>API: Compute request hash (SHA-256 of payload)
    
    API->>DB: Query IdempotencyRecord WHERE key = 'IDEMP-XYZ'
    alt Idempotency Key Exists
        alt Payload Hash Matches
            DB-->>API: Return existing response body
            API-->>Patient: 201 Created (Cached Booking Details)
        else Payload Hash Differs
            API-->>Patient: 400 Bad Request (Key Reused with Mismatched Payload)
        end
    else New Request
        API->>DB: BEGIN TRANSACTION
        API->>DB: SELECT * FROM availability_slots WHERE id = slot_id FOR UPDATE
        
        alt Slot Not Found OR slot.doctor_id != doctor_id
            API->>DB: ROLLBACK
            API-->>Patient: 404 / 400 Error
        else Slot Already Booked (is_booked == true)
            API->>DB: ROLLBACK
            API-->>Patient: 409 Conflict (Slot already taken)
        else Slot Available
            API->>DB: UPDATE availability_slots SET is_booked = true WHERE id = slot_id
            API->>DB: INSERT INTO consultations (patient_id, doctor_id, slot_id, status)
            API->>DB: INSERT INTO payments (consultation_id, amount, status)
            API->>DB: INSERT INTO idempotency_records (key, request_hash, response_code, response_body)
            API->>DB: COMMIT TRANSACTION
            
            API->>Audit: record_audit(action="CREATE_BOOKING", actor=patient_id)
            Audit->>DB: INSERT INTO audit_logs
            
            API-->>Patient: 201 Created (Booking Details, Meet Link, Payment Reference)
        end
    end
```
