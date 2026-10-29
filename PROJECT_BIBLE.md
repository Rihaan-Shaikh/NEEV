# NEEV — Complete Four-Phase Engineering & Product Blueprint

**National Education Evidence & Verification**

**Product tagline:** NEEV — Proof Behind Every Record.

NEEV will be developed as a serious, security-conscious student-enrolment integrity and regulatory monitoring platform intended for the AICTE ecosystem—not as a disposable hackathon interface.

The implementation plan below is based on your uploaded NEEV source-of-truth document. That document defines the central product as a system that distinguishes submitted records from validated, corroborated and reviewed records; preserves the history of changes; identifies discrepancies; and supports accountable human verification. *AICTE_APAAR_Student_Data_Platfo…*

The objective is to develop the entire product through four independently testable phases, with both frontend and backend work completed in every phase. Each phase must leave you with a working application, a usable interface, functioning APIs, persistent database behaviour, automated tests and a clear acceptance checklist.

I will not give you implementation prompts here. This is the engineering plan that will govern those prompts later.

---

## 1. First, Establish What We Are Actually Building

### 1.1 Product definition

NEEV is a proposed Student Enrolment Integrity and Regulatory Monitoring Platform for AICTE-approved institutions.

Its purpose is to connect:

- Institutional student-enrolment submissions.
- Approved institution, programme and intake information.
- APAAR-linked academic identity, where authorized validation is available.
- Data-quality and regulatory-rule validation.
- Duplicate and conflicting enrolment detection.
- Evidence provenance and record history.
- Institutional correction workflows.
- AICTE monitoring, review and audit-case management.
- Restricted, purpose-specific student-record verification.
- Reporting and authorized data exchange.

The key differentiator is not a collection of charts. It is a reliable workflow in which each important finding can be traced to a record, rule, source, timestamp and review outcome.

Your source document explicitly establishes that a valid APAAR identifier does not, by itself, prove current enrolment, and that a duplicate or anomaly must not automatically be treated as fraud. These distinctions must be enforced in the database, backend rules, frontend labels and reporting. *AICTE_APAAR_Student_Data_Platfo…*

### 1.2 Four rules that govern the entire build

#### Rule A — No fabricated government capabilities

We must not claim to have live APAAR, DigiLocker, NAD, AISHE, AICTE or university integration unless the required authorization, technical access and actual integration exist.

When real access is unavailable, we build an integration adapter with synthetic responses and explicitly display **SIMULATED** or **UNAVAILABLE**.

The application must distinguish:

1. Institution-submitted data.
2. Data that passed structural validation.
3. Data that passed configured business rules.
4. Data matched against an authorized source.
5. Data independently corroborated for a specific claim.
6. Data reviewed by an authorized human.

These are different evidence states, not interchangeable green ticks. *AICTE_APAAR_Student_Data_Platfo…*

#### Rule B — No hidden or untraceable business logic

Every important rule must have:

- A stable rule identifier.
- A clear purpose.
- An explicit severity.
- A defined input.
- A defined evaluation method.
- An explainable result.
- A version.
- A test suite.
- A documented owner or configuration authority.

Regulatory rules must not be scattered across React components, API routes and random utility functions.

#### Rule C — Security must exist at the data boundary

Hiding a button in the frontend is not authorization.

Every protected backend operation must verify the user's identity, permissions, institutional scope and allowed action. Database queries must also enforce the relevant access scope.

A user from Institution A must not obtain Institution B's student records by changing an ID in a URL, request body or API parameter.

#### Rule D — A phase is not complete merely because the screen looks good

Every phase must deliver a complete, testable vertical slice:

**Frontend → API → business logic → database → response → updated UI.**

A beautiful interface backed by hardcoded data does not pass. Neither does a backend with no usable interface.

---

## 2. The Four-Phase Product Map

The phases must build on one another without leaving essential modules until the end.

| Phase | Name | What becomes operational |
|---|---|---|
| Phase 1 | Secure Foundation & Enrolment Core | Application shell, authentication, role separation, institution/programme/intake records, student enrolment records, batch upload, deterministic validation and intake reconciliation. |
| Phase 2 | Integrity Ledger & Discrepancy Resolution | Cross-institution conflict detection, provenance, version history, audit events, findings, institutional corrections, evidence attachments and review workflows. |
| Phase 3 | AICTE Oversight & Regulatory Case Management | National and institutional dashboards, explainable risk prioritization, audit cases, assignments, responses, review decisions, reporting, exports and operational configuration. |
| Phase 4 | Controlled Verification, Security Hardening & Release Readiness | Limited-purpose verification references/QRs, access logging, expiry and revocation, end-to-end workflow completion, security testing, performance testing, deployment infrastructure, backups, monitoring and release evidence. |

Every phase includes frontend, backend, database, security, automated tests and manual acceptance testing.

Phase 4 is not a place where we begin fixing architectural problems left by Phases 1–3. The earlier phases must already have proper architecture and tested interfaces. Phase 4 adds the final product capabilities and validates the complete system.

### What "deployment-ready" will mean

There is an important distinction between building a deployable application and establishing that a government organization can safely use it in production.

We can engineer the application to have production-oriented architecture, strong controls, repeatable deployment, automated testing and documented operational procedures. However, no responsible engineering plan can guarantee zero defects, zero security risk or unconditional government deployment readiness.

Actual production authorization also depends on matters outside the code itself: official data access, approved policies, hosting requirements, privacy/legal review, security assessment, operational ownership and integration approvals.

NEEV must therefore aim for a production-engineered, deployment-capable system with documented evidence of readiness, not an unsupported claim of absolute perfection.

---

## 3. Architecture Decisions to Lock Before Development

These decisions form the engineering baseline. They should not be changed casually during implementation.

### 3.1 Recommended technology stack

The stack should be professional, maintainable, secure and suitable for a data-heavy institutional platform. We should not introduce microservices, Kubernetes or AI infrastructure merely to make the project appear sophisticated.

| Layer | Recommended choice | Purpose |
|---|---|---|
| Frontend | Next.js with React and TypeScript | Structured application, reusable UI, routing and typed interfaces. |
| Styling | Tailwind CSS with a documented design-token system | Consistent spacing, typography, responsive layouts and component styling. |
| UI primitives | Accessible, composable components built on a mature component foundation | Consistent dialogs, dropdowns, menus, form controls and keyboard behaviour. |
| Forms | React Hook Form with Zod, or an equivalent typed validation approach | Reliable form state and client-side input validation. |
| API communication | A typed API client generated from the backend OpenAPI schema where practical | Reduces frontend/backend contract mismatches. |
| Backend | FastAPI with Python | REST API, request validation, dependency-based authorization and documented endpoints. |
| Database | PostgreSQL | Relational integrity, constraints, transactions, indexing and reliable reporting queries. |
| ORM | SQLAlchemy 2.x | Explicit, maintainable data-access layer. |
| Database migrations | Alembic | Version-controlled schema changes and repeatable deployment. |
| Authentication | A well-tested authentication implementation using established cryptographic libraries | Password verification, token/session management and account security. |
| Background processing | A task queue and worker when upload volume or processing duration requires it | Large batch processing, retries and scheduled jobs. |
| File storage | A storage abstraction, with private object storage in deployment | Secure roster and evidence-file storage. |
| Testing | Pytest, API integration tests, frontend tests and Playwright end-to-end tests | Automated regression, authorization and user-flow verification. |
| Deployment | Containerized services, environment-based configuration and a managed PostgreSQL deployment where appropriate | Reproducible builds and controlled release. |
| Monitoring | Structured application logs, metrics, error reporting and health checks | Operational visibility without leaking student information. |

Exact dependency versions should be pinned and validated when the repository is initialized. We should not blindly use the newest release of every package without checking compatibility.

#### Why a modular monolith?

NEEV should begin as a modular monolith: one clearly structured backend application with well-separated modules, one primary relational database and separate background workers if needed.

The code can be organized into independent business modules without introducing the operational complexity of many separately deployed services.

This gives us:

- Simpler local development.
- Easier transaction management.
- Fewer network and deployment failure points.
- Clear ownership of business logic.
- Easier automated testing.
- A straightforward path to split components later if real scale or organizational requirements justify it.

Your source document also recommends a modular monolith, relational constraints, versioned rules and replaceable integration adapters. *AICTE_APAAR_Student_Data_Platfo…*

### 3.2 Proposed repository structure

The final structure should be adjusted after the actual repository is inspected. The following is the intended architecture, not an instruction to overwrite an existing codebase blindly.

```text
neev/
│
├── frontend/
│   ├── app/
│   │   ├── (public)/
│   │   │   ├── login/
│   │   │   └── access-denied/
│   │   │
│   │   ├── (protected)/
│   │   │   ├── overview/
│   │   │   ├── institutions/
│   │   │   ├── programmes/
│   │   │   ├── enrolments/
│   │   │   ├── submissions/
│   │   │   ├── findings/
│   │   │   ├── audit-cases/
│   │   │   ├── verification/
│   │   │   ├── reports/
│   │   │   └── administration/
│   │   │
│   │   ├── api/                 # Only if framework routing requires it
│   │   ├── layout.tsx
│   │   └── global styles
│   │
│   ├── components/
│   │   ├── layout/
│   │   ├── navigation/
│   │   ├── tables/
│   │   ├── forms/
│   │   ├── charts/
│   │   ├── feedback/
│   │   └── domain/
│   │
│   ├── features/
│   │   ├── authentication/
│   │   ├── institutions/
│   │   ├── submissions/
│   │   ├── enrolments/
│   │   ├── findings/
│   │   ├── audit-cases/
│   │   ├── verification/
│   │   └── reporting/
│   │
│   ├── lib/
│   │   ├── api-client/
│   │   ├── schemas/
│   │   ├── permissions/
│   │   └── utilities/
│   │
│   └── tests/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── policies/
│   │   ├── rules/
│   │   ├── integrations/
│   │   ├── workers/
│   │   └── main.py
│   │
│   ├── migrations/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── authorization/
│   │   ├── security/
│   │   └── fixtures/
│   │
│   └── pyproject.toml
│
├── infrastructure/
│   ├── containers/
│   ├── deployment/
│   └── monitoring/
│
├── docs/
│   ├── architecture.md
│   ├── data-dictionary.md
│   ├── api-contracts.md
│   ├── security-model.md
│   ├── threat-model.md
│   ├── assumptions-register.md
│   ├── testing.md
│   └── deployment-runbook.md
│
├── .env.example
├── .gitignore
├── README.md
└── docker-compose.yml
```

#### Structural rules

1. API endpoints must not contain substantial business logic.
2. Database models must not double as unrestricted public API responses.
3. Authentication, authorization and data-access policies must be separate concerns.
4. Regulatory rules must be implemented in testable rule modules.
5. Integration code must sit behind explicit adapter interfaces.
6. Configuration must be separated from application code.
7. Database changes must use migrations.
8. Tests must live in intentional locations.
9. Production secrets must never appear in source files or committed configuration.
10. The frontend must consume actual API responses for operational data.

We will not create unnecessary files, packages, services or tests merely to make the repository look larger. Every component must serve a clear purpose.

---

## 4. Database Design — The Foundation of NEEV

The database is one of the most important decisions in the entire project. We should design it before implementing the features that depend on it.

The schema below is the proposed logical design. It establishes the relationships and integrity requirements needed by the four phases. Final fields and constraints must still be reconciled with the existing repository and confirmed policy definitions.

### 4.1 Database design principles

#### Principle 1: Separate entities that represent different things

An institution is not a programme.

A programme is not an approved-intake record.

A student identity is not an enrolment.

A submission batch is not the same thing as the records submitted in it.

A validation finding is not an audit case.

An audit event is not an ordinary application log.

These distinctions prevent the schema from becoming a collection of enormous tables with duplicated information.

#### Principle 2: Use internal identifiers

Every principal entity should have an immutable internal identifier, normally a UUID or another suitable primary key.

APAAR ID must not be used as the primary key of the entire enrolment system. It is a sensitive external identifier whose validation and availability may vary.

#### Principle 3: Enforce integrity in PostgreSQL

Use:

- Primary keys.
- Foreign keys.
- Appropriate unique constraints.
- Check constraints.
- Required-field constraints.
- Transactions.
- Carefully selected indexes.

Do not rely exclusively on Python validation to preserve database integrity.

#### Principle 4: Version policy-dependent information

Approved intake and category rules may change by academic year or effective date. Store their source, version and effective period.

A rule applied to an earlier submission must remain identifiable even if the current rule changes.

#### Principle 5: Preserve historical truth

Correcting a record must not silently erase what was previously submitted.

NEEV needs both a current view of records and a traceable history of material changes.

### 4.2 Proposed relational schema

The following tables are the baseline for planning. Individual tables can be introduced in the phase where they become necessary, but their relationships should be designed consistently from the beginning.

#### A. Identity, access and institutional scope

##### `users`

Stores platform user accounts.

| Field | Purpose |
|---|---|
| id | Primary key. |
| email_normalized | Normalized login identifier; unique where the account model requires it. |
| password_hash | Strong password hash, never a plaintext password. |
| display_name | Name displayed in the interface. |
| account_status | Invited, active, locked, suspended or deactivated according to the account lifecycle. |
| email_verified_at | Verification timestamp, if email verification is used. |
| last_login_at | Last successful login timestamp. |
| created_at | Account creation timestamp. |
| updated_at | Last account update timestamp. |

Do not store password-reset tokens, raw refresh tokens or other reusable credentials in plaintext.

##### `roles`

Stores defined platform roles.

Examples:

- PLATFORM_ADMIN
- AICTE_ADMIN
- AICTE_OFFICER
- INSTITUTION_ADMIN
- INSTITUTION_OPERATOR
- AUDITOR
- VERIFIER
- STUDENT

