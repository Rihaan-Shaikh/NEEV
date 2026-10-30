# NEEV — End-to-End User Journeys and Business Workflows

> **Document Version**: 1.0.0-PROD-AUDIT  
> **Verification Status**: End-to-end verified via browser automation and database ledger inspections  
> **Target Regulatory Ecosystem**: All India Council for Technical Education (AICTE)  
> **Key Tenets**: 100% Deterministic Rule Engine, Cryptographic HMAC Privacy, Immutable Sequential Versioning, Statutory Human-in-the-Loop Oversight.

---

## 1. Workflow Architecture Overview

NEEV establishes an auditable regulatory bridge connecting institutional student enrolments, approved statutory capacities, discrepancy investigation, and third-party credential verification.

```
+----------------------------------------------------------------------------------------------------+
|                                    NEEV OPERATIONAL WORKFLOW MAP                                   |
+----------------------------------------------------------------------------------------------------+

 [1. Capacity Sanction]           [2. Ingestion & Roster]           [3. Deterministic Validation]
  AICTE Approval Bureau            Technical Institution             Deterministic Rule Engine
           |                                |                                   |
  Approves Intake Sanctions         Submits Admission Roster            Evaluates SCH, APA, INT
  (e.g. 120 seats BTech)            via CSV Dropzone                    & HMAC-SHA256 Fingerprints
           |                                |                                   |
           +--------------------------------+-----------------------------------+
                                            |
                                            v
                                 [4. Reconciliation & Conflict]
                                  Cross-Institution Conflict Engine
                                  - Intra-College Overlap (DUP-001)
                                  - Inter-College Conflict (DUP-002)
                                  - Seat Ceiling Breach (INT-002)
                                            |
                      +---------------------+---------------------+
                      |                                           |
             [No Discrepancies]                          [Discrepancies Found]
                      |                                           |
                      v                                           v
           [Immutable Ledger v1]                         [Open Findings Queue]
            Active Enrolments                             State Machine Governed
            Masked APAAR Fingerprints                     (OPEN -> AWAITING_RESPONSE)
                      |                                           |
                      v                                           v
           [Controlled Verification]                     [5. Risk Prioritization Engine]
            Public VRF References                         6-Factor Deterministic Score (0-100)
            Zero-Knowledge Disclosures                    (ROUTINE -> WATCH -> PRIORITY_REVIEW)
                                                                  |
                                                                  v
                                                         [6. Regulatory Audit Cases]
                                                          Formal Docket Opened
                                                          Assigned Reviewer Deliberation
                                                          Clarification Requests & Hearing
                                                                  |
                                                                  v
                                                         [7. Statutory Determination]
                                                          - Sanction Imposed
                                                          - Intake Reduced
                                                          - Resolved Compliant
```

---

## 2. Core Workflows in Detail

### WORKFLOW 1: Secure Authentication, Session Restoration & Scope Scoping

```
User visits /login
        |
        v
Submits Credentials (email, password)
        |
        +---- Invalid Credentials ----> HTTP 401: Alert Banner ("Invalid email or password")
        |
        +---- Suspended Account   ----> HTTP 403: Alert Banner ("Account is suspended")
        |
        v
Credentials Validated (bcrypt)
        |
        v
Session Issued:
  1. Short-lived JWT Access Token -> Held strictly in React memory (inMemoryToken)
  2. Long-lived Refresh Token -> HttpOnly, SameSite=lax cookie
  3. Non-sensitive active flag -> localStorage ("neev_session_active" = "true")
        |
        v
Redirect to /overview
        |
        v
User triggers Browser Refresh (F5)
        |
        v
AuthProvider mounts:
  - Detects "neev_session_active" in localStorage
  - Dispatches POST /api/v1/auth/refresh (attaching HttpOnly cookie)
  - Receives fresh access token + user claims
  - Calls GET /api/v1/auth/me to restore profile
        |
        v
User remains seamlessly authenticated on current screen
```

