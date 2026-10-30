# NEEV — Comprehensive Browser Automation QA Test Report

> **Document Version**: 1.0.0-PROD-AUDIT  
> **Testing Framework**: Playwright Automation Engine (Node.js v24.22.0 / Playwright v1.64.1)  
> **Browser Engine**: Chromium Headless 156.0.8078.4 (Windows 64-bit)  
> **Execution Date & Time**: 2026-10-30T09:24:32+05:30 (IST)  
> **Primary Test Lead**: Senior QA Automation Engineer & Security Reviewer

---

## A. Test Environment

| Parameter | Local Development Target | Deployed Production Cloud Target |
|---|---|---|
| **Frontend URL** | `http://localhost:3000` | `https://neev01.vercel.app` |
| **Backend Core API** | `http://127.0.0.1:8000` | `https://neev-api-eqq1.onrender.com` |
| **Database Engine** | Neon Serverless PostgreSQL 16+ | Neon Serverless PostgreSQL 16+ |
| **API Path Prefix** | `/api/v1` | `/api/v1` |
| **Browser Environment** | Chromium (Playwright CFT v1248) | Chromium (Playwright CFT v1248) |
| **Screen Viewport** | $1440 \times 900$ (Desktop High-DPI) | $1440 \times 900$ (Desktop High-DPI) |
| **Authenticated Roles Tested** | `AICTE_ADMIN`, `INSTITUTION_ADMIN` | `AICTE_ADMIN`, `INSTITUTION_ADMIN` |
| **Negative Security Accounts** | `disabled.user@neev.aicte.gov.in` (Suspended) | `disabled.user@neev.aicte.gov.in` (Suspended) |

---

## B. Overall Test Summary

```
========================================================================
                      NEEV AUTOMATED QA SCORECARD
========================================================================
 Total Discovered Application Routes: 23
 Total Interactive Screens Explored:  15 Core Views + 7 Public/Auth Views
 Total Formal Test Cases Executed:    33 Scenarios
 Passed Test Cases:                  33 (100.0%)
 Failed Test Cases:                  0  (0.0%)
 Blocked Test Cases:                 0  (0.0%)
 Unverified / Skipped Screens:        0  (0.0%)
------------------------------------------------------------------------
 End-to-End User Journeys Verified:   8 Distinct Workflows
 Browser Console Errors Captured:     4 (All classified as expected status codes)
 Failed Network HTTP Requests:       0
 High / Critical Defects Unresolved: 0
 Production Deployment Health:        100% Operational (Vercel + Render + Neon)
========================================================================
```

---

## C. Comprehensive Test Case Execution Matrix

