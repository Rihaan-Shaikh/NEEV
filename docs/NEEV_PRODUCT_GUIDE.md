# NEEV — Master Product Guide & System Manual

> **Document Version**: 1.0.0-PROD-AUDIT  
> **System Classification**: National Student Enrolment Integrity, Discrepancy Resolution & Regulatory Monitoring Platform  
> **Design Mandate**: All India Council for Technical Education (AICTE)  
> **Core Motto**: *Proof Behind Every Record*

---

## 1. Twenty Core System Questions & Definitive Answers

### Question 1: What is NEEV?
**NEEV (National Education Evidence & Verification)** is an enterprise-grade regulatory integrity platform engineered for higher education authorities (specifically the AICTE ecosystem). It bridges institutional admission submissions, statutory approved academic intake capacities, and identity validation workflows into an auditable, tamper-evident regulatory ledger.

### Question 2: What problem does it address?
In conventional higher education administration, regulatory oversight is retroactive and paper-driven. Regulators face three critical failures:
1. **Intake Ceiling Breaches**: Colleges admit students exceeding statutory sanctioned capacities without real-time detection.
2. **Ghost & Dual Enrolments**: Students concurrently enroll in multiple technical institutions across different states to secure dual qualifications or claim duplicate public scholarships.
3. **Data Tampering & Identity Exposure**: Retrospective edits to student databases occur without version tracking, while handling sensitive national identifiers (such as APAAR or Aadhaar) in cleartext exposes student privacy to catastrophic data breaches.

### Question 3: Who are the primary users?
NEEV serves five distinct user groups:
1. **AICTE National Administrators**: Executive regulators overseeing nationwide capacity adherence and policy compliance.
2. **AICTE Regulatory Officers / Reviewers**: Technical investigators examining discrepancy findings, managing audit dockets, and issuing statutory notices.
3. **Institutional Administrators**: College Principals and Registrars responsible for submitting admission rosters and resolving discrepancy notices.
4. **Institutional Data Operators**: Admissions staff uploading batch rosters and performing pre-commit inspections.
5. **Third-Party Verifiers & Employers**: External organizations (corporates, embassies, background screeners) validating student credentials.

### Question 4: What does each user do?
* **National Admins**: Review the national dashboard, inspect capacity reconciliation, supervise the 6-factor risk queue, and assign formal audit cases to reviewers.
* **Regulatory Reviewers**: Investigate cross-college duplicate flags (`DUP-002`), issue clarification letters, append deliberation notes, and record statutory case decisions.
* **Institution Admins**: Upload student CSV admission rosters, submit documented explanations for flagged discrepancies, apply versioned student corrections, and issue purpose-bound verification tokens.
* **Verifiers**: Enter reference tracking codes or bearer tokens on the public resolver to confirm legitimate enrolment credentials without viewing private student files.

### Question 5: What are the major modules?
NEEV is organized into seven integrated modules:
1. **Security & Session Gateway**: In-memory JWT access token management, HttpOnly refresh cookies, and tenant authorization scoping.
2. **Batch Ingestion & Validation Pipeline**: Stream-based CSV parser enforcing schema checks, date formats, and intake ceilings.
3. **Cross-Institution Conflict Engine**: Deterministic duplicate and overlap detector running over HMAC-SHA256 identity fingerprints.
4. **Deterministic Risk Prioritization Engine (v1.0.0)**: 6-factor explainable scoring engine (0–100) categorizing institutions into risk bands.
5. **Regulatory Audit Case & Docket Workflow**: State-machine governed legal docket management for formal compliance investigations.
6. **Immutable Ledger & Version Trail**: Sequential record versioning (`HIS-001`, `HIS-002`) preserving complete change histories.
7. **Controlled Public Verification Resolver**: Zero-knowledge credential resolver issuing and verifying purpose-bound references.

### Question 6: How do the modules work together?
Admission rosters uploaded by colleges pass through the **Validation Engine**. Clean records are committed to the **Immutable Ledger**, while their HMAC-SHA256 identity fingerprints are evaluated by the **Conflict Engine**. Detected dual enrolments generate **Discrepancy Findings**. The **Risk Engine** aggregates open findings and capacity variances to update institutional risk scores. High-risk colleges trigger **Regulatory Audit Cases**, which result in formal determinations. Verified enrolments can be independently confirmed through the **Public Verification Resolver**.

### Question 7: What happens to a record after it enters the system?
1. **Schema Parsing**: Ingestion pipeline sanitizes each field and parses dates.
2. **Cryptographic Fingerprinting**: The raw 12-digit APAAR is transformed into an HMAC-SHA256 fingerprint using a private salt. The raw APAAR is discarded from memory and never stored in the database.
3. **Capacity Cross-Check**: Active students in the programme are reconciled against the statutory approved intake.
4. **Ledger Commitment**: A row is inserted into `enrolment_records` with version $1$. A historical snapshot is initialized in `enrolment_record_versions`.
5. **Audit Logging**: An immutable audit event is appended to `audit_events`.

### Question 8: How are errors or discrepancies handled?
Errors are handled deterministically at two levels:
* **Pre-Commit Ingestion**: Roster rows failing schema or date checks are flagged in a pre-commit preview table with rule codes (`SCH-001`, `APA-002`). The user must resolve them before finalizing the batch.
* **Post-Commit Regulatory Discrepancies**: Conflicts between committed records (such as duplicate active enrolments across two colleges) generate a formal **Finding** governed by a rigid state machine (`OPEN` -> `AWAITING_RESPONSE` -> `UNDER_REVIEW` -> `RESOLVED` / `ESCALATED`).

