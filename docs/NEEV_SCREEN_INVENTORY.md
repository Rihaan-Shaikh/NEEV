# NEEV — Complete Product Screen & Actionable Control Inventory

> **Document Version**: 1.0.0-PROD-AUDIT  
> **Verification Status**: Verified via Real Browser Automation (Playwright / Chromium Engine)  
> **Environments Tested**:  
> - Local Development: `http://localhost:3000` (Frontend) / `http://127.0.0.1:8000` (FastAPI Core)  
> - Production Cloud: `https://neev01.vercel.app` (Vercel Edge) / `https://neev-api-eqq1.onrender.com` (Render Core)  
> **Database Engine**: Neon Serverless PostgreSQL 16+ (`neondb`)

---

## 1. Executive Screen Directory

| Screen ID | Screen Name | Route | Category | Access Scope / Role | Test Status | Evidence Reference |
|---|---|---|---|---|---|---|
| **SCR-PUB-01** | Public Landing & Regulatory Portal | `/` | Public | Unauthenticated / All | **PASS** | `docs/evidence/01_landing_page.png` |
| **SCR-PUB-02** | Security Gateway & Sign In | `/login` | Authentication | Unauthenticated / All | **PASS** | `docs/evidence/02_login_page_unauthenticated.png` |
| **SCR-PUB-03** | Password Recovery Request | `/forgot-password` | Authentication | Unauthenticated / All | **PASS** | `docs/evidence/03_forgot_password_page.png` |
| **SCR-PUB-04** | Password Reset Completion | `/reset-password` | Authentication | Token-Bearer / Public | **PASS** | `docs/evidence/04_reset_password_page.png` |
| **SCR-PUB-05** | Public Third-Party Verification Resolver | `/verify` | Verification | Public / Employers / Verifiers | **PASS** | `docs/evidence/05_public_verify_page.png` |
| **SCR-PUB-06** | Institutional Onboarding Application | `/register` | Registration | Prospective Institutions | **PASS** | `docs/evidence/06_register_page.png` |
| **SCR-PUB-07** | 404 Route Not Found Error Page | `/*` (Fallback) | Error | All | **PASS** | `docs/evidence/07_not_found_page.png` |
| **SCR-CORE-01** | National & Institutional Oversight Dashboard | `/overview` | Oversight | Authenticated (All Roles) | **PASS** | `docs/evidence/10_post_login_overview.png` |
| **SCR-CORE-02** | Academic Programmes & Capacity Ledger | `/programmes` | Capacity | Authenticated (All Roles) | **PASS** | `docs/evidence/15_screen_programmes.png` |
| **SCR-CORE-03** | Student Enrolment Ledger & Version Trail | `/enrolments` | Records | Authenticated (All Roles) | **PASS** | `docs/evidence/16_screen_enrolments.png` |
| **SCR-CORE-04** | Batch Roster Ingestion & Dropzone | `/submissions` | Ingestion | `INSTITUTION_ADMIN`, `AICTE_ADMIN` | **PASS** | `docs/evidence/17_screen_submissions.png` |
| **SCR-CORE-05** | Discrepancy Findings Registry | `/findings` | Integrity | Authenticated (All Roles) | **PASS** | `docs/evidence/18_screen_findings.png` |
| **SCR-CORE-06** | Finding Detail & Resolution State Machine | `/findings/[id]` | Integrity | Authenticated (Scoped) | **PASS** | `docs/evidence/19_screen_finding_detail.png` |
| **SCR-CORE-07** | Deterministic Risk Prioritization Queue | `/risk-queue` | Oversight | Authenticated (All Roles) | **PASS** | `docs/evidence/20_screen_risk_queue.png` |
| **SCR-CORE-08** | Regulatory Audit Case Docket & Docket Index | `/cases` | Governance | `AICTE_ADMIN`, `AICTE_OFFICER`, `AUDITOR` | **PASS** | `docs/evidence/21_screen_cases.png` |
| **SCR-CORE-09** | Audit Case Dossier, Notes & Determination | `/cases/[id]` | Governance | Regulatory Reviewers / Scoped | **PASS** | `docs/evidence/22_screen_case_detail.png` |
| **SCR-CORE-010** | Technical Institutions Directory | `/institutions` | Institutions | Authenticated (All Roles) | **PASS** | `docs/evidence/23_screen_institutions.png` |
| **SCR-CORE-011** | Institutional Risk Profile Breakdown | `/institutions/[id]/risk-profile`| Oversight | Authenticated (Scoped) | **PASS** | `docs/evidence/24_screen_institution_risk_profile.png` |
| **SCR-CORE-012** | Regulatory Reports Catalog & Export Queue | `/reports` | Reporting | Authenticated (Role-governed) | **PASS** | `docs/evidence/25_screen_reports.png` |
| **SCR-CORE-013** | Verification Reference Governance | `/verification-references` | Verification | `INSTITUTION_ADMIN`, `AICTE_ADMIN` | **PASS** | `docs/evidence/26_screen_verification_references.png` |
| **SCR-CORE-014** | External Integration Adapters Telemetry | `/integrations` | System Health | Authenticated (All Roles) | **PASS** | `docs/evidence/27_screen_integrations.png` |
| **SCR-CORE-015** | Regulatory Notifications & Event Center | `/notifications` | Activity | Authenticated (All Roles) | **PASS** | `docs/evidence/28_screen_notifications.png` |

---

## 2. In-Depth Screen Analysis

