# NEEV — National Education Evidence & Verification System Architecture & Security Review

> **Document Version**: 1.0.0-PROD-AUDIT  
> **Classification**: Statutory Technical Architecture Specification & Security Audit  
> **Environments**: Local (`localhost:3000` / `127.0.0.1:8000`) & Production Cloud (`neev01.vercel.app` / `neev-api-eqq1.onrender.com`)  
> **Database**: PostgreSQL 16+ on Neon Cloud (`neondb`)

---

## 1. System Technology Stack

```
+-----------------------------------------------------------------------------------------+
|                                    NEEV TECHNOLOGY STACK                                |
+-----------------------------------------------------------------------------------------+
| Layer                  | Technology                 | Version      | Key Responsibilities            |
+------------------------+----------------------------+--------------+---------------------------------+
| Presentation / Client  | Next.js (App Router)       | 16.4.3       | Reactive UI, AppShell, SSR/PPR  |
| UI Framework           | React & TypeScript         | 19.3.0 / 5.x | Strictly-typed component tree   |
| Styling & Icons        | Tailwind CSS & Lucide      | 4.x / 1.61.0 | Regulatory UI, Accessible themes|
| API Core Gateway       | FastAPI / Starlette        | 0.115+ / 3.x | OpenAPI, REST endpoints, CORS   |
| Runtime & Language     | Python (CPython)           | 3.12.10      | Core service engines, pipelines |
| Async Database Driver  | asyncpg                    | 0.30.0       | High-throughput async connection|
| ORM & SQL Toolkit      | SQLAlchemy (2.0 Async)     | 2.0.38       | Relational models & migrations  |
| Migration Engine       | Alembic                    | 1.14.1       | Version-controlled schema DDL   |
| Database Engine        | PostgreSQL                 | 16.4 (Neon)  | ACID relational ledger & tables |
| Cryptography & Hash    | hashlib & bcrypt           | Standard/4.0 | HMAC-SHA256, bcrypt salt        |
| Automated QA Engine    | Playwright & pytest        | 1.64 / 9.1   | Real browser QA & unit tests    |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Core Architecture Diagrams

### 2.1 System Architecture Topology

```mermaid
flowchart TD
    subgraph ClientTier["Client Presentation Tier"]
        Browser["Modern Web Browser (Chromium / Edge / Safari)"]
        NextApp["Next.js 16 App Router (Vercel Edge / Node.js)"]
        AppShell["Authenticated AppShell & Navigation"]
        AuthContext["AuthProvider (In-Memory Token & Session Guard)"]
    end

    subgraph SecurityGateway["API Security & Middleware Gateway"]
        Uvicorn["Uvicorn ASGI Gateway (Render Cloud / Local)"]
        CorsMid["CORSMiddleware (Vercel & Local Allowlist)"]
        RateLimit["In-Memory Rate Limiter (IP/Route Scoped: 30 req/min)"]
        SecHeaders["Strict Security Headers (nosniff, DENY, XSS, CSP)"]
        LogRedactor["Sensitive Data Redaction Filter (APAAR / Passwords)"]
    end

    subgraph ApplicationCore["FastAPI Application Services (Python 3.12)"]
        AuthRouter["Authentication Router (/api/v1/auth)"]
        SubService["Submission & Roster Ingestion Pipeline"]
        RuleEngine["Deterministic Validation Engine (SCH/APA/INT)"]
        ConflictEngine["Cross-Institution Conflict Engine (DUP Rules)"]
        RiskEngine["Deterministic Risk Engine (6-Factor v1.0.0)"]
        CaseService["Regulatory Case Docket & Deliberation Engine"]
        VerifyService["Controlled Verification Token & Resolver"]
        ReportService["Sanitized Regulatory Report Generator"]
    end

    subgraph RelationalLedger["Relational Ledger (Neon Serverless PostgreSQL 16)"]
        Postgres[(PostgreSQL 16 Engine)]
        CoreTables["institutions, programmes, academic_years, approved_intake"]
        EnrolmentTables["enrolment_records, student_identities, enrolment_record_versions"]
        IntegrityTables["findings, finding_responses, evidence_metadata"]
        CaseTables["audit_cases, audit_case_findings, clarification_requests, decisions"]
        AuditTrail["audit_events (Append-Only Cryptographic Log)"]
        SessionStore["refresh_sessions (Hashed Tokens & Device Fingerprints)"]
    end

    subgraph ExternalAdapters["Simulated Government Integration Adapters"]
        DigiAdapter["DigiLocker / APAAR Identity Adapter"]
        AISHEAdapter["AISHE Institutional Master Adapter"]
        NADAdapter["National Academic Depository Adapter"]
        BoardAdapter["State Technical Education Board Adapter"]
    end

    Browser --> NextApp
    NextApp --> AuthContext
    AuthContext --> AppShell
    NextApp -->|HTTPS / REST API| Uvicorn

    Uvicorn --> CorsMid
    CorsMid --> RateLimit
    RateLimit --> SecHeaders
    SecHeaders --> LogRedactor

    LogRedactor --> AuthRouter
    LogRedactor --> SubService
    LogRedactor --> ConflictEngine
    LogRedactor --> RiskEngine
    LogRedactor --> CaseService
    LogRedactor --> VerifyService
    LogRedactor --> ReportService

    SubService --> Postgres
    ConflictEngine --> Postgres
    RiskEngine --> Postgres
    CaseService --> Postgres
    VerifyService --> Postgres
    ReportService --> Postgres
    AuthRouter --> SessionStore

    ConflictEngine -.-> DigiAdapter
    RiskEngine -.-> AISHEAdapter
    VerifyService -.-> NADAdapter