### Question 9: How does risk review work?
NEEV strictly rejects opaque machine learning algorithms. The **Risk Engine (v1.0.0)** computes a 100% deterministic score from 0 to 100 based on six explicit factors:
1. Capacity Discrepancy (Max 25 pts)
2. Unresolved Cross-Institution Conflicts (Max 25 pts)
3. Identifier & Data Quality Problems (Max 15 pts)
4. Unusual Post-Admission Roster Changes (Max 15 pts)
5. External Source-Reconciliation Gaps (Max 10 pts)
6. Overdue Unresolved Findings (Max 10 pts)
Every score is accompanied by an exact mathematical point breakdown and a plain-language explanation.

### Question 10: How are findings and audit cases managed?
* **Findings** track specific operational anomalies (e.g. Student A enrolled at both DIT and MTU).
* **Audit Cases** are formal statutory dockets opened against institutions demonstrating systemic breaches or non-responsiveness. Dockets hold attached findings, tracked clarification requests with statutory deadlines, confidential reviewer notes, and binding legal decisions (`SANCTION_IMPOSED`, `INTAKE_REDUCED`).

### Question 11: How does verification work?
Third parties never query the database directly or inspect cleartext student records. An authorized institutional admin issues an opaque verification reference (`VRF-2026-XXXX`) bound to a pre-approved disclosure profile (e.g. name, programme, active status). An external employer enters the code on `/verify`. The resolver confirms validity, increments usage counters, logs an access audit event with client IP hash, and renders a tamper-evident credential certificate.

### Question 12: What information can decision-makers see?
National decision-makers see:
* Real-time active student numbers across all technical programmes.
* Exact seat variances comparing approved quotas to active rosters.
* National distribution of institutions across risk bands (`ROUTINE`, `WATCH`, `REVIEW_RECOMMENDED`, `PRIORITY_REVIEW`).
* Active cross-institutional fraud alerts.
* Formal audit dockets and impending institutional response deadlines.

### Question 13: What evidence does the system retain?
1. **Immutable Version History**: Every correction to an enrolment record preserves the complete JSON snapshot of the previous state, timestamp, acting user ID, and mandatory written rationale.
2. **Audit Event Log**: Append-only log recording logins, uploads, transitions, notes, and token generations.
3. **Private Evidence Vault**: Uploaded PDFs (transfer certificates, court orders) stored with SHA-256 integrity hashes and tenant-scoped access controls.
4. **Verification Access Logs**: Every public query is logged with client IP hash, timestamp, user agent, and disclosed claims.

### Question 14: What does the system automate?
* Real-time seat capacity reconciliation against versioned AICTE approval letters.
* HMAC-SHA256 identity fingerprinting and cross-institutional duplicate detection.
* 6-factor deterministic risk score calculation and tier classification.
* Token generation, expiration tracking, and single-use limit enforcement.
* Rate limiting, sensitive data redaction, and spreadsheet formula injection shielding.

### Question 15: What decisions still require human judgment?
NEEV enforces a strict **Human-in-the-Loop** architecture:
* Discrepancies generate findings, but **final regulatory determinations** (closing a case, revoking college accreditation, reducing approved seats) require an authorized regulatory officer's explicit action and documented legal order.
* Genuine student transfer disputes require human review of uploaded transfer certificates.

### Question 16: What is implemented and verified today?
1. Full Next.js 16 frontend with 23 routes and reactive AppShell.
2. Complete FastAPI backend with 76 OpenAPI routes and 83 operations.
3. Live Neon PostgreSQL database with 39 relational tables.
4. Session restoration and page-refresh persistence verified in real browser sessions.
5. Deterministic validation rules (`SCH`, `APA`, `INT`).
6. Cross-institution conflict engine (`DUP-001` through `DUP-004`).
7. 6-factor deterministic risk engine (v1.0.0).
8. Audit case docket management, notes, and decisions.
9. Controlled public verification resolver with bearer tokens.
10. Formula-sanitized regulatory CSV exports.

### Question 17: What is implemented but not yet verified with live government production feeds?
* **External Government Identity APIs**: The adapters for DigiLocker/APAAR, AISHE, and National Academic Depository (NAD) are implemented and contract-tested using simulated endpoints. Live production ministry APIs require formal institutional MOUs and enterprise credentials.

### Question 18: What is incomplete or planned for Phase 5?
* Direct biometric-backed DigiLocker single sign-on for students.
* Automated OCR extraction for scanned physical transfer certificates.
* Multi-signature regulatory determination orders using electronic signatures (e-Sign).

### Question 19: What are the main technical and operational limitations?
* **Free Cloud Sleep Delays**: On Render free tier, the cold-start delay on first request can reach 40 seconds after inactivity (local dev server responds in under 5 ms).
* **CSV Format Strictness**: Roster ingestion strictly expects UTF-8 CSV formatting; legacy binary `.xls` files must be exported to `.csv` before upload.

### Question 20: What should a judge or stakeholder remember after a demonstration?
NEEV is **not a mock or a concept portal** — it is a functioning, tamper-evident regulatory platform that solves real higher education governance challenges:
1. It eliminates **unapproved over-enrolment** through automated intake reconciliation.
2. It detects **ghost and duplicate students** across colleges without compromising student privacy.
3. It replaces subjective regulatory inspections with **100% explainable, deterministic risk scoring**.
4. It provides **zero-knowledge third-party verification** for students and employers.

