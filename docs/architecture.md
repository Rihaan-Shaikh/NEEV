# NEEV Architecture Documentation — Phase 1 & Phase 2

## 1. System Overview
NEEV is engineered as a secure, modular monolith consisting of:
- **Frontend Layer**: Next.js (App Router, React 19, TypeScript) styled with Tailwind CSS according to NEEV's restrained cream, charcoal, and gold design tokens. Features accessible sentence-case typography, collapsible/expandable navigation sidebar with tooltip overlays, responsive layouts, and zero hardcoded data.
- **Backend Layer**: FastAPI (Python 3.12) with Pydantic V2 request/response schemas, dependency-injected policies, and layered service modules (`ConflictDetectionService`, `FindingService`, `EnrolmentCorrectionService`, `EvidenceService`, `NotificationService`).
- **Data Access & Storage**: SQLAlchemy 2.x ORM with async database sessions (`asyncpg`) and Alembic version-controlled migrations located in `backend/migrations/`. PostgreSQL 16+ is the sole supported database across development, testing, staging, and production (SQLite is strictly prohibited in all environments).

## 2. Security Boundaries & Institutional Scope
1. **Authentication & Session Lifecycle**:
   - Access tokens are short-lived signed JWTs held exclusively in client memory (never stored in `localStorage` or `sessionStorage`).
   - Refresh tokens are delivered via `HttpOnly`, `SameSite=Lax` cookies.
   - Client API requests coordinate token refreshes through a singleton in-flight promise (`coordinateTokenRefresh`), preventing race conditions and competing refresh storms.
   - Refresh tokens are tracked in `refresh_sessions` via SHA-256 hashes (never plaintext).
   - Replay of previously rotated tokens triggers immediate session-family revocation.
   - Logout is idempotent and safely terminates active server-side sessions.
2. **Password Recovery & Account Provisioning**:
   - Password reset requests produce cryptographically secure, unpredictable 32-byte tokens hashed with SHA-256 in `password_reset_tokens`.
   - Responses are generic to prevent account enumeration.
   - Successful reset updates the bcrypt password hash, invalidates the reset token immediately, and terminates all active refresh sessions.
   - Account creation is controlled: public self-registration is disabled; accounts and scopes are provisioned by authorized administrators.
3. **Institutional Isolation**:
   - Every protected object request validates the actor's permitted `user_scopes`.
   - Direct object identifier tampering in queries or URLs fails with HTTP 403 Forbidden.
   - Scope checks are applied directly in database queries and service boundaries.
4. **Identifier Protection**:
   - APAAR identifiers are masked by default (`••••-••••-XXXX`).
   - Exact-matching uses a keyed HMAC-SHA256 fingerprint with a secret server-side pepper (`APAAR_FINGERPRINT_KEY`) to prevent rainbow table reverse lookups.
5. **Spreadsheet Formula Injection Neutralization**:
   - Values beginning with formula control characters (`=`, `+`, `-`, `@`, `\t`, `\r`) are escaped with a prepended single quote before spreadsheet export.

## 3. Deterministic Validation Engine (Phase 1)
Validation is rule-based, deterministic, explainable, and independent of frontend code:
- `SCH-001`: Required field missing
- `SCH-002`: Invalid date format
- `SCH-003`: Invalid enumeration
- `SCH-004`: Invalid programme reference
- `SCH-005`: Invalid academic year
- `SCH-006`: Intra-batch duplicate identifier
- `APA-001`: Missing APAAR identifier (recorded as unlinked quality warning)
- `APA-002`: Malformed APAAR identifier (must be 12-digit numeric)
- `APA-003`: Format valid but source unverified/simulated (distinct evidence state)
- `ENR-001`: Unsupported enrolment status
- `INT-001`: Approved intake capacity reference missing
- `INT-002`: Active count exceeds approved intake
- `INT-003`: Reported total differs from calculated count

## 4. Phase 2: Enrolment Integrity Ledger & Discrepancy Resolution

