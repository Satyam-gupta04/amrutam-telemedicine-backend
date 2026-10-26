# Security Checklist & Verification Matrix

## 1. Authentication & Session Management
- [x] Secure password storage using PBKDF2-HMAC-SHA256 (100,000 rounds)
- [x] JWT token generation with expiration (60 minutes default)
- [x] Two-Factor Authentication (TOTP-compatible MFA) implementation
- [x] Immediate token invalidation on bad signatures or expiration
- [x] Login endpoint rate limiting to mitigate brute-force attacks

## 2. Authorization & Role-Based Access Control (RBAC)
- [x] User roles strictly segmented (`patient`, `doctor`, `admin`)
- [x] Route-level dependencies enforcing role restrictions via `require_roles()`
- [x] Data ownership enforcement (patients can only see their own consultations and prescriptions)
- [x] Doctor-only authorization for issuing and updating medical prescriptions
- [x] Admin-only authorization for viewing audit logs and platform analytics

## 3. Input Validation & Data Sanitation
- [x] Strong schema validation via Pydantic on all request bodies
- [x] Email format and domain validation via `email-validator`
- [x] Protection against SQL injection through SQLAlchemy ORM parameter binding
- [x] Protection against Cross-Site Scripting (XSS) through strict JSON API responses
- [x] Size and type bounds on strings, integer IDs, and numeric fees

## 4. Concurrency & Idempotency
- [x] Idempotency-Key support on POST `/api/v1/bookings`
- [x] SHA-256 payload verification rejecting mismatched parameter reuse
- [x] Pessimistic database row locking on slot reservation (`SELECT ... FOR UPDATE`)
- [x] Database level unique constraints preventing race-condition double bookings

## 5. Audit Logging & Compliance
- [x] Dedicated `audit_logs` table recording user logins, registrations, bookings, cancellations, and prescriptions
- [x] Recording of client IP addresses and actor IDs
- [x] Correlation tracking with `X-Request-ID` header on every HTTP transaction
- [x] Exclusion of sensitive authentication tokens and passwords from logs

## 6. Infrastructure & Deployment Security
- [x] PostgreSQL database hosted in private subnets without public internet exposure
- [x] Encrypted database storage at rest using AWS KMS
- [x] TLS 1.3 encryption in transit terminated at Application Load Balancer
- [x] Non-root Docker execution user pattern for production containers
- [x] Secrets configured through environment variables rather than hardcoded files
