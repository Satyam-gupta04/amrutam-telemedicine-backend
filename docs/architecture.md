# Architecture – Amrutam Telemedicine Backend

## What this system does

This is the backend for Amrutam's telemedicine platform. Patients can register, search for doctors, book consultation slots, attend video consultations, and receive digital prescriptions. Doctors manage their availability and issue prescriptions. Admins can see analytics and audit logs.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| API | FastAPI (Python) | Fast, auto-generates Swagger docs, easy to read |
| Database | PostgreSQL (SQLite in dev) | Reliable, supports row-level locking |
| Auth | JWT + PBKDF2-SHA256 | Stateless, secure password hashing |
| Deployment | Docker + Docker Compose | Reproducible local and cloud setup |
| CI | GitHub Actions | Runs tests on every push |

---

## High-Level Data Flow

```
Client (Mobile / Browser)
        │
        ▼ HTTPS
   FastAPI App (8000)
   ├── Auth Middleware (JWT check)
   ├── Rate Limiter (120 req/min per IP)
   ├── Request ID tracking
        │
        ▼
   Route Handler (auth / doctors / bookings / consultations)
        │
        ▼
   Business Logic Layer (services/)
        │
        ▼
   PostgreSQL Database
   (users, doctors, slots, consultations, prescriptions, payments, audit_logs)
```

---

## Booking Flow (Concurrency Safe)

1. Patient sends `POST /api/v1/bookings` with `doctor_id`, `slot_id`, and optional `Idempotency-Key` header.
2. Server checks if the idempotency key was already used → if yes, returns same result without creating a duplicate.
3. Server opens a DB transaction and locks the slot row with `SELECT FOR UPDATE`.
4. If slot is free → marks it booked, creates Consultation + Payment records, commits.
5. If slot is already taken → returns `409 Conflict`.
6. Audit log entry is written after the booking.

This means even if two patients click "Book" at the exact same millisecond, only one booking goes through.

---

## Scaling Plan (100k daily consultations)

- Run multiple FastAPI instances behind a load balancer (e.g. AWS ALB).
- Use PostgreSQL read replicas for doctor search queries.
- Add Redis caching for doctor listings (short TTL).
- Partition the `consultations` and `audit_logs` tables by month once data grows.
- Point-in-time recovery (PITR) on RDS for backups. RPO < 5 min.

---

## Availability Target: 99.95%

- Deploy on AWS ECS Fargate across 2 availability zones.
- RDS Multi-AZ with automatic failover.
- Health check on `/health` endpoint.
- Rolling deployments (zero downtime).