### 4.1 Cross-Institution Conflict Detection Engine
The conflict detection engine evaluates candidate records sharing the same protected comparison fingerprint (`apaar_comparison_fingerprint`) across institutions:
- `DUP-001`: Exact identifier conflict within a batch.
- `DUP-002`: Exact identifier conflict across institution records (simultaneous active enrolments in overlapping academic years).
- `DUP-003`: Potential duplicate requiring manual document review.
- `DUP-004`: Documented transfer or historical transition (student enrolled at Institution A with `TRANSFERRED` or `WITHDRAWN` status before or concurrently with Institution B).
- `HIS-001`: Material record change without required correction reason (minimum 10 characters).
- `HIS-002`: Record version mismatch during concurrent update (optimistic concurrency lock violation).
- `SRC-001`: Source provenance unavailable or incomplete.
- `SRC-002`: Simulated integration result presented for review.
- `WF-001`: Invalid finding-state transition.
- `WF-002`: Required response or resolution rationale missing (mandatory rationale for terminal transitions).

The reconciliation process is idempotent: re-running `/api/v1/integrity/reconcile` re-evaluates active conflicts, updates timestamps (`last_detected_at`), and does not duplicate existing active findings.

### 4.2 Immutable Enrolment Record Versioning
- Model: `EnrolmentRecordVersion` in table `enrolment_record_versions`.
- Uniqueness constraint: `UniqueConstraint("enrolment_record_id", "version_number", name="uq_enrolment_record_version")`.
- Optimistic Concurrency: `POST /api/v1/enrolments/{id}/corrections` requires `expected_version`. If the database `record_version` does not match `expected_version`, an HTTP 409 Conflict is raised (Rule `HIS-002`).
- Mandatory Reason: Every correction requires a documented `correction_reason` (Rule `HIS-001`).
- Automated Revalidation: After snapshot creation and record update, the conflict engine automatically revalidates conflicts for the affected student and updates relevant finding states.

### 4.3 Controlled Findings Lifecycle
Findings transition through a strictly governed state machine:
```
OPEN ───► AWAITING_INSTITUTION_RESPONSE ───► RESPONSE_RECEIVED ───► UNDER_REVIEW ───► RESOLVED
  │                                                                       │       ├──► DISMISSED
  └───────────────────────────────────────────────────────────────────────┘       └──► ESCALATED
```
- Endpoint: `POST /api/v1/findings/{id}/transition`.
- Validation: Validates source status against permitted transitions.
- Mandatory Rationale: Transitions to `RESOLVED`, `DISMISSED`, or `ESCALATED` require `rationale` with >= 10 characters (Rule `WF-002`).
- RBAC: Institutional admins can transition findings to `UNDER_REVIEW` or `RESPONSE_RECEIVED`; only national administrators (`AICTE_ADMIN`, `PLATFORM_ADMIN`) are authorized to execute terminal resolutions or dismissals.

### 4.4 Secure Evidence Management
- Upload: `POST /api/v1/findings/{id}/evidence`. Validates 10MB file limit, allowlisted content types (PDF, PNG, JPG), path sanitization, and SHA-256 cryptographic checksum calculation.
- Storage: Files stored in `backend/storage/evidence/` with random UUID names (`{uuid}_{sha256[:16]}.bin`), outside public web roots.
- Download: `GET /api/v1/evidence/{id}` streams file content via `FileResponse` with `content_disposition_type="attachment"`. Enforces institutional isolation: users can only download evidence associated with their own institution or findings where they are a party; national admins have system-wide access.
- Audit: Every upload and download generates an immutable `AuditEvent`.

### 4.5 Workflow Notifications System
- Model: `Notification` in table `notifications`.
- Scoped delivery: Filtered by recipient user ID, target institution ID, or role target.
- Endpoints: `GET /api/v1/notifications`, `GET /api/v1/notifications/unread-count`, `PATCH /api/v1/notifications/{id}/read`, `POST /api/v1/notifications/mark-all-read`.
- Triggered automatically on conflict detection, response submission, and lifecycle transitions.

## 5. Phase 3: AICTE Oversight & Regulatory Case Management

