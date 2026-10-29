const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface UserScope {
  id: string;
  scope_type: "NATIONAL" | "INSTITUTION";
  institution_id?: string | null;
  valid_from: string;
  valid_until?: string | null;
}

export interface User {
  id: string;
  email_normalized: string;
  display_name: string;
  account_status: string;
  roles: string[];
  scopes: UserScope[];
  permissions: string[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  user: User;
}

export interface InstitutionListResponse {
  items: Institution[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Institution {
  id: string;
  official_institution_code: string;
  name: string;
  institution_type: string;
  state_code: string;
  district_code: string;
  address?: string | null;
  status: string;
  source_reference: string;
  is_synthetic: boolean;
  programmes_count: number;
  enrolments_count: number;
  created_at: string;
  updated_at: string;
}

export interface Programme {
  id: string;
  institution_id: string;
  institution_name?: string;
  official_programme_code: string;
  programme_name: string;
  qualification_level: string;
  academic_discipline: string;
  status: string;
  created_at: string;
  active_intake?: number | null;
  active_enrolments_count: number;
}

export interface AcademicYear {
  id: string;
  label: string;
  start_date: string;
  end_date: string;
  status: string;
}

export interface Batch {
  id: string;
  institution_id: string;
  institution_name?: string;
  academic_year_id: string;
  academic_year_label?: string;
  programme_id?: string | null;
  programme_name?: string | null;
  submission_type: string;
  source_type: string;
  processing_status: string;
  source_filename?: string;
  row_count: number;
  valid_count: number;
  accepted_count: number;
  rejected_count: number;
  flagged_count: number;
  ruleset_version: string;
  receipt_reference?: string | null;
  created_at: string;
}

export interface FindingDetail {
  rule_code: string;
  field_name?: string | null;
  severity: "ERROR" | "WARNING" | "INFO";
  explanation: string;
  raw_value?: string | null;
}

export interface RowPreviewItem {
  row_number: number;
  processing_status: "VALID" | "ERROR" | "WARNING";
  raw_data: Record<string, any>;
  normalized_data?: Record<string, any> | null;
  errors: FindingDetail[];
  warnings: FindingDetail[];
}

export interface BatchPreview {
  batch: Batch;
  total_rows: number;
  valid_rows: number;
  error_rows: number;
  warning_rows: number;
  rows: RowPreviewItem[];
  validation_summary: Record<string, number>;
}

export interface EnrolmentRecord {
  id: string;
  institution_id: string;
  institution_name: string;
  programme_id: string;
  programme_name: string;
  official_programme_code: string;
  academic_year_id: string;
  academic_year_label: string;
  institution_student_id: string;
  student_full_name: string;
  masked_apaar_id?: string | null;
  apaar_validation_status: string;
  admission_date: string;
  enrolment_status: string;
  admission_category: string;
  supernumerary_category?: string | null;
  source_submission_batch_id?: string | null;
  created_at: string;
}

export interface ReconciliationItem {
  programme_id: string;
  programme_name: string;
  official_programme_code: string;
  academic_year_label: string;
  approved_intake?: number | null;
  calculated_active_enrolments: number;
  variance?: number | null;
  reconciliation_status: "BALANCED" | "UNDER_CAPACITY" | "CAPACITY_EXCEEDED" | "MISSING_REFERENCE";
  rule_basis: string;
  is_capacity_exceeded: boolean;
  is_synthetic: boolean;
}

export interface DashboardSummary {
  institutions_count: number;
  programmes_count: number;
  selected_academic_year: string;
  batches_by_status: Record<string, number>;
  total_students_count: number;
  active_students_count: number;
  recent_submissions: Batch[];
  validation_issues_count: number;
  programmes_exceeding_capacity: number;
  reconciliation_items: ReconciliationItem[];
}

// Token storage in memory only for high security (Project Bible directive)
// Do NOT store tokens in localStorage or sessionStorage.
let inMemoryToken: string | null = null;
let activeRefreshPromise: Promise<string | null> | null = null;

export const setAccessToken = (token: string | null) => {
  inMemoryToken = token;
};

export const getAccessToken = (): string | null => {
  return inMemoryToken;
};

export async function coordinateTokenRefresh(): Promise<string | null> {
  if (activeRefreshPromise) {
    return activeRefreshPromise;
  }

  activeRefreshPromise = (async () => {
    try {
      const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        credentials: "include",
      });
      if (refreshRes.ok) {
        const data: TokenResponse = await refreshRes.json();
        setAccessToken(data.access_token);
        return data.access_token;
      }
      setAccessToken(null);
      return null;
    } catch {
      setAccessToken(null);
      return null;
    } finally {
      activeRefreshPromise = null;
    }
  })();

