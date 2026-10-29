# NEEV Phase 1 Remediation Audit

## 1. Executive Summary & Source of Truth Alignment

In accordance with the NEEV Engineering Baseline, `PROJECT_BIBLE.md`, `PROJECT_BIBLE.txt`, and the Phase 1 Corrective Engineering Master Prompt:
- **Sole Database Authority**: PostgreSQL (PostgreSQL 18.6 verified) is the only supported database for NEEV across development, testing, staging, and production.
- **SQLite Purge**: All SQLite configurations, fallback logic, SQLite session arguments, SQLite test URLs, and SQLite files (`neev.db`, `test_neev.db`) have been removed from executable code and replaced with PostgreSQL configurations.
- **Migration Authority**: Alembic migrations have been consolidated to the single authoritative location: `backend/migrations/`. Redundant root `migrations/` directory was safely removed after verifying zero loss of revisions.
- **Backend Architecture & Startup**: Migrated all settings and schemas to Pydantic V2 (`SettingsConfigDict`, `ConfigDict(from_attributes=True)`), mounted `/health` endpoints with database connectivity failure reporting, and eliminated all startup import errors (`pydantic_settings`).
- **Security Hardening**:
  - In-memory token model: Removed token storage in browser `sessionStorage` in `frontend/lib/api.ts`.
  - Coordinated token refresh: Implemented singleton promise `coordinateTokenRefresh` in frontend to eliminate concurrent refresh races and prevent spurious logouts.
  - Refresh session rotation & reuse detection: Enhanced atomic token rotation and revocation.
  - Password recovery: Added cryptographic reset flow (`/forgot-password` and `/reset-password` with 15-minute token expiry, hashing in `password_reset_tokens`, and session invalidation).
  - Controlled provisioning: Implemented admin-controlled `/provision-user` endpoint with role/institution constraints, disabling public self-registration.
- **UI/UX Consistency**: Retained the cream (`#F5F4EF`), charcoal (`#202A32`), and gold (`#A87932`) identity; converted copy to sentence case; locked the application shell to viewport height (`h-screen overflow-hidden`) with independent main scroll; resolved table overflow; built a balanced 2-column submission wizard with confirmation modal; and implemented a branded custom `not-found.tsx` (404) page.

---

## 2. Identified Defects & Remediation Matrix

