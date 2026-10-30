# NEEV — Known Issues, Technical Limitations & Operational Register

> **Document Version**: 1.0.0-PROD-AUDIT  
> **Classification**: Platform Quality & Technical Transparency Register  
> **Evaluation Date**: 2026-10-30  
> **Scope**: Verified Local Architecture & Deployed Cloud Architecture

---

## 1. Executive Summary

This register provides an unvarnished, technically rigorous record of all known platform limitations, environmental boundaries, non-critical deprecation notices, and architectural constraints across the NEEV platform.

---

## 2. Technical Limitations & Operational Realities

### LIM-001: Free Cloud Hosting Cold-Start Delays on Render
* **Symptom**: Outbound requests to `https://neev-api-eqq1.onrender.com` may take between 30 and 50 seconds to return an initial response if the service has been inactive for more than 15 minutes.
* **Root Cause**: The backend API is hosted on Render’s free tier, which scales compute instances down to zero during idle periods.
* **Impact on Production**: First-time page visits may observe loading spinners or temporary delay. Once warmed up, response times stabilize under 80 milliseconds.
* **Local Development Behavior**: Local execution (`http://127.0.0.1:8000`) has zero cold-start delay (responses resolve in 2 to 6 ms).
* **Recommended Production Remediation**: Upgrade to Render Starter / Standard tier or migrate container workload to Amazon ECS / Google Cloud Run with minimum instance count set to $\ge 1$.

### LIM-002: External Government Adapters are Contract-Simulated
* **Symptom**: On `/integrations`, the DigiLocker/APAAR, AISHE, and NAD adapters report contract test status `PASSED` but indicate `is_simulated = true`.
* **Root Cause**: Live production REST APIs for national identity verification (DigiLocker / UIDAI) require statutory bilateral MOUs, dedicated government VPN tunnels, and enterprise IP whitelisting.
* **Verification Status**: All integration adapters are fully implemented with real HTTP client interfaces, schema payload validation, and deterministic mock responses conforming to ministry specifications.
* **Impact**: Zero impact on core system integrity, duplicate detection, or intake reconciliation.

### LIM-003: CSV Ingestion Format Constraints
* **Symptom**: Institutional student roster upload accepts strictly `.csv` files. Binary Excel workbooks (`.xls`, `.xlsx`) are rejected by the dropzone validator.
* **Root Cause**: Ingestion engine uses a high-performance streaming CSV parser designed to minimize memory footprint and eliminate malicious macro execution vulnerabilities.
* **Remediation for Users**: Institutional operators must export spreadsheets to standard UTF-8 Comma Separated Values (`.csv`) before uploading.

### LIM-004: Pydantic V2 Deprecation Warnings in Test Output
* **Symptom**: During `pytest` runs, warnings are emitted regarding class-based `Config` in `app/schemas/oversight.py` (`PydanticDeprecatedSince20`).
* **Root Cause**: Pydantic V2 recommends `ConfigDict` rather than inner `class Config:`.
* **Impact**: Zero runtime failure. All 65 backend unit and integration tests pass successfully without error.
* **Planned Remediation**: Update schema models in next maintenance release to use `model_config = ConfigDict(from_attributes=True)`.

### LIM-005: Starlette HTTP 422 Deprecation Notice
* **Symptom**: Warning emitted: `StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead`.
* **Root Cause**: Python 3.12 / Starlette 0.40+ standards modernization.
* **Impact**: Zero runtime failure. HTTP 422 responses continue to be returned properly to frontend clients.

---

## 3. Successfully Resolved Defects Register

| Defect ID | Severity | Component | Problem Description | Root Cause | Implemented Fix | Verification Evidence |
|---|---|---|---|---|---|---|
| **DEF-001** | **CRITICAL** | Frontend Auth | User logged out upon page refresh (`F5`) | `inMemoryToken` wiped on reload; premature `/auth/me` call before refresh completed triggered session expiration | Coordinated refresh deduplication (`coordinateTokenRefresh`), active session marker (`hasSessionActive`), and 15s backend rotation grace period | **Verified PASS** in Playwright tests `SESS-001` and `SESS-002` |
| **DEF-002** | **HIGH** | CORS Gateway | Vercel production frontend blocked by CORS on Render API | `BACKEND_CORS_ORIGINS` was restricted to local ports | Added `https://neev01.vercel.app` and regex `r"^https://.*\.vercel\.app$"` in `backend/app/main.py` | **Verified PASS** on live cloud |
| **DEF-003** | **MEDIUM** | Public Verify | Reference code query case-sensitivity mismatch | Public reference codes entered in lower-case failed matching against uppercase DB codes | Added case normalization (`public_reference_code.strip().upper()`) in `VerificationService` | **Verified PASS** in test `PUB-005B` |
| **DEF-004** | **LOW** | CSV Export | Spreadsheet formula injection vulnerability | Cells starting with `=`, `+`, `-`, `@` could execute malicious commands if opened in Excel | Implemented `sanitizeSpreadsheetCell` which prefixes vulnerable cells with `'` | **Verified PASS** in `test_reports.py` |

