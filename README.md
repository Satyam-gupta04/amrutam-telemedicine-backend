# Amrutam Telemedicine Backend

Production-grade backend system for Amrutam's Telemedicine platform, designed for high scalability (100k daily consultations), high availability (99.95%), enterprise security (RBAC, MFA, Idempotency), and end-to-end observability.

---

## 1. Quick Overview

- **Framework:** FastAPI (Python 3.9+)
- **Database:** PostgreSQL (with SQLite support for zero-dependency local testing)
- **Cache & Rate Limiting:** Redis + in-memory fallback
- **Authentication:** JWT with PBKDF2-SHA256 password hashing and TOTP Two-Factor Authentication
- **Reliability:** Concurrency-safe slot booking with pessimistic row locks and HTTP Idempotency key handling
- **Infrastructure:** Docker, Docker Compose, Terraform (AWS ECS, RDS Multi-AZ, VPC, ALB), GitHub Actions CI

---

## 2. Project Directory Structure

```text
amrutam-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entrypoint & middleware
│   ├── config.py                # Environment configuration settings
│   ├── database.py              # Database engine & session generator
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py          # Passwords, JWT, RBAC & MFA logic
│   │   └── middleware.py        # Request ID, metrics, rate limiting
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py            # SQLAlchemy relational database tables
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic request & response validation
│   ├── services/
│   │   ├── __init__.py
│   │   ├── booking_service.py   # Concurrency, transactions & idempotency
│   │   └── audit_service.py     # Compliance & audit trail recording
│   └── api/
│       ├── __init__.py
│       ├── auth.py              # Register, login, me, MFA endpoints
│       ├── doctors.py           # Search, profile, availability slots
│       ├── bookings.py          # Safe appointment reservation & cancellation
│       ├── consultations.py     # Consultation lifecycle (start, complete)
│       ├── prescriptions.py     # Doctor diagnosis & medical prescriptions
│       ├── payments.py          # Payment tracking & confirmation
│       └── admin.py             # User listing, audit logs & analytics
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test database fixtures, client & tokens
│   ├── test_auth.py             # Authentication & MFA test suite
│   ├── test_doctors.py          # Doctor catalog & slots test suite
│   ├── test_bookings.py         # Concurrency, idempotency & duplicate checks
│   ├── test_consultations.py    # Status transitions & prescription tests
│   ├── test_security.py         # RBAC & unauthenticated access tests
│   └── test_admin.py            # Platform metrics & audit log tests
├── docs/
│   ├── architecture.md          # 100k scale, p95 targets, service topology
│   ├── booking-sequence.md      # Mermaid sequence diagram for booking
│   ├── er-diagram.md            # Mermaid entity-relationship diagram
│   ├── threat-model.md          # OWASP Top 10, attack surfaces & encryption
│   ├── security-checklist.md    # Implemented verification matrix
│   └── reliability.md           # Sagas, retries, partitioning & backup/DR
├── infra/
│   └── terraform/
│       ├── main.tf              # AWS VPC, Multi-AZ RDS, ECS, ALB
│       ├── variables.tf         # Configurable infrastructure inputs
│       └── outputs.tf           # Terraform deployment outputs
├── .github/
│   └── workflows/
│       └── ci.yml               # Automated CI test pipeline
├── Dockerfile                   # Production container definition
├── docker-compose.yml           # Local multi-container stack (API, DB, Redis)
├── requirements.txt             # Python dependencies
├── openapi.json                 # Exported OpenAPI 3.1 specification
├── .env.example                 # Example configuration environment variables
└── README.md
```

---

## 3. How to Run Locally

### Option A: Local Python Virtual Environment

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd Pharmaceuticals
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables:**
   ```bash
   cp .env.example .env
   ```

5. **Start the API server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