### SCR-PUB-01: Public Landing & Regulatory Portal
* **Route**: `/`
* **Purpose**: Public entryway communicating NEEV's statutory mandate under AICTE, core capabilities, real-time platform metrics, and direct links to authenticated portals and public verification.
* **Intended User**: Public, students, institutional leaders, regulatory evaluators.
* **Preconditions**: None. Open to public internet without authentication.
* **Navigation Path**: Direct URL access or clicking the NEEV emblem from header.
* **Main UI Components**:
  * Regulatory Emblem banner with Government of India and AICTE branding.
  * Hero Section: "National Education Evidence & Verification" tagline "Proof Behind Every Record".
  * Direct action buttons: "Launch Platform / Sign In" (`/login`), "Public Verification Resolver" (`/verify`), "Register Institution" (`/register`).
  * Architecture feature highlights: Intake Reconciliation, Cryptographic Duplicate Detection, Versioned Audit Ledger, Explainable Risk Scoring.
* **Available Controls & Verified Actions**:
  * `Sign In` Button -> Navigates to `/login` [Verified PASS].
  * `Verify Reference` Button -> Navigates to `/verify` [Verified PASS].
  * `Register Institution` Button -> Navigates to `/register` [Verified PASS].
* **Backend APIs Used**: None (static public page).
* **Validation & Error Behavior**: Clean client-side rendering with full responsiveness across desktop and mobile viewports.
* **Browser Test Evidence**: `docs/evidence/01_landing_page.png`.

---

### SCR-PUB-02: Security Gateway & Sign In
* **Route**: `/login`
* **Purpose**: Secure credential-based access gateway issuing short-lived in-memory JWT access tokens and partitioned `HttpOnly` refresh session cookies.
* **Intended User**: All registered regulatory officers, institution admins, data operators, auditors.
* **Preconditions**: Unauthenticated. If user is already authenticated, AppShell redirects to `/overview`.
* **Navigation Path**: Direct navigation or clicking "Sign In" from any unauthenticated screen.
* **Main UI Components**:
  * Email input (`input[type="email"]`).
  * Password input (`input[type="password"]`) with masked character security.
  * Submit button ("Sign In to NEEV").
  * Secondary links: "Forgot Password?" (`/forgot-password`), "Register New Institution" (`/register`), "Public Verification Resolver" (`/verify`).
  * Alert display banner for authentication rejections.
* **Available Controls & Verified Actions**:
  * Form Submission with Invalid Credentials -> Renders alert banner: "Invalid email or password" [Verified PASS].
  * Form Submission with Suspended User (`disabled.user@neev.aicte.gov.in`) -> Renders alert: "Account is suspended. Please contact regulatory administrator" [Verified PASS].
  * Form Submission with Valid Admin Credentials -> Authenticates, sets `inMemoryToken`, establishes `SameSite=lax` cookie, sets `neev_session_active=true` in localStorage, and redirects to `/overview` [Verified PASS].
  * "Forgot Password?" Link -> Navigates to `/forgot-password` [Verified PASS].
* **Backend APIs Used**: `POST /api/v1/auth/login`.
* **Database Entities**: `users`, `roles`, `user_roles`, `user_scopes`, `refresh_sessions`, `audit_events`.
* **Security & Hardening**:
  * Rate-limited at 30 requests/minute per client IP via FastAPI middleware (`HTTP 429`).
  * Passwords hashed with `bcrypt` (12 rounds). Zero plaintext passwords stored.
  * User emails normalized to lower-case.
* **Browser Test Evidence**: `docs/evidence/02_login_page_unauthenticated.png`, `docs/evidence/08_invalid_login_feedback.png`, `docs/evidence/09_suspended_user_login.png`.

---

### SCR-PUB-03: Password Recovery Request
* **Route**: `/forgot-password`
* **Purpose**: Allows authorized personnel who lost access to initiate a secure out-of-band password reset request.
* **Intended User**: Registered users needing password recovery.
* **Preconditions**: Publicly accessible.
* **Navigation Path**: Link on `/login` or direct URL.
* **Main UI Components**:
  * Official email input field.
  * "Send Recovery Instructions" button.
  * Back to sign-in link (`/login`).
  * Success confirmation banner.
* **Available Controls & Verified Actions**:
  * Submit Email -> Calls `POST /api/v1/auth/forgot-password`. Emits generic timing-safe success message ("If an account is associated with this email, recovery instructions have been dispatched") to prevent user enumeration attacks [Verified PASS].
* **Backend APIs Used**: `POST /api/v1/auth/forgot-password`.
* **Database Entities**: `password_reset_tokens`, `users`, `audit_events`.
* **Browser Test Evidence**: `docs/evidence/03_forgot_password_page.png`.

---

### SCR-PUB-04: Password Reset Completion
* **Route**: `/reset-password`
* **Purpose**: Token-gated screen allowing a user possessing a valid cryptographic recovery token to set a new compliant password.
* **Intended User**: Recovering user.
* **Preconditions**: Requires URL query param `?token=<reset_token>`.
* **Main UI Components**:
  * New password and password confirmation inputs.
  * "Update Password" button.
  * Error callout if token is missing, expired, or previously consumed.
* **Available Controls & Verified Actions**:
  * Loaded without token -> Shows clean error alert: "Password reset token is missing or invalid. Please request a new link." [Verified PASS].
  * Submit valid token + compliant password -> Calls `POST /api/v1/auth/reset-password`, invalidates all active sessions for the user, commits new hash, and redirects to `/login` [Verified PASS via test suite].
* **Backend APIs Used**: `POST /api/v1/auth/reset-password`.
* **Database Entities**: `password_reset_tokens`, `users`, `refresh_sessions`, `audit_events`.
* **Browser Test Evidence**: `docs/evidence/04_reset_password_page.png`.

---

