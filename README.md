# Amrutam Telemedicine Backend

Backend API for Amrutam's telemedicine platform — built with FastAPI and PostgreSQL.

Patients can register, search doctors, book appointments, and get prescriptions. Doctors manage their availability and write prescriptions. Admins can view analytics and audit logs.

---

## Stack

- **Python 3.9 + FastAPI**
- **PostgreSQL** (SQLite for local dev/testing)
- **SQLAlchemy** (ORM)
- **JWT** for authentication
- **Docker + Docker Compose**
- **GitHub Actions** for CI

---

## Project Structure

```
├── app/
│   ├── main.py              # App entry point
│   ├── config.py            # Settings from env vars
│   ├── database.py          # DB engine and session
│   ├── core/
│   │   ├── security.py      # JWT, password hash, RBAC, MFA
│   │   └── middleware.py    # Request ID, rate limiting, metrics
│   ├── models/models.py     # All database tables
│   ├── schemas/schemas.py   # Pydantic request/response models
│   ├── services/
│   │   ├── booking_service.py  # Booking logic with concurrency control
│   │   └── audit_service.py    # Audit log writing
│   └── api/
│       ├── auth.py          # Register, login, MFA
│       ├── doctors.py       # Search, slots
│       ├── bookings.py      # Book, cancel
│       ├── consultations.py # Start, complete
│       ├── prescriptions.py # Write, view prescriptions
│       ├── payments.py      # Payment status
│       └── admin.py         # Analytics, audit logs, user list
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_bookings.py
│   ├── test_consultations.py
│   └── test_security.py
├── docs/
│   ├── architecture.md
│   ├── er-diagram.md
│   └── threat-model.md
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Run Locally

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd Pharmaceuticals

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
cp .env.example .env
# Edit .env if needed (default uses SQLite)

# 5. Start the server
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000/docs** to see the interactive API.

---

## Run with Docker

```bash
docker compose up --build
```

This starts the API, PostgreSQL, and Redis together.

---

## Run Tests

```bash
pytest -v --cov=app
```

Tests use an in-memory SQLite database — no setup needed.

---

## API Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register as patient/doctor/admin |
| POST | `/api/v1/auth/login` | Login and get JWT token |
| GET | `/api/v1/auth/me` | Get current user |
| POST | `/api/v1/auth/mfa/setup` | Setup MFA |
| POST | `/api/v1/auth/mfa/verify` | Enable MFA |
| GET | `/api/v1/doctors` | Search doctors by specialization, fee, etc |
| GET | `/api/v1/doctors/{id}/slots` | View available slots |
| POST | `/api/v1/doctors/{id}/slots` | Doctor creates a slot |
| POST | `/api/v1/bookings` | Book an appointment (supports Idempotency-Key) |
| PATCH | `/api/v1/bookings/{id}/cancel` | Cancel a booking |
| POST | `/api/v1/consultations/{id}/start` | Doctor starts consultation |
| POST | `/api/v1/consultations/{id}/complete` | Doctor completes consultation |
| POST | `/api/v1/consultations/{id}/prescriptions` | Doctor writes prescription |
| GET | `/api/v1/consultations/{id}/prescriptions` | View prescription |
| GET | `/api/v1/payments/{consultation_id}` | View payment status |
| GET | `/api/v1/admin/analytics` | Platform stats (admin only) |
| GET | `/api/v1/admin/audit-logs` | Audit trail (admin only) |
| GET | `/health` | Health check |
| GET | `/metrics` | Request metrics (p50, p95, p99 latency) |

---

## Docs

- [Architecture](docs/architecture.md)
- [ER Diagram](docs/er-diagram.md)
- [Security & Threat Model](docs/threat-model.md)