* **Real-World Problem**: Conventional regulatory portals suffer from session drops or expose JWTs in unencrypted `localStorage`, leading to cross-site scripting (XSS) credential theft.
* **Initiating Actor**: All users.
* **Starting Screen**: `/login`.
* **Required Inputs**: Email address and password.
* **Backend Validations**: Rate limiting (30 requests/min), bcrypt verification, account status validation (`account_status == 'active'`).
* **Database Records Created/Updated**: Creates row in `refresh_sessions` with token hash, client IP hash, user agent, and expiration timestamp. Appends entry to `audit_events`.
* **Result Visible to User**: Immediate transition to `/overview` with role-scoped sidebar navigation.

---

### WORKFLOW 2: Institutional Student Roster Ingestion & Pre-Commit Validation

```
Institution Admin opens /submissions
        |
        v
Selects Academic Year & Programme
        |
        v
Uploads CSV Roster (max 10 MB)
        |
        v
Server creates SubmissionBatch (Status: VALIDATING)
        |
        v
Pipeline processes rows through ValidationEngine:
  - SCH-001: Required field check (Student Name, Roll No, Admission Date)
  - SCH-002: ISO Date format check (YYYY-MM-DD)
  - APA-001/002: APAAR 12-digit format check
  - APA-003: HMAC-SHA256 computation (zero cleartext APAAR stored)
  - INT-002: Approved intake capacity reconciliation
        |
        v
Server produces Batch Preview:
  - Total rows count
  - Valid rows count
  - Error rows with rule codes and plain-language remediation instructions
        |
        +---- Uncorrectable Errors ----> Batch marked REJECTED / Resubmission required
        |
        v
Institution Admin inspects Preview & clicks "Finalize Submission"
        |
        v
Batch Committed:
  - Valid records persisted to enrolment_records (version = 1)
  - Student identity fingerprints written to student_identities
  - Cryptographic Submission Receipt generated with SHA-256 batch hash
  - Audit event logged
        |
        v
Receipt reference code displayed; records visible on /enrolments
```

* **Real-World Problem**: Manual spreadsheet submissions contain invisible errors, ghost students, or intake violations that are detected only after admissions close.
* **Initiating Actor**: `INSTITUTION_ADMIN` or `INSTITUTION_OPERATOR`.
* **Starting Screen**: `/submissions`.
* **Required Documents**: Standard AICTE admission CSV roster containing: `institution_student_id`, `student_full_name`, `apaar_id`, `admission_date`, `admission_category`, `supernumerary_category`.
* **Backend Validations**:
  * File size check (`< 10 MB`).
  * MIME/extension verification (`text/csv`).
  * Schema conformity (`SCH-001` through `SCH-006`).
  * Intake ceiling checks (`INT-001`, `INT-002`).
* **Database Records Created**: `submission_batches`, `submission_rows`, `submission_receipts`, `validation_runs`, `validation_findings`, `student_identities`, `enrolment_records` (v1), `audit_events`.
* **Result Visible to User**: Interactive preview grid with error/warning counts, followed by signed cryptographic receipt `RCT-2026-XXXX`.

---

### WORKFLOW 3: Cross-Institution Duplicate Detection & Discrepancy Findings

```
New student enrolment ingested
        |
        v
HMAC-SHA256 Fingerprint generated with isolated secret salt
        |
        v
ConflictDetectionService queries student_identities by fingerprint
        |
        v
Multiple active records identified with identical fingerprint?
        |
        +-- NO  --> Clean record; persisted to ledger; zero findings
        |
        +-- YES --> Compare pair characteristics:
                     |
                     +-- Same College + Both ACTIVE in same AY
                     |   --> Rule DUP-001 (Intra-Institution Multiple Enrolment) [ERROR]
                     |
                     +-- Different Colleges + Both ACTIVE in same AY
                     |   --> Rule DUP-002 (Cross-Institution Dual Enrolment) [CRITICAL]
                     |
                     +-- Different Colleges + One TRANSFERRED / WITHDRAWN
                     |   --> Rule DUP-004 (Documented Legitimate Transfer) [INFO]
                     |
                     +-- Other overlapping states
                         --> Rule DUP-003 (Administrative Ambiguity) [WARNING]
        |
        v
System creates Finding record in status "OPEN":
  - Attaches primary and secondary enrolment IDs
  - Sets severity (CRITICAL for DUP-002)
  - Dispatches automated regulatory Notification to both institutions
        |
        v
Finding appears on /findings registry & triggers recalculation of Institutional Risk Scores
```