### SCR-PUB-05: Public Third-Party Verification Resolver
* **Route**: `/verify`
* **Purpose**: Zero-knowledge verification portal allowing third parties (background screening agencies, prospective employers, state boards) to verify student enrolment credentials using single-use bearer tokens or reference codes without gaining access to the student's full regulatory record or APAAR identity.
* **Intended User**: External verifiers, employers, students.
* **Preconditions**: None. Rate-limited public portal.
* **Navigation Path**: Direct URL access or link from login page.
* **Main UI Components**:
  * Verification Reference Input: Code (`VRF-2026-XXXX`) or raw bearer token (`neev_vrf_...`).
  * Purpose selection tag / confirmation disclaimer.
  * "Verify Record" primary action button.
  * Structured Disclosed Claims Card:
    * Student Full Name
    * Institution Name
    * Programme Code and Title
    * Enrolment Status (e.g. `ACTIVE`)
    * Academic Year
    * Verification Timestamp & Cryptographic Verification Badge.
* **Available Controls & Verified Actions**:
  * Enter sample valid reference code `VRF-2026-DIT001` -> Resolves immediately; presents verified credentials of student Aarav Sharma at Delhi Institute of Technology; increments usage counter in database; logs access audit event with client IP hash [Verified PASS].
  * Enter invalid or expired token -> Displays error banner: "Verification token invalid, expired, or maximum allowed queries exceeded." [Verified PASS].
* **Backend APIs Used**: `POST /api/v1/verify`.
* **Database Entities**: `verification_references`, `verification_access_logs`, `enrolment_records`, `institutions`, `programmes`.
* **Security & Hardening**:
  * Rate-limited at 30 requests/minute.
  * APAAR identifier is strictly excluded from disclosure payloads under all conditions.
* **Browser Test Evidence**: `docs/evidence/05_public_verify_page.png`, `docs/evidence/05b_public_verify_result.png`.

---

### SCR-PUB-06: Institutional Onboarding Application
* **Route**: `/register`
* **Purpose**: Self-service institutional registration interface for new technical colleges applying to join the NEEV verification network.
* **Intended User**: College Principals, Registrar officers.
* **Preconditions**: Unauthenticated.
* **Main UI Components**:
  * Official AICTE Institution Permanent ID input.
  * Legal Institution Name and Type (Central University, State University, Private Aided, Deemed).
  * State and District dropdown selectors.
  * Administrative Officer Email & Phone.
  * Supporting approval letter reference number.
  * "Submit Registration Application" button.
* **Available Controls & Verified Actions**:
  * Submit Valid Registration -> Submits `POST /api/v1/institutions`, records institution in `PENDING_APPROVAL` status, creates audit event [Verified PASS].
* **Backend APIs Used**: `POST /api/v1/institutions`.
* **Database Entities**: `institutions`, `audit_events`.
* **Browser Test Evidence**: `docs/evidence/06_register_page.png`.

---

### SCR-PUB-07: 404 Route Not Found Error Page
* **Route**: Fallback route `/_not-found`
* **Purpose**: Prevents white-screen or stack-trace crashes when an invalid URL is entered, guiding users safely back to the portal.
* **Intended User**: All users.
* **Main UI Components**:
  * 404 Header with NEEV Shield emblem.
  * Plain-language explanation: "The page you are looking for does not exist or has been moved."
  * "Return to Dashboard / Home" button.
* **Browser Test Evidence**: `docs/evidence/07_not_found_page.png`.

---

### SCR-CORE-01: National & Institutional Oversight Dashboard
* **Route**: `/overview`
* **Purpose**: Executive control center providing real-time regulatory oversight metrics, intake capacity reconciliation, discrepancy summaries, and multi-factor risk distributions.
* **Intended User**:
  * **National Officers (`AICTE_ADMIN`, `AICTE_OFFICER`, `AUDITOR`)**: Country-wide perspective across all institutions.
  * **Institutional Leaders (`INSTITUTION_ADMIN`, `INSTITUTION_OPERATOR`)**: Tenant-scoped view restricted strictly to their own college.
* **Preconditions**: Authenticated session.
* **Navigation Path**: Sidebar navigation "Overview", or default post-login landing.
* **Main UI Components**:
  1. **Top Metric Cards**:
     * Total Enrolments (Live database count).
     * Active Enrolments (Students in `ACTIVE` statutory state).
     * Covered Institutions / Enrolled Programmes.
     * Approved Seat Capacity Utilization.
     * Open Discrepancy Findings count.
  2. **Academic Year Selector**: Dropdown to switch between `2024-2025` (Active), `2023-2024` (Historical), and `2025-2026` (Upcoming).
  3. **Capacity Reconciliation Table**:
     * Programme Code & Name.
     * Approved Intake (statutory AICTE sanction).
     * Active Enrolment count.
     * Seat Variance (+/-).
     * Compliance Badge (`BALANCED`, `UNDER_CAPACITY`, `CAPACITY_EXCEEDED`, `MISSING_REFERENCE`).
  4. **Risk Prioritization Summary**: Distribution chart showing counts of institutions in `ROUTINE`, `WATCH`, `REVIEW_RECOMMENDED`, and `PRIORITY_REVIEW`.
  5. **Recent Ingestion Batches**: Latest CSV rosters submitted with row-count, error-count, and receipt link.
* **Available Controls & Verified Actions**:
  * Academic Year Dropdown -> Re-fetches dashboard metrics for selected year [Verified PASS].
  * Full Page Browser Refresh (`F5`) -> Session cleanly restores via HttpOnly cookie; metrics immediately re-render without redirecting to login [Verified PASS].
  * Click on Discrepancy badge -> Navigates to `/findings` filtered by institution [Verified PASS].
* **Backend APIs Used**: `GET /api/v1/dashboard/national`, `GET /api/v1/dashboard/institution/{id}`, `GET /api/v1/academic-years`.
* **Database Entities**: `enrolment_records`, `programmes`, `approved_intake_versions`, `institutions`, `findings`, `risk_calculations`.
* **Browser Test Evidence**: `docs/evidence/10_post_login_overview.png`, `docs/evidence/11_session_persistence_after_refresh_overview.png`, `docs/evidence/14_screen_overview.png`, `docs/evidence/30_inst_admin_overview.png`.

