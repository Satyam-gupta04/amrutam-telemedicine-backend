# Threat Model & Security Analysis

## 1. Attack Surface Analysis
Amrutam's Telemedicine backend exposes REST endpoints to patients, doctors, and system administrators. The primary vectors include:
- **Authentication Endpoints (`/auth/login`, `/auth/register`):** Potential brute force, credential stuffing, and account enumeration.
- **Booking & Scheduling (`/bookings`):** Concurrency race conditions, denial of service through rapid slot hoarding, and replay attacks.
- **Medical Records & Prescriptions (`/consultations/{id}/prescriptions`):** Unauthorized disclosure of protected health information (PHI), tampering with prescriptions, and privilege escalation.
- **Administrative APIs (`/admin/*`):** Targeted privilege escalation or unauthorized data exfiltration.

---

## 2. OWASP Top 10 Mitigations

| OWASP Risk | Threat Description | Implemented Mitigation in Amrutam Backend |
|---|---|---|
| **A01: Broken Access Control** | Patient reading another patient's medical history or issuing prescriptions. | Explicit role verification (`require_roles`) and ownership validation checking `consultation.patient_id == current_user.id` or `doctor.user_id == current_user.id`. |
| **A02: Cryptographic Failures** | Cleartext passwords or exposed secrets. | Passwords hashed using PBKDF2-HMAC-SHA256 with 100,000 iterations and system salt. Sensitive env vars stored outside code repository. TLS 1.3 enforced for transport. |
| **A03: Injection** | SQL injection in queries or search parameters. | SQLAlchemy ORM parameterized queries used across all database calls. Direct raw SQL strings are completely excluded. |
| **A04: Insecure Design** | Double-booking slots or race conditions. | Database transaction isolation with row-level locks (`SELECT ... FOR UPDATE`), unique slot constraints, and mandatory idempotency key handling. |
| **A05: Security Misconfiguration** | Debug logs displaying tokens or credentials in production. | Sensitive fields (passwords, tokens, MFA secrets) explicitly filtered from responses and audit logs. Default debug disabled via configuration. |
| **A06: Vulnerable & Outdated Components** | Vulnerable packages in supply chain. | Automated dependency scanning using Dependabot and pinned versions in `requirements.txt`. |
| **A07: Identification & Auth Failures** | Session hijacking or credential theft. | Signed JWT access tokens with 60-minute expiration, Argon2/PBKDF2 password security, and optional TOTP Two-Factor Authentication. |
| **A08: Software & Data Integrity Failures** | Replay of financial or booking transactions. | Header-based idempotency keys with SHA-256 request payload hashing preventing duplicated state changes. |
| **A09: Security Logging & Monitoring Failures** | Undetected unauthorized access attempts. | Immutable `audit_logs` table recording actor ID, action name, resource ID, IP address, and timestamp for all critical transactions. |
| **A10: Server-Side Request Forgery (SSRF)** | Exploitation of internal network through external URL fetches. | No outbound URL fetching based on arbitrary client-supplied addresses. Video room links are server-generated UUIDs. |

---

## 3. Data Classification

| Classification Level | Examples | Security Controls Applied |
|---|---|---|
| **Public** | Doctor names, bios, specializations, consultation fees | Public read APIs with rate-limiting protection. |
| **Confidential / Internal** | System metrics, application error traces, aggregated booking statistics | Restricted to Admin role with authenticated JWT tokens. |
| **Strictly Confidential / PHI** | Diagnoses, medications, consultation notes, patient phone numbers | AES-256 encrypted at rest in PostgreSQL, TLS 1.3 in transit, strict RBAC ownership check. |
| **Credentials & Secrets** | Password hashes, JWT secrets, MFA keys | Salted PBKDF2/Argon2 hashes, never returned in API payloads, stored in environment variables. |

---

## 4. Key & Secret Rotation Procedure
1. **JWT Secret Keys:** Rotated periodically with support for a dual-key grace window during transitions.
2. **Database Credentials:** Managed via AWS Secrets Manager with automated 90-day rotation and IAM database authentication where available.
3. **MFA Secrets:** Bound directly to user record and re-generated on user request.