* **Real-World Problem**: Students concurrently enrolling in multiple government-funded technical colleges to secure dual seats or claim duplicate scholarships.
* **Initiating Actor**: Automated engine running on ingestion or on-demand reconciliation.
* **Starting Screen**: `/findings`.
* **Privacy Assurance**: The cross-institutional check never exposes the raw APAAR number. The match is computed purely over HMAC-SHA256 fingerprints.
* **Database Records Created**: `findings`, `notifications`, `audit_events`.
* **Next Possible Action**: Regulatory Officer opens the finding and initiates an inquiry or moves status to `AWAITING_INSTITUTION_RESPONSE`.

---

### WORKFLOW 4: Discrepancy Finding Resolution State Machine

```
Finding Created (Status: OPEN)
        |
        v
Regulatory Officer reviews Finding on /findings/[id]
        |
        v
Officer transitions finding to "AWAITING_INSTITUTION_RESPONSE"
  - Mandatory documented instruction provided
  - Both college principals receive high-priority notification
        |
        v
Institution Admin opens Finding Dossier:
  - Reviews conflicting record comparison
  - Uploads supporting evidence (Transfer Certificate PDF)
  - Enters written legal explanation
  - Submits Response
        |
        v
System records FindingResponse (Status -> "RESPONSE_RECEIVED")
        |
        v
Regulatory Officer reviews uploaded evidence and response:
        |
        +-- Genuine Transfer Verified --> Status -> RESOLVED (Transferred record updated)
        |
        +-- False Claim / Refusal     --> Status -> ESCALATED (Attached to formal Audit Case)
        |
        +-- Erroneous Flag            --> Status -> DISMISSED (With recorded rationale)
```

* **Real-World Problem**: Informal, ad-hoc resolution of discrepancies via phone calls or emails without an audit trail.
* **Permitted State Graph (`PERMITTED_TRANSITIONS`)**:
  * `OPEN` -> `AWAITING_INSTITUTION_RESPONSE`, `UNDER_REVIEW`
  * `AWAITING_INSTITUTION_RESPONSE` -> `RESPONSE_RECEIVED`, `UNDER_REVIEW`
  * `RESPONSE_RECEIVED` -> `UNDER_REVIEW`
  * `UNDER_REVIEW` -> `RESOLVED`, `DISMISSED`, `ESCALATED`
  * `ESCALATED` -> `UNDER_REVIEW`, `RESOLVED`, `DISMISSED`
  * `RESOLVED` / `DISMISSED` -> Terminal states.
* **Enforced Business Rule (`WF-001`)**: Arbitrary state jumps are rejected with `HTTP 400`. Documented rationales are mandatory.

---

### WORKFLOW 5: Deterministic Institutional Risk Scoring & Inspection Prioritization

```
Scheduled job or Officer triggers POST /institutions/{id}/recalculate-risk
        |
        v
RiskEngineService v1.0.0 fetches latest PostgreSQL data:
        |
        |--- Factor 1: Capacity Discrepancy (Max 25 pts)
        |    Active enrolments vs versioned approved intake across all programmes
        |
        |--- Factor 2: Unresolved Cross-Institution Conflicts (Max 25 pts)
        |    Active findings under DUP-001, DUP-002, DUP-003
        |
        |--- Factor 3: Identifier & Data Quality Problems (Max 15 pts)
        |    Ratio of missing or malformed APAAR identifiers
        |
        |--- Factor 4: Unusual Roster Changes (Max 15 pts)
        |    Post-admission enrolment version corrections count
        |
        |--- Factor 5: Source-Reconciliation Gap (Max 10 pts)
        |    Enrolments awaiting external verification
        |
        |--- Factor 6: Repeated Unresolved Prior Findings (Max 10 pts)
        |    Findings pending institution response past SLA
        |
        v
Total Score Calculated = Sum(Factors 1..6) [Clamped 0.0 to 100.0]
        |
        v
Risk Band Categorized:
  - 0.0  to < 20.0: ROUTINE (Clean standing)
  - 20.0 to < 40.0: WATCH (Minor discrepancies observed)
  - 40.0 to < 70.0: REVIEW_RECOMMENDED (Audit recommended)
  - 70.0 to 100.0 : PRIORITY_REVIEW (Immediate regulatory investigation mandated)
        |
        v
Plain-language explanation synthesized and persisted to risk_calculations
        |
        v
Institution ranking updated in real-time on /risk-queue
```