| Test ID | Screen / Workflow | Preconditions | Steps | Expected Result | Actual Result | Status | Screenshot Evidence |
|---|---|---|---|---|---|---|---|
| **PUB-001** | Public Landing Page (`/`) | Browser open, unauthenticated | Navigate to `http://localhost:3000/` | Landing page renders Government emblem, AICTE title, and call-to-action buttons | Page loaded with title "National education evidence and verification"; hero detected | **PASS** | `docs/evidence/01_landing_page.png` |
| **PUB-002** | Login Page Initial State (`/login`) | Unauthenticated | Navigate to `http://localhost:3000/login` | Displays clean sign-in card with email and password inputs | Email & password inputs present and responsive | **PASS** | `docs/evidence/02_login_page_unauthenticated.png` |
| **PUB-003** | Password Recovery Request (`/forgot-password`) | Unauthenticated | Navigate to `/forgot-password` | Displays official email input and recovery dispatch button | Form rendered; input accepts valid email | **PASS** | `docs/evidence/03_forgot_password_page.png` |
| **PUB-004** | Password Reset Completion (`/reset-password`) | Unauthenticated, no token | Navigate to `/reset-password` | Gracefully indicates missing or invalid token without crashing | Displays clean token error alert | **PASS** | `docs/evidence/04_reset_password_page.png` |
| **PUB-005** | Public Verification Resolver (`/verify`) | Unauthenticated | Navigate to `/verify` | Verification reference input rendered with purpose disclaimer | Input present; rate-limiting active | **PASS** | `docs/evidence/05_public_verify_page.png` |
| **PUB-005B**| Verification Resolution Query | Unauthenticated | Enter code `VRF-2026-DIT001` & submit | Resolves student Aarav Sharma's active enrolment at DIT | Certificate rendered with green verified seal | **PASS** | `docs/evidence/05b_public_verify_result.png` |
| **PUB-006** | Institutional Registration (`/register`) | Unauthenticated | Navigate to `/register` | Institutional onboarding form rendered with statutory fields | Form inputs present for AICTE ID and college info | **PASS** | `docs/evidence/06_register_page.png` |
| **PUB-007** | 404 Error Page (`/non-existent`) | Unauthenticated | Navigate to `/non-existent-route-for-testing` | Custom 404 page displayed with return navigation | 404 page rendered cleanly with back navigation | **PASS** | `docs/evidence/07_not_found_page.png` |
| **AUTH-001**| Invalid Credentials Rejection | Unauthenticated | Enter wrong credentials on `/login` and submit | Rejects with HTTP 401; displays alert banner | Red alert banner displayed: "Invalid email or password" | **PASS** | `docs/evidence/08_invalid_login_feedback.png` |
| **AUTH-002**| Suspended User Access Block | Account status = `suspended` | Enter `disabled.user@neev.aicte.gov.in` and submit | Rejects with HTTP 403; warns user of suspension | Red alert banner displayed: "Account is suspended" | **PASS** | `docs/evidence/09_suspended_user_login.png` |
| **AUTH-003**| National Admin Login | Active `AICTE_ADMIN` account | Enter valid credentials and submit | Authenticates, sets memory token, redirects to `/overview` | Successfully redirected to `http://localhost:3000/overview` | **PASS** | `docs/evidence/10_post_login_overview.png` |
| **SESS-001**| Full-Page Refresh Persistence | Authenticated on `/overview` | Trigger browser reload (`F5`) | AuthProvider restores session via HttpOnly cookie; stays on screen | Post-refresh URL remains `/overview`; session restored | **PASS** | `docs/evidence/11_session_persistence_after_refresh_overview.png` |
| **SESS-002**| Page Refresh on Secondary Screen | Authenticated on `/programmes` | Navigate to `/programmes`, trigger browser reload | Session persists; programmes table loads 5 rows | Post-refresh URL remains `/programmes`; session intact | **PASS** | `docs/evidence/12_session_persistence_after_refresh_programmes.png` |
| **SESS-003**| Direct Navigation in Fresh Tab | Same browser context | Open new tab directly to `http://localhost:3000/enrolments` | Session restored via cookie; displays student ledger | URL is `/enrolments`; renders student records table | **PASS** | `docs/evidence/13_direct_navigation_new_tab.png` |
| **SCR-001** | National Overview Dashboard (`/overview`) | Authenticated as National Admin | Inspect oversight metrics, cards, and capacity widget | Metric cards show Total Enrolments, Active Count, Capacity | Renders live database numbers; capacity table active | **PASS** | `docs/evidence/14_screen_overview.png` |
| **SCR-002** | Programmes & Capacity Ledger (`/programmes`) | Authenticated | Inspect degree programmes directory | Lists 5 programmes with approved intake and AICTE EOA refs | Table renders 5 programme rows with status badges | **PASS** | `docs/evidence/15_screen_programmes.png` |
| **SCR-003** | Student Enrolment Ledger (`/enrolments`) | Authenticated | Inspect student roster records | Shows masked APAAR (e.g. `XXXXXXXX1234`), roll numbers | 15 rows rendered per page; zero cleartext APAAR | **PASS** | `docs/evidence/16_screen_enrolments.png` |
| **SCR-004** | Batch Submissions Dropzone (`/submissions`) | Authenticated | Inspect ingestion history & CSV dropzone | Dropzone interactive; batch history table visible | Dropzone accepting CSV; historical batch visible | **PASS** | `docs/evidence/17_screen_submissions.png` |
| **SCR-005** | Discrepancy Findings Registry (`/findings`) | Authenticated | Inspect open discrepancy findings | Displays open conflict findings with severity badges | Table renders 2 active findings (DUP-002, INT-002) | **PASS** | `docs/evidence/18_screen_findings.png` |
| **SCR-006** | Finding Detail & Resolution (`/findings/[id]`) | Authenticated | Click finding link to open detail view | Renders student comparison, state transitions bar | Finding detail loaded with permitted state actions | **PASS** | `docs/evidence/19_screen_finding_detail.png` |
| **SCR-007** | Deterministic Risk Queue (`/risk-queue`) | Authenticated | Inspect institution risk ranking | Lists institutions with 6-factor scores and risk bands | DIT and MTU ranked with score 20.0 (WATCH band) | **PASS** | `docs/evidence/20_screen_risk_queue.png` |
| **SCR-008** | Regulatory Audit Cases Index (`/cases`) | Authenticated | Inspect statutory audit dockets | Lists open dockets with docket number and assigned reviewer | Table renders 2 audit case records | **PASS** | `docs/evidence/21_screen_cases.png` |
| **SCR-009** | Audit Case Dossier (`/cases/[id]`) | Authenticated | Click case link to open docket dossier | Dossier shows deliberation notes, hearings, determinations | Case detail loaded with reviewer action buttons | **PASS** | `docs/evidence/22_screen_case_detail.png` |
| **SCR-010** | Technical Institutions Directory (`/institutions`) | Authenticated | Inspect registered colleges directory | Lists 3 technical colleges with AICTE codes and state filters | Directory renders 3 technical institutions | **PASS** | `docs/evidence/23_screen_institutions.png` |
| **SCR-011** | Institutional Risk Profile (`/institutions/[id]/risk-profile`) | Authenticated | Inspect 6-factor breakdown for DIT | Transparent factor gauge displaying score 20.0 / 100 | Visual breakdown of all 6 constituent factor points | **PASS** | `docs/evidence/24_screen_institution_risk_profile.png` |
| **SCR-012** | Regulatory Reports Center (`/reports`) | Authenticated | Inspect reporting catalog and jobs queue | 4 regulatory compliance export templates available | Report catalog and download queue visible | **PASS** | `docs/evidence/25_screen_reports.png` |
| **SCR-013** | Verification Reference Governance (`/verification-references`) | Authenticated | Inspect active verification tokens | Displays issued tokens, tracking codes, and query usage | Table renders sample token VRF-2026-DIT001 (1/5 used) | **PASS** | `docs/evidence/26_screen_verification_references.png` |
| **SCR-014** | External Integration Adapters (`/integrations`) | Authenticated | Inspect government adapter telemetry | 5 adapter cards with status, latency, and contract tests | Displays DigiLocker, AISHE, NAD, Board, AICTE Bureau | **PASS** | `docs/evidence/27_screen_integrations.png` |
| **SCR-015** | Notifications Center (`/notifications`) | Authenticated | Inspect system alerts and announcements | Lists chronological regulatory events with read/unread flags | Notification center rendered with Mark All Read button | **PASS** | `docs/evidence/28_screen_notifications.png` |
| **AUTH-004**| User Sign Out Action | Authenticated | Click "Sign Out" in header | Clears memory token, invalidates session, redirects to `/login` | Redirected to `/login`; session terminated | **PASS** | `docs/evidence/29_post_logout_screen.png` |
| **AUTH-005**| Post-Logout Protected Route Guard | Unauthenticated (post logout) | Attempt direct navigation to `/overview` | Guard intercepts; redirects unauthenticated user to `/login` | Access blocked; redirected immediately to `/login` | **PASS** | Direct URL verification |
| **ROLE-001**| Institutional Admin Scoped Overview | `INSTITUTION_ADMIN` credentials | Log in as DIT Admin (`admin@dit.synthetic.edu.in`) | Overview scoped strictly to Delhi Institute of Technology | Header displays DIT tenant banner; metrics isolated | **PASS** | `docs/evidence/30_inst_admin_overview.png` |
| **ROLE-002**| Institutional Admin Scoped Risk Queue | `INSTITUTION_ADMIN` credentials | Navigate to `/risk-queue` | National controls hidden; scoped institution view rendered | Risk queue rendered in tenant-safe scoped mode | **PASS** | `docs/evidence/31_inst_admin_risk_queue.png` |
| **PROD-001**| Production Deployment E2E | Live Cloud (`neev01.vercel.app`) | Perform login, page refresh, and verification on Vercel | End-to-end cloud infrastructure operational without errors | 100% PASS on Vercel Edge + Render Core API | **PASS** | `docs/evidence/prod_03_post_login_overview.png` |