### 5.1 Relational Schema Architecture (Migration `dbb6316d7bec`)
Phase 3 extends the PostgreSQL schema with 7 forward-only, foreign-key-constrained tables without duplicating Phase 1/2 entities:
- `risk_calculations`: Immutable historical risk snapshots. Stores `institution_id`, `academic_year_id`, `total_score` (0–100), `risk_band`, `calculation_version` (`v1.0.0`), `input_snapshot` (JSON), `factors` (JSON), `completeness_state`, `explanation`, and `is_active` flag. Superseded calculations remain permanently in history.
- `audit_cases`: Formal regulatory investigation cases. References `institution_id`, `programme_id`, `academic_year_id`, `assigned_reviewer_id`, `status`, `priority`, `case_category`, `creation_rationale`, and `response_deadline`.
- `audit_case_findings`: Association table linking cases directly to canonical Phase 2 `Finding` records.
- `audit_case_events`: Complete audit event stream tracking state transitions, actions, and reviewer notes with `is_internal` visibility flag.
- `clarification_requests`: Formal inquiries issued to institutions. References `audit_case_id`, `institution_id`, `issuing_officer_id`, `status` (`PENDING_RESPONSE`, `RESPONSE_RECEIVED`, `EXPIRED`, `CANCELLED`), response explanation, evidence links, and response timestamps.
- `audit_case_decisions`: Immutable regulatory determinations. Stores `decision_type` (`RESOLVED`, `ESCALATED`, `CLOSED_NO_ACTION`), mandatory `decision_rationale` (>= 10 chars), `follow_up_action`, and reviewer identity.
- `report_jobs`: Background/asynchronous reporting tasks. Tracks `report_type`, `status` (`QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`), filters snapshot, output file path, row count, file size, and sanitized error messages.

### 5.2 Deterministic Risk Engine (`RiskEngineService` v1.0.0)
The risk engine operates strictly on deterministic application rules. Machine learning, LLM calls, probabilistic models, and automated penalties are strictly prohibited.
- **Factor 1: Capacity Discrepancy (Max 25 pts)**: Ratio of approved intake exceeded by active enrolments.
- **Factor 2: Unresolved Cross-Institution Conflict (Max 25 pts)**: Counts active `DUP-002` findings.
- **Factor 3: Identifier & Data Quality (Max 15 pts)**: Penalizes missing APAAR (`APA-001`), malformed identifiers (`APA-002`), and schema errors (`SCH-001`).
- **Factor 4: Unusual Roster Changes (Max 15 pts)**: Detects high correction velocity across enrolment records.
- **Factor 5: Source Reconciliation Gap (Max 10 pts)**: Missing approval intake baselines (`INT-001`).
- **Factor 6: Repeated Prior Findings (Max 10 pts)**: Persistent unresolved historical findings across cycles.
- **Risk Bands**:
  - `ROUTINE`: 0–19 points
  - `WATCH`: 20–39 points
  - `REVIEW_RECOMMENDED`: 40–59 points
  - `PRIORITY_REVIEW`: 60–100 points
- Scores serve solely as review-prioritization metrics and are never presented as fraud probabilities.

### 5.3 Audit Case Workflow & State Machine (`AuditCaseService`)
Cases follow an explicit, server-enforced state machine:
```
OPEN ───► ASSIGNED ───► UNDER_REVIEW ───► CLARIFICATION_REQUESTED ───► RESPONSE_RECEIVED ───► UNDER_REVIEW
  │          │               │                                                                    │
  │          │               └────────────────────────────────────────────────────────────────────┤
  └──────────┴────────────────────────────────────────────────────────────────────────────────────┼──► RESOLVED
                                                                                                  ├──► ESCALATED
                                                                                                  └──► CLOSED_NO_ACTION
```
- Validation: Direct jumps bypassing review or illegal transitions are rejected with HTTP 422.
- Assignment: Validates that assignee exists, is active, and possesses regulatory reviewer permissions (`REGULATOR_OFFICER` or `SYSTEM_ADMIN`).
- Reviewer Notes: Internal notes (`is_internal = True`) are visible only to regulatory officers and filtered out of all institutional responses.
- Decisions: Terminal determinations require mandatory rationale (>= 10 chars) and record immutable events.