---

### SCR-CORE-02: Academic Programmes & Capacity Ledger
* **Route**: `/programmes`
* **Purpose**: Regulatory ledger of all sanctioned academic degrees, qualification levels, discipline classifications, and version-controlled seat quotas.
* **Intended User**: All authenticated roles (National Admins manage; Institutions inspect).
* **Navigation Path**: Sidebar navigation item "Programmes".
* **Main UI Components**:
  * Search bar (filter by programme name or code).
  * Institution filter dropdown (National mode).
  * Data Table:
    * Programme Code (e.g. `BTECH-CSE`, `MTECH-AI`).
    * Title & Qualification Level (`UNDERGRADUATE`, `POSTGRADUATE`).
    * Academic Discipline.
    * Current Approved Intake Version & Seat Count.
    * Approval Letter Reference (`AICTE/EOA/2024-25/...`).
    * Status (`APPROVED`, `UNDER_REVIEW`, `DISCONTINUED`).
* **Available Controls & Verified Actions**:
  * Filter by Programme Code -> Instantly filters rows in browser [Verified PASS].
  * Page Refresh -> Session persists, 5 rows loaded [Verified PASS].
* **Backend APIs Used**: `GET /api/v1/programmes`, `GET /api/v1/programmes/{id}/intake`.
* **Database Entities**: `programmes`, `programme_approvals`, `approved_intake_versions`, `institutions`.
* **Browser Test Evidence**: `docs/evidence/12_session_persistence_after_refresh_programmes.png`, `docs/evidence/15_screen_programmes.png`.

---

### SCR-CORE-03: Student Enrolment Ledger & Version Trail
* **Route**: `/enrolments`
* **Purpose**: The statutory student enrolment database. Displays masked student identities, admission dates, categories, APAAR verification statuses, and complete immutable record version histories.
* **Intended User**: All authenticated roles (scoped by institution).
* **Navigation Path**: Sidebar navigation item "Enrolments".
* **Main UI Components**:
  * Search by Student Name or Institution Roll Number.
  * Filter by Enrolment Status (`ACTIVE`, `TRANSFERRED`, `WITHDRAWN`, `COMPLETED`, `SUSPENDED`).
  * Filter by APAAR Validation Status (`VERIFIED`, `MALFORMED`, `MISSING`, `SIMULATED`).
  * Data Table:
    * Roll Number & Student Full Name.
    * Masked APAAR ID (e.g. `XXXXXXXX1234` — raw 12-digit number is never sent to browser).
    * Institution & Programme.
    * Admission Category (General, OBC, SC, ST, EWS).
    * Supernumerary Quota (TFWS, J&K, NRI, PMSSS).
    * Current Record Version (`v1`, `v2`).
    * Actions: "View History", "Apply Correction".
  * **Enrolment History Drawer / Modal**:
    * Chronological version timeline showing changes, modified fields, documented reason (`HIS-001`), and acting user.
* **Available Controls & Verified Actions**:
  * Search by name -> Filters table dynamically [Verified PASS].
  * Direct URL navigation in fresh tab -> Restores session cleanly and renders table with 15 rows [Verified PASS].
* **Backend APIs Used**: `GET /api/v1/enrolments`, `GET /api/v1/enrolments/{id}`, `GET /api/v1/enrolments/{id}/history`, `POST /api/v1/enrolments/{id}/corrections`.
* **Database Entities**: `enrolment_records`, `enrolment_record_versions`, `student_identities`, `institutions`, `programmes`.
* **Browser Test Evidence**: `docs/evidence/13_direct_navigation_new_tab.png`, `docs/evidence/16_screen_enrolments.png`.

---

### SCR-CORE-04: Batch Roster Ingestion & Dropzone
* **Route**: `/submissions`
* **Purpose**: Primary operational ingestion pipeline for institutional student admissions. Supports CSV roster uploads, schema validation, row-by-row error detection, pre-commit previews, and statutory cryptographic submission receipts.
* **Intended User**: `INSTITUTION_ADMIN`, `INSTITUTION_OPERATOR`, `AICTE_ADMIN`.
* **Navigation Path**: Sidebar navigation item "Submissions".
* **Main UI Components**:
  * Drag-and-drop file upload zone accepting `.csv` files up to 10 MB.
  * Academic Year and Programme selector dropdowns.
  * Ingestion History Table:
    * Batch ID and Source Filename.
    * Upload Timestamp.
    * Processing Status (`PENDING`, `VALIDATING`, `PREVIEW_READY`, `COMPLETED`, `REJECTED`).
    * Statistics: Total Rows, Valid Rows, Rejected Rows, Flagged Warnings.
    * Action button: "View Preview", "Download Receipt".
  * Pre-commit Preview Modal: Shows parsed rows color-coded by validation outcome with rule codes (`SCH-001`, `APA-002`, `INT-002`).
* **Available Controls & Verified Actions**:
  * Dropzone rendered and interactive [Verified PASS].
  * Batches table rendered with historical submission records [Verified PASS].
* **Backend APIs Used**: `GET /api/v1/batches`, `POST /api/v1/batches`, `POST /api/v1/batches/{id}/file`, `GET /api/v1/batches/{id}/preview`, `POST /api/v1/batches/{id}/finalize`, `GET /api/v1/batches/{id}/receipt`.
* **Database Entities**: `submission_batches`, `submission_rows`, `submission_receipts`, `validation_runs`, `validation_findings`.
* **Browser Test Evidence**: `docs/evidence/17_screen_submissions.png`.

---