* **Real-World Problem**: Regulators relying on subjective inspection decisions or opaque AI models that colleges contest in judicial reviews.
* **Explainability Guarantee**: Every score includes a machine-readable snapshot and a human-readable narrative explaining exactly how many points were awarded for each factor.
* **Database Records Created**: `risk_calculations` (sets previous calculation `is_active = false`), `audit_events`.

---

### WORKFLOW 6: Regulatory Audit Case Docket & Statutory Determination

```
AICTE Regulatory Officer inspects high-risk institution on /risk-queue
        |
        v
Clicks "Initiate Audit Case"
        |
        v
Enters Docket Details on /cases:
  - Subject Institution
  - Category (e.g. INTAKE_BREACH, SYSTEMIC_DUPLICATES)
  - Priority (CRITICAL, HIGH, MEDIUM)
  - Mandatory Creation Rationale (> 20 chars)
  - Attaches relevant Finding IDs
        |
        v
Audit Case created (Status: OPEN, Docket: CSE-2026-XXXX)
        |
        v
National Admin assigns Regulatory Reviewer (Status -> ASSIGNED)
        |
        v
Reviewer opens Docket on /cases/[id]:
  - Enters confidential deliberation notes
  - Dispatches formal Clarification Request with response deadline
        |
        v
Institution receives clarification alert and submits formal reply
        |
        v
Reviewer conducts statutory hearing / evidence review (Status -> UNDER_REVIEW)
        |
        v
Reviewer records Statutory Case Decision:
  - Decision Type: SANCTION_IMPOSED / INTAKE_REDUCED / RESOLVE_COMPLIANT
  - Detailed Legal Findings & Statutory Order text
        |
        v
Case transitioned to RESOLVED or CLOSED_NO_ACTION; permanent audit log sealed
```

* **Real-World Problem**: Disjointed legal proceedings where institutional responses and officer notes are scattered across paper dockets and emails.
* **Permitted Transitions**: `OPEN` -> `ASSIGNED` -> `UNDER_REVIEW` -> `CLARIFICATION_REQUESTED` -> `RESPONSE_RECEIVED` -> `RESOLVED`.
* **Database Records Created**: `audit_cases`, `audit_case_findings`, `audit_case_events`, `clarification_requests`, `audit_case_decisions`, `audit_events`.

---

### WORKFLOW 7: Immutable Enrolment Correction & Version Audit Trail

```
Institution Admin discovers data entry error in enrolled student record
        |
        v
Navigates to /enrolments and clicks "Apply Correction"
        |
        v
Correction Modal opens displaying current record (Version = N)
        |
        v
Admin modifies allowed fields (e.g. admission category, spelling fix)
        |
        v
Admin enters mandatory justification (HIS-001: min 10 characters)
        |
        v
Submits PATCH /api/v1/enrolments/{id}/corrections with expected_version = N
        |
        +-- expected_version != current_version
        |   --> HTTP 409 Conflict (HIS-002: Optimistic concurrency collision)
        |
        +-- expected_version == current_version
            --> Current state archived into enrolment_record_versions (snapshot JSON)
            --> Record updated in enrolment_records (current_record_version = N + 1)
            --> Immutable audit event logged with user ID, diff, and reason
            --> Trigger re-evaluation of conflict rules
        |
        v
Modal closes; version tag increments in UI; "View History" shows permanent timeline
```