Not every role must be fully exposed in the initial demonstration. The authorization model should nevertheless be designed to support distinct permissions.

##### `permissions`

Stores granular actions, such as:

- institution.read
- institution.manage
- enrolment.read
- enrolment.write
- batch.submit
- finding.respond
- audit_case.assign
- audit_case.resolve
- report.export
- verification.issue
- verification.read
- user.manage
- rules.configure

A role should receive explicit permissions rather than inheriting unrestricted administrative access by default.

##### `user_roles`

Maps users to roles.

Important fields:

- user_id
- role_id
- granted_by
- granted_at
- revoked_at, where applicable

##### `user_scopes`

Defines the institutional or organizational scope associated with a user's access.

Possible fields:

- id
- user_id
- scope_type
- institution_id, when the scope is institution-specific
- valid_from
- valid_until
- granted_by

A user can have more than one permitted scope, but access must be explicitly granted.

For example, an institution administrator should not automatically gain national visibility simply because they can manage users at their own institution.

##### `institutions`

Stores institutional reference information.

Important fields:

- id
- official_institution_code, where available
- name
- institution_type
- state_code
- district_code
- address, only to the extent required
- status
- source_reference
- created_at
- updated_at

The official institution code should have an appropriate uniqueness constraint when its source and uniqueness rules are confirmed.

Synthetic demonstration institutions must be clearly identifiable as synthetic.

#### B. Programme, intake and policy configuration

##### `programmes`

Represents a programme offered by an institution.

Important fields:

- id
- institution_id
- official_programme_code, where available
- programme_name
- qualification_level
- academic_discipline, if needed
- status
- created_at
- updated_at

Relationship:

```text
institutions 1 ─── N programmes
```

An institution may offer many programmes.

##### `academic_years`

Stores academic-year reference data.

Fields:

- id
- label
- start_date
- end_date
- status

Academic-year boundaries must not be inferred from arbitrary date arithmetic. They should follow the confirmed policy definition.

##### `programme_approvals`

Represents the approval of a programme for a particular period.

Fields:

- id
- programme_id
- academic_year_id
- approval_reference
- approval_status
- source_reference
- effective_from
- effective_until
- version
- recorded_at

This separates programme existence from the approval applicable to a particular academic year.

##### `approved_intake_versions`

Stores approved capacity and its history.

Fields:

- id
- programme_approval_id
- approved_intake
- source_type
- source_reference
- version
- effective_from
- effective_until
- recorded_by
- recorded_at

Capacity changes must create new versions rather than silently rewriting the original approval.

##### `seat_category_rules`

Stores category-specific policy rules.

Fields:

- id
- rule_code
- rule_name
- programme_scope
- academic_year_scope
- rule_version
- effective_from
- effective_until
- configuration
- source_reference
- status

The configuration structure can hold validated rule parameters, but its shape must be defined and checked by the application. Arbitrary user-supplied executable expressions must not be accepted.

**Important:** Do not hardcode one universal interpretation of NRI, OCI, Foreign National or supernumerary seats. The applicable rules must be confirmed for the relevant programme, institution type and academic year. Your source document explicitly identifies these as policy questions that require authoritative confirmation. *AICTE_APAAR_Student_Data_Platfo…*

#### C. Student identity and enrolment

##### `student_identities`

Represents the student identity information required for the platform.

Fields:

- id
- apaar_id_ciphertext, where encrypted identifier storage is appropriate.
- apaar_id_fingerprint, a keyed, non-reversible comparison value for exact-match detection.
- apaar_validation_status
- apaar_validation_source
- apaar_validation_checked_at
- created_at
- updated_at

The fingerprint should use a suitable keyed cryptographic construction and protected secret management. A plain, unsalted hash of a numeric identifier is not an adequate substitute for protecting a sensitive identifier.

The fingerprint is an internal comparison aid. It does not prove that the APAAR ID is authentic or belongs to the named person.

Only collect the identity attributes required by the approved data model. Do not automatically add Aadhaar, family information, biometrics or other sensitive attributes.

##### `enrolment_records`

Represents a student's reported enrolment at an institution.

Fields:

- id
- student_identity_id
- institution_id
- programme_id
- academic_year_id
- institution_student_id
- admission_date
- enrolment_status
- admission_category
- nri_status, where applicable
- oci_status, where applicable
- foreign_national_status, where applicable
- supernumerary_category, where applicable
- source_submission_batch_id
- current_record_version_id
- created_at
- updated_at

Relationship:

```text
Institution
    |
    └── Programme
            |
            └── Academic-year approval / intake
                    |
                    └── Enrolment records
```

One student identity can have multiple enrolment records over time. Such records must not automatically be treated as invalid: legitimate transfers, completed programmes and other permitted situations need explicit handling.

The application must define how it determines the current active enrolment set, rather than assuming that every record ever created is active.

##### `enrolment_record_versions`

Preserves the history of submitted record values.

Fields:

- id
- enrolment_record_id
- version_number
- snapshot_data
- change_reason
- changed_by
- changed_at
- source_batch_id
- validation_run_id

The snapshot must contain only the necessary record fields and must be protected according to the sensitivity of that data.

A new version should be created for material corrections. Ordinary read operations must never create new versions.

##### `enrolment_status_history`

Tracks changes in enrolment status.

Fields:

- id
- enrolment_record_id
- previous_status
- new_status
- effective_at
- recorded_at
- reason_code
- changed_by

This is useful for distinguishing a real conflict from a record that has since been transferred, withdrawn or completed.

#### D. Submission and ingestion

##### `submission_batches`

Represents a submission attempt.

Fields:

- id
- institution_id
- academic_year_id
- submission_type
- source_type
- submitted_by
- submitted_at
- processing_status
- source_filename
- source_checksum
- row_count
- accepted_count
- rejected_count
- flagged_count
- ruleset_version
- receipt_reference
- created_at

The original file should be retained only according to the documented retention and operational policy. Its checksum helps identify identical submissions; it is not proof that the contents are truthful.

##### `submission_rows`

Represents individual rows during batch processing.

Fields:

- id
- batch_id
- row_number
- processing_status
- normalized_data
- errors
- warnings
- linked_enrolment_record_id
- processed_at

The row staging area separates incoming data from accepted canonical records.

This matters because an upload containing errors should not silently corrupt the active registry.

##### `submission_receipts`

Stores the receipt associated with a completed submission.

Fields:

- id
- batch_id
- receipt_reference
- issued_at
- receipt_status
- summary_snapshot

The receipt must accurately report what happened: received, processing, accepted, partially accepted or rejected. A successful upload is not the same as a successful validation.

#### E. Validation and evidence

##### `validation_rules`

Stores rule metadata.

Fields:

- id
- rule_code
- name
- description
- category
- severity
- version
- effective_from
- effective_until
- status

##### `validation_runs`

Represents one execution of a validation set.

Fields:

- id
- batch_id, if batch-based
- institution_id
- programme_id
- academic_year_id
- ruleset_version
- started_at
- completed_at
- status
- summary

##### `validation_findings`

Represents an individual detected issue.

Fields:

- id
- rule_id
- validation_run_id
- batch_id
- enrolment_record_id, when applicable
- finding_category
- severity
- status
- explanation
- evidence_summary
- first_detected_at
- last_detected_at
- resolved_at

A finding should reference the rule and affected records. The frontend should not invent explanations based on the finding's colour or title.

##### `evidence_sources`

Represents the origin of information used to support a claim.

Fields:

- id
- source_type
- source_name
- source_status
- authority_scope
- reference_identifier
- observed_at
- recorded_at
- limitations

Source types should distinguish institution submissions, institution ERP feeds, authorized identity validation, authorized academic sources, student confirmation, manual document review and AICTE review.

##### `evidence_items`

Represents evidence associated with a record, finding or case.

Fields:

- id
- evidence_source_id
- enrolment_record_id, when applicable
- finding_id, when applicable
- audit_case_id, when applicable
- evidence_type
- storage_reference, where applicable
- checksum
- created_by
- created_at
- access_classification

Do not place arbitrary file contents into normal application logs. Uploaded evidence requires private storage, strict access controls and file-type and size validation.

#### F. Integrity ledger and audit trail

##### `audit_events`

Records material application events.

Fields:

- id
- actor_user_id, where applicable
- actor_type
- action
- target_type
- target_id
- occurred_at
- purpose_code, where required
- request_id
- outcome
- metadata
- integrity_metadata

The metadata must be carefully allowlisted. Sensitive payloads should not be copied into the event table indiscriminately.

Events should cover material operations such as:

- Account and role changes.
- Record creation and correction.
- Submission finalization.
- Rule changes.
- Finding resolution.
- Case assignment and closure.
- Verification-reference creation and revocation.
- Sensitive record access.
- Exports.

Audit events should be append-only at the application level, with restrictive database permissions and suitable integrity monitoring. A conventional tamper-evident audit design is appropriate; blockchain is not required.

#### G. Findings and discrepancy resolution

##### `finding_responses`

Stores an institution's response to a finding.

Fields:

- id
- finding_id
- responding_user_id
- response_type
- explanation
- submitted_at
- status

##### `finding_response_evidence`

Links permitted evidence to a response.

Fields:

- id
- finding_response_id
- evidence_item_id

##### `finding_resolution_history`

Preserves resolution decisions.

Fields:

- id
- finding_id
- previous_status
- new_status
- resolution_code
- resolution_note
- reviewed_by
- resolved_at

A correction does not automatically dismiss a finding. The relevant rule must run again, and the resolution process must follow the configured workflow.

#### H. Audit case management

##### `audit_cases`

Represents a formal review case.

Fields:

- id
- case_reference
- institution_id
- programme_id, when applicable
- academic_year_id
- case_type
- priority
- status
- selection_reason
- assigned_to
- response_deadline
- opened_by
- opened_at
- closed_at
- final_outcome

##### `audit_case_findings`

Links findings to cases.

Fields:

- audit_case_id
- finding_id
- linked_at

This is a many-to-many relationship: a case may contain several findings, and a finding may be referenced in more than one relevant review context if the policy permits it.

##### `audit_case_events`

Stores the case-specific workflow timeline.

Fields:

- id
- audit_case_id
- actor_user_id
- event_type
- description
- created_at

##### `audit_case_decisions`

Stores documented review decisions.

Fields:

- id
- audit_case_id
- decision_type
- decision_rationale
- decided_by
- decided_at

A risk score may help prioritize a case. It must not independently determine guilt, penalties or regulatory sanctions.

#### I. Controlled verification

##### `verification_references`

Stores limited-purpose verification references.

Fields:

- id
- public_reference_id
- enrolment_record_id
- issued_by
- purpose_code
- issued_at
- expires_at
- revoked_at
- verification_policy_version
- status

The public reference should be unpredictable and must not reveal internal database identifiers or APAAR IDs.

##### `verification_requests`

Records individual verification attempts.

Fields:

- id
- verification_reference_id
- requester_type
- purpose_code
- requested_at
- outcome
- request_id

##### `verification_access_events`

Records relevant disclosure events.

Fields:

- id
- verification_request_id
- disclosed_fields
- disclosure_policy_version
- occurred_at

Only the minimum permitted information should be returned. A verifier must not gain unrestricted access to a student's record through a QR code.

#### J. Reporting, integrations and administration

##### `integration_sources`

Stores integration configuration and operational status.

Fields:

- id
- source_name
- integration_type
- mode
- status
- last_successful_sync_at
- capability_description
- limitations
- configuration_reference

Secrets must not be stored directly in ordinary configuration fields. Use a suitable secrets manager or deployment secret mechanism.

##### `integration_sync_runs`

Stores sync attempts.

Fields:

- id
- integration_source_id
- started_at
- completed_at
- status
- records_processed
- error_summary

##### `report_jobs`

Stores report-generation requests where asynchronous processing is necessary.

Fields:

- id
- requested_by
- report_type
- scope
- filters
- status
- created_at
- completed_at
- storage_reference
- expires_at

Exports containing sensitive records must have restricted access, short-lived download access where appropriate and an audit event.

##### `notification_events`

Tracks notifications generated by the application.

Fields:

- id
- recipient_user_id
- notification_type
- related_object_type
- related_object_id
- created_at
- read_at
- delivery_status

Do not include sensitive student information in email or push-notification content unless the approved policy explicitly requires it.

### 4.3 The essential relationships

The central data relationships should look like this:

```text
INSTITUTIONS
    |
    +----< USER_SCOPES >---- USERS
    |
    +----< PROGRAMMES
                |
                +----< PROGRAMME_APPROVALS
                              |
                              +----< APPROVED_INTAKE_VERSIONS
                              |
                              +----< ENROLMENT_RECORDS
                                            |
                                            +---- STUDENT_IDENTITIES
                                            |
                                            +----< ENROLMENT_RECORD_VERSIONS
                                            |
                                            +----< ENROLMENT_STATUS_HISTORY
                                            |
                                            +----< EVIDENCE_ITEMS
                                            |
                                            +----< VERIFICATION_REFERENCES
                                            |
                                            +----< VALIDATION_FINDINGS

INSTITUTIONS
    |
    +----< SUBMISSION_BATCHES
                  |
                  +----< SUBMISSION_ROWS
                  |
                  +----< VALIDATION_RUNS
                                  |
                                  +----< VALIDATION_FINDINGS

VALIDATION_FINDINGS
    |
    +----< FINDING_RESPONSES
    |
    +----< FINDING_RESOLUTION_HISTORY
    |
    +----< AUDIT_CASE_FINDINGS >---- AUDIT_CASES
                                          |
                                          +----< AUDIT_CASE_EVENTS
                                          |
                                          +----< AUDIT_CASE_DECISIONS

USERS / SERVICES
    |
    +----< AUDIT_EVENTS

INTEGRATION_SOURCES
    |
    +----< INTEGRATION_SYNC_RUNS
```