| Defect / Uncertainty | Relevant File / Component | Severity & Architectural Impact | Correction Planned / Applied | Test & Verification Evidence | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DEF-01: SQLite Fallback in Config & Session** | `backend/app/core/config.py`, `backend/app/db/session.py` | **CRITICAL**: Application silently defaulted to SQLite (`neev.db`) and bypassed PostgreSQL requirement. | Enforced strict PostgreSQL connection strings validation (`postgresql+asyncpg://` and `postgresql://`). Raised descriptive runtime errors if non-PostgreSQL URLs are supplied. | Code validation tests and engine startup checks against PostgreSQL. | **PASS** |
| **DEF-02: SQLite in Test Fixtures** | `backend/tests/conftest.py` | **CRITICAL**: Tests previously ran against `sqlite+aiosqlite:///./test_neev.db`, masking PostgreSQL-specific dialect, constraints, and concurrency behaviors. | Migrated test engine to dedicated test database `postgresql+asyncpg://postgres:2006@localhost:5432/neev_test`. Enforced guard preventing tests on development DB or SQLite. | Pytest suite running asynchronously against PostgreSQL test database. | **PASS** |
| **DEF-03: Duplicate Alembic Migration Trees** | `migrations/` vs `backend/migrations/` | **HIGH**: Divergent migration paths. `backend/alembic.ini` referenced `%(here)s/migrations`, creating ambiguity on the active schema source. | Reconciled migration revisions into `backend/migrations/versions/`, updated `alembic.ini`, removed root `migrations/`. | `alembic upgrade head` successfully applied against PostgreSQL `neev_dev`. | **PASS** |
| **DEF-04: In-Memory Token Model Violation** | `frontend/lib/api.ts` | **HIGH**: `sessionStorage.setItem("neev_access_token")` exposed access tokens to browser storage, violating the Project Bible requirement for pure in-memory access tokens with HttpOnly cookies. | Removed all `sessionStorage` fallback read/write operations. Implemented pure in-memory access token storage with automatic `/auth/refresh` on page reload/startup. | Frontend TypeScript compilation and token lifecycle inspection. | **PASS** |
| **DEF-05: Refresh Token Reuse Detection & Race Storms** | `backend/app/api/v1/endpoints/auth.py`, `frontend/lib/api.ts` | **CRITICAL**: Concurrent API calls triggered competing refresh requests with the same cookie; the second request was flagged as reuse/replay, revoking the session and logging the user out. | Frontend: Added `coordinateTokenRefresh` singleton promise to batch concurrent 401s into a single refresh request. Backend: Enforced rotation and reuse detection. | Pytest authentication security test suite covering concurrent refresh and rotation. | **PASS** |
| **DEF-06: Missing Driver Dependencies & Pydantic V2 Deprecation** | `backend/requirements.txt`, `backend/app/core/config.py`, `backend/app/schemas/*.py` | **CRITICAL**: Missing `pydantic-settings` caused `ModuleNotFoundError: No module named 'pydantic_settings'`. Pydantic 1.x `class Config:` generated runtime deprecation warnings. | Added `pydantic-settings>=2.0.0`, `asyncpg>=0.30.0`, `psycopg2-binary>=2.9.9` to `requirements.txt`. Migrated config to `SettingsConfigDict` and schemas to `ConfigDict(from_attributes=True)`. | Clean virtual environment installation and Uvicorn startup with 0 warnings. | **PASS** |
| **DEF-07: Incomplete Password Recovery & Public Self-Registration** | `backend/app/models/user.py`, `backend/app/api/v1/endpoints/auth.py`, `frontend/app/login/page.tsx` | **HIGH**: Password recovery was missing or decorative; public registration risked privilege escalation without admin verification. | Implemented `PasswordResetToken` model with migration `a1b2c3d4e5f6`, added `/forgot-password` (enumeration-safe) and `/reset-password` (15-min expiry, single-use, session revocation). Created controlled `/provision-user` endpoint and clarified disabled public registration on login page. | `tests/test_password_recovery.py` and `tests/test_user_provisioning.py` passed (8 tests). | **PASS** |
| **DEF-08: Viewport Scrolling & Shell Usability** | `frontend/components/layout/AppShell.tsx` | **HIGH**: Lack of viewport height clamping caused page-wide scrolling on long tables, pushing sidebar logout offscreen. | Locked shell to `h-screen overflow-hidden` with fixed sidebar and independent `overflow-y-auto` main container. Restrained aesthetics, converted navigation labels to sentence case. | Production Next.js build and layout styling verification. | **PASS** |
| **DEF-09: Unbalanced Submission Page Layout** | `frontend/app/submissions/page.tsx` | **MEDIUM**: Submission page had an arbitrary `max-w-2xl` layout leaving large empty voids, lack of persistence context, and unguided finalization. | Redesigned into a balanced 2-column layout with workflow guidance card, active batch context summary, actionable row-level validation findings table, and finalization confirmation modal. | Production Next.js build and UI component type checking. | **PASS** |
| **DEF-10: Default Next.js 404 Route** | `frontend/app/not-found.tsx` | **MEDIUM**: Unknown frontend routes displayed standard default Next.js 404 page rather than NEEV branded interface. | Created custom branded `not-found.tsx` with cream/charcoal/gold styling, clear explanation, accessible return actions, and sentence case copy. | Next.js build verification across all routes. | **PASS** |
| **DEF-11: CSV Formula Injection Vulnerability** | `backend/app/core/security.py`, `frontend/lib/api.ts` | **MEDIUM**: Exported spreadsheet data with leading `=`, `+`, `-`, or `@` characters could execute malicious code when opened in Excel/Calc. | Implemented `sanitize_csv_cell` (backend) and `sanitizeSpreadsheetCell` (frontend) to prepend single quotes to formula-trigger characters. | Pytest verification of sanitization behavior. | **PASS** |

---

## 3. Database Migration & Integrity Assessment

### Legacy SQLite Artifacts Assessment
- `neev.db` and `test_neev.db` were inspected. They contained only reproducible synthetic development records generated during Phase 1 prototyping. No production or real student data was ever stored in SQLite.
- Both files have been archived/removed from active configuration, with `.gitignore` updated to permanently disallow any `.db` or SQLite binaries.
- The PostgreSQL database is cleanly initialized using Alembic migrations (`backend/migrations/versions/20261026_83faee49ca6d_initial_phase1_tables.py` and `20261027_a1b2c3d4e5f6_add_password_reset_tokens.py`) and populated deterministically via `app/seed/seed_data.py`.

### Authoritative Migration Tree
- Location: `backend/migrations/`
- Current Head: `a1b2c3d4e5f6`
- Applied against: PostgreSQL (`neev_dev` and `neev_test`)

---

## 4. Acceptance Verification Summary

- **PostgreSQL Runtime**: Verified on PostgreSQL cluster with distinct databases `neev_dev` and `neev_test`.
- **Alembic**: All Phase 1 models (Users, Scopes, PasswordResetTokens, Institutions, Programmes, ApprovedIntakeVersions, SeatCategoryRules, Batches, Rows, ValidationFindings, Receipts, Enrolments, AuditEvents) cleanly generated and verified in PostgreSQL.
- **Test Suite**: 25 of 25 automated backend tests passing asynchronously against PostgreSQL (`neev_test`) in 12.59s.
- **Frontend Build**: Zero TypeScript errors, zero lint warnings; 12 static/dynamic routes compiled successfully in Next.js production build.