### SCR-CORE-05: Discrepancy Findings Registry
* **Route**: `/findings`
* **Purpose**: Centralized registry of all detected regulatory discrepancies: duplicate enrolments across colleges (`DUP-002`), intra-institution double enrolments (`DUP-001`), capacity exceedances (`INT-002`), and identifier anomalies.
* **Intended User**: All authenticated roles (tenant-scoped for colleges).
* **Navigation Path**: Sidebar navigation item "Findings".
* **Main UI Components**:
  * Filter by Severity: `CRITICAL`, `ERROR`, `WARNING`, `INFO`.
  * Filter by Status: `OPEN`, `AWAITING_INSTITUTION_RESPONSE`, `RESPONSE_RECEIVED`, `UNDER_REVIEW`, `RESOLVED`, `DISMISSED`, `ESCALATED`.
  * Findings Data Table:
    * Finding ID and Rule Code.
    * Primary Institution & Secondary Institution (for cross-college conflicts).
    * Detected Discrepancy Explanation.
    * Current State Badge.
    * Creation Date.
    * "Inspect Finding" link to detail screen.
* **Available Controls & Verified Actions**:
  * Click on finding link -> Navigates to `/findings/[id]` detail screen [Verified PASS].
* **Backend APIs Used**: `GET /api/v1/findings`.
* **Database Entities**: `findings`, `institutions`, `enrolment_records`, `validation_rules`.
* **Browser Test Evidence**: `docs/evidence/18_screen_findings.png`.

---

### SCR-CORE-06: Finding Detail & Resolution State Machine
* **Route**: `/findings/[id]`
* **Purpose**: In-depth examination and resolution workspace for a specific discrepancy finding. Governs statutory workflow transitions and institution responses with mandatory documented rationales.
* **Intended User**: Regulatory Officers (full transition rights) and Institutional Admins (response submission rights).
* **Navigation Path**: Clicking a finding from `/findings` or from the audit case view.
* **Main UI Components**:
  * Header with Rule Code, Severity Badge, and Current Workflow Status.
  * Side-by-side Student & Enrolment Comparison:
    * Primary Institution Record (Name, Roll No, Programme, Status).
    * Conflicting Secondary Institution Record (if cross-institutional).
  * State Machine Action Bar: Permitted transitions based on caller role (`WF-001` enforced).
  * Institutional Response Timeline: Thread of submitted explanations, attachments, and officer determinations.
  * Evidence Upload Box: Drag-and-drop supporting proof documents (transfer certificates, admission withdrawal forms).
* **Available Controls & Verified Actions**:
  * Transition State -> Calls `POST /api/v1/findings/{id}/transition`. Enforces mandatory rationale and valid state graph [Verified PASS].
  * Submit Response -> Calls `POST /api/v1/findings/{id}/responses` [Verified PASS].
* **Backend APIs Used**: `GET /api/v1/findings/{id}`, `POST /api/v1/findings/{id}/transition`, `POST /api/v1/findings/{id}/responses`, `POST /api/v1/findings/{id}/evidence`.
* **Database Entities**: `findings`, `finding_responses`, `evidence_metadata`, `audit_events`.
* **Browser Test Evidence**: `docs/evidence/19_screen_finding_detail.png`.

---

### SCR-CORE-07: Deterministic Risk Prioritization Queue
* **Route**: `/risk-queue`
* **Purpose**: Regulatory oversight queue that ranks all technical institutions by their deterministic 6-factor risk score (0–100) to prioritize regulatory audits and physical inspections without black-box machine learning.
* **Intended User**: National Regulatory Leadership, AICTE Inspection Officers.
* **Navigation Path**: Sidebar navigation item "Risk Queue".
* **Main UI Components**:
  * Summary Cards: Total Scored Institutions, High Priority Review Count, Watchlist Count.
  * Risk Queue Table:
    * Institution Name and Permanent Code.
    * State and District.
    * Risk Score (0 to 100) and Categorization Band (`ROUTINE`, `WATCH`, `REVIEW_RECOMMENDED`, `PRIORITY_REVIEW`).
    * Active Discrepancies Count.
    * Completeness State (`COMPLETE`, `PARTIAL_NO_INTAKE`, `PARTIAL_MISSING_EXTERNAL`).
    * Last Calculation Timestamp.
    * Actions: "View Full Profile", "Recalculate Score", "Initiate Audit Case".
* **Available Controls & Verified Actions**:
  * Click "View Full Profile" -> Navigates to `/institutions/[id]/risk-profile` [Verified PASS].
  * Trigger "Recalculate Score" -> Executes `POST /api/v1/institutions/{id}/recalculate-risk` and refreshes score instantly [Verified PASS].
* **Backend APIs Used**: `GET /api/v1/risk-queue`, `POST /api/v1/institutions/{id}/recalculate-risk`.
* **Database Entities**: `risk_calculations`, `institutions`, `findings`, `enrolment_records`.
* **Browser Test Evidence**: `docs/evidence/20_screen_risk_queue.png`, `docs/evidence/31_inst_admin_risk_queue.png`.

---

### SCR-CORE-08: Regulatory Audit Case Docket & Docket Index
* **Route**: `/cases`
* **Purpose**: Regulatory docket management screen listing formal statutory audit proceedings opened against non-compliant institutions.
* **Intended User**: `AICTE_ADMIN`, `AICTE_OFFICER`, `AUDITOR`.
* **Navigation Path**: Sidebar navigation item "Audit Cases".
* **Main UI Components**:
  * Case Statistics: Open Cases, Under Review, Clarification Pending, Resolved.
  * Cases Data Table:
    * Case Docket Number (e.g. `CSE-2026-XXXX`).
    * Subject Institution.
    * Category (`INTAKE_BREACH`, `CROSS_INSTITUTION_DUPLICATE`, `SYSTEMIC_DATA_ANOMALY`).
    * Priority (`CRITICAL`, `HIGH`, `MEDIUM`, `ROUTINE`).
    * Assigned Regulatory Reviewer.
    * Workflow Status (`OPEN`, `ASSIGNED`, `UNDER_REVIEW`, `CLARIFICATION_REQUESTED`, `RESPONSE_RECEIVED`, `RESOLVED`, `CLOSED_NO_ACTION`).
    * Response Deadline Date.
    * "Open Case Dossier" link.
  * "Create Audit Case" Modal Button (initiates formal docket with mandatory rationale).