This is a logical relationship map. Exact foreign keys, uniqueness rules, delete behaviour and indexing decisions must be implemented explicitly in the database migrations.

### 4.4 Database constraints that matter most

At minimum, the schema design must address:

- Unique internal IDs.
- Unique institution codes where officially applicable.
- Valid foreign-key relationships.
- Valid status values.
- Non-negative approved-intake values.
- Correct effective-date ranges.
- Correct version numbering.
- Prevention of duplicate version numbers for the same record.
- Appropriate uniqueness for receipt references.
- Protection against duplicate processing of the same idempotent submission.
- Prevention of invalid relationships between institutions, programmes and enrolments.
- Valid relationships between findings, rules and validation runs.
- Valid relationships between verification references and their underlying records.

Do not create a blanket unique constraint that permits only one historical enrolment per student. Historical records and legitimate transfers must remain possible.

Likewise, do not create a simplistic database constraint that prevents every student identity from being linked to multiple enrolments. The system must distinguish legitimate history from conflicting active records.

### 4.5 Indexing and query performance

Indexes should be selected according to actual access patterns.

Likely candidates include:

- Foreign keys used in frequent joins.
- Institution and academic-year filters.
- Programme and academic-year filters.
- Submission batch status.
- Finding status and severity.
- Audit case status, priority and assignment.
- Record version lookups.
- Verification-reference lookup.
- Indexed exact-match fingerprint for protected identifier comparisons.

Use composite indexes when common queries filter by multiple fields.

Do not index every column automatically. Indexes consume storage and slow writes.

For national-scale datasets, query plans, realistic data volumes, pagination and performance tests must inform further optimization.

---

## 5. Authentication, JWT and Authorization — Shared Across All Four Phases

Authentication is a foundation, not a feature to postpone until Phase 4.

### 5.1 JWT design

JWT is a token format, not a complete authentication system. We must design the surrounding account, session, refresh, revocation and authorization behaviour carefully.

A reasonable first-party authentication design is:

- Short-lived access tokens.
- Secure refresh-token handling.
- Token rotation on refresh.
- Refresh-token reuse detection.
- Session revocation.
- Account status checks.
- Server-side permission checks.
- Appropriate protection against cross-site request forgery when cookies are used for authentication.

#### Recommended browser handling

For a browser application, avoid putting long-lived authentication tokens in localStorage.

A preferable arrangement is:

1. Keep short-lived access credentials out of persistent browser storage where practical.
2. Store refresh credentials in a Secure, HttpOnly cookie with an appropriate SameSite policy and path.
3. Protect refresh and other cookie-authenticated state-changing operations against CSRF.
4. Use HTTPS in deployment.
5. Rotate refresh tokens and invalidate the previous token.
6. Revoke sessions on logout, account suspension and relevant security events.
7. Never log tokens or include them in URLs.

The exact implementation must be chosen and tested against the frontend deployment model. We should not invent our own cryptography.

#### JWT claims

Only necessary claims should be included, such as:

- `sub`: user identifier.
- `iss`: issuer.
- `aud`: intended audience.
- `iat`: issued-at time.
- `exp`: expiry.
- `jti`: token identifier, if needed for the chosen lifecycle.

Do not treat a role claim embedded in a long-lived token as permanently authoritative. If permissions change or an account is disabled, the application needs a strategy for making those changes effective promptly.

#### Refresh-session storage

If refresh sessions are stored in the database, store a protected token hash or another appropriate non-reusable representation, along with:

- Session identifier.
- User identifier.
- Issued time.
- Expiry.
- Revocation time.
- Rotation lineage where needed.
- Relevant device/session metadata, without collecting unnecessary fingerprinting data.

A raw refresh token must not be stored in plaintext.

### 5.2 Password security

The authentication system must use a reputable password-hashing algorithm supported by a maintained library, with appropriate parameters.

It must also implement:

- Password policy appropriate to the account type.
- Login throttling.
- Generic error messages that do not reveal whether an account exists.
- Account recovery with short-lived, single-use tokens.
- Secure password-reset completion.
- Session invalidation after security-sensitive account changes.
- Protection against credential stuffing and brute-force attempts.
- MFA for privileged users where feasible and required by the deployment policy.

### 5.3 Authorization model

NEEV requires both role-based and scope-based authorization.

For example:

| Role | Permitted scope |
|---|---|
| AICTE administrator | Explicitly authorized regulatory and administrative functions. |
| AICTE officer | Assigned or otherwise authorized institutions, programmes, records and cases. |
| Institution administrator | Authorized operations for their own institution. |
| Institution operator | Assigned submission, correction and response functions within their institution. |
| Auditor | Assigned audit cases and necessary supporting evidence. |
| Student | Their own permitted record and correction/dispute functions. |
| Verifier | A limited-purpose verification result, not unrestricted student-record access. |
| Platform administrator | Operational administration; sensitive business-data access remains controlled and audited. |

A platform administrator must not automatically become an unrestricted reader of all student information merely because they maintain the software.

### 5.4 Object-level authorization

Every endpoint that accepts an object identifier must check whether the user may access that specific object.

Examples of objects requiring scope enforcement:

- Institution.
- Programme.
- Student identity.
- Enrolment record.
- Submission batch.
- Finding.
- Evidence item.
- Audit case.
- Report.
- Verification reference.

Changing `/records/record-A` to `/records/record-B` must not allow unauthorized access.

This needs automated tests that attempt to cross institutional boundaries. Frontend restrictions alone do not satisfy the requirement.

### 5.5 Security controls shared by every phase

From Phase 1 onward:

- Validate all input on the backend.
- Use parameterized database operations.
- Configure CORS for approved origins.
- Set appropriate security headers.
- Rate-limit sensitive endpoints.
- Avoid exposing stack traces in production responses.
- Protect file uploads.
- Avoid sensitive information in logs.
- Keep secrets outside source control.
- Apply least privilege to database and service accounts.
- Use dependency and vulnerability checks.
- Ensure errors do not disclose protected record details.
- Audit material administrative actions.
- Test permission failures as well as successful requests.

These controls are consistent with the security and privacy requirements in the source document. *AICTE_APAAR_Student_Data_Platfo…*

---

## 6. UI/UX System — The Design Must Be Deliberate

NEEV must look like a serious regulatory platform: precise, restrained, readable, data-rich and easy to operate.

It must not look like a generic AI-generated SaaS dashboard full of gradients, pills, floating cards and oversized empty space.

### 6.1 Recommended visual direction

Design concept: **a national regulatory evidence workspace.**

Use an editorial, institutional interface with clear hierarchy, strong table design, meaningful status indicators and compact but readable information density.

#### Colour palette

The following is a proposed palette for the implementation:

| Token | Colour | Use |
|---|---|---|
| --color-app-bg | #F5F4EF | Main application background. |
| --color-surface | #FFFFFF | Main content surfaces. |
| --color-surface-muted | #EEEDE7 | Secondary panels and grouped content. |
| --color-sidebar | #202A32 | Primary navigation background. |
| --color-sidebar-hover | #2D3943 | Sidebar hover and active surfaces. |
| --color-text-primary | #202A32 | Main text. |
| --color-text-secondary | #606B73 | Supporting labels and descriptions. |
| --color-border | #D9DCD7 | Dividers, table borders and field outlines. |
| --color-accent | #A87932 | Restrained emphasis and selected highlights. |
| --color-accent-hover | #896027 | Accent hover state. |
| --color-success | #26745B | Successful operations. |
| --color-warning | #946316 | Warnings requiring attention. |
| --color-danger | #A33E3E | Destructive actions and serious errors. |
| --color-info | #315F83 | Informational states. |

Status colours must always be accompanied by text or an accessible icon. Colour alone must never communicate whether a record is validated, disputed or unresolved.

The accent colour is an interface-design choice, not a claim about official AICTE branding.

### 6.2 Typography

Use a highly readable, restrained typographic system.

- **Headings:** a professional serif or refined display face, used sparingly.
- **Body and interface:** a neutral sans-serif family.
- **Tables and identifiers:** a highly legible sans-serif, with monospaced styling only for short technical identifiers where it improves scanning.

Typography should be consistent, not decorative.

Do not make every heading enormous. This is a working data platform, not a marketing landing page.

### 6.3 Layout rules

#### Application shell

Use a conventional, left-aligned application layout:

```text
┌─────────────────────────────────────────────────────────────────┐
│ NEEV       Context / Academic Year       Search   Alerts  User  │
├───────────────┬─────────────────────────────────────────────────┤
│               │                                                 │
│ Overview      │ Page title                                      │
│ Institutions  │ Brief explanation / contextual actions          │
│ Programmes    │                                                 │
│ Submissions   │ Primary content                                 │
│ Enrolments    │                                                 │
│ Findings      │ Tables / forms / detail panels                  │
│ Audit cases   │                                                 │
│ Reports       │                                                 │
│ Administration│                                                 │
│               │                                                 │
└───────────────┴─────────────────────────────────────────────────┘
```

The sidebar should support clear active states and compact navigation. The top bar should display the relevant context without becoming a row of decorative chips.

#### Page alignment

- Use a consistent page container.
- Align content to the left.
- Use grids where they improve scanning.
- Give tables adequate width.
- Avoid vertically centring entire application pages.
- Avoid placing every form inside a tiny central card.
- Use side panels or detail pages where they preserve context.
- Make the primary action obvious.
- Use a stable breadcrumb convention on deeper pages.

### 6.4 Tables

Tables are a primary NEEV interface component.

They should support the relevant combination of:

- Search.
- Filters.
- Sorting.
- Pagination.
- Loading state.
- Empty state.
- Error state.
- Row selection where needed.
- Bulk operations with explicit confirmation.
- Column visibility where justified.
- Clear status labels.
- Responsive overflow behaviour.
- Accessible keyboard navigation.

Do not render thousands of records in one browser table. Pagination or another appropriate server-driven approach should be used.

For sensitive fields, use masking by default and require explicit authorization for full-value access.

### 6.5 Forms

Every important form must have:

- Clear field labels.
- Required/optional indicators.
- Input help where the field is ambiguous.
- Inline validation.
- Backend error handling.
- Submission progress.
- Duplicate-submission protection.
- Unsaved-change handling where necessary.
- Success and failure feedback.
- Keyboard and screen-reader accessibility.

For complex forms, group fields by task rather than placing every field in one long, undifferentiated column.

### 6.6 Buttons and interaction design

Define a small button system:

- **Primary:** one dominant action per relevant page or workflow.
- **Secondary:** alternative, non-destructive actions.
- **Tertiary:** low-emphasis actions.
- **Destructive:** deletion, revocation or other irreversible operations.
- **Icon-only:** only when the icon has an accessible name and its meaning is clear.

Avoid using a rounded capsule shape for every control. Use consistent, moderate corner radii.

Buttons must have clear hover, focus, disabled, loading and pressed states.

### 6.7 Motion

Animation should communicate state changes rather than decorate the screen.

Use subtle motion for:

- Opening a detail panel.
- Displaying a notification.
- Showing a menu.
- Expanding a section.
- Transitioning between closely related views.

Do not animate every card independently or delay routine administrative operations for visual effect.

Respect reduced-motion preferences.

### 6.8 Required UI states

Every data-driven screen must have the appropriate states:

1. Initial loading.
2. Successful data display.
3. Empty dataset.
4. No results after filtering.
5. Validation error.
6. Permission denied.
7. Network failure.
8. Expired session.
9. Server error.
10. Successful mutation.
11. Partial success, where applicable.
12. Processing or background-job status.

A blank page with no explanation is never an acceptable error state.

### 6.9 Accessibility

Build accessibility into the components:

- Semantic HTML.
- Keyboard operation.
- Visible focus indicators.
- Labelled inputs.
- Accessible dialog behaviour.
- Screen-reader-friendly status announcements.
- Sufficient contrast.
- Error messages linked to their fields.
- Accessible table navigation.
- Reduced-motion support.

Accessibility is not a final colour-contrast patch. It affects the component architecture.

---

## 7. Shared Engineering Standards for All Phases

### 7.1 API contract discipline

Use versioned API routes, such as `/api/v1/...`.

Each endpoint should have:

- A defined request schema.
- A defined response schema.
- Authentication requirements.
- Authorization requirements.
- Input validation.
- Documented error responses.
- Pagination where relevant.
- Rate limits where appropriate.
- Idempotency for retry-sensitive write operations.
- A request or correlation identifier.
- Tests.

FastAPI's generated OpenAPI documentation should accurately represent the implemented API.

The frontend should use the documented contract instead of independently guessing field names or response structures.

### 7.2 Standard error handling

Return consistent, structured errors.

A useful error response includes:

- A stable error code.
- A safe, human-readable message.
- Field-level validation details where applicable.
- A request identifier.
- An appropriate HTTP status.

Do not return stack traces, SQL statements, secrets or sensitive record contents.

### 7.3 Transaction discipline

Operations that must succeed or fail together should run in database transactions.

Examples include:

- Finalizing a submission batch.
- Creating a corrected record version.
- Resolving a finding and recording its resolution history.
- Issuing a verification reference and its audit event.
- Changing a role and recording the authorization event.

For long-running batch processing, use a deliberate state machine and idempotent processing rather than attempting to hold a single database transaction open throughout an entire large upload.

### 7.4 Testing discipline

Every phase needs a combination of:

- Unit tests.
- Database integration tests.
- API tests.
- Authorization tests.
- Cross-institution isolation tests.
- Frontend component tests.
- End-to-end tests.
- Regression tests for previously discovered bugs.

Security-sensitive tests must include negative cases. It is not enough to prove that an authorized user can read a record; we must also prove that unauthorized users cannot.

### 7.5 Repository and file discipline

The coding workflow must:

