# Security & Threat Model

## What we protect against

### 1. Password attacks
Passwords are hashed with PBKDF2-HMAC-SHA256 (100,000 rounds). Even if the database leaks, raw passwords are not recoverable. We never store or return passwords anywhere.

### 2. Unauthorized access (RBAC)
Every route checks the user's role before doing anything:
- Patients can only see their own consultations and prescriptions.
- Doctors can only write prescriptions for their own consultations.
- Admin endpoints are blocked for everyone except admins.

### 3. JWT token security
Tokens expire in 60 minutes. Invalid or tampered tokens are rejected immediately with a 401.

### 4. Double booking (race conditions)
The booking endpoint locks the slot row with `SELECT FOR UPDATE` inside a DB transaction. Even concurrent requests cannot book the same slot twice. The `idempotency_records` table also prevents the same request from being replayed.

### 5. Rate limiting
The middleware limits each IP to 120 requests/minute. Requests beyond this get a 429 error.

### 6. Input validation
All request data goes through Pydantic schemas. Invalid types, missing fields, or bad email formats are rejected before the code even runs.

### 7. SQL injection
We use SQLAlchemy ORM everywhere. No raw SQL strings. Injection is not possible.

### 8. Medical data privacy
Prescriptions are only readable by the patient who owns the consultation, the doctor who wrote it, or an admin. No other user can access another user's medical data.

### 9. Audit trail
Every important action (login, register, book, cancel, prescribe) is logged to `audit_logs` with actor ID, IP address, and timestamp. This is admin-only readable.

### 10. MFA (Two-Factor Authentication)
Users can optionally enable TOTP-compatible MFA. Once enabled, login requires both password and a 6-digit time-based code.

---

## What we do NOT have (honest limitations)

- No real payment gateway integration (status is manually confirmed for this assignment).
- No email/SMS verification on registration.
- No HTTPS termination in the app itself (this is handled by a reverse proxy/load balancer in production).
- No key rotation automation (SECRET_KEY rotation requires a redeploy).