* **Available Controls & Verified Actions**:
  * Click on case link -> Navigates to `/cases/[id]` detail view [Verified PASS].
  * Filter cases by status and priority -> Updates list dynamically [Verified PASS].
* **Backend APIs Used**: `GET /api/v1/audit-cases`, `POST /api/v1/audit-cases`, `GET /api/v1/audit-cases/reviewers`.
* **Database Entities**: `audit_cases`, `institutions`, `users`, `audit_case_findings`.
* **Browser Test Evidence**: `docs/evidence/21_screen_cases.png`.

---

### SCR-CORE-09: Audit Case Dossier, Notes & Determination
* **Route**: `/cases/[id]`
* **Purpose**: Complete regulatory case docket containing attached discrepancy findings, reviewer deliberation notes, formal clarification requests, and statutory case decisions.
* **Intended User**: Assigned AICTE Regulatory Reviewers, National Officers.
* **Navigation Path**: Selected from `/cases` table.
* **Main UI Components**:
  * Case Metadata Header: Institution, Docket ID, Priority, Filing Officer, Status.
  * Linked Findings Tab: Specific discrepancy records attached to the docket.
  * Clarification Requests Tab: Official formal letters dispatched to the institution with tracked deadlines and institutional responses.
  * Reviewer Notes Log: Confidential deliberation notes appended by regulatory officers.
  * Statutory Determination Action Box:
    * Final Case Decision recording (`RESOLVE_COMPLIANT`, `SANCTION_IMPOSED`, `INTAKE_REDUCED`, `NO_ACTION`).
    * Legal Rationale input.
* **Available Controls & Verified Actions**:
  * Add Reviewer Note -> Calls `POST /api/v1/audit-cases/{id}/notes` [Verified PASS].
  * Transition Status -> Calls `POST /api/v1/audit-cases/{id}/events` [Verified PASS].
  * Record Final Decision -> Calls `POST /api/v1/audit-cases/{id}/decisions` [Verified PASS].
* **Backend APIs Used**: `GET /api/v1/audit-cases/{id}`, `POST /api/v1/audit-cases/{id}/notes`, `POST /api/v1/audit-cases/{id}/events`, `POST /api/v1/audit-cases/{id}/decisions`, `POST /api/v1/audit-cases/{id}/clarification-requests`.
* **Database Entities**: `audit_cases`, `audit_case_events`, `audit_case_decisions`, `clarification_requests`, `audit_events`.
* **Browser Test Evidence**: `docs/evidence/22_screen_case_detail.png`.

---

### SCR-CORE-010: Technical Institutions Directory
* **Route**: `/institutions`
* **Purpose**: Complete directory of higher education technical institutions registered with AICTE.
* **Intended User**: All authenticated roles.
* **Navigation Path**: Sidebar navigation item "Institutions".
* **Main UI Components**:
  * Search by Institution Name or AICTE Code (`AICTE-SYNTH-XXXX`).
  * Filter by State and Institution Type (`CENTRAL_UNIVERSITY`, `STATE_UNIVERSITY`, `PRIVATE_AIDED`, `PRIVATE_UNAIDED`).
  * Directory Table:
    * Permanent Code & Institution Name.
    * State & District.
    * Type & Status (`ACTIVE`, `PENDING_APPROVAL`, `SUSPENDED`).
    * Active Programmes Count.
    * Total Enrolled Students.
    * "View Risk Profile" action button.
* **Available Controls & Verified Actions**:
  * Filter by State -> Filters table [Verified PASS].
  * Click "Risk Profile" -> Directs to `/institutions/[id]/risk-profile` [Verified PASS].
* **Backend APIs Used**: `GET /api/v1/institutions`, `GET /api/v1/institutions/{id}`.
* **Database Entities**: `institutions`, `programmes`, `enrolment_records`.
* **Browser Test Evidence**: `docs/evidence/23_screen_institutions.png`.

---

### SCR-CORE-011: Institutional Risk Profile Breakdown
* **Route**: `/institutions/[id]/risk-profile`
* **Purpose**: Transparent, explainable breakdown of the 6 constituent factors determining an institution's risk score. Provides full regulatory auditability and eliminates arbitrary enforcement disputes.
* **Intended User**: Regulatory Officers and Institutional Leaders (for their own institution).
* **Navigation Path**: Clicked from `/institutions` or `/risk-queue`.
* **Main UI Components**:
  * Institution Overview Card: Official Name, Code, Location, Active Academic Year.
  * Total Score Gauge & Risk Band Indicator (e.g. `20.0 / 100` — `WATCH`).
  * 6 Factor Progress Cards with Points Awarded vs Maximum Points:
    1. **Capacity Discrepancy** (Score / 25 pts) — Programmes exceeding approved intake.
    2. **Cross-Institution Conflicts** (Score / 25 pts) — Active dual-enrolment flags (`DUP-001`, `DUP-002`).
    3. **Identifier & Quality Gaps** (Score / 15 pts) — Malformed or missing APAAR identities.
    4. **Unusual Roster Changes** (Score / 15 pts) — Post-submission corrections.
    5. **Source-Reconciliation Gap** (Score / 10 pts) — Pending external API verification.
    6. **Prior Unresolved Findings** (Score / 10 pts) — Overdue findings awaiting institution reply.
  * Plain-Language Explanation: Natural language summary justifying the score.
  * Audit Snapshot Metadata: Timestamp, engine version (`v1.0.0`), completeness flag.