- Inspect the existing repository before modifying it.
- Preserve unrelated working code.
- Avoid destructive rewrites without a justified plan.
- Avoid duplicate implementations of the same component.
- Remove genuinely obsolete files only after confirming they are no longer referenced.
- Avoid generating test files that are not run or maintained.
- Keep the dependency list deliberate.
- Keep setup instructions current.
- Maintain a useful `.env.example` without real secrets.
- Build and test after meaningful changes.
- Leave the repository in a state that can be reviewed and committed by you.

No Git operations are part of the implementation workflow. You retain control over Git and GitHub.

---

## 8. APAAR Research and Policy-Validation Rules

The uploaded specification describes APAAR as a unique academic identifier and explains why identity linking must be separated from verification of current enrolment. It also lists the official questions that still require confirmation, including API availability, permitted fields, approved-intake authority and category-specific rules. *AICTE_APAAR_Student_Data_Platfo…*

We must preserve that distinction throughout the implementation.

### 8.1 Official-source research is a continuing requirement

Use official sources for claims about:

- APAAR's purpose and documented behaviour.
- Officially documented identifier format.
- APAAR privacy and data-handling policies.
- AICTE approval and intake definitions.
- Seat-category and supernumerary-seat rules.
- Official reporting requirements.
- Available APIs and their authorization requirements.
- Relevant legal and government security requirements.

Start with the official resources identified in the source document:

- APAAR official portal
- APAAR FAQs
- APAAR privacy policy
- AISHE official portal
- AISHE survey information
- National Academic Depository

These are starting points for research, not evidence that NEEV has permission to access those systems.

### 8.2 Maintain an assumptions register

Every unresolved question should have an explicit record.

Suggested fields:

| Field | Meaning |
|---|---|
| assumption_id | Stable reference. |
| topic | The policy or integration question. |
| current_understanding | What is presently known. |
| evidence_source | Official source, if available. |
| confidence_status | Confirmed, partially confirmed, unconfirmed or contradicted. |
| implementation_effect | Which system behaviour depends on the answer. |
| owner | Person responsible for resolving it. |
| resolution_required_by | Milestone at which the question must be settled. |
| resolution_notes | Final evidence and decision. |

Examples of unresolved questions:

- Is an authorized APAAR validation API available for the proposed use?
- What does it actually return?
- Which source is authoritative for approved intake?
- How are NRI, OCI, FN and supernumerary seats treated for each relevant programme and year?
- Which fields are mandatory, optional or prohibited?
- Which student-record disclosures are permitted?
- What retention and correction rules apply?

Where policy remains unconfirmed, the system should use explicit configuration and clearly labelled synthetic data—not a guessed rule presented as official policy.

---

# PHASE 1 — Secure Foundation & Enrolment Core

## Objective

Build the first genuinely functional version of NEEV.

At the end of Phase 1, a user should be able to log in, see the appropriate workspace, work within their authorized institutional scope, inspect institution/programme/intake data, upload a synthetic student roster, correct basic data-quality issues, submit a batch, and see accurate validation and intake-reconciliation results.

This phase must deliver both frontend and backend. We will not build a frontend mockup and postpone the backend.

## 1.1 Phase 1 scope

Phase 1 includes:

1. Repository and architecture foundation.
2. Database migrations and initial reference data.
3. Authentication.
4. Role-based and institution-scoped authorization.
5. Application navigation and page layouts.
6. Institution management.
7. Programme and academic-year management.
8. Approved-intake reference data.
9. Student identity and enrolment records.
10. Submission batch creation.
11. CSV roster upload and preview.
12. Deterministic schema validation.
13. Intake reconciliation.
14. Submission receipts.
15. Audit events for important Phase 1 actions.
16. Automated tests and a repeatable local setup.

The upload-to-validation workflow is the first complete vertical slice.

## 1.2 Frontend deliverables

### A. Login page

Purpose: Allow authorized users to enter the system.

The page should include:

- NEEV wordmark and product identity.
- Clear page heading.
- Email or approved login identifier.
- Password input with show/hide control.
- Sign-in button.
- Loading state.
- Field validation.
- Generic invalid-credentials message.
- Account-disabled or access-denied messaging that does not expose unnecessary account information.
- Accessible keyboard navigation.
- Responsive layout.
- Appropriate session-expiry handling.

Do not implement an arbitrary public registration form if the intended user model requires administrator-issued accounts.

For the initial build, use synthetic demo accounts with clearly documented setup. Their credentials must not be hardcoded into production configuration.

### B. Protected application shell

After successful login, display the main application shell.

Primary navigation:

- Overview.
- Institutions.
- Programmes & Intake.
- Submissions.
- Enrolments.
- Administration, where permitted.

Later phases will add the full discrepancy, audit and verification workflows.

Navigation must reflect the user's permissions. However, the backend must independently enforce the same permissions.

### C. Initial overview page

The Phase 1 overview should show metrics calculated from the database:

- Institutions available to the current user.
- Programmes in scope.
- Academic year currently selected.
- Submission batches by status.
- Student records in the selected scope.
- Latest submission activity.
- Validation issues requiring attention.

Do not hardcode KPI numbers into the components.

If the database is empty, show a purposeful empty state explaining how an authorized administrator can load the necessary reference data.

### D. Institutions page

Provide:

- Institution list.
- Search.
- Pagination.
- Status filter.
- Institution detail view.
- Programme list for the institution.
- Relevant submission history.

Only authorized users should be able to create or update institutional reference data.

An institution administrator should see their own institution, not a national directory of unrestricted student information.

### E. Programmes & Intake page

Provide:

- Programme list.
- Institution and academic-year filters.
- Programme detail.
- Approval reference.
- Approved intake.
- Applicable category-rule references.
- Source and effective-date information.
- Clear indication when data is synthetic or unconfirmed.

The interface must distinguish an actual confirmed approval source from a synthetic demonstration value.

### F. Submission workflow

The submission workflow should be a guided sequence.

**Step 1 — Select context**

The user selects:

- Institution, restricted to their authorized scope.
- Academic year.
- Programme or permitted programme group.
- Submission type.

**Step 2 — Select file**

Initially, support a clearly defined CSV schema.

The page must show:

- Supported file format.
- Maximum permitted file size.
- Required columns.
- Optional columns.
- Example template.
- File-processing limitations.

The backend must independently validate all of these conditions.

**Step 3 — Preview**

Display:

- Total rows detected.
- Valid rows.
- Rows with errors.
- Rows with warnings.
- Missing fields.
- Invalid formats.
- Duplicate rows within the file.
- Invalid programme references.
- Invalid status values.

Allow the user to inspect row-level problems before finalization.

**Step 4 — Resolve errors**

Provide an understandable list of affected rows and fields.

The first phase does not need a sophisticated spreadsheet editor, but it must make errors actionable.

**Step 5 — Submit**

When the user finalizes a valid or policy-permitted partially valid batch:

- Show the submission progress.
- Prevent accidental duplicate finalization.
- Return a receipt reference.
- Display the final processing status and counts.

If the batch is rejected, the UI must say why.

### G. Enrolment table

Provide a searchable, paginated table with columns such as:

- Institution student ID.
- Masked APAAR identifier, if present.
- Programme.
- Academic year.
- Admission date.
- Enrolment status.
- Validation state.
- Latest source batch.

Do not display the complete APAAR ID by default.

Provide a record-detail page showing the permitted identity and enrolment fields, their source and their validation state.

A record that passes format checks must not be labelled officially APAAR-verified.

## 1.3 Backend modules

Phase 1 should introduce the core application modules.

### `auth`

Responsibilities:

- Login.
- Logout.
- Access-token issuance.
- Refresh-session lifecycle.
- Password verification.
- Account-status checks.
- Password-reset flow if included.
- Authentication error handling.

### `authorization`

Responsibilities:

- Role and permission resolution.
- Institutional scope checks.
- Protected-object access checks.
- Administrative permission enforcement.

### `institutions`

Responsibilities:

- Institution retrieval.
- Authorized creation and updates.
- Institution status.
- Institutional reference data.

### `programmes`

Responsibilities:

- Programme retrieval.
- Programme and academic-year relationships.
- Approval references.
- Programme status.

### `intake`

Responsibilities:

- Approved-intake versions.
- Effective dates.
- Source provenance.
- Configured category treatment.
- Reconciliation inputs.

### `enrolments`

Responsibilities:

- Student identity linkage.
- Enrolment record creation.
- Record retrieval.
- Status handling.
- Field-level validation.
- Institution-scoped queries.

### `submissions`

Responsibilities:

- Batch creation.
- File parsing.
- Row staging.
- Validation execution.
- Batch state transitions.
- Finalization.
- Receipt generation.
- Idempotency.

### `validation`

Responsibilities:

- Schema rules.
- Required-field rules.
- Date validation.
- Enumeration validation.
- Identifier format checks.
- Intra-batch duplicate detection.
- Programme-reference checks.
- Findings generation.

### `reconciliation`

Responsibilities:

- Active enrolment counting.
- Approved-intake comparison.
- Category-aware calculation.
- Variance calculation.
- Missing-reference handling.

### `audit`

Responsibilities:

- Recording material Phase 1 actions.
- Capturing actor and timestamp.
- Associating actions with request identifiers.
- Ensuring audit failures are handled according to the operation's criticality.

## 1.4 Phase 1 API contract

These are proposed API contracts, not official AICTE endpoints.

| Method and endpoint | Purpose | Authorization requirement |
|---|---|---|
| POST /api/v1/auth/login | Authenticate a user. | Public endpoint with throttling. |
| POST /api/v1/auth/refresh | Rotate or renew an authenticated session. | Valid refresh session and CSRF protection where applicable. |
| POST /api/v1/auth/logout | Revoke the current session. | Authenticated session. |
| GET /api/v1/auth/me | Return the current user's identity and permitted capabilities. | Authenticated user. |
| GET /api/v1/institutions | List institutions within the permitted scope. | Authorized institution or regulatory scope. |
| GET /api/v1/institutions/{institutionId} | Retrieve an institution. | Object-level authorization. |
| POST /api/v1/institutions | Create an institution record. | Explicit administrative permission. |
| PATCH /api/v1/institutions/{institutionId} | Update permitted institution fields. | Explicit administrative permission. |
| GET /api/v1/institutions/{institutionId}/programmes | List programmes for an institution. | Object-level authorization. |
| GET /api/v1/programmes | Search programmes within permitted scope. | Authorized scope. |
| GET /api/v1/programmes/{programmeId} | Retrieve programme detail. | Object-level authorization. |
| GET /api/v1/programmes/{programmeId}/intake | Retrieve applicable intake data. | Object-level authorization. |
| GET /api/v1/academic-years | Retrieve configured academic years. | Authenticated user or permitted public subset, according to policy. |
| POST /api/v1/batches | Create a submission batch. | Institution submission permission. |
| POST /api/v1/batches/{batchId}/file | Upload a roster file. | Batch ownership and institution scope. |
| GET /api/v1/batches/{batchId} | Retrieve batch status and metadata. | Batch scope. |
| GET /api/v1/batches/{batchId}/preview | Retrieve row-level preview and validation summary. | Batch scope. |
| POST /api/v1/batches/{batchId}/finalize | Finalize a validated batch. | Authorized batch owner and valid state. |
| GET /api/v1/batches/{batchId}/receipt | Retrieve the submission receipt. | Batch scope. |
| GET /api/v1/enrolments | Search enrolments within permitted scope. | Record-read permission. |
| GET /api/v1/enrolments/{recordId} | Retrieve an enrolment record. | Object-level authorization. |
| GET /api/v1/dashboard/summary | Retrieve summary metrics for the permitted scope. | Authorized dashboard access. |
| GET /api/v1/health/live | Process liveness check. | Deployment policy. |
| GET /api/v1/health/ready | Readiness check for required dependencies. | Restricted or operational endpoint. |

Additional endpoints may be introduced if a real workflow requires them, but each must have a documented purpose. We should not create endpoints merely to inflate the API count.

#### Important API rules

- Every endpoint must validate input.
- All protected endpoints must authenticate and authorize.
- All institution-owned objects must be scope-checked.
- Pagination must be bounded.
- Errors must use the shared error format.
- Write operations must use transactions where needed.
- Retry-sensitive operations must be idempotent.
- Sensitive identifiers must not appear in URL query parameters.
- Rate limits must be applied to authentication and other abuse-sensitive endpoints.
- Logs must use request IDs without logging credentials or entire student payloads.

## 1.5 Phase 1 validation rules

Each implemented rule must have a stable identifier and tests.

| Rule ID | Check | Expected behaviour |
|---|---|---|
| SCH-001 | Required field missing | Reject the row or mark it according to the defined submission policy. |
| SCH-002 | Invalid date | Report the exact row and field. |
| SCH-003 | Invalid enumeration | Identify the unsupported value. |
| SCH-004 | Invalid programme reference | Prevent the row from being silently linked to the wrong programme. |
| SCH-005 | Invalid academic year | Reject or flag the invalid reference. |
| SCH-006 | Duplicate row in the batch | Identify the duplicate according to the documented row-comparison rules. |
| APA-001 | Missing APAAR ID | Record the missing identifier state. |
| APA-002 | Malformed APAAR-like value | Flag the format issue using the officially confirmed format rule. |
| APA-003 | Format valid but no authorized source match | Keep format validation and source verification separate. |
| ENR-001 | Unsupported enrolment status | Reject or flag the invalid status. |
| INT-001 | Approved-intake reference missing | Mark reconciliation as unavailable or incomplete; do not invent capacity. |
| INT-002 | Active count exceeds configured permitted capacity | Create an explainable finding using the applicable rule version. |
| INT-003 | Reported total differs from calculated total | Display the difference and its calculation basis. |

The list is an initial rule catalogue, not a claim that it contains every future regulatory rule.