---

## D. Historical Defect Investigation & Resolution Analysis

### Defect Investigation: The Page-Refresh Logout Anomaly (DEF-HIST-001)

#### 1. Symptom Description
In prior development snapshots, users could successfully sign in with valid credentials, but triggering a browser refresh (`F5`) or navigating directly to a protected route in a new tab caused the user to become immediately logged out and bounced back to `/login`.

#### 2. Root Cause Analysis
* **Architecture Constraint**: The NEEV Project Bible mandates that sensitive JWT access tokens must **never** be stored in persistent browser storage (`localStorage` or `sessionStorage`) to eliminate XSS token exfiltration vulnerabilities. Access tokens were stored strictly in React state (`inMemoryToken`).
* **The Breakage Mechanism**: Upon page refresh, JavaScript memory is completely wiped. When `AuthProvider` mounted, `inMemoryToken` was null. The initial implementation attempted to fetch `/auth/me` before completing a coordinated token refresh. Because `/auth/me` returned `401 Unauthorized`, the global session expiration listener immediately triggered `notifySessionExpired()`, which redirected the user to `/login?session_expired=1`.
* **Cookie-Header Desynchronization**: Furthermore, the refresh token cookie was not being properly coordinated with CORS credentials across decoupled origin boundaries.

#### 3. Applied Remediation (Commit `aec093a`)
1. **Coordinated Token Refresh Pipeline (`frontend/lib/api.ts`)**:
   Introduced `coordinateTokenRefresh()` with in-flight promise deduplication. If multiple concurrent requests trigger on page reload, they share the exact same refresh promise rather than issuing conflicting refresh calls.
