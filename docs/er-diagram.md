# Database ER Diagram

```mermaid
erDiagram
    USERS ||--o| PROFILES : "has"
    USERS ||--o| DOCTORS : "is a"
    USERS ||--o{ CONSULTATIONS : "books as patient"
    DOCTORS ||--o{ AVAILABILITY_SLOTS : "creates"
    DOCTORS ||--o{ CONSULTATIONS : "conducts"
    AVAILABILITY_SLOTS ||--o| CONSULTATIONS : "reserved by"
    CONSULTATIONS ||--o| PRESCRIPTIONS : "has"
    CONSULTATIONS ||--o| PAYMENTS : "billed via"

    USERS {
        string id PK
        string email
        string password_hash
        string role
        boolean is_active
        boolean mfa_enabled
        string mfa_secret
        datetime created_at
    }

    PROFILES {
        string id PK
        string user_id FK
        string full_name
        string phone
        string gender
        string address
    }

    DOCTORS {
        string id PK
        string user_id FK
        string specialization
        int experience_years
        float consultation_fee
        string bio
        float rating
    }

    AVAILABILITY_SLOTS {
        string id PK
        string doctor_id FK
        datetime start_time
        datetime end_time
        boolean is_booked
    }

    CONSULTATIONS {
        string id PK
        string patient_id FK
        string doctor_id FK
        string slot_id FK
        string status
        string notes
        string meet_link
        datetime created_at
    }

    PRESCRIPTIONS {
        string id PK
        string consultation_id FK
        string diagnosis
        string medicines
        string instructions
        datetime issued_at
    }

    PAYMENTS {
        string id PK
        string consultation_id FK
        float amount
        string currency
        string status
        string transaction_ref
    }

    AUDIT_LOGS {
        string id PK
        string actor_id
        string action
        string resource
        string details
        string ip_address
        datetime created_at
    }

    IDEMPOTENCY_RECORDS {
        string id PK
        string key
        string request_hash
        int response_code
        string response_body
        datetime created_at
    }
```