#### Example reconciliation

Suppose a synthetic programme has:

- Approved intake: 120.
- Active student enrolment records: 116.
- Applicable category rules: configured and available.
- No unresolved capacity exception.

NEEV should show the configured intake, calculated active count and variance.

If the count is 123, the system must apply the configured rules before generating a finding. It must not assume that every seat category is governed by the same capacity treatment.

If the relevant intake source is missing or stale, the system should display that limitation instead of presenting an unsupported violation.

## 1.6 Phase 1 database migrations

Phase 1 should create the initial schema for:

- Users.
- Roles.
- Permissions.
- User-role mappings.
- User scopes.
- Institutions.
- Programmes.
- Academic years.
- Programme approvals.
- Approved-intake versions.
- Seat-category rule configuration.
- Student identities.
- Enrolment records.
- Submission batches.
- Submission rows.
- Submission receipts.
- Validation rules.
- Validation runs.
- Validation findings.
- Audit events.

Some relationships may require placeholder or nullable foreign keys during initial creation, but the final migrations must enforce valid relationships without circular dependency problems.

Do not introduce all future tables as unused, undocumented empty structures simply because they appear in the eventual plan. Implement the necessary baseline entities now and add the remaining modules when their phase begins.

#### Initial synthetic dataset

Seed enough data to test:

- Two or more synthetic institutions.
- Multiple programmes.
- Multiple academic years.
- Different approved-intake values.
- Valid enrolment records.
- Missing identifier values.
- Malformed identifier values.
- Duplicate rows.
- An institution whose enrolment exceeds its configured capacity.
- A legitimate historical or inactive record.

All synthetic records must be visibly marked as demonstration data.

## 1.7 Phase 1 acceptance criteria

Phase 1 is complete only when all the following are demonstrated.

#### Authentication

- A valid demo user can sign in.
- Invalid credentials do not expose account-existence details.
- A disabled account cannot access protected operations.
- Logout revokes the relevant session.
- Expired sessions are handled correctly.
- Refresh-token rotation behaves as designed.
- Unauthenticated requests to protected endpoints are rejected.

#### Authorization

- An institution administrator sees only their permitted institutional scope.
- Direct requests for another institution's records are denied.
- A user without administrative permission cannot create or update institution reference data.
- Protected endpoints enforce permissions independently of the frontend.

#### Data integrity

- Migrations create the schema from a clean database.
- Seed data is repeatable.
- Invalid foreign-key references are rejected.
- Database constraints are exercised by tests.
- Approved-intake versions preserve their history.

#### Upload and validation

- A valid CSV can be uploaded and previewed.
- Invalid rows show row-level feedback.
- Missing and malformed identifiers are distinguished.
- Duplicate rows are identified.
- The batch receives a unique receipt.
- Repeated finalization does not duplicate records.
- Dashboard figures update from actual stored data.

#### User experience

- The core workflow works without manually editing database rows.
- Loading, empty, validation and error states are implemented.
- The layout works at the intended desktop viewport and remains usable on smaller screens.
- Sensitive identifiers are masked by default.

#### Engineering

- Backend unit and integration tests pass.
- Frontend tests pass.
- Production frontend build succeeds.
- Database migrations work from a clean database.
- The setup instructions are sufficient to run the application locally.
- No secrets or real student records are committed.

**Phase 1 deliverable:** A secure, testable upload-to-validation application with real database-backed data.

---

# PHASE 2 — Integrity Ledger & Discrepancy Resolution

## Objective

Turn the Phase 1 data-entry and validation application into a traceable integrity system.

At the end of Phase 2, NEEV must identify cross-institution conflicts, distinguish potential duplicates from legitimate transfers, preserve record versions, record evidence provenance, allow institutional responses and maintain an accountable discrepancy-resolution history.

This phase implements the first major differentiator of NEEV: the Enrolment Integrity Ledger.

Your source document defines this ledger as a versioned history of what was reported, when it changed, who changed it and why. *AICTE_APAAR_Student_Data_Platfo…*

## 2.1 Phase 2 scope

Add:

1. Cross-institution duplicate and conflict detection.
2. Status-aware conflict rules.
3. Enrolment record version history.
4. Evidence-source and provenance tracking.
5. Validation-finding lifecycle.
6. Institution correction workflow.
7. Finding response and resolution history.
8. Controlled evidence attachments.
9. Audit timeline.
10. Notifications for relevant workflow events.
11. Frontend screens for findings and correction.
12. Backend endpoints and permission checks.
13. Automated conflict, history and authorization tests.

## 2.2 Cross-institution conflict detection

#### Exact-match logic

The system should be able to identify the same protected APAAR identifier appearing across multiple records, subject to the configured scope and policy.

Use the protected comparison fingerprint described in the database design rather than exposing the identifier to ordinary matching queries.

The detection service must evaluate:

- Whether the records belong to the same or different institutions.
- Whether their academic years overlap.
- Whether the records are currently active.
- Whether the enrolment dates conflict.
- Whether a transfer or withdrawal explains the relationship.
- Whether the rule applies to the relevant programme and enrolment type.

A match is a conflict signal, not a fraud verdict.

#### Legitimate transfer example

A synthetic student is recorded at Institution A, then transfers to Institution B.

If Institution A's record is correctly marked as transferred with an appropriate effective date, the system must not automatically treat the historical records as proof of simultaneous active enrolment.

The system should preserve both records and their histories.

If Institution A's record remains active and conflicts with Institution B's record, the system may create a review finding.

#### Missing identifier handling

A missing APAAR ID must not be replaced by an invented value.

Do not create an automatic person-level match based only on a similar name.

If a future matching process uses authorized additional attributes, it must:

- Be based on a documented, lawful purpose.
- Identify the attributes and method used.
- Create a candidate match for review.
- Explain the reason for the candidate.
- Avoid automatic adverse action.
- Apply restricted access to sensitive matching information.

#### Conflict-detection service

The service should return a structured result containing:

- Rule identifier.
- Affected record references.
- Conflict type.
- Explanation.
- Relevant status and date information.
- Source references.
- Suggested next action.
- Detection timestamp.

This structure allows the frontend to explain a finding without independently reimplementing the rule.

## 2.3 Record versioning

Every material record correction should create a new version.

The system must preserve:

- The previous version.
- The new version.
- The actor.
- The timestamp.
- The correction reason.
- The source submission or correction request.
- The relevant validation results.
- The finding-resolution history, where applicable.

#### Required behaviour

If a user corrects an incorrect admission date:

1. The backend checks the user's authorization.
2. The backend validates the new value.
3. The operation runs in a transaction.
4. The previous version remains available.
5. A new record version is created.
6. A material audit event is recorded.
7. Relevant validation rules are rerun.
8. The UI shows the new current value.
9. The history view shows what changed and why.

The current record should not be overwritten in a way that destroys its history.

The implementation must also protect against lost updates. Where concurrent corrections are possible, use optimistic concurrency or an equivalent mechanism so that a user does not unknowingly overwrite another user's newer changes.

## 2.4 Findings lifecycle

Define an explicit workflow rather than allowing findings to move between arbitrary statuses.

A reasonable initial lifecycle is:

```text
OPEN
  |
  +----> AWAITING_INSTITUTION_RESPONSE
  |                |
  |                v
  |        RESPONSE_RECEIVED
  |                |
  |                v
  +----------> UNDER_REVIEW
                   |
          +--------+---------+
          |        |         |
          v        v         v
       RESOLVED  DISMISSED  ESCALATED
```

The exact transitions must be enforced by the backend.

The frontend must not be able to set an arbitrary status simply by submitting a string.

#### Finding transition requirements

For each transition, define:

- Permitted source statuses.
- Permitted target statuses.
- Required actor permission.
- Required fields.
- Whether a reason is mandatory.
- Whether a notification is required.
- Which audit event must be recorded.

For example, dismissing a material finding may require a documented rationale and reviewer permission.

A correction submission may trigger revalidation, but it must not automatically mark the finding resolved unless the rule and workflow explicitly support that outcome.

## 2.5 Evidence provenance

Each relevant record or finding should communicate where the information came from.

Possible source labels:

- Institution submission.
- Institution ERP.
- Authorized identity validation.
- Authorized academic record.
- Student confirmation.
- Manual document review.
- AICTE review.
- External source unavailable.
- Simulated integration.

For each source, store the source status and limitations.

The interface must not treat a source as universally authoritative for every claim.

For example, evidence of a degree award may support the claim that a qualification was issued. It does not necessarily prove that the student is currently enrolled at a particular institution.

#### Evidence attachment workflow

If the workflow permits supporting documents:

1. The user selects an allowed file.
2. The backend verifies size and file type.
3. The file is stored in private storage.
4. A checksum is recorded.
5. Access is restricted by institution and case permissions.
6. An audit event records the relevant action.
7. The file is accessible only to authorized users.

Where production deployment requires malware scanning, that capability must be implemented and tested before accepting real files. A filename extension alone is not a security check.

## 2.6 Phase 2 frontend screens

### A. Findings inbox

The findings page should contain:

- Finding reference.
- Institution.
- Programme.
- Academic year.
- Rule category.
- Severity.
- Status.
- First-detected date.
- Last-updated date.
- Assigned reviewer, where relevant.

Filters should include status, institution, programme, academic year, category and severity where applicable.

A finding row must explain the issue in plain language.

### B. Finding detail

The detail view should show:

1. Finding title and status.
2. Rule identifier and version.
3. Plain-language explanation.
4. Affected record references.
5. Relevant evidence.
6. Source provenance.
7. Detection timestamps.
8. Institution response history.
9. Resolution history.
10. Available next actions for the current user.

The UI must not simply display a red warning without telling the user why it exists.

### C. Enrolment record history

Show:

- Current version.
- Previous versions.
- Changed fields.
- Previous and new values, subject to permissions.
- Change reason.
- Actor.
- Timestamp.
- Related submission.
- Related findings.
- Validation results associated with the change.

### D. Institution response screen

Institution users should be able to:

- Open a finding.
- Read the explanation.
- View the permitted affected-record information.
- Submit a correction or explanation.
- Attach permitted evidence.
- See submission status.
- Track whether the response has been reviewed.
- View the documented resolution when authorized.

### E. Evidence viewer

The evidence viewer should display metadata and access-controlled content.

It must not expose files simply because the user can access the finding's public or general metadata.

## 2.7 Phase 2 API contract

| Method and endpoint | Purpose |
|---|---|
| GET /api/v1/findings | Search findings within the authorized scope. |
| GET /api/v1/findings/{findingId} | Retrieve finding detail. |
| GET /api/v1/enrolments/{recordId}/history | Retrieve permitted record history. |
| POST /api/v1/enrolments/{recordId}/corrections | Submit a correction through the controlled workflow. |
| GET /api/v1/findings/{findingId}/responses | Retrieve permitted response history. |
| POST /api/v1/findings/{findingId}/responses | Submit an institutional explanation or response. |
| POST /api/v1/findings/{findingId}/evidence | Attach permitted supporting evidence. |
| POST /api/v1/findings/{findingId}/transition | Request an allowed finding-state transition. |
| GET /api/v1/enrolments/{recordId}/evidence | Retrieve permitted evidence metadata. |
| GET /api/v1/evidence/{evidenceId} | Retrieve authorized evidence content or a controlled download reference. |
| GET /api/v1/audit-events | Search permitted audit events. |
| GET /api/v1/integrity/conflicts | Retrieve detected conflict candidates within the permitted scope. |
| POST /api/v1/integrity/reconcile | Request an authorized reconciliation operation, if exposed as a separate operation. |

For long-running reconciliation jobs, prefer an asynchronous job resource rather than blocking a request until the entire dataset has been processed.

Every write endpoint must enforce the appropriate state transition and authorization rules.

## 2.8 Phase 2 validation and conflict rules

Add rules such as:

| Rule ID | Purpose |
|---|---|
| DUP-001 | Exact identifier conflict within a batch. |
| DUP-002 | Exact identifier conflict across institution records. |
| DUP-003 | Potential duplicate that requires manual review. |
| DUP-004 | Possible conflict explained by a documented transfer or historical status. |
| HIS-001 | Material record change without a required correction reason. |
| HIS-002 | Record version mismatch during concurrent update. |
| SRC-001 | Source provenance unavailable or incomplete. |
| SRC-002 | Simulated integration result presented for review. |
| WF-001 | Invalid finding-state transition. |
| WF-002 | Required response or resolution rationale missing. |

A rule may be informational, warning-level or review-worthy. It should not be assigned a severity merely because a red colour makes the UI look more dramatic.

## 2.9 Phase 2 acceptance criteria

#### Conflict detection

- Exact duplicate identifiers can be detected across synthetic institutions.
- A legitimate historical transfer is not automatically classified as fraud.
- An unresolved active-record conflict produces an explainable finding.
- A missing identifier does not produce an invented identity match.
- Findings reference the actual rule that generated them.

#### Integrity ledger

- A correction creates a new version.
- Previous values remain available to authorized reviewers.
- Each material change records actor and timestamp.
- Correction reasons are retained where required.
- Concurrent updates cannot silently overwrite newer data.

#### Workflow

- Institution users can submit a response.
- Unauthorized users cannot resolve findings.
- Invalid transitions are rejected by the backend.
- Resolution decisions include the required rationale.
- Revalidation results are connected to the finding's lifecycle.

#### Evidence

- Evidence files are stored privately.
- Unauthorized users cannot retrieve them.
- File metadata and access events are recorded as required.
- Simulated and unavailable sources are clearly identified.

#### Regression

All Phase 1 acceptance tests must still pass.

**Phase 2 deliverable:** A functioning enrolment integrity ledger, discrepancy-resolution workflow and cross-institution conflict engine.

---

# PHASE 3 — AICTE Oversight & Regulatory Case Management