### 5.4 Clarification Workflow
1. An authorized regulatory officer issues a clarification request specifying reference, subject, instructions, and deadline.
2. The case status automatically transitions to `CLARIFICATION_REQUESTED` and an in-app notification is dispatched to the institution.
3. The authorized institution administrator submits a formal response with explanation.
4. The case transitions to `RESPONSE_RECEIVED`, durable timestamps are recorded, and the reviewer is notified.
5. All communications are preserved in the case timeline.

### 5.5 Regulatory Reporting Subsystem (`ReportingService`)
The reporting engine generates verified CSV artifacts from real PostgreSQL tables with strict security controls:
1. **Report Catalogue (10 Standard Reports)**:
   - `INSTITUTION_ENROLMENT_RECONCILIATION`: Institution-level enrolment counts, active enrolments, and capacity baseline.
   - `PROGRAMME_INTAKE_VARIANCE`: Approved intake, active enrolment, variance, and status per programme.
   - `DATA_QUALITY_SUMMARY`: Completeness percentages and schema validation metrics.
   - `IDENTIFIER_COVERAGE_VALIDATION`: APAAR coverage, valid format percentages, and unverified source counts.
   - `DUPLICATE_CONFLICT_FINDINGS`: Canonical list of active duplicate and cross-institution conflicts.
   - `FINDING_RESOLUTION_PERFORMANCE`: Average response turnaround and resolution rates.
   - `SUBMISSION_TIMELINESS`: Timeliness of roster batch submissions across academic cycles.
   - `AUDIT_CASE_STATUS_OUTCOMES`: Open and resolved cases, assigned reviewers, and recorded outcomes.
   - `HISTORICAL_RECORD_CHANGES`: Audit trail of enrolment record corrections and version history.
   - `STATE_PROGRAMME_AGGREGATES`: Macro aggregate enrolments and capacities grouped by state code.
2. **Spreadsheet Formula Injection Neutralization**:
   - Every exported cell beginning with dangerous formula characters (`=`, `+`, `-`, `@`, `\t`, `\r`) is neutralized with a prepended single quote (`'`).
3. **Tenant Isolation**:
   - Non-national users can generate and download reports strictly for their assigned institution ID. Downloading reports belonging to another institution is rejected with HTTP 403 Forbidden.

### 5.6 Oversight Dashboards (`DashboardOversightService`)
- **National Oversight Dashboard (`GET /api/v1/dashboard/national`)**: Calculates 12 statutory metrics directly from PostgreSQL, including covered institutions, programmes with intake, submitted vs active enrolments, submission completion rate, APAAR validity rate, unresolved conflicts, intake reviews needed, open cases, and risk band distribution.
- **Institution Dashboard (`GET /api/v1/dashboard/institution/{id}`)**: Scoped view providing institutional submission progress, intake reconciliation summary, open findings, clarification requests, and risk band. Enforces strict tenant boundaries.

## 6. Phase 4: Final Implementation, Verification References, Integrations & Security Hardening

### 6.1 Limited-Purpose Verification References (`VerificationService`)
1. **Opaque Bearer Token Architecture**:
   - Issued via `POST /api/v1/verification-references` for eligible enrolment records within the caller's authorized institutional scope.
   - Generates a high-entropy bearer token (`neev_vrf_<40_hex_chars>`).
   - The raw token is returned to the client strictly once in the creation response and is **never stored in plaintext**.
   - PostgreSQL stores only `reference_token_hash = sha256(raw_token)` and an opaque public reference code `VRF-2026-<8_hex_chars>`.
2. **Privacy-Preserving Disclosure Profiles**:
   - Authorized issuers select an allowlist of permitted claims: student name, programme, institution, enrolment status, academic year, and admission date.
   - Raw APAAR identifiers and comparisons keys are **strictly prohibited** from disclosure profiles.