```

---

### 2.2 Login & Session Restoration Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User as Institutional / Regulatory User
    participant Browser as Browser (React App)
    participant AuthContext as AuthProvider (Client Memory)
    participant API as FastAPI Backend (/api/v1/auth)
    participant DB as PostgreSQL (refresh_sessions)

    User->>Browser: Enters email and password
    Browser->>API: POST /auth/login {email, password}
    API->>API: Validate bcrypt hash & active account status
    API->>DB: Record new refresh_session (token hash, IP, expiry)
    API-->>Browser: HTTP 200 OK
    Note over API,Browser: Header: Set-Cookie: refresh_token=...; HttpOnly; SameSite=Lax; Secure
    Note over API,Browser: Body: {access_token: "JWT...", user: {...}}

    Browser->>AuthContext: Store access_token in React memory (inMemoryToken)
    Browser->>Browser: Set localStorage("neev_session_active", "true")
    Browser->>Browser: Navigate to /overview

    Note over Browser,API: User triggers Full-Page Refresh (F5)
    Browser->>Browser: Memory wiped! inMemoryToken is null.
    AuthContext->>Browser: Reads localStorage("neev_session_active") -> true
    AuthContext->>API: POST /auth/refresh (Browser sends HttpOnly cookie automatically)
    API->>DB: Validate refresh token hash & rotation grace period (15s)
    API->>DB: Rotate refresh token & update session record
    API-->>AuthContext: HTTP 200 OK {access_token: "NewJWT...", user: {...}}
    AuthContext->>AuthContext: Set inMemoryToken with new JWT
    AuthContext->>API: GET /auth/me (Authorization: Bearer NewJWT)
    API-->>AuthContext: HTTP 200 OK {user_profile, roles, permissions, scopes}
    AuthContext-->>Browser: Session Restored! User remains on /overview.
```

---

### 2.3 Record Ingestion, Validation & Intake Reconciliation Flow