## Objective

Build the regulatory oversight layer that turns validated records and explainable findings into actionable work for authorized AICTE officers.

At the end of Phase 3, an authorized officer should be able to understand the current state of the covered dataset, identify institutions and programmes that require attention, inspect the reasons behind a risk signal, create an audit case, assign responsibility, request clarification, review the response, document a decision and generate appropriately scoped reports.

The system must prioritize human attention without presenting risk scores as proof of misconduct.

Your source document defines this as an explainable risk-and-audit workflow, with explicit factors, documented case handling and human review. *AICTE_APAAR_Student_Data_Platfo…*

## 3.1 Phase 3 scope

Add:

1. National oversight dashboard.
2. Institution dashboard.
3. Programme and academic-year analytics.
4. Consistent KPI definitions.
5. Explainable risk calculations.
6. Risk review queue.
7. Audit case creation.
8. Case assignment and reassignment.
9. Institution clarification requests.
10. Reviewer notes and decisions.
11. Case timeline.
12. Case closure and reopening rules, if policy permits.
13. Report generation.
14. Permission-aware CSV exports.
15. Reporting and aggregation services.
16. Audit and regression tests for all new operations.

## 3.2 Dashboard design

### A. AICTE national overview

This page should answer the questions an authorized regulatory officer needs to answer first.

#### Primary metrics

- Number of covered institutions.
- Number of programmes with usable approval/intake data.
- Total submitted enrolment records in the selected scope.
- Active enrolment count.
- Submission completion rate.
- Percentage of records with complete required fields.
- Percentage of records with valid-format APAAR identifiers.
- Number of unresolved duplicate/conflict findings.
- Number of programmes requiring intake review.
- Number of open institutional correction requests.
- Number of open audit cases.
- Distribution of review priorities.

Every metric must have a defined calculation, source, period and denominator.

For example, a percentage of records with valid-format APAAR IDs must specify whether its denominator includes all submitted records, active records or only records for which an identifier is required.

Do not mix these definitions between pages.

#### Visualizations

Use visualizations only when they improve interpretation.

Useful options include:

- Submission completion by state.
- Record-validation status distribution.
- Intake versus reported enrolment.
- Findings by category.
- Open versus resolved cases over time.
- Risk-priority distribution.
- Submission trends by academic year.

Each visualization must be driven by actual database queries or derived metrics. Provide a table or equivalent accessible representation for users who cannot interpret the chart.

### B. Institution dashboard

Institution users should see their own institution's:

- Submission progress.
- Programme-level intake reconciliation.
- Record-validation summary.
- Open findings.
- Responses awaiting review.
- Resolved findings.
- Recent changes.
- Latest submission receipt.
- API or integration status, where applicable.

An institution should not see another institution's student-level records simply because it appears in a comparison chart.

### C. Programme detail

The programme page should display:

- Institution.
- Programme and qualification level.
- Academic year.
- Approval reference.
- Approved intake and source.
- Applicable category rules.
- Active enrolment count.
- Reported total, where supplied.
- Calculated variance.
- Record-validation summary.
- Related findings.
- Related audit cases.

The page must explain when the figures are incomplete because a reference source is unavailable.

### D. Institution risk profile

Display:

- Current risk-priority band.
- Overall illustrative score, if configured.
- Component-by-component factors.
- Relevant unresolved findings.
- Data-quality trend.
- Duplicate/conflict trend.
- Intake reconciliation.
- Recent material roster changes.
- Open and resolved cases.
- Peer-comparison context, if used.

Peer comparisons must explain how the comparison group was defined. Being different from an average must never automatically be treated as misconduct.

## 3.3 Explainable risk engine

The initial risk engine should use transparent, deterministic rules and documented calculations.

Do not introduce a machine-learning model without sufficient representative labelled data, evaluation methodology and a defensible reason to use it.

#### Suggested illustrative components

The source document proposes the following starting weights:

| Component | Illustrative maximum |
|---|---|
| Capacity discrepancy | 25 |
| Unresolved cross-institution conflict | 25 |
| Identifier/data-quality problems | 15 |
| Unusual roster changes | 15 |
| Unresolved source-reconciliation gap | 10 |
| Repeated unresolved prior findings | 10 |
| **Total** | **100** |

These are prototype defaults, not official AICTE policy.

The implementation must not treat them as fixed regulatory truth.

#### Calculation requirements

Each component must have:

- A documented definition.
- Its own input metrics.
- Its own rule or calculation version.
- A clear contribution to the overall score.
- Tests.
- A plain-language explanation.
- Defined handling of missing information.

The final score must be reproducible from stored inputs and the relevant rule version.

If the calculation changes later, the system should be able to explain which version was used for a historical score.

#### Example

Suppose a synthetic institution has:

- A capacity discrepancy.
- Two unresolved cross-institution conflicts.
- A relatively high missing-identifier rate.

The system can assign a review priority based on the configured weights and actual findings.

It must show which factors contributed to that result.

It must not display a fabricated statement such as "This institution has an 87% probability of fraud" unless a separate, properly validated model supports that exact probabilistic interpretation.

#### Risk bands

Use restrained labels:

- Routine
- Watch
- Review recommended
- Priority review

These labels represent prioritization, not guilt.

A missing external source should not automatically raise suspicion. The source may simply be unavailable for technical or legal reasons.

#### Risk history

Store the risk calculation and its explanation so the application can show:

- When the score was calculated.
- Which rules were used.
- Which findings contributed.
- Which factors changed.
- Whether a correction changed the result.
- Whether the result was superseded by a later calculation.

The score should not silently change without a traceable basis.

## 3.4 Audit case management

### Case creation

An authorized officer should be able to create a case from:

- One or more relevant findings.
- An institution/programme review.
- A configured review recommendation.
- Another authorized, documented trigger.

The case must record why it was created.

### Case fields

The case should contain:

- Case reference.
- Institution.
- Programme and academic year, where applicable.
- Case category.
- Priority.
- Selection rationale.
- Linked findings.
- Assigned reviewer.
- Response deadline, where applicable.
- Current status.
- Created timestamp.
- Closure information.

### Case workflow

A reasonable starting workflow is:

```text
OPEN
  |
  v
ASSIGNED
  |
  v
UNDER_REVIEW
  |
  +----> CLARIFICATION_REQUESTED
  |                |
  |                v
  |        RESPONSE_RECEIVED
  |                |
  |                v
  +----------> UNDER_REVIEW
                   |
          +--------+----------+
          |        |          |
          v        v          v
       RESOLVED  ESCALATED  CLOSED_NO_ACTION
```

The final state names and transitions must be approved for the chosen operating model.

Not every case must follow every state. The backend should define permitted transitions and required information for each transition.

### Assignment

Authorized officers should be able to:

- Assign a case.
- Reassign a case.
- View their assigned cases.
- Filter by priority and status.
- Record relevant review notes.
- Request clarification.
- Review responses.
- Record a decision.

Assignment changes must be audited.

### Clarification requests

A clarification request should specify:

- What needs clarification.
- Which records or findings are involved.
- What information is requested.
- The permitted response method.
- The deadline, if applicable.
- The issuing officer.
- The timestamp.

The request must not unnecessarily expose unrelated student records.

### Case decision

The reviewer must record:

- Decision type.
- Rationale.
- Relevant findings and evidence.
- Reviewer identity.
- Decision timestamp.
- Follow-up action, if applicable.

Do not allow a case to be closed with a required decision rationale missing.

The application supports human regulatory decision-making; it does not independently impose penalties.

## 3.5 Reporting and exports

### Required report types

1. Institution-level enrolment reconciliation.
2. Programme/intake variance.
3. Data-quality summary.
4. Identifier coverage and validation status.
5. Duplicate/conflict findings.
6. Finding-resolution performance.
7. Submission timeliness.
8. Audit case status and outcomes.
9. Historical record changes.
10. State/programme aggregates.
11. Authorized institution-specific reports.

### Report design

Each report must include:

- Report title.
- Generation timestamp.
- Academic year or reporting period.
- Applied filters.
- Scope.
- Metric definitions where necessary.
- Source status.
- Relevant limitations.
- Data classification.

### Export controls

Before generating an export, the backend must check:

- The user's role.
- The user's permitted institutional scope.
- The requested fields.
- The requested filters.
- The report type.
- The data classification.
- Any applicable export restrictions.

An export must not bypass the authorization checks applied to the screen from which it was requested.

Where practical, use asynchronous report jobs for large datasets.

Store the export securely, enforce appropriate expiry and record the relevant audit event.

Do not include unnecessary identifiers or sensitive fields in aggregate reports.

## 3.6 Phase 3 database additions

Add the following modules if not already present:

- audit_cases
- audit_case_findings
- audit_case_events
- audit_case_decisions
- report_jobs
- Any required risk-calculation history table.
- Any required notification tables.
- Additional audit-event classifications for the new operations.

A risk-calculation history table may contain:

- id
- institution_id
- programme_id, when applicable
- academic_year_id
- score
- risk_band
- calculation_version
- input_snapshot
- explanation
- calculated_at

The snapshot should retain enough information to explain the score without indiscriminately duplicating sensitive student data.

The calculation must use a stable, versioned definition.

## 3.7 Phase 3 API contract

| Method and endpoint | Purpose |
|---|---|
| GET /api/v1/dashboard/national | Retrieve national overview metrics for an authorized scope. |
| GET /api/v1/dashboard/institution/{institutionId} | Retrieve institution-specific metrics. |
| GET /api/v1/institutions/{institutionId}/risk-profile | Retrieve risk factors and relevant history. |
| GET /api/v1/risk-queue | Retrieve the authorized review queue. |
| GET /api/v1/risk-calculations/{calculationId} | Retrieve a calculation and its explanation. |
| POST /api/v1/audit-cases | Create a case. |
| GET /api/v1/audit-cases | Search cases within the authorized scope. |
| GET /api/v1/audit-cases/{caseId} | Retrieve case detail. |
| PATCH /api/v1/audit-cases/{caseId}/assignment | Assign or reassign a case. |
| POST /api/v1/audit-cases/{caseId}/events | Record an allowed case workflow event. |
| POST /api/v1/audit-cases/{caseId}/clarification-requests | Request institutional clarification. |
| POST /api/v1/audit-cases/{caseId}/decisions | Record an authorized review decision. |
| GET /api/v1/reports | Retrieve available report definitions and permitted options. |
| POST /api/v1/reports | Create a report job or report request. |
| GET /api/v1/reports/{reportId} | Retrieve report status and metadata. |
| GET /api/v1/reports/{reportId}/download | Download a permitted report through a controlled mechanism. |
| GET /api/v1/notifications | Retrieve notifications for the authenticated user. |

Each endpoint must implement the correct state transitions, permissions and scope restrictions.

## 3.8 Phase 3 frontend additions

The interface should add:

- National overview.
- Institution dashboard.
- Programme detail.
- Institution risk profile.
- Risk queue.
- Audit case list.
- Audit case detail workspace.
- Case assignment controls.
- Clarification-request form.
- Review-decision form.
- Report catalogue.
- Report-generation status.
- Export history where required.

The case workspace should be designed for sustained professional use. The officer should not need to open ten separate pages to understand a case.

A useful detail layout is:

```text
Case reference / Status / Priority

Institution and programme context

Why this case was created
--------------------------------
Triggering findings
Evidence provenance
Risk contributors
Relevant history

Institution response
--------------------------------
Submitted explanation
Supporting evidence
Response timestamp

Review workspace
--------------------------------
Reviewer notes
Decision rationale
Next action

Case timeline
--------------------------------
Assignment
Clarification requests
Responses
Decisions
Status changes
```

This is a structural example, not a requirement to copy a particular visual design. The final layout should preserve readability, context and clear action hierarchy.

## 3.9 Phase 3 acceptance criteria

#### Dashboards

- Metrics are derived from stored data.
- Filters change the relevant figures.
- Definitions and denominators are consistent.
- Missing reference data is shown honestly.
- Institution users cannot access other institutions' student-level data.

#### Risk engine

- Scores are reproducible from stored inputs and versioned rules.
- The UI explains every contributing factor.
- Missing evidence is handled according to the defined rules.
- A correction can change the relevant findings and subsequent calculations.
- Risk does not automatically create a fraud verdict or penalty.

#### Audit cases

- An authorized officer can create a case.
- A case can be assigned and reassigned according to permissions.
- Clarification requests are recorded.
- Institutional responses are linked to the appropriate case.
- Decisions require the necessary rationale.
- Every material case transition is traceable.

#### Reports

- Reports use real database data.
- Filters and scope restrictions are enforced.
- Unauthorized fields cannot be exported.
- Download access is controlled.
- Export operations are auditable.

#### Regression

All Phase 1 and Phase 2 acceptance tests must still pass.

**Phase 3 deliverable:** A complete regulatory oversight workflow that connects data, findings, risk prioritization, case management and reporting.

---

# PHASE 4 — Controlled Verification, Security Hardening & Release Readiness

## Objective

Complete NEEV's remaining end-to-end capabilities and prepare the application for controlled deployment.

Phase 4 is not a cosmetic polishing phase. It completes the limited-purpose verification workflow and validates the reliability, security, performance, recoverability and operational behaviour of the entire system.

The source document explicitly includes synthetic QR/reference verification, limited-purpose output, expiry/revocation and clear source-adapter status, followed by security testing, load testing, accessibility review, backups, monitoring and a controlled pilot. *AICTE_APAAR_Student_Data_Platfo…*

## 4.1 Phase 4 scope

Add or complete:

1. Limited-purpose verification references.
2. QR/reference issuance.
3. Verification request handling.
4. Expiry and revocation.
5. Purpose-specific response policies.
6. Verification access history.
7. Full workflow integration.
8. Security testing.
9. Authorization regression testing.
10. Database and migration validation.
11. Performance and load testing.
12. Accessibility review.
13. Deployment configuration.
14. Monitoring and alerting.
15. Backup and recovery validation.
16. Operational documentation.
17. Release checklist and readiness evidence.