6. **Open the interactive documentation:**
   - Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
   - Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
   - Observability metrics: [http://127.0.0.1:8000/metrics](http://127.0.0.1:8000/metrics)

---

### Option B: Docker Compose (Full Stack with PostgreSQL & Redis)

Run the entire production stack with a single command:
```bash
docker compose up --build
```

This starts:
- **FastAPI Backend:** Available on port `8000`
- **PostgreSQL 15:** Available on port `5432`
- **Redis 7:** Available on port `6379`

To stop the containers:
```bash
docker compose down
```

---

## 4. Running Automated Tests

Run the full automated test suite with coverage report:
```bash
pytest -v --cov=app --cov-report=term-missing
```

### What the test suite covers:
- **Authentication:** Registration, login, invalid passwords, duplicate emails, MFA setup and code verification.
- **Doctor Catalog:** Search filtering by specialization, fee, and experience; slot publishing.
- **Booking Concurrency & Idempotency:** Duplicate booking prevention (409 Conflict), Idempotency key replay (201 original data returned), Idempotency key payload mismatch detection (400 Bad Request), and cancellation.
- **Consultation Lifecycle & Prescriptions:** State transitions (booked -> in_progress -> completed), prescription issuance by authorized doctors, rejection of patient prescription issuance.
- **Security & RBAC:** Rejection of unauthenticated calls, rejection of invalid JWT tokens, blocking non-admin users from admin analytics and audit logs.
- **Compliance & Admin:** Platform analytics aggregation, payment status confirmation, and audit logs listing.

---

## 5. API Reference Highlights

| Category | Method | Endpoint | Description |
|---|---|---|---|
| **Health** | `GET` | `/health` | Service vitality and status |
| **Metrics** | `GET` | `/metrics` | Request counts, status breakdown, p50/p95/p99 latency |
| **Auth** | `POST` | `/api/v1/auth/register` | Register new user and profile |
| **Auth** | `POST` | `/api/v1/auth/login` | Login and receive JWT access token |
| **Auth** | `GET` | `/api/v1/auth/me` | Fetch current authenticated user |
| **Auth** | `POST` | `/api/v1/auth/mfa/setup` | Generate TOTP MFA secret |
| **Auth** | `POST` | `/api/v1/auth/mfa/verify` | Verify OTP code and enable MFA |
| **Doctors** | `GET` | `/api/v1/doctors` | Search doctors by specialization, experience, fee |
| **Doctors** | `GET` | `/api/v1/doctors/{id}/slots` | View available consultation slots |
| **Doctors** | `POST` | `/api/v1/doctors/{id}/slots` | Create doctor availability slot |
| **Bookings**| `POST` | `/api/v1/bookings` | Book appointment (supports `Idempotency-Key` header) |
| **Bookings**| `GET` | `/api/v1/bookings` | View user's appointments |
| **Bookings**| `PATCH`| `/api/v1/bookings/{id}/cancel` | Cancel booking and release slot |
| **Consult** | `POST` | `/api/v1/consultations/{id}/start` | Doctor starts consultation |
| **Consult** | `POST` | `/api/v1/consultations/{id}/complete`| Doctor marks consultation completed |
| **Prescribe**| `POST`| `/api/v1/consultations/{id}/prescriptions` | Doctor writes prescription |
| **Prescribe**| `GET` | `/api/v1/consultations/{id}/prescriptions` | View consultation prescription |
| **Payments**| `POST` | `/api/v1/payments/{consultation_id}/confirm` | Confirm payment completion |
| **Admin** | `GET` | `/api/v1/admin/analytics` | Summary of users, consultations, and revenue |
| **Admin** | `GET` | `/api/v1/admin/audit-logs` | Tamper-resistant compliance audit trail |

---

## 6. Submission & Demo Checklist

- [x] Working backend source code with modular architecture and dependency injection
- [x] Relational database models and constraints in PostgreSQL
- [x] Concurrency protection and pessimistic row locking
- [x] Header-based request idempotency implementation
- [x] Role-based access control (patient, doctor, admin)
- [x] TOTP Two-Factor Authentication support
- [x] Rate limiting and request ID tracking middleware
- [x] Observability metrics (`/metrics`) with latency percentiles
- [x] Exported OpenAPI specification (`openapi.json`)
- [x] Architecture document (`docs/architecture.md`)
- [x] Booking sequence diagram (`docs/booking-sequence.md`)
- [x] Relational ER diagram (`docs/er-diagram.md`)
- [x] Threat model and OWASP analysis (`docs/threat-model.md`)
- [x] Security checklist (`docs/security-checklist.md`)
- [x] Reliability, Sagas, Partitioning & DR plan (`docs/reliability.md`)
- [x] Infrastructure as Code in Terraform (`infra/terraform/`)
- [x] Automated CI/CD pipeline (`.github/workflows/ci.yml`)
- [x] Automated test suite passing with high coverage