```mermaid
sequenceDiagram
    autonumber
    actor Admin as College Admin (DIT)
    participant UI as /submissions Dropzone
    participant Svc as SubmissionService
    participant Val as ValidationEngine
    participant DB as PostgreSQL Database

    Admin->>UI: Uploads student_roster.csv (max 10 MB)
    UI->>Svc: POST /batches/{batch_id}/file (multipart/form-data)
    Svc->>Svc: Compute SHA-256 batch file hash
    Svc->>DB: Insert SubmissionBatch (Status: VALIDATING)
    
    loop For each CSV row
        Svc->>Val: Validate row schema (SCH-001, SCH-002)
        Val->>Val: Check 12-digit APAAR format (APA-002)
        Val->>Val: Compute HMAC-SHA256 fingerprint (Zero cleartext APAAR)
        Val->>DB: Query ApprovedIntakeVersion for Programme
        Val->>Val: Check active enrolment count against ceiling (INT-002)
        Val-->>Svc: Row status (VALID / ERROR / WARNING)
    end

    Svc->>DB: Persist SubmissionRows & ValidationFindings
    Svc-->>UI: Return Batch Preview {valid_rows, error_rows, summary}
    UI-->>Admin: Displays pre-commit inspection table

    Admin->>UI: Clicks "Finalize Submission"
    UI->>Svc: POST /batches/{batch_id}/finalize
    Svc->>DB: Commit valid rows to enrolment_records (v1)
    Svc->>DB: Commit fingerprints to student_identities
    Svc->>DB: Generate SubmissionReceipt (RCT-2026-XXXX)
    Svc->>DB: Append immutable AuditEvent
    Svc-->>UI: Return receipt code and confirmation
```

---

### 2.4 Discrepancy-to-Resolution Lifecycle Flow

```mermaid
stateDiagram-v2
    [*] --> OPEN: Ingestion or Reconciliation detects DUP/INT rule violation

    OPEN --> AWAITING_INSTITUTION_RESPONSE: Regulatory Officer reviews and issues notice
    OPEN --> UNDER_REVIEW: Officer investigates directly

    AWAITING_INSTITUTION_RESPONSE --> RESPONSE_RECEIVED: College uploads evidence & written reply
    AWAITING_INSTITUTION_RESPONSE --> UNDER_REVIEW: Escalated due to pending deadline

    RESPONSE_RECEIVED --> UNDER_REVIEW: Officer reviews submitted proof

    UNDER_REVIEW --> RESOLVED: Legitimate student transfer verified (DUP-004)
    UNDER_REVIEW --> DISMISSED: Discrepancy confirmed erroneous
    UNDER_REVIEW --> ESCALATED: Unresolved violation forwarded to formal Audit Case Docket

    ESCALATED --> UNDER_REVIEW: Returned for further hearing
    ESCALATED --> RESOLVED: Resolved after sanction compliance

    RESOLVED --> [*]
    DISMISSED --> [*]
```

---

### 2.5 Role-Based Authorization & Institutional Scope Model

```mermaid
erDiagram
    USER ||--o{ USER_ROLE : "has"
    ROLE ||--o{ USER_ROLE : "assigned to"
    ROLE ||--o{ ROLE_PERMISSION : "grants"
    PERMISSION ||--o{ ROLE_PERMISSION : "defined in"
    USER ||--o{ USER_SCOPE : "scoped by"
    INSTITUTION ||--o{ USER_SCOPE : "bounds"
    USER ||--o{ REFRESH_SESSION : "holds"
    INSTITUTION ||--o{ PROGRAMME : "offers"
    PROGRAMME ||--o{ ENROLMENT_RECORD : "contains"
    USER ||--o{ AUDIT_EVENT : "authors"

    USER {
        uuid id PK
        string email_normalized UK
        string password_hash
        string display_name
        string account_status "active|suspended"
    }

    ROLE {
        uuid id PK
        string code "AICTE_ADMIN|INSTITUTION_ADMIN|AUDITOR"
        string name
    }

    USER_SCOPE {
        uuid id PK
        uuid user_id FK
        string scope_type "NATIONAL|INSTITUTION"
        uuid institution_id FK "nullable for NATIONAL"
    }

    INSTITUTION {
        uuid id PK
        string official_institution_code UK
        string name
        string status "ACTIVE|SUSPENDED"
    }
```

