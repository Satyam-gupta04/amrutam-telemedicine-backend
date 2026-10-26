# Amrutam Telemedicine Backend - Architecture Document

## 1. System Overview & Objectives
Amrutam's Telemedicine System is built to handle end-to-end digital healthcare workflows: patient discovery of practitioners, slot reservation, remote video consultations, encrypted electronic prescriptions, payment status verification, and compliance audit tracking.

### Core Targets
- **Scale:** 100,000 consultations per day (average ~1.15 consultations/sec; peak ~15-25 booking writes/sec and 200-300 read requests/sec).
- **Latency:** Reads p95 < 200ms; Writes p95 < 500ms.
- **Availability:** 99.95% uptime (< 21.9 minutes of allowed downtime per month).
- **Security:** Argon2/PBKDF2-SHA256 password hashing, TOTP-compatible MFA, role-based access control (RBAC), TLS 1.3 in transit, AES-256 at rest, and tamper-resistant audit logs.

---

## 2. High-Level Architecture

```
                          [ Client Applications ]
                   (Web / Mobile Patient & Doctor Apps)
                                     |
                                     v [HTTPS / TLS 1.3]
                        [ Application Load Balancer ]
                                     |
                     +---------------+---------------+
                     |                               |
                     v                               v
             [ FastAPI Node 1 ]              [ FastAPI Node 2 ]
          (Observability, RBAC,           (Observability, RBAC,
           Idempotency, Validation)        Idempotency, Validation)
                     |                               |
        +------------+------------+                  |
        |                         |                  |
        v                         v                  v
[ Redis Cluster ]        [ PostgreSQL Primary (Writer) ]
- Rate Limiting           - Transactions with Row Locks
- Session/Slot Cache      - Users, Doctors, Consultations
                          - Prescriptions, Audit Logs
                                  |
                                  v [Streaming Replication]
                         [ PostgreSQL Read Replica ]
                          - Doctor Catalog & Search
                          - Analytics & Admin Queries
```

---

## 3. Modular Service Architecture & Dependency Injection
The codebase uses clean separation of concerns:
- **`app/api/` (Routing Layer):** Handles HTTP request parsing, header validation (e.g. `Idempotency-Key`), schema binding, and response serialization.
- **`app/core/` (Cross-Cutting Concerns):** Security functions, JWT decoding, PBKDF2 hashing, TOTP MFA validation, and request-id/latency tracking middleware.
- **`app/services/` (Business Logic Layer):** Pure business logic isolated from HTTP dependencies. Contains `booking_service.py` (transactional slot locking and idempotency verification) and `audit_service.py` (compliance logging).
- **`app/models/` (Data Persistence Layer):** Declarative SQLAlchemy entities with relational constraints, foreign keys, and indexes.
- **`app/schemas/` (Contract & Validation Layer):** Pydantic schemas validating input structure, types, password complexity, and role constraints.

FastAPI's dependency injection (`Depends`) provides database sessions and authenticated user context into route handlers, allowing easy unit testing with in-memory SQLite mocks.

---

## 4. Scalability Strategy (100k Daily Consultations)

### Read Scaling
1. **Read Replicas:** Read-heavy operations (doctor profile search, available slot browsing) are routed to PostgreSQL read replicas.
2. **Caching:** Active doctor directories and slot availability lists are cached in Redis with short TTLs (15 to 60 seconds).
3. **Database Indexing:** B-Tree indexes on `doctors.specialization`, `doctors.experience_years`, `availability_slots.doctor_id`, and `availability_slots.start_time`.

### Write Scaling & Concurrency
1. **Pessimistic Row Locking (`SELECT ... FOR UPDATE`):** When booking a slot, the system selects the requested slot row with an exclusive lock. If a concurrent request attempts to book the same slot, it waits or receives a 409 Conflict.
2. **Database Unique Constraints:** An additional database constraint (`unique_doctor_slot`) guarantees that duplicate slots or overlapping consultations cannot be committed.
3. **Idempotency Safeguard:** Every write request accepts an `Idempotency-Key` header. When the client retries over a flaky mobile network, the server returns the cached response instead of charging or booking twice.

---

## 5. Availability (99.95% SLA)
To achieve less than 21.9 minutes of monthly downtime:
- **Stateless Application Servers:** FastAPI containers run in ECS Fargate across multiple availability zones behind an Application Load Balancer.
- **Multi-AZ PostgreSQL:** Managed AWS RDS PostgreSQL with automatic synchronous multi-AZ standby failover within 60 seconds.
- **Health Checks & Circuit Breaking:** `/health` endpoint checks container vitality, database connectivity, and Redis responsiveness.
- **Zero-Downtime Rolling Deployments:** ECS deploys new tasks and verifies health checks before draining older tasks.