* **Real-World Problem**: Database administrators executing untracked direct SQL edits, altering student caste or category records retroactively.
* **Governing Rules**:
  * `HIS-001`: Mandatory justification required.
  * `HIS-002`: Optimistic concurrency locking prevents overwrite races.
  * `HIS-003`: Cleartext APAAR edits strictly prohibited.

---

### WORKFLOW 8: Controlled Third-Party Verification with Purpose-Bound Token

```
Employer / Embassy requires proof of student Aarav Sharma's degree
        |
        v
Institution Admin opens /verification-references
        |
        v
Clicks "Issue Verification Reference"
        |
        v
Selects Student & configures Limited Disclosure Profile:
  - Disclose Student Name: YES
  - Disclose Programme Title: YES
  - Disclose Enrolment Status: YES
  - Disclose Academic Year: YES
  - Disclose Admission Date: NO
  - Disclose APAAR / Aadhaar: STRICTLY FORBIDDEN (Enforced in backend)
  - Max queries allowed: 5
  - Expiry: 30 days
        |
        v
System generates:
  1. Cryptographic Bearer Token: neev_vrf_<40_hex_chars>
  2. Public Tracking Reference: VRF-2026-DIT001
  3. SHA-256 Token Hash stored in database (raw token never stored)
        |
        v
Admin provides public code or token to student / employer
        |
        v
Employer visits public portal /verify
        |
        v
Enters VRF-2026-DIT001 & clicks "Verify Record"
        |
        v
Backend Verification Resolver executes:
  - Verifies token hash exists, status is ACTIVE, not expired, usage < max_uses
  - Increments use_count
  - Logs VerificationAccessLog with client IP hash & user agent
  - Returns strictly authorized claims in JSON
        |
        v
Browser renders Tamper-Evident Verification Certificate with green seal
```

---

## 3. Step-by-Step Practical Operator Guides

### Guide 1: For AICTE National Administrators
**Objective**: Detect institutions exceeding approved intake and initiate an audit docket.
1. Open `http://localhost:3000/login` (or production `https://neev01.vercel.app/login`).
2. Enter email `aicte.admin@neev.aicte.gov.in` and password `NeevAdmin@2026`. Submit.
3. On `/overview`, examine the **Capacity Reconciliation** widget. Note any programmes flagged with red `CAPACITY_EXCEEDED` badges.
4. Click **Risk Queue** in the sidebar (`/risk-queue`).
5. Locate the highest-ranked institution in `PRIORITY_REVIEW` or `WATCH` band. Click **View Full Profile**.
6. On `/institutions/[id]/risk-profile`, review the 6-factor score breakdown.
7. Click **Audit Cases** in sidebar (`/cases`).
8. Click **Initiate Audit Case**. Select the institution, choose category `INTAKE_BREACH`, set priority `HIGH`, provide justification, and submit.
9. Verify the docket appears on the docket list.

### Guide 2: For Technical College Administrators
**Objective**: Submit a student admission batch and review ingestion findings.
1. Open `/login` and sign in as `admin@dit.synthetic.edu.in` with password `DitAdmin@2026`.
2. Notice the UI header confirms tenant scope: `Delhi Institute of Technology [DEMO-SYNTHETIC]`.
3. In sidebar, select **Submissions** (`/submissions`).
4. In the upload dropzone, drag-and-drop the admission roster (e.g. `sample_data/valid_roster.csv`).
5. Select Academic Year `2024-2025` and programme `BTECH-CSE`.
6. Click **Inspect Roster Preview**. Verify valid row count.
7. Click **Finalize Batch**. System outputs signed receipt reference `RCT-2026-XXXX`.
8. In sidebar, click **Enrolments** (`/enrolments`) to verify new students appear with masked APAAR fingerprints.

### Guide 3: For Third-Party Verifiers & Employers
**Objective**: Verify a job applicant's student status without requesting sensitive identity documents.
1. Open the public verification resolver at `/verify` (no login required).
2. Enter reference code `VRF-2026-DIT001`.
3. Click **Verify Record**.
4. Observe the resolved claims card: Student Aarav Sharma, Computer Science & Engineering, Delhi Institute of Technology, Status: `ACTIVE`.
5. Verify the green cryptographic validation seal and timestamp.