---

### 2.6 Record Movement & Version History Data Flow

```mermaid
flowchart LR
    CSV[CSV Ingestion Roster] --> Batch[submission_batches]
    Batch --> Parser[Row Parser & Sanitize]
    Parser --> Fingerprint[HMAC-SHA256 Fingerprint Generator]
    Fingerprint --> Ident[student_identities]
    Parser --> Records[enrolment_records v1]
    
    Records --> Correction{Admin Correction\nHIS-001 / HIS-002}
    Correction -->|Archive Snapshot| Versions[enrolment_record_versions]
    Correction -->|Increment Version| Records
    Correction -->|Log Diff| Audit[audit_events Append-Only]

    Records --> Conflict[Conflict Detection Engine]
    Conflict --> Findings[findings DUP-001..004]
    Findings --> Risk[Risk Engine 6-Factors]
    Risk --> Queue[risk_calculations Queue]
    Queue --> Cases[audit_cases Docket]
```

---

## 3. Comprehensive Security Review Findings

| ID | Category | Severity | Item Checked | Status | Observation & Remediation |
|---|---|---|---|---|---|
| **SEC-001** | Authentication | **CRITICAL** | Password Hashing Standard | **PASS** | `bcrypt` (12 rounds) enforced. Zero plaintext storage. |
| **SEC-002** | Authentication | **CRITICAL** | Session Token Storage | **PASS** | Access tokens kept strictly in memory; refresh tokens in `HttpOnly`, `SameSite=lax` cookies. Project Bible directive compliant. |
| **SEC-003** | Authorization | **HIGH** | Tenant Isolation Scoping | **PASS** | `enforce_institution_scope` strictly bounds institutional admins to their own college records. Cross-tenant access returns `HTTP 403`. |
| **SEC-004** | Privacy | **CRITICAL** | Student Identity Protection (APAAR) | **PASS** | Raw 12-digit APAAR numbers are never stored in cleartext. Deterministic HMAC-SHA256 comparison fingerprints are computed with an isolated secret key. |
| **SEC-005** | Privacy | **HIGH** | Data Redaction in Logging | **PASS** | `setup_secure_logging()` intercepts standard and logger output, redacting passwords, tokens, and 12-digit number patterns matching APAAR format. |
| **SEC-006** | Integrity | **HIGH** | Optimistic Concurrency Control | **PASS** | `HIS-002` prevents overwrite races during record corrections via `expected_version` checks. Returns `HTTP 409 Conflict` on mismatch. |
| **SEC-007** | Integrity | **HIGH** | Mandatory Rationale Enforcement | **PASS** | `HIS-001` and `WF-001` mandate documented rationales for record modifications, state machine transitions, and case openings. |
| **SEC-008** | Ingestion | **MEDIUM** | Formula Injection (CSV / Excel) | **PASS** | `sanitizeSpreadsheetCell` escapes dangerous spreadsheet calculation prefixes (`=`, `+`, `-`, `@`, `\t`, `\r`) with single quotes on export. |
| **SEC-009** | Availability | **MEDIUM** | Rate Limiting Enforcement | **PASS** | Middleware enforces 30 requests/minute limit on sensitive endpoints (`/auth/login`, `/auth/forgot-password`, `/verify`). Returns `HTTP 429`. |
| **SEC-010** | Infrastructure | **HIGH** | Security Response Headers | **PASS** | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1`, strict `Referrer-Policy`, and `Permissions-Policy` active. |
| **SEC-011** | Public Portal | **MEDIUM** | Controlled Verifications Disclosure | **PASS** | `/verify` strictly discloses pre-approved claim subsets (name, programme, status). Sensitive attributes (APAAR, admission date) are completely masked. |
| **SEC-012** | Database | **CRITICAL** | Database Engine Constraint | **PASS** | SQLite is explicitly prohibited by Pydantic model validator. System runs exclusively on enterprise PostgreSQL 16+. |