  return activeRefreshPromise;
}

export function sanitizeSpreadsheetCell(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "";
  const str = String(value);
  if (str.length > 0 && ["=", "+", "-", "@", "\t", "\r"].includes(str[0])) {
    return `'${str}`;
  }
  return str;
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAccessToken();
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    credentials: "include", // send HttpOnly cookies for refresh token
  });

  const isPublicAuthEndpoint =
    endpoint === "/auth/login" ||
    endpoint === "/auth/refresh" ||
    endpoint === "/auth/forgot-password" ||
    endpoint === "/auth/reset-password";

  if (response.status === 401 && !isPublicAuthEndpoint) {
    // Coordinated single refresh operation: wait for active or start single refresh
    const freshToken = await coordinateTokenRefresh();
    if (freshToken) {
      // Retry original request exactly once with new token
      headers.set("Authorization", `Bearer ${freshToken}`);
      const retryRes = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
        credentials: "include",
      });
      if (retryRes.ok) {
        return retryRes.json();
      }
      let retryError = "Request failed after session refresh.";
      try {
        const errJson = await retryRes.json();
        retryError = errJson.message || errJson.detail || retryRes.statusText;
      } catch {
        retryError = retryRes.statusText;
      }
      throw new Error(retryError);
    }
  }

  if (!response.ok) {
    let errorDetail = "An unexpected error occurred.";
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.message || errorJson.detail || JSON.stringify(errorJson);
    } catch {
      errorDetail = response.statusText || `Request failed with HTTP ${response.status}`;
    }
    const err: any = new Error(errorDetail);
    err.status = response.status;
    throw err;
  }

  return response.json();
}

// ================= Phase 2 Types & Methods =================

export interface FindingItem {
  id: string;
  rule_code: string;
  rule_version: string;
  category: string;
  severity: "CRITICAL" | "ERROR" | "WARNING" | "INFO";
  status: "OPEN" | "AWAITING_INSTITUTION_RESPONSE" | "RESPONSE_RECEIVED" | "UNDER_REVIEW" | "RESOLVED" | "DISMISSED" | "ESCALATED";
  explanation: string;
  structured_evidence_json?: string | null;
  primary_institution_id: string;
  primary_institution_name?: string | null;
  secondary_institution_id?: string | null;
  secondary_institution_name?: string | null;
  programme_id?: string | null;
  programme_name?: string | null;
  academic_year_id?: string | null;
  academic_year_label?: string | null;
  primary_enrolment_id?: string | null;
  primary_student_name?: string | null;
  primary_institution_student_id?: string | null;
  primary_masked_apaar?: string | null;
  secondary_enrolment_id?: string | null;
  secondary_student_name?: string | null;
  secondary_institution_student_id?: string | null;
  secondary_masked_apaar?: string | null;
  assigned_reviewer_id?: string | null;
  assigned_reviewer_name?: string | null;
  resolution_rationale?: string | null;
  resolved_by_user_id?: string | null;
  resolved_at?: string | null;
  first_detected_at: string;
  last_detected_at: string;
  created_at: string;
  updated_at: string;
  responses_count: number;
  evidence_count: number;
}