2. **Session Presence Indicator (`hasSessionActive`)**:
   Introduced a non-sensitive boolean flag `neev_session_active` stored in `localStorage`. This flag contains zero credentials or tokens. It merely tells `AuthProvider` that an active session cookie is expected, directing it to call `/auth/refresh` before giving up.
3. **Backend Refresh Token Rotation Grace Period (`backend/app/api/v1/endpoints/auth.py`)**:
   Implemented a 15-second grace window (`REFRESH_GRACE_PERIOD_SECONDS = 15`) on the backend. When React 19 strict-mode mounts components twice in rapid succession, both requests successfully exchange tokens without invalidating the session as a false token reuse attack.

#### 4. Retest & Verification in Real Browser
Automated test `SESS-001` explicitly refreshed `/overview`, and `SESS-002` refreshed `/programmes`. Both tests passed with zero session loss. The user remained seamlessly logged in across both local and production Vercel environments.

---

## E. Browser Console & Network Log Review

During the automated 33-test Playwright suite, all browser console messages and network transactions were captured:

```json
{
  "total_console_errors": 4,
  "failed_network_requests": 0
}
```

### Classification of Captured Console Errors:
1. `Failed to load resource: 404 (Not Found)` on `http://localhost:3000/non-existent-route-for-testing`  
   * **Classification**: **Harmless / Expected Test Result**. Generated purposefully by test `PUB-007` to confirm custom 404 error page handling.
2. `Failed to load resource: 401 (Unauthorized)` on `http://localhost:8000/api/v1/auth/login`  
   * **Classification**: **Harmless / Expected Test Result**. Generated purposefully by test `AUTH-001` to verify credential rejection on wrong password.
3. `Failed to load resource: 403 (Forbidden)` on `http://localhost:8000/api/v1/auth/login`  
   * **Classification**: **Harmless / Expected Test Result**. Generated purposefully by test `AUTH-002` to confirm suspended account blocking.
4. `Failed to load resource: 401 (Unauthorized)` on `http://localhost:8000/api/v1/institutions/.../risk-profile`  
   * **Classification**: **Harmless Transient State**. Intercepted cleanly by `apiRequest()` which automatically completed coordinated token refresh and re-dispatched the request successfully. Zero user impact.

There were **zero unhandled JavaScript exceptions**, **zero React hydration errors**, **zero CORS header errors**, and **zero failed network calls**.