3. **Atomic Concurrency & Row Locking**:
   - Resolving references via `POST /api/v1/verify` executes within an explicit database transaction using PostgreSQL row locking:
     ```python
     select(VerificationReference).where(...).with_for_update(of=VerificationReference)
     ```
   - Prevents race conditions where concurrent requests could exceed configured `max_uses`.
4. **Revocation & Audit**:
   - Issuers can revoke active references via `POST /api/v1/verification-references/{id}/revoke` requiring a mandatory rationale (>= 5 characters).
   - An immutable audit event is appended to `audit_events` and verification access attempts are recorded in `verification_access_logs`.
5. **Synthetic Demonstration Disclaimer**:
   - All verification results return the mandatory statutory disclaimer:
     > **Synthetic demonstration — not an official APAAR verification.**

### 6.2 External Source Integrations Status (`IntegrationService`)
1. **Source Reliability & Transparency Center (`GET /api/v1/integrations/status`)**:
   - Tracks 5 educational and regulatory source adapters:
     - `APAAR_DIGILOCKER`: DigiLocker Student Identity & Academic Records API
     - `AISHE_PORTAL`: All India Survey on Higher Education Registry
     - `NAD_PORTAL`: National Academic Depository
     - `STATE_TECH_BOARD`: State Technical Education Directorate Portals
     - `AICTE_APPROVAL_PORTAL`: AICTE Institution & Programme Approval Registry
2. **Simulation Guarantee**:
   - Every adapter explicitly exposes its simulation flag (`is_simulated = True`), health status, latency, supported claims, and known limitations.
   - Zero live government endpoints are fabricated; results clearly state prototype status.
3. **Simulated Contract Probing (`POST /api/v1/integrations/{adapter_code}/test-contract`)**:
   - Executes non-mutating simulated contract tests to verify response latency and schema compliance.

### 6.3 Operational Security & Hardening
1. **Startup Configuration Validation (`app/core/config.py`)**:
   - Enforces PostgreSQL as the sole database dialect; SQLite is strictly rejected.
   - In staging and production environments (`ENVIRONMENT=production`), startup fails immediately if `SECRET_KEY` or `APAAR_FINGERPRINT_KEY` use development placeholders or are less than 32 characters long.
2. **Security Response Headers Middleware (`app/main.py`)**:
   - Automatically injects defensive headers on all responses:
     - `X-Content-Type-Options: nosniff`
     - `X-Frame-Options: DENY`
     - `X-XSS-Protection: 1; mode=block`
     - `Referrer-Policy: strict-origin-when-cross-origin`
     - `Permissions-Policy: geolocation=(), camera=(), microphone=()`
     - `Cache-Control: no-store, no-cache, must-revalidate` on sensitive authentication, verification, and reporting endpoints.
3. **Sensitive Route Rate Limiting**:
   - In-memory rate limiting applied to `/api/v1/auth/login`, `/api/v1/auth/forgot-password`, and `/api/v1/verify` (30 requests/minute per IP) returning HTTP 429 `RATE_LIMIT_EXCEEDED` with `Retry-After: 60`.
4. **Sensitive Data Redaction Filter (`app/core/logging_config.py`)**:
   - `SensitiveDataRedactingFilter` intercepts all log records:
     - 12-digit numeric patterns matching APAAR are masked as `••••-••••-XXXX`.
     - Passwords, bearer tokens, and secrets in strings or query logs are replaced with `[REDACTED_SECRET]` and `[REDACTED_TOKEN]`.

### 6.4 PostgreSQL Disaster Recovery & Backup Drill
1. **Automated Drill Script (`scripts/backup_restore_drill.py`)**:
   - Dumps `neev_dev` using `pg_dump -Fc` (custom compressed format).
   - Restores dump into an isolated target database `neev_restore_test` using `pg_restore`.
   - Iterates through all 39 PostgreSQL relational tables in `information_schema.tables`, comparing row counts between source and restored database.
   - Verified 100% parity across all tables with zero data corruption or relationship loss.