No simulated integration may be presented as a live government integration.

## 4.2 Controlled verification workflow

### A. Reference issuance

An authorized issuer selects a permitted record and initiates a verification reference.

The backend must verify:

- The issuer's identity.
- The issuer's permission to issue references.
- The record's existence.
- The record's permitted verification state.
- The requested purpose.
- The applicable disclosure policy.
- Any relevant expiry or eligibility conditions.

The system then creates a reference with an unpredictable public identifier.

The public reference must not expose:

- The internal enrolment-record ID.
- The student's APAAR ID.
- A predictable sequential identifier.
- Unnecessary personal information.

### B. QR generation

The QR code should contain a URL or reference that resolves to the verification workflow.

It should not embed the full student profile.

The QR itself is not proof of authenticity. The backend must resolve the reference, check its status and apply the appropriate policy.

### C. Verification request

The verifier opens the reference or enters it into the verification page.

The system checks:

1. Whether the reference exists.
2. Whether it has expired.
3. Whether it has been revoked.
4. Whether the requested purpose is permitted.
5. Whether the verifier's access conditions are satisfied.
6. Which fields may be disclosed.
7. Whether the response can be generated from the available evidence.

The application must return a clear result if the reference is invalid, expired, revoked or unavailable.

### D. Limited-purpose result

The result should disclose only the fields required by the approved verification purpose.

A possible response structure may include:

- Verification reference status.
- Issuing institution.
- Permitted programme or qualification context.
- Record status, if authorized and supported.
- Verification timestamp.
- Source limitations.
- Clear indication if an external integration is simulated or unavailable.

The exact fields must be governed by the disclosure policy. The system must not assume that every verifier may see the student's entire record.

### E. Expiry and revocation

Authorized issuers must be able to revoke a reference where permitted.

The backend must reject a revoked or expired reference even if the QR image still exists.

Revocation must take effect at the backend boundary; merely hiding the QR in the UI is insufficient.

### F. Access logging

The system should record:

- Reference ID.
- Request timestamp.
- Request outcome.
- Permitted purpose.
- Disclosure policy version.
- Fields disclosed.
- Relevant requester context, where authorized and necessary.

Do not store full tokens, credentials or excessive personal data in access logs.

## 4.3 Phase 4 database additions

Implement and validate:

- verification_references
- verification_requests
- verification_access_events
- Additional integration metadata where required.
- Operational event types.
- Report expiry or cleanup metadata, where required.

Reference lifecycle rules must be enforced by the backend.

Database transactions should keep reference issuance and its required audit event consistent. If the operation cannot be recorded according to the required audit policy, it should not silently succeed while losing the corresponding event.

## 4.4 Phase 4 API contract

| Method and endpoint | Purpose |
|---|---|
| POST /api/v1/verification-references | Issue a limited-purpose reference. |
| GET /api/v1/verification-references/{referenceId} | Retrieve permitted reference metadata for an authorized issuer. |
| POST /api/v1/verification-references/{referenceId}/revoke | Revoke an active reference where permitted. |
| POST /api/v1/verification/resolve | Resolve a public reference and return an appropriate limited result. |
| GET /api/v1/verification-requests | Retrieve permitted verification-request history. |
| GET /api/v1/verification-requests/{requestId} | Retrieve authorized request detail. |
| GET /api/v1/verification-references/{referenceId}/access-history | Retrieve access history for an authorized issuer. |
| GET /api/v1/integrations/status | Retrieve permitted integration status information. |
| GET /api/v1/health/live | Verify that the service process is alive. |
| GET /api/v1/health/ready | Verify readiness of required dependencies. |

The public resolution endpoint needs careful abuse controls. Its output must be limited even when the caller is not an authenticated institutional user.

Apply rate limiting and monitoring. Avoid unrestricted reference enumeration.

## 4.5 Phase 4 frontend additions

### A. Reference issuance page

Authorized users should be able to:

- Select an eligible record.
- Choose an allowed verification purpose.
- Review the proposed disclosure.
- Set an allowed expiry.
- Issue the reference.
- View the generated QR.
- Copy the reference.
- Revoke it when permitted.
- Inspect its current status.

### B. Verification result page

The page should clearly distinguish:

- Valid reference.
- Expired reference.
- Revoked reference.
- Invalid reference.
- Verification pending.
- Source unavailable.
- Simulated verification.
- Successful limited-purpose result.

Do not show a green "Verified" badge when the result only means that a reference exists.

The interface should explain what was verified and what was not.

### C. Verification history

Authorized issuers should be able to see:

- Reference creation.
- Purpose.
- Expiry.
- Revocation.
- Verification attempts.
- Outcomes.
- Disclosed fields.
- Relevant timestamps.

### D. Integration status

Provide an integration-status view showing:

- Source name.
- Live, simulated or unavailable mode.
- Connection status.
- Last successful synchronization, where applicable.
- Error status.
- Supported claims.
- Known limitations.

A simulated integration must remain visibly simulated throughout the application, including in exports and reports where relevant.

## 4.6 Complete end-to-end product validation

Before the final release candidate, execute the entire core workflow from beginning to end.

### Workflow A — Institutional onboarding

1. An authorized administrator creates or loads a synthetic institution.
2. An institution administrator receives the appropriate access.
3. The user logs in.
4. The application displays the correct institution scope.
5. Programmes and intake data are available.
6. The user sees the relevant submission requirements.

### Workflow B — Submission and validation

1. The institution selects an academic year and programme.
2. The institution uploads a synthetic roster.
3. The system parses the file.
4. Invalid rows receive specific explanations.
5. Valid rows are staged and validated.
6. Intake reconciliation runs against the applicable configured rules.
7. The institution finalizes the batch.
8. The system issues a receipt.
9. The overview reflects the updated stored data.

### Workflow C — Duplicate/conflict resolution

1. A conflict is detected across synthetic institutions.
2. A finding is created with the applicable rule and explanation.
3. An authorized user opens the finding.
4. The institution submits a correction or explanation.
5. The correction creates a new record version where applicable.
6. Validation runs again.
7. An authorized reviewer records the resolution.
8. The audit timeline reflects the complete sequence.

### Workflow D — AICTE review

1. An authorized officer opens the review queue.
2. The officer inspects a risk explanation.
3. The officer creates a case.
4. The officer assigns the case.
5. A clarification request is recorded.
6. An institutional response is received.
7. The reviewer records a decision.
8. The case status and dashboard update.
9. An authorized report can be generated.

### Workflow E — Controlled verification

1. An authorized issuer selects a permitted record.
2. A verification reference is issued.
3. The QR/reference resolves correctly.
4. The response contains only the permitted fields.
5. The request is recorded.
6. The reference expires or is revoked.
7. Subsequent requests correctly report that status.
8. Unauthorized users cannot retrieve the full record.

All five workflows must be repeatable using synthetic data.

## 9. Phase 4 Security Verification Plan

Security work must produce evidence, not just a list of installed libraries.

### 9.1 Authentication tests

Test:

- Invalid credentials.
- Expired access tokens.
- Expired refresh sessions.
- Refresh-token rotation.
- Refresh-token reuse.
- Logout and revocation.
- Disabled accounts.
- Password-reset token expiry and reuse, if implemented.
- Rate limiting.
- Concurrent refresh attempts.
- Session invalidation after relevant security changes.

### 9.2 Authorization tests

For every sensitive resource, test:

- Unauthenticated access.
- Authenticated but unauthorized access.
- Wrong institutional scope.
- Wrong role.
- Direct object-ID substitution.
- Access to another institution's batch.
- Access to another institution's findings.
- Access to restricted evidence.
- Unauthorized case resolution.
- Unauthorized rule configuration.
- Unauthorized report export.
- Unauthorized verification-reference issuance or revocation.

These tests should be automated where possible.

### 9.3 Input and application-security tests

Test:

- Malformed request bodies.
- Oversized requests.
- Invalid file uploads.
- Unexpected file types.
- Malicious filenames.
- CSV formula injection in exported files.
- Invalid pagination values.
- Invalid enum values.
- SQL injection attempts.
- Cross-site scripting through user-controlled text.
- CSRF where cookie-based authentication is used.
- Excessive request rates.
- Sensitive information in error responses.
- Accidental exposure of environment variables.
- Unauthorized file-download attempts.

Security tests must be performed in an authorized test environment with synthetic data.

### 9.4 Database and audit tests

Test:

- Foreign-key integrity.
- Constraint enforcement.
- Transaction rollback.
- Concurrent updates.
- Duplicate submission handling.
- Audit-event creation.
- Unauthorized audit-event modification.
- Migration from a clean database.
- Migration from the previous supported schema version.
- Backup restoration.
- Retention and deletion behaviour according to the implemented policy.

### 9.5 Dependency and configuration checks

Before a release candidate:

- Review dependency vulnerabilities.
- Pin and audit dependencies.
- Verify secret management.
- Review CORS configuration.
- Review TLS and cookie settings.
- Check production debug settings.
- Review access to database and object storage.
- Check logging configuration.
- Review container and deployment permissions.
- Ensure test credentials are not deployed as production credentials.

A successful test suite does not prove that the application is invulnerable. Findings must be triaged, fixed and retested.

## 10. Performance and Reliability Verification

NEEV must be tested with realistic synthetic data volumes rather than only a handful of seed records.

### 10.1 Performance test scenarios

Measure:

- Login and session handling.
- Dashboard queries.
- Institution and programme search.
- Paginated enrolment queries.
- Batch upload.
- CSV parsing.
- Validation execution.
- Duplicate/conflict detection.
- Intake reconciliation.
- Case-list queries.
- Report generation.
- Verification-reference resolution.

Test both normal operation and expected peak workload.

### 10.2 Batch processing

For large uploads, avoid keeping an HTTP request open for the entire processing operation.

A suitable workflow is:

```text
Upload received
      |
      v
Batch stored with processing state
      |
      v
Background worker claims job
      |
      v
Rows parsed and validated
      |
      v
Results stored
      |
      v
Batch status updated
      |
      v
Frontend polls or receives status updates
```

The job system must support:

- Safe retries.
- Idempotent processing.
- Explicit failure states.
- Bounded concurrency.
- Timeouts.
- Appropriate backoff.
- Error reporting.
- Recovery after worker interruption.

A failed job must not leave the batch marked as successfully completed.

### 10.3 Query performance

Use:

- Server-side pagination.
- Appropriate indexes.
- Query-plan inspection.
- Aggregation queries designed for the relevant access patterns.
- Bounded filters.
- Efficient joins.
- Avoidance of N+1 queries.
- Caching only where consistency and authorization implications are understood.

Do not introduce a cache that can leak one institution's data into another institution's response.

### 10.4 Reliability targets

Actual targets must be chosen after understanding the expected deployment environment.

Define and test:

- Expected concurrent users.
- Expected institutions.
- Expected records per institution.
- Expected submission size.
- Expected submission frequency.
- Target response times.
- Availability expectations.
- Recovery time objective.
- Recovery point objective.
- Backup frequency.
- Maximum acceptable data loss under the approved recovery plan.

Do not claim a service-level agreement that has not been measured and operationally supported.

## 11. Deployment and Operational Readiness

### 11.1 Environment separation

Maintain distinct environments for:

- Local development.
- Automated testing.
- Staging or pre-release validation.
- Production, when authorized.

Use separate credentials, databases, storage and configuration for each environment.

Never use production student data as a shortcut for development.

### 11.2 Configuration and secrets

Required practices:

- Environment-based configuration.
- Secret manager or equivalent protected deployment secrets.
- No secrets committed to Git.
- No secrets in screenshots or documentation.
- No production credentials in `.env.example`.
- No sensitive data in frontend build variables.
- Rotation procedure for compromised secrets.

### 11.3 Database migrations

Release procedures must support:

1. A backup or other approved recovery checkpoint.
2. Migration validation.
3. Application/database compatibility checks.
4. Migration execution.
5. Post-migration health checks.
6. Rollback or forward-recovery procedure.
7. Documented handling of partially completed deployments.

Do not assume every database migration can be safely reversed. Some changes require a forward-fix or a carefully planned compatibility window.

### 11.4 Backups and disaster recovery

The system must have a documented strategy for:

- Database backups.
- Private evidence storage backups.
- Retention.
- Backup encryption.
- Restricted backup access.
- Restore testing.
- Recovery after corruption or accidental deletion.
- Recovery after a compromised credential.
- Verification that restored records retain the required integrity history.

A backup is not useful merely because the backup job says "success." At least one recovery procedure must be tested.

### 11.5 Monitoring and incident response

Provide:

- Application health monitoring.
- Database connectivity monitoring.
- Worker health monitoring.
- Background-job failure alerts.
- Authentication-failure monitoring.
- Suspicious access monitoring.
- Bulk-export monitoring.
- Error-rate monitoring.
- Storage and resource monitoring.
- Incident response documentation.

Monitoring systems must not become another place where student information is accidentally exposed.

### 11.6 Deployment documentation

The release documentation should include:

- Architecture overview.
- Environment setup.
- Required environment variables.
- Database initialization.
- Migration instructions.
- Seed-data instructions for development only.
- Build and test commands.
- Deployment steps.
- Health-check procedures.
- Backup and restore procedures.
- Security configuration.
- Troubleshooting guidance.
- Known limitations.
- Incident response contacts and responsibilities, when established.

The exact deployment platform should be selected according to the authorized hosting requirements. We should not assume that a convenient public hosting service automatically meets the requirements for sensitive government data.

### 11.7 Phase 4 acceptance criteria

#### Verification