* **Available Controls & Verified Actions**:
  * Direct URL navigation and refresh -> Renders DIT profile correctly [Verified PASS].
* **Backend APIs Used**: `GET /api/v1/institutions/{id}/risk-profile`.
* **Database Entities**: `risk_calculations`, `institutions`, `programmes`, `findings`, `enrolment_records`.
* **Browser Test Evidence**: `docs/evidence/24_screen_institution_risk_profile.png`.

---

### SCR-CORE-012: Regulatory Reports Catalog & Export Queue
* **Route**: `/reports`
* **Purpose**: Statutory reporting center for generating, scheduling, and exporting sanitized CSV and PDF compliance reports with mandatory CSV injection defense (`sanitizeSpreadsheetCell`).
* **Intended User**: Regulatory Officers (`AICTE_ADMIN`, `AICTE_OFFICER`, `AUDITOR`) and Institution Admins.
* **Navigation Path**: Sidebar navigation item "Reports".
* **Main UI Components**:
  * **Report Catalog Cards**:
    * National Intake Capacity Compliance Summary.
    * Cross-Institutional Conflict & Duplicate Audit Report.
    * Institutional Risk Ranking & Inspection Prioritization Dossier.
    * APAAR Identifier Quality & Coverage Statistics.
  * **Generate Report Dialog**: Select academic year, format (`CSV`, `PDF`), and scope filter.
  * **Generated Reports Queue**: List of generated reports with file size, generation timestamp, status (`READY`, `GENERATING`, `FAILED`), and direct "Download Report" button.
* **Available Controls & Verified Actions**:
  * View Report Catalog -> Renders 4 standard regulatory report types [Verified PASS].
  * Download Report -> Fetches sanitized export with formula shielding [Verified PASS].
* **Backend APIs Used**: `GET /api/v1/reports`, `POST /api/v1/reports`, `GET /api/v1/reports/{id}/download`.
* **Database Entities**: `report_jobs`, `audit_events`.
* **Browser Test Evidence**: `docs/evidence/25_screen_reports.png`.

---

### SCR-CORE-013: Verification Reference Governance
* **Route**: `/verification-references`
* **Purpose**: Administrative console for managing, issuing, and revoking purpose-bound student verification references.
* **Intended User**: `INSTITUTION_ADMIN`, `AICTE_ADMIN`.
* **Navigation Path**: Sidebar navigation item "Verifications".
* **Main UI Components**:
  * Reference Summary Stats: Active References, Total Queries Resolved, Revoked References.
  * Reference Table:
    * Public Tracking Code (`VRF-2026-DIT001`).
    * Student Roll Number & Full Name.
    * Stated Purpose (`EMPLOYMENT_VERIFICATION`, `ACADEMIC_ADMISSION`, `VISA_SCREENING`).
    * Permitted Disclosure Profile (summary of authorized claims).
    * Usage Counter vs Maximum Uses Limit (e.g. `1 / 5`).
    * Expiration Date.
    * Status (`ACTIVE`, `EXPIRED`, `REVOKED`).
    * Action button: "Revoke Reference".
  * "Issue New Reference" Modal: Select student, configure allowed fields, set expiry and max uses.
* **Available Controls & Verified Actions**:
  * View References Table -> Displays active sample reference `VRF-2026-DIT001` [Verified PASS].
  * Revoke Reference -> Calls `POST /api/v1/verification-references/{id}/revoke` [Verified PASS via test suite].
* **Backend APIs Used**: `GET /api/v1/verification-references`, `POST /api/v1/verification-references`, `POST /api/v1/verification-references/{id}/revoke`.
* **Database Entities**: `verification_references`, `verification_access_logs`, `enrolment_records`.
* **Browser Test Evidence**: `docs/evidence/26_screen_verification_references.png`.

---

### SCR-CORE-014: External Integration Adapters Telemetry
* **Route**: `/integrations`
* **Purpose**: Telemetry and health console tracking connectivity, response latencies, supported claims, and contract tests for simulated and live external government data sources.
* **Intended User**: All authenticated personnel.
* **Navigation Path**: Sidebar navigation item "Integrations".
* **Main UI Components**:
  * Adapter Health Cards:
    1. **DigiLocker / APAAR Identity Gateway**: Simulated / Live format validation and HMAC fingerprinting.
    2. **AISHE Institutional Master Database**: Annual census cross-reference adapter.
    3. **National Academic Depository (NAD)**: Degree and convocation verification adapter.
    4. **State Technical Education Boards**: Lateral entry and diploma verification adapter.
    5. **AICTE Central Approval Bureau (EDB)**: Sanctioned intake capacity mirror.
  * Adapter Detail per card: Status (`CONFIGURED`, `SIMULATED`, `NOT_CONFIGURED`), Latency (ms), Supported Claims array, Known Limitations note, Contract Test Status (`PASSED`, `SKIPPED`).
  * "Run Contract Test" trigger button.
* **Available Controls & Verified Actions**:
  * View Adapter Telemetry -> Displays all 5 adapters with real metrics and simulated disclaimers [Verified PASS].
* **Backend APIs Used**: `GET /api/v1/integrations/status`, `POST /api/v1/integrations/{adapter}/test-contract`.
* **Database Entities**: `integration_status_logs`.
* **Browser Test Evidence**: `docs/evidence/27_screen_integrations.png`.

---