export interface FindingResponseItem {
  id: string;
  finding_id: string;
  submitting_user_id: string;
  submitting_user_name?: string | null;
  institution_id: string;
  institution_name?: string | null;
  response_type: string;
  explanation: string;
  related_correction_id?: string | null;
  review_status: string;
  reviewer_notes?: string | null;
  submitted_at: string;
}

export interface EvidenceMetadataItem {
  id: string;
  finding_id?: string | null;
  enrolment_record_id?: string | null;
  original_filename: string;
  media_type: string;
  file_size_bytes: number;
  sha256_checksum: string;
  uploader_user_id: string;
  uploader_name?: string | null;
  institution_id: string;
  institution_name?: string | null;
  evidence_category: string;
  source_provenance: string;
  scanning_status: string;
  uploaded_at: string;
}

export interface FindingDetailItem extends FindingItem {
  responses: FindingResponseItem[];
  evidence_attachments: EvidenceMetadataItem[];
  permitted_transitions: string[];
}

export interface FindingListResponse {
  items: FindingItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface NotificationItem {
  id: string;
  recipient_user_id?: string | null;
  target_institution_id?: string | null;
  role_target?: string | null;
  title: string;
  message: string;
  event_type: string;
  related_resource_type: string;
  related_resource_id: string;
  is_read: boolean;
  created_at: string;
}

export interface EnrolmentVersionItem {
  id: string;
  enrolment_record_id: string;
  version_number: number;
  snapshot_json: string;
  change_reason: string;
  changed_by: string;
  changed_at: string;
}

export interface EnrolmentHistory {
  current_version: number;
  enrolment_id: string;
  student_full_name: string;
  institution_student_id: string;
  masked_apaar_id?: string | null;
  versions: EnrolmentVersionItem[];
}

export interface EnrolmentCorrectionResponse {
  success: boolean;
  enrolment_id: string;
  new_version: number;
  message: string;
  revalidation_findings: string[];
}

// ================= Phase 3 Interfaces =================

export interface RiskFactorBreakdown {
  capacity_discrepancy: number;
  unresolved_conflicts: number;
  data_quality: number;
  unusual_roster_changes: number;
  source_reconciliation_gap: number;
  repeated_prior_findings: number;
  total_score: number;
  risk_band: "ROUTINE" | "WATCH" | "REVIEW_RECOMMENDED" | "PRIORITY_REVIEW";
  completeness_state: string;
  explanation: string;
}

export interface RiskCalculationItem {
  id: string;
  institution_id: string;
  institution_name?: string | null;
  programme_id?: string | null;
  programme_name?: string | null;
  academic_year_id?: string | null;
  academic_year_label?: string | null;
  total_score: number;
  risk_band: "ROUTINE" | "WATCH" | "REVIEW_RECOMMENDED" | "PRIORITY_REVIEW";
  calculation_version: string;
  factors: RiskFactorBreakdown;
  input_snapshot: Record<string, any>;
  explanation: string;
  completeness_state: string;
  calculated_at: string;
  is_active: boolean;
}

export interface RiskQueueItem {
  institution_id: string;
  institution_name: string;
  official_code: string;
  state: string;
  total_score: number;
  risk_band: "ROUTINE" | "WATCH" | "REVIEW_RECOMMENDED" | "PRIORITY_REVIEW";
  unresolved_findings_count: number;
  active_cases_count: number;
  last_calculated_at: string;
  completeness_state: string;
  primary_driver: string;
}

export interface RiskQueueResponse {
  items: RiskQueueItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface InstitutionRiskProfile {
  institution_id: string;
  institution_name: string;
  official_code: string;
  current_calculation?: RiskCalculationItem | null;
  history: RiskCalculationItem[];
  unresolved_findings_count: number;
  active_cases_count: number;
  programmes_exceeding_capacity_count: number;
}

export interface AuditCaseListItem {
  id: string;
  case_reference: string;
  institution_id: string;
  institution_name: string;
  programme_name?: string | null;
  case_category: string;
  priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  status: "OPEN" | "ASSIGNED" | "UNDER_REVIEW" | "CLARIFICATION_REQUESTED" | "RESPONSE_RECEIVED" | "RESOLVED" | "ESCALATED" | "CLOSED_NO_ACTION";
  assigned_reviewer_id?: string | null;
  assigned_reviewer_name?: string | null;
  linked_findings_count: number;
  response_deadline?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuditCaseListResponse {
  items: AuditCaseListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AuditCaseFindingItem {
  id: string;
  finding_id: string;
  rule_code: string;
  severity: string;
  status: string;
  explanation: string;
  linked_at: string;
}

export interface AuditCaseEventItem {
  id: string;
  event_type: string;
  actor_name?: string | null;
  from_status?: string | null;
  to_status?: string | null;
  description: string;
  is_internal: boolean;
  created_at: string;
}

export interface ClarificationRequestItem {
  id: string;
  audit_case_id: string;
  case_reference?: string | null;
  institution_id: string;
  institution_name?: string | null;
  request_reference: string;
  subject: string;
  information_requested: string;
  response_deadline?: string | null;
  status: "PENDING_RESPONSE" | "RESPONSE_RECEIVED" | "EXPIRED" | "CANCELLED";
  issuing_officer_name?: string | null;
  response_explanation?: string | null;
  response_evidence_id?: string | null;
  responded_by_user_name?: string | null;
  responded_at?: string | null;
  created_at: string;
}

export interface AuditCaseDecisionItem {
  id: string;
  audit_case_id: string;
  decision_type: "RESOLVED" | "ESCALATED" | "CLOSED_NO_ACTION";
  decision_rationale: string;
  follow_up_action?: string | null;
  reviewer_name?: string | null;
  decided_at: string;
}

export interface AuditCaseDetail {
  id: string;
  case_reference: string;
  institution_id: string;
  institution_name: string;
  programme_id?: string | null;
  programme_name?: string | null;
  academic_year_id?: string | null;
  academic_year_label?: string | null;
  case_category: string;
  priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  status: "OPEN" | "ASSIGNED" | "UNDER_REVIEW" | "CLARIFICATION_REQUESTED" | "RESPONSE_RECEIVED" | "RESOLVED" | "ESCALATED" | "CLOSED_NO_ACTION";
  creation_rationale: string;
  assigned_reviewer_id?: string | null;
  assigned_reviewer_name?: string | null;
  response_deadline?: string | null;
  created_by_user_name?: string | null;
  created_at: string;
  updated_at: string;
  closed_at?: string | null;
  closure_reason?: string | null;
  findings: AuditCaseFindingItem[];
  events: AuditCaseEventItem[];
  clarification_requests: ClarificationRequestItem[];
  decisions: AuditCaseDecisionItem[];
  permitted_transitions: string[];
}

export interface ReportDefinition {
  report_type: string;
  title: string;
  description: string;
  allowed_formats: string[];
  requires_institution_scope: boolean;
  data_classification: string;
}

export interface ReportJobItem {
  id: string;
  report_type: string;
  report_title: string;
  status: "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED";
  institution_id?: string | null;
  institution_name?: string | null;
  academic_year_label?: string | null;
  row_count?: number | null;
  file_size_bytes?: number | null;
  error_message?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface NationalDashboardMetrics {
  covered_institutions_count: number;
  programmes_with_intake_count: number;
  total_submitted_enrolments: number;
  total_active_enrolments: number;
  submission_completion_rate_pct: number;
  required_fields_complete_pct: number;
  valid_format_apaar_pct: number;
  unresolved_conflict_findings_count: number;
  programmes_requiring_intake_review_count: number;
  open_correction_requests_count: number;
  open_audit_cases_count: number;
  risk_band_distribution: Record<string, number>;
  findings_by_category: Record<string, number>;
  cases_by_status: Record<string, number>;
  academic_year_label: string;
}

export interface InstitutionDashboardMetrics {
  institution_id: string;
  institution_name: string;
  official_code: string;
  submission_progress_pct: number;
  total_enrolments_count: number;
  active_enrolments_count: number;
  programmes_count: number;
  programmes_exceeding_capacity_count: number;
  open_findings_count: number;
  findings_awaiting_response_count: number;
  responses_submitted_count: number;
  resolved_findings_count: number;
  open_clarification_requests_count: number;
  active_audit_cases_count: number;
  latest_receipt_reference?: string | null;
  current_risk_band: string;
  current_risk_score: number;
  academic_year_label: string;
}

// ================= Phase 4 Verification & Integrations =================

export interface VerificationReferenceItem {
  id: string;
  public_reference_code: string;
  enrolment_record_id: string;
  student_full_name: string;
  institution_id: string;
  institution_name: string;
  programme_name?: string | null;
  academic_year_label?: string | null;
  purpose: string;
  disclosure_profile: Record<string, boolean>;
  status: "ACTIVE" | "REVOKED" | "EXPIRED" | "EXHAUSTED";
  max_uses?: number | null;
  use_count: number;
  expires_at: string;
  revoked_at?: string | null;
  revocation_reason?: string | null;
  created_at: string;
  access_logs_count: number;
}

export interface VerificationReferenceCreatedResponse extends VerificationReferenceItem {
  raw_bearer_token: string;
}

export interface VerificationReferenceListResponse {
  items: VerificationReferenceItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface VerificationResultResponse {
  outcome: "SUCCESS" | "INVALID_TOKEN" | "EXPIRED" | "REVOKED" | "USE_LIMIT_EXCEEDED" | "RECORD_INELIGIBLE";
  public_reference_code?: string | null;
  verified_at: string;
  purpose?: string | null;
  disclosed_claims?: Record<string, any> | null;
  synthetic_disclaimer: string;
  message: string;
}

export interface IntegrationStatusItem {
  adapter_code: string;
  adapter_name: string;
  status: string;
  is_simulated: boolean;
  last_checked_at: string;
  latency_ms?: number | null;
  supported_claims: string[];
  known_limitations: string;
  contract_test_status: string;
  error_code?: string | null;
}

export interface IntegrationTestResponse {
  adapter_code: string;
  contract_test_status: string;
  latency_ms: number;
  checked_at: string;
  message: string;
}

export interface DashboardFiltersResponse {
  academic_years: { id: string; label: string; status: string }[];
  states: string[];
  risk_bands: string[];
  case_statuses: string[];
  case_priorities: string[];
}

export const api = {
  // Findings
  listFindings: (params: Record<string, any> = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") query.append(k, String(v));
    });
    return apiRequest<FindingListResponse>(`/findings?${query.toString()}`);
  },
  getFindingDetail: (id: string) => apiRequest<FindingDetailItem>(`/findings/${id}`),
  submitFindingResponse: (id: string, data: { response_type: string; explanation: string; related_correction_id?: string }) =>
    apiRequest<FindingResponseItem>(`/findings/${id}/responses`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  transitionFinding: (id: string, data: { target_status: string; rationale?: string }) =>
    apiRequest<FindingItem>(`/findings/${id}/transition`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  uploadFindingEvidence: (id: string, formData: FormData) =>
    apiRequest<EvidenceMetadataItem>(`/findings/${id}/evidence`, {
      method: "POST",
      body: formData,
    }),

  // Enrolments history and corrections
  getEnrolmentHistory: (id: string) => apiRequest<EnrolmentHistory>(`/enrolments/${id}/history`),
  submitEnrolmentCorrection: (id: string, data: { expected_version: number; correction_reason: string; admission_date?: string; enrolment_status?: string; admission_category?: string; supernumerary_category?: string }) =>
    apiRequest<EnrolmentCorrectionResponse>(`/enrolments/${id}/corrections`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getEnrolmentEvidence: (id: string) => apiRequest<EvidenceMetadataItem[]>(`/enrolments/${id}/evidence`),
  getEvidenceDownloadUrl: (evidenceId: string) => `${API_BASE}/evidence/${evidenceId}`,

  // Notifications
  listNotifications: (params: { is_read?: boolean; limit?: number; offset?: number } = {}) => {
    const query = new URLSearchParams();
    if (params.is_read !== undefined) query.append("is_read", String(params.is_read));
    if (params.limit !== undefined) query.append("limit", String(params.limit));
    if (params.offset !== undefined) query.append("offset", String(params.offset));
    return apiRequest<NotificationItem[]>(`/notifications?${query.toString()}`);
  },
  getUnreadNotificationsCount: () => apiRequest<{ unread_count: number }>("/notifications/unread-count"),
  markNotificationRead: (id: string) => apiRequest<NotificationItem>(`/notifications/${id}/read`, { method: "PATCH" }),
  markAllNotificationsRead: () => apiRequest<{ success: boolean; marked_read_count: number }>("/notifications/mark-all-read", { method: "POST" }),

  // Integrity reconciliation
  triggerReconciliation: () => apiRequest<any>("/integrity/reconcile", { method: "POST" }),
  getConflictCandidates: () => apiRequest<any[]>("/integrity/conflicts"),

  // ================= Phase 3 Oversight & Case Management =================
  getNationalDashboard: (ayId?: string, instId?: string) => {
    const query = new URLSearchParams();
    if (ayId) query.append("academic_year_id", ayId);
    if (instId) query.append("institution_id", instId);
    const qs = query.toString();
    return apiRequest<NationalDashboardMetrics>(`/dashboard/national${qs ? `?${qs}` : ""}`);
  },

  getInstitutionDashboard: (institutionId: string) =>
    apiRequest<InstitutionDashboardMetrics>(`/dashboard/institution/${institutionId}`),

  getRiskQueue: (params: { risk_band?: string; institution_id?: string; search?: string; page?: number; page_size?: number } = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") query.append(k, String(v));
    });
    const qs = query.toString();
    return apiRequest<RiskQueueResponse>(`/risk-queue${qs ? `?${qs}` : ""}`);
  },

  getInstitutionRiskProfile: (institutionId: string, ayId?: string) => {
    const qs = ayId ? `?academic_year_id=${ayId}` : "";
    return apiRequest<InstitutionRiskProfile>(`/institutions/${institutionId}/risk-profile${qs}`);
  },

  getRiskCalculation: (calcId: string) =>
    apiRequest<RiskCalculationItem>(`/risk-calculations/${calcId}`),

  recalculateRisk: (institutionId: string) =>
    apiRequest<RiskCalculationItem>(`/institutions/${institutionId}/recalculate-risk`, { method: "POST" }),

  listCases: (params: { status?: string; priority?: string; institution_id?: string; search?: string; page?: number; page_size?: number } = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") query.append(k, String(v));
    });
    const qs = query.toString();
    return apiRequest<AuditCaseListResponse>(`/audit-cases${qs ? `?${qs}` : ""}`);
  },

  getCaseDetail: (caseId: string) =>
    apiRequest<AuditCaseDetail>(`/audit-cases/${caseId}`),

  createCase: (data: { institution_id: string; programme_id?: string; academic_year_id?: string; case_category: string; priority: string; creation_rationale: string; finding_ids?: string[] }) =>
    apiRequest<AuditCaseListItem>("/audit-cases", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  listReviewers: () =>
    apiRequest<{ id: string; display_name: string; email: string; role: string }[]>("/audit-cases/reviewers"),

  assignCase: (caseId: string, data: { reviewer_id: string; rationale?: string }) =>
    apiRequest<AuditCaseDetail>(`/audit-cases/${caseId}/assignment`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  transitionCase: (caseId: string, data: { target_status: string; rationale: string }) =>
    apiRequest<AuditCaseDetail>(`/audit-cases/${caseId}/events`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  addCaseNote: (caseId: string, data: { note: string; is_internal: boolean }) =>
    apiRequest<AuditCaseEventItem>(`/audit-cases/${caseId}/notes`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  createClarificationRequest: (caseId: string, data: { subject: string; information_requested: string; response_deadline?: string }) =>
    apiRequest<ClarificationRequestItem>(`/audit-cases/${caseId}/clarification-requests`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getClarificationRequest: (requestId: string) =>
    apiRequest<ClarificationRequestItem>(`/clarification-requests/${requestId}`),

  submitClarificationResponse: (requestId: string, data: { explanation: string; evidence_id?: string }) =>
    apiRequest<ClarificationRequestItem>(`/clarification-requests/${requestId}/response`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  recordCaseDecision: (caseId: string, data: { decision_type: string; decision_rationale: string; follow_up_action?: string }) =>
    apiRequest<AuditCaseDecisionItem>(`/audit-cases/${caseId}/decisions`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  listReportDefinitions: () =>
    apiRequest<ReportDefinition[]>("/reports"),

  createReportJob: (data: { report_type: string; institution_id?: string; academic_year_id?: string; state?: string; date_from?: string; date_to?: string }) =>
    apiRequest<ReportJobItem>("/reports", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  listReportJobs: () =>
    apiRequest<ReportJobItem[]>("/reports/jobs"),

  getReportDownloadUrl: (jobId: string) => `${API_BASE}/reports/${jobId}/download`,

  listInstitutions: (params: { search?: string; page?: number; page_size?: number } = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") query.append(k, String(v));
    });
    const qs = query.toString();
    return apiRequest<{ items: { id: string; name: string; official_institution_code: string; state_code?: string }[]; total: number }>(`/institutions${qs ? `?${qs}` : ""}`);
  },

  // ================= Phase 4 Verification & Integrations =================
  listVerificationReferences: (params: { institution_id?: string; status?: string; search?: string; page?: number; page_size?: number } = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") query.append(k, String(v));
    });
    const qs = query.toString();
    return apiRequest<VerificationReferenceListResponse>(`/verification-references${qs ? `?${qs}` : ""}`);
  },

  getVerificationReference: (id: string) =>
    apiRequest<VerificationReferenceItem>(`/verification-references/${id}`),

  issueVerificationReference: (data: { enrolment_record_id: string; purpose: string; disclosure_profile: Record<string, boolean>; expires_in_days?: number; max_uses?: number | null }) =>
    apiRequest<VerificationReferenceCreatedResponse>("/verification-references", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  revokeVerificationReference: (id: string, data: { revocation_reason: string }) =>
    apiRequest<VerificationReferenceItem>(`/verification-references/${id}/revoke`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  verifyReferenceToken: (reference_token: string) =>
    apiRequest<VerificationResultResponse>("/verify", {
      method: "POST",
      body: JSON.stringify({ reference_token }),
    }),

  listIntegrationStatuses: () =>
    apiRequest<IntegrationStatusItem[]>("/integrations/status"),

  getIntegrationStatus: (adapterCode: string) =>
    apiRequest<IntegrationStatusItem>(`/integrations/${adapterCode}/status`),

  testIntegrationContract: (adapterCode: string) =>
    apiRequest<IntegrationTestResponse>(`/integrations/${adapterCode}/test-contract`, {
      method: "POST",
    }),

  getDashboardFilters: () =>
    apiRequest<DashboardFiltersResponse>("/dashboard/filters"),

  listEnrolments: (params: { institution_id?: string; academic_year_id?: string; search?: string; page?: number; limit?: number; page_size?: number } = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") query.append(k, String(v));
    });
    const qs = query.toString();
    return apiRequest<{ items: any[]; total: number; page: number; limit: number }>(`/enrolments${qs ? `?${qs}` : ""}`);
  },
};