- Authorized issuers can create permitted references.
- References are unpredictable.
- QR codes do not contain unrestricted student profiles.
- Expired and revoked references are rejected.
- Verification output follows the configured disclosure policy.
- Verification attempts are recorded.
- Simulated integrations are explicitly identified.
- Unauthorized users cannot enumerate references or access full records.

#### Security

- Authentication regression tests pass.
- Authorization and institutional-isolation tests pass.
- No unresolved critical or high-severity security finding remains without an explicitly approved mitigation or exception.
- Secrets are not exposed.
- Sensitive data is not unnecessarily logged.
- File handling follows the implemented security controls.
- Security configuration is documented and verified.

#### Reliability

- Database migrations are reproducible.
- Backup restoration has been tested.
- Batch jobs recover appropriately from failure.
- Retry operations do not duplicate records.
- Performance has been measured against the agreed test workload.
- Health checks reflect actual service readiness.
- Monitoring and alerting have been exercised.

#### Product completeness

- All core end-to-end workflows work.
- Dashboard figures reflect the underlying data.
- All major screens have appropriate loading, empty, error and success states.
- Keyboard accessibility and responsive behaviour have been reviewed.
- Reports and exports respect authorization.
- The application can be deployed from documented instructions in a clean environment.

**Phase 4 deliverable:** A complete, security-tested, deployment-capable release candidate with verification functionality and documented operational readiness.

---

## 12. Complete Feature-to-Phase Mapping

This is the master checklist that prevents features from being forgotten or implemented inconsistently.

| Feature | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---|---|---|---|---|
| Application foundation | Build | Extend | Extend | Harden |
| Authentication | Implement | Maintain | Maintain | Security-validate |
| JWT/session lifecycle | Implement | Test regressions | Test regressions | Full security validation |
| Roles and permissions | Core implementation | Extend for findings | Extend for cases/reports | Full authorization audit |
| Institution management | Build | Use in conflict workflows | Use in dashboards/cases | Validate operational controls |
| Programme management | Build | Use in conflict detection | Use in analytics | Validate end-to-end |
| Academic years | Build | Use in historical checks | Use in reporting | Validate |
| Approved intake | Build | Use in discrepancy rules | Use in risk/reporting | Validate rule correctness |
| Student identities | Build | Extend matching and provenance | Use within authorized reporting | Security validation |
| Enrolment records | Build | Version and reconcile | Use in cases and reports | Full workflow validation |
| CSV submission | Build | Revalidation/correction support | Operational monitoring | Load and reliability tests |
| Batch processing | Build | Extend processing where needed | Operational reporting | Performance and recovery tests |
| Deterministic validation | Build | Extend conflict and history rules | Use in risk calculations | Full regression |
| Intake reconciliation | Build | Recalculate after corrections | Dashboard and reporting | Full regression |
| Duplicate/conflict detection | Basic intra-batch detection | Cross-institution detection | Risk and case integration | Load and false-positive review |
| Record version history | Establish initial model | Complete integrity ledger | Use in review history | Validate persistence/recovery |
| Audit events | Core events | Material corrections and resolutions | Cases, assignments and decisions | Integrity and security validation |
| Evidence provenance | Initial source metadata | Full evidence relationships | Case review | Disclosure and access testing |
| Institutional correction workflow | Basic data correction | Complete finding responses | Clarification requests and case integration | End-to-end validation |
| Findings lifecycle | Initial validation findings | Full resolution lifecycle | Risk/case integration | Regression |
| National dashboard | Basic operational summary | Findings and conflict counts | Full regulatory dashboard | Performance and access review |
| Institution dashboard | Basic submission metrics | Correction and finding metrics | Full institution workspace | Regression |
| Risk scoring | Not required beyond basic validation | Provide conflict inputs | Implement explainable scoring | Validate calculations and limitations |
| Risk queue | Not required | Supply relevant findings | Implement | Regression |
| Audit case management | Not required | Findings can be linked where needed | Full implementation | End-to-end validation |
| Reporting | Basic submission receipt | History/finding reports as needed | Full regulatory reports | Export security validation |
| Controlled verification | Not required | Establish provenance and record-history foundations | Prepare required data model | Implement and validate |
| QR/reference issuance | Not required | Not required | Not required | Implement |
| Reference expiry/revocation | Not required | Not required | Not required | Implement |
| External integration adapters | Define interface and source labels | Use source provenance | Show operational status | Validate adapter and fallback behaviour |
| Simulated government responses | Clearly label test data | Preserve source labels | Show limitations in cases/reports | Verify no false live claims |
| File storage | Submission handling | Private evidence storage | Case evidence access | Storage security and recovery |
| Notifications | Minimal workflow feedback | Finding-related notifications | Case and response notifications | Delivery and privacy validation |
| Automated tests | Foundation | Expand | Expand | Full release suite |
| Performance testing | Basic measurements | Conflict-processing measurements | Dashboard/report measurements | Formal workload tests |
| Accessibility | Build into components | Extend | Extend | Full review |
| Deployment configuration | Local reproducible setup | Maintain | Maintain | Release configuration and runbooks |
| Backup and recovery | Design considerations | Protect historical data | Protect reporting and case data | Test recovery |
| Monitoring | Basic logs and health checks | Add workflow visibility | Add queue/report visibility | Operational monitoring and alerts |
| Production readiness | Establish good engineering foundations | Preserve integrity | Complete operational workflows | Validate and document readiness |

This mapping is deliberate. For example, JWT authentication is not something we will build again in Phase 4. We establish it in Phase 1, extend it as new permissions appear, and subject it to a more comprehensive security review in Phase 4.

Likewise, the database is not redesigned independently in each phase. We establish its foundational relationships in Phase 1 and evolve it through controlled migrations.

---

## 13. Cross-Phase Database and API Change Rules

Because we are developing NEEV incrementally, we need strict control over how the system evolves.

### 13.1 Database migrations

Every schema change must be represented by a migration.

For example:

- Phase 1 introduces the core institutional and enrolment model.
- Phase 2 adds record-version, provenance and correction-workflow capabilities.
- Phase 3 adds case-management and reporting structures.
- Phase 4 completes verification and operational requirements.

Each migration must be tested against the supported previous schema version.

The implementation must not simply drop the existing database and recreate it whenever a schema change is inconvenient.

Development seed data may be recreated intentionally, but that must be a deliberate, documented development operation—not the normal migration process.

### 13.2 API compatibility

New endpoints should be added without unexpectedly breaking earlier workflows.

When an API contract must change:

1. Identify affected consumers.
2. Document the change.
3. Update backend schemas.
4. Update the generated or maintained API client.
5. Update frontend usage.
6. Update tests.
7. Check the other previously completed workflows.

Avoid creating duplicate endpoints that do the same thing under slightly different names.

### 13.3 Rule versioning

The system must preserve the rule version used for a validation or risk calculation.

If an approved rule changes, historical results should remain explainable.

A later revalidation may produce a different result, but the system must distinguish:

- The original result.
- The rule version that produced it.
- The new result.
- The reason for the change.

### 13.4 Seed data and production data

Synthetic development data must be isolated from real operational data.

The application must not automatically seed demo users, demo institutions or synthetic enrolments into a production environment.

Production initialization should require an explicit, controlled procedure.

---

## 14. Master Definition of Done for NEEV

NEEV should not be considered complete simply because all four phases have been coded.

The release candidate must satisfy the following conditions.

### A. Product functionality

- [ ] Institutional users can submit student-level records.
- [ ] Data validation is functional.
- [ ] Approved-intake reconciliation is functional.
- [ ] Cross-institution conflict detection is functional.
- [ ] Findings have explanations and rule references.
- [ ] Material corrections preserve history.
- [ ] Institutions can respond to findings.
- [ ] Authorized reviewers can resolve findings.
- [ ] AICTE users can inspect dashboards and review queues.
- [ ] Risk calculations are explainable and reproducible.
- [ ] Audit cases have a functioning lifecycle.
- [ ] Reports and exports work.
- [ ] Controlled verification references can be issued and resolved.
- [ ] Expiry and revocation work.
- [ ] Simulated integrations are clearly labelled.

### B. Data integrity

- [ ] Database relationships are enforced.
- [ ] Migrations are repeatable.
- [ ] Referential integrity is tested.
- [ ] Historical record versions are preserved.
- [ ] Material actions have appropriate audit events.
- [ ] Batch retries do not duplicate records.
- [ ] Concurrent corrections are handled safely.
- [ ] Dashboard figures reconcile with their underlying data.

### C. Security and privacy

- [ ] Authentication and session lifecycle are tested.
- [ ] Role and scope restrictions are enforced by the backend.
- [ ] Cross-institution isolation tests pass.
- [ ] Sensitive identifiers are masked by default.
- [ ] Unnecessary personal data is not collected.
- [ ] Evidence files are access-controlled.
- [ ] Export permissions are enforced.
- [ ] Sensitive data is not unnecessarily logged.
- [ ] Secrets are managed securely.
- [ ] The threat model and security decisions are documented.
- [ ] Security findings are triaged, resolved or explicitly managed before release.

### D. User experience

- [ ] The interface follows the design system.
- [ ] Tables and forms are usable for real administrative tasks.
- [ ] Loading, empty, error and success states are implemented.
- [ ] Navigation respects the user's permissions.
- [ ] Forms provide useful validation feedback.
- [ ] Accessibility has been reviewed.
- [ ] Responsive layouts have been tested.
- [ ] The interface does not rely on decorative fake metrics or nonfunctional buttons.

### E. Engineering and operations

- [ ] Backend tests pass.
- [ ] Frontend tests pass.
- [ ] API integration tests pass.
- [ ] Authorization regression tests pass.
- [ ] End-to-end tests pass.
- [ ] A clean frontend build succeeds.
- [ ] Database migrations work from a clean environment.
- [ ] Backup restoration has been tested.
- [ ] Performance has been measured against defined workloads.
- [ ] Monitoring and health checks work.
- [ ] Deployment instructions have been tested.
- [ ] No real student data or secrets are included in the development seed files.
- [ ] Known limitations and unconfirmed integrations are documented.

### F. Official-use readiness

- [ ] Required government or institutional integrations have been authorized before being activated.
- [ ] The authoritative intake source has been confirmed.
- [ ] Applicable category rules have been verified.
- [ ] Applicable privacy, retention and disclosure requirements have been reviewed.
- [ ] The intended hosting environment meets the approved requirements.
- [ ] Security and operational assessments required for the deployment have been completed.
- [ ] Pilot and rollout responsibilities have been established.

The last group cannot be completed through coding alone. It requires the appropriate institutional decisions, authorizations and verification.

---

## 15. The Working Method We Will Follow

The four phases are the complete product roadmap. We will then implement them one phase at a time.

Your role is to run the application, inspect the actual output, test the user journeys and report what happens. My role is to help define the implementation requirements, review the coding agent's output, identify gaps, design tests, interpret failures and determine whether the phase has actually met its acceptance criteria.

The coding agent is the implementation mechanism—not the source of product truth.

### Step 1 — Establish the baseline

Before the first implementation begins, the repository must be inspected.

We need to know:

- What files already exist.
- Which stack is actually present.
- Whether the application already has authentication.
- Whether a database exists.
- Whether migrations exist.
- Whether the frontend and backend are already connected.
- Which components can be reused.
- Which existing code conflicts with this plan.
- Which environment and setup instructions already work.

No destructive rewrite should happen before this inspection.

### Step 2 — Complete Phase 1

Phase 1 will be implemented according to its full specification.

When the implementation is returned, we will review the actual files and test evidence—not just a statement that the coding agent has finished.

We will check the authentication flow, database relationships, endpoints, upload process, validation results, intake reconciliation, frontend states and automated tests.

### Step 3 — Fix Phase 1 issues before progressing

If testing reveals an issue, we will identify the underlying cause and define a coordinated fix.

A proper fix may involve multiple files or layers. For example, a broken dashboard count may originate in a database query, an incorrect backend aggregation, a mismatched response schema or a frontend assumption.

We should fix the actual cause rather than applying a superficial UI workaround.

After the fix, the relevant tests must be rerun, along with regression tests for previously working functionality.

### Step 4 — Freeze the accepted Phase 1 baseline

Once Phase 1 passes its acceptance criteria, its existing behaviour becomes the baseline for Phase 2.

This does not mean the code can never change. It means future changes must preserve the agreed behaviour unless a deliberate, justified change is approved.

### Step 5 — Repeat for Phases 2, 3 and 4

Each phase follows the same sequence:

1. Review its requirements.
2. Implement the frontend and backend together.
3. Run migrations and tests.
4. Inspect the actual application.
5. Test successful and unsuccessful workflows.
6. Identify defects.
7. Fix the underlying causes.
8. Rerun relevant tests.
9. Confirm regression safety.
10. Accept the phase before moving forward.

This keeps the project manageable and gives you a stable, testable application after every phase.

---

## 16. Final Product Direction

NEEV must be built around five principles:

1. **Evidence before confidence:** A submitted record, a valid identifier and independently corroborated enrolment are different things.
2. **Traceability before convenience:** Important changes, findings and decisions must retain their history.
3. **Explainability before artificial intelligence:** Start with transparent rules and introduce more advanced models only when their value can be established.
4. **Security before exposure:** Access to records, evidence and reports must be limited to authorized purposes.
5. **Operational substance before presentation:** The interface must be excellent, but every important screen must represent real functionality backed by the system.

The main architectural challenge is not building four separate products. It is building one coherent system in four controlled increments, with consistent database relationships, API contracts, permissions, design standards and testing discipline.

The result we are aiming for is a complete NEEV application in which an institution can submit and correct records, the platform can detect and explain discrepancies, authorized officers can review cases, and limited-purpose verification can be performed without exposing the underlying student database.

That is the standard against which every phase should be evaluated.