### SCR-CORE-015: Regulatory Notifications & Event Center
* **Route**: `/notifications`
* **Purpose**: Real-time notification hub for regulatory alerts, discrepancy assignments, audit case updates, and clarification responses.
* **Intended User**: All authenticated users.
* **Navigation Path**: Bell icon in header title bar or sidebar link.
* **Main UI Components**:
  * Notification List grouped chronologically (Today, Earlier).
  * Notification Item: Icon by category, title, explanatory body text, timestamp, read/unread state.
  * "Mark All as Read" header button.
* **Available Controls & Verified Actions**:
  * Click "Mark All as Read" -> Dispatches `POST /api/v1/notifications/mark-all-read`, updates UI state [Verified PASS].
* **Backend APIs Used**: `GET /api/v1/notifications`, `PATCH /api/v1/notifications/{id}/read`, `POST /api/v1/notifications/mark-all-read`, `GET /api/v1/notifications/unread-count`.
* **Database Entities**: `notifications`.
* **Browser Test Evidence**: `docs/evidence/28_screen_notifications.png`.

---

## 3. Actionable Controls Inventory Matrix

| Control Category | Control Label | Screen Location | Associated Action / API | Role Permission | Verified State |
|---|---|---|---|---|---|
| **Auth** | Sign In Submit | `/login` | `POST /api/v1/auth/login` | Public | **VERIFIED PASS** |
| **Auth** | Sign Out | AppShell Header | `POST /api/v1/auth/logout` | Authenticated | **VERIFIED PASS** |
| **Auth** | Send Recovery Link | `/forgot-password` | `POST /api/v1/auth/forgot-password` | Public | **VERIFIED PASS** |
| **Auth** | Reset Password Submit | `/reset-password` | `POST /api/v1/auth/reset-password` | Token Bearer | **VERIFIED PASS** |
| **Public** | Resolve Verification Code | `/verify` | `POST /api/v1/verify` | Public | **VERIFIED PASS** |
| **Public** | Register Institution | `/register` | `POST /api/v1/institutions` | Public | **VERIFIED PASS** |
| **Navigation** | Academic Year Filter | `/overview`, `/programmes` | Client state & API refetch | All | **VERIFIED PASS** |
| **Navigation** | Refresh Page (`F5`) | All Protected Screens | Coordinated token refresh (`/auth/refresh`) | Authenticated | **VERIFIED PASS** |
| **Records** | Search Student Roster | `/enrolments` | Client/API search filter | Scoped | **VERIFIED PASS** |
| **Records** | Submit Record Correction | `/enrolments` (Modal) | `POST /api/v1/enrolments/{id}/corrections` | `INSTITUTION_ADMIN` | **VERIFIED PASS** |
| **Ingestion** | Upload CSV Roster | `/submissions` | `POST /api/v1/batches` & `.../file` | `INSTITUTION_ADMIN` | **VERIFIED PASS** |
| **Ingestion** | Finalize Ingestion Batch | `/submissions` (Preview) | `POST /api/v1/batches/{id}/finalize` | `INSTITUTION_ADMIN` | **VERIFIED PASS** |
| **Ingestion** | Download Batch Receipt | `/submissions` | `GET /api/v1/batches/{id}/receipt` | `INSTITUTION_ADMIN` | **VERIFIED PASS** |
| **Findings** | Filter Discrepancies | `/findings` | Severity & status dropdowns | All | **VERIFIED PASS** |
| **Findings** | Transition Finding State | `/findings/[id]` | `POST /api/v1/findings/{id}/transition` | `AICTE_ADMIN`, Reviewer | **VERIFIED PASS** |
| **Findings** | Submit Finding Response | `/findings/[id]` | `POST /api/v1/findings/{id}/responses` | `INSTITUTION_ADMIN` | **VERIFIED PASS** |
| **Findings** | Upload Finding Evidence | `/findings/[id]` | `POST /api/v1/findings/{id}/evidence` | Scoped | **VERIFIED PASS** |
| **Risk** | Recalculate Risk Score | `/risk-queue`, `/institutions/[id]` | `POST /api/v1/institutions/{id}/recalculate-risk` | `AICTE_ADMIN` | **VERIFIED PASS** |
| **Audit Cases** | Open New Audit Case | `/cases` (Modal) | `POST /api/v1/audit-cases` | `AICTE_ADMIN`, Officer | **VERIFIED PASS** |
| **Audit Cases** | Assign Reviewer | `/cases/[id]` | `PATCH /api/v1/audit-cases/{id}/assignment` | `AICTE_ADMIN` | **VERIFIED PASS** |
| **Audit Cases** | Dispatch Clarification | `/cases/[id]` | `POST /api/v1/audit-cases/{id}/clarification-requests` | Assigned Reviewer | **VERIFIED PASS** |
| **Audit Cases** | Add Reviewer Note | `/cases/[id]` | `POST /api/v1/audit-cases/{id}/notes` | Assigned Reviewer | **VERIFIED PASS** |
| **Audit Cases** | Record Case Decision | `/cases/[id]` | `POST /api/v1/audit-cases/{id}/decisions` | Assigned Reviewer | **VERIFIED PASS** |
| **Reports** | Generate Report Job | `/reports` | `POST /api/v1/reports` | Officer / Admin | **VERIFIED PASS** |
| **Reports** | Download Sanitized CSV | `/reports` | `GET /api/v1/reports/{id}/download` | Officer / Admin | **VERIFIED PASS** |
| **Verifications**| Issue Verification Token | `/verification-references` | `POST /api/v1/verification-references` | `INSTITUTION_ADMIN` | **VERIFIED PASS** |
| **Verifications**| Revoke Reference | `/verification-references` | `POST /api/v1/verification-references/{id}/revoke`| `INSTITUTION_ADMIN` | **VERIFIED PASS** |
| **Notifications**| Mark All Read | `/notifications` | `POST /api/v1/notifications/mark-all-read` | Authenticated | **VERIFIED PASS** |

