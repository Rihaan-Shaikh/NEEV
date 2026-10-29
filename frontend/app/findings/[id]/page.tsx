"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import { 
  api, 
  FindingDetailItem, 
  FindingResponseItem, 
  EvidenceMetadataItem 
} from "@/lib/api";
import { 
  AlertTriangle, 
  ArrowLeft, 
  Building2, 
  Calendar, 
  CheckCircle2, 
  Clock, 
  Download, 
  FileText, 
  GraduationCap, 
  Info, 
  Layers, 
  MessageSquare, 
  Send, 
  ShieldAlert, 
  ShieldCheck, 
  Upload, 
  UserCheck, 
  X,
  AlertCircle
} from "lucide-react";

function FindingDetailInner({ params }: { params: Promise<{ id: string }> }) {
  const unwrappedParams = use(params);
  const findingId = unwrappedParams.id;

  const [finding, setFinding] = useState<FindingDetailItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modals state
  const [showResponseModal, setShowResponseModal] = useState(false);
  const [responseType, setResponseType] = useState("EXPLANATION");
  const [responseExplanation, setResponseExplanation] = useState("");
  const [isSubmittingResponse, setIsSubmittingResponse] = useState(false);
  const [responseError, setResponseError] = useState<string | null>(null);

  const [showTransitionModal, setShowTransitionModal] = useState(false);
  const [targetStatus, setTargetStatus] = useState("");
  const [transitionRationale, setTransitionRationale] = useState("");
  const [isSubmittingTransition, setIsSubmittingTransition] = useState(false);
  const [transitionError, setTransitionError] = useState<string | null>(null);

  const [showEvidenceModal, setShowEvidenceModal] = useState(false);
  const [evidenceCategory, setEvidenceCategory] = useState("TRANSFER_CERTIFICATE");
  const [evidenceFile, setEvidenceFile] = useState<File | null>(null);
  const [isUploadingEvidence, setIsUploadingEvidence] = useState(false);
  const [evidenceError, setEvidenceError] = useState<string | null>(null);

  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const loadFinding = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getFindingDetail(findingId);
      setFinding(data);
    } catch (err: any) {
      setError(err.message || "Failed to load discrepancy details.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (findingId) {
      loadFinding();
    }
  }, [findingId]);

  const handleResponseSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!responseExplanation.trim()) {
      setResponseError("Please provide an institutional explanation.");
      return;
    }
    setIsSubmittingResponse(true);
    setResponseError(null);
    try {
      await api.submitFindingResponse(findingId, {
        response_type: responseType,
        explanation: responseExplanation.trim()
      });
      setShowResponseModal(false);
      setResponseExplanation("");
      setActionSuccess("Institutional explanation recorded successfully in the audit trail.");
      await loadFinding();
    } catch (err: any) {
      setResponseError(err.message || "Failed to submit response.");
    } finally {
      setIsSubmittingResponse(false);
    }
  };

  const handleTransitionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetStatus) {
      setTransitionError("Please select a target status.");
      return;
    }
    const terminalStatuses = ["RESOLVED", "DISMISSED", "ESCALATED"];
    if (terminalStatuses.includes(targetStatus) && transitionRationale.trim().length < 10) {
      setTransitionError("A detailed rationale (minimum 10 characters) is required for this lifecycle decision.");
      return;
    }
    setIsSubmittingTransition(true);
    setTransitionError(null);
    try {
      await api.transitionFinding(findingId, {
        target_status: targetStatus,
        rationale: transitionRationale.trim() || undefined
      });
      setShowTransitionModal(false);
      setTransitionRationale("");
      setActionSuccess(`Finding status updated to ${targetStatus.toLowerCase().replace(/_/g, " ")}.`);
      await loadFinding();
    } catch (err: any) {
      setTransitionError(err.message || "Failed to update lifecycle status.");
    } finally {
      setIsSubmittingTransition(false);
    }
  };

  const handleEvidenceUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!evidenceFile) {
      setEvidenceError("Please select a document to upload.");
      return;
    }
    setIsUploadingEvidence(true);
    setEvidenceError(null);
    try {
      const formData = new FormData();
      formData.append("file", evidenceFile);
      formData.append("evidence_category", evidenceCategory);
      formData.append("source_provenance", "INSTITUTION_DOCUMENT_UPLOAD");

      await api.uploadFindingEvidence(findingId, formData);
      setShowEvidenceModal(false);
      setEvidenceFile(null);
      setActionSuccess("Supporting evidence uploaded and secured.");
      await loadFinding();
    } catch (err: any) {
      setEvidenceError(err.message || "Failed to upload evidence.");
    } finally {
      setIsUploadingEvidence(false);
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case "CRITICAL":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 border border-red-200">Critical severity</span>;
      case "ERROR":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800 border border-orange-200">Error severity</span>;
      case "WARNING":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200">Warning severity</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">Info</span>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "OPEN":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200">Open</span>;
      case "AWAITING_INSTITUTION_RESPONSE":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 border border-purple-200">Awaiting institution response</span>;
      case "RESPONSE_RECEIVED":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">Response received</span>;
      case "UNDER_REVIEW":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 border border-indigo-200">Under review</span>;
      case "RESOLVED":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 border border-emerald-200">Resolved</span>;
      case "DISMISSED":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-300">Dismissed</span>;
      case "ESCALATED":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 border border-red-200">Escalated</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">{status}</span>;
    }
  };

  return (
    <AppShell>
      <div className="space-y-6 max-w-7xl mx-auto pb-12">
        {/* Navigation Breadcrumb & Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#CBD5E1]">
          <div className="flex items-center gap-3">
            <Link 
              href="/findings" 
              className="p-2 rounded-full border border-[#CBD5E1] text-[#475569] hover:text-[#0F2942] hover:bg-slate-100 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <div className="flex items-center gap-2 text-xs text-[#475569]">
                <span className="font-semibold text-[#0F2942]">Discrepancy record</span>
                <span>•</span>
                <span className="font-medium text-slate-700">{finding?.rule_code || "..."}</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-[#0F2942] mt-0.5">Discrepancy resolution dossier</h1>
            </div>
          </div>

          {finding && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  setShowResponseModal(true);
                  setResponseError(null);
                }}
                className="btn-rounded-secondary text-xs"
              >
                <MessageSquare className="w-3.5 h-3.5 text-slate-500" />
                Submit response
              </button>

              <button
                onClick={() => {
                  setShowEvidenceModal(true);
                  setEvidenceError(null);
                }}
                className="btn-rounded-secondary text-xs"
              >
                <Upload className="w-3.5 h-3.5 text-slate-500" />
                Upload evidence
              </button>

              {finding.permitted_transitions && finding.permitted_transitions.length > 0 && (
                <button
                  onClick={() => {
                    setTargetStatus(finding.permitted_transitions[0] || "");
                    setShowTransitionModal(true);
                    setTransitionError(null);
                  }}
                  className="btn-rounded-primary text-xs"
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-sky-300" />
                  Transition status
                </button>
              )}
            </div>
          )}
        </div>

        {/* Action feedback message */}
        {actionSuccess && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-emerald-800 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{actionSuccess}</span>
            </div>
            <button onClick={() => setActionSuccess(null)} className="text-emerald-700 hover:text-emerald-900">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Loading and Error States */}
        {isLoading && (
          <div className="bg-white rounded-2xl border border-[#CBD5E1] p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-slate-300 border-t-[#0F2942]"></div>
            <p className="mt-3 text-xs text-[#475569]">Loading discrepancy dossier...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-red-800">
            <div className="flex items-center gap-2 font-semibold text-sm">
              <AlertCircle className="w-4 h-4" />
              <span>Failed to load finding details</span>
            </div>
            <p className="mt-1 text-xs text-red-700">{error}</p>
            <button 
              onClick={loadFinding}
              className="mt-3 btn-rounded-secondary text-xs"
            >
              Retry
            </button>
          </div>
        )}

        {finding && !isLoading && (
          /* Clean 2-Column Dossier Split (65% Main Dossier + 35% Action Panel - NO 3-COLUMN LAYOUT) */
          <div className="flex flex-col lg:flex-row gap-6">
            {/* Left Column (65%): Main Details, Affected Enrolments, Responses, Evidence */}
            <div className="w-full lg:w-2/3 space-y-6">
              {/* Finding Core Overview Card */}
              <div className="bg-white rounded-2xl border border-[#CBD5E1] p-6 shadow-xs space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#E2E8F0]">
                  <div className="flex items-center gap-2">
                    {getStatusBadge(finding.status)}
                    {getSeverityBadge(finding.severity)}
                    <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-300 font-medium">
                      {finding.rule_code} (v{finding.rule_version})
                    </span>
                  </div>
                  <div className="text-xs text-[#475569] flex items-center gap-1.5 tabular-nums">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>First detected: {new Date(finding.first_detected_at).toLocaleString()}</span>
                  </div>
                </div>

                <div>
                  <h2 className="text-sm font-semibold text-[#0F2942]">Discrepancy rule explanation</h2>
                  <p className="mt-1.5 text-xs text-[#1E293B] bg-slate-50 p-4 rounded-xl border border-slate-200 leading-relaxed">
                    {finding.explanation}
                  </p>
                </div>

                {finding.resolution_rationale && (
                  <div className="p-3.5 bg-emerald-50 rounded-xl border border-emerald-200 text-xs">
                    <span className="font-semibold text-emerald-900 block mb-1">Official resolution rationale:</span>
                    <p className="text-emerald-800">{finding.resolution_rationale}</p>
                    {finding.resolved_at && (
                      <p className="mt-1 text-emerald-700 tabular-nums">Resolved at: {new Date(finding.resolved_at).toLocaleString()}</p>
                    )}
                  </div>
                )}
              </div>

              {/* Side-by-side Affected Enrolment Records */}
              <div className="bg-white rounded-2xl border border-[#CBD5E1] p-6 shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-bold text-[#0F2942] flex items-center gap-2">
                    <Layers className="w-4 h-4 text-slate-500" />
                    <span>Enrolment records in conflict</span>
                  </h2>
                  <span className="text-xs text-[#475569]">Cross-institution comparison</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Primary Record */}
                  <div className="p-4 rounded-xl border border-[#CBD5E1] bg-slate-50 space-y-3">
                    <div className="flex items-center justify-between border-b border-[#CBD5E1] pb-2">
                      <span className="text-xs font-semibold text-[#0F2942]">Institution record A</span>
                      {finding.primary_enrolment_id && (
                        <Link 
                          href={`/enrolments?search=${encodeURIComponent(finding.primary_student_name || "")}`}
                          className="text-xs text-[#1E40AF] hover:underline font-medium"
                        >
                          View in registry →
                        </Link>
                      )}
                    </div>
                    <div className="space-y-1.5 text-xs">
                      <div>
                        <span className="text-slate-500 block text-[11px]">Institution</span>
                        <span className="font-semibold text-[#0F2942]">{finding.primary_institution_name || "N/A"}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[11px]">Student full name</span>
                        <span className="font-medium text-[#1E293B]">{finding.primary_student_name || "N/A"}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[11px]">Protected APAAR ID</span>
                        <span className="text-slate-700 tabular-nums">{finding.primary_masked_apaar || "Unlinked"}</span>
                      </div>
                    </div>
                  </div>

                  {/* Secondary Record */}
                  <div className="p-4 rounded-xl border border-[#CBD5E1] bg-slate-50 space-y-3">
                    <div className="flex items-center justify-between border-b border-[#CBD5E1] pb-2">
                      <span className="text-xs font-semibold text-[#0F2942]">Institution record B</span>
                      {finding.secondary_enrolment_id && (
                        <Link 
                          href={`/enrolments?search=${encodeURIComponent(finding.secondary_student_name || "")}`}
                          className="text-xs text-[#1E40AF] hover:underline font-medium"
                        >
                          View in registry →
                        </Link>
                      )}
                    </div>
                    <div className="space-y-1.5 text-xs">
                      <div>
                        <span className="text-slate-500 block text-[11px]">Institution</span>
                        <span className="font-semibold text-[#0F2942]">{finding.secondary_institution_name || "None / Single-institution"}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[11px]">Student full name</span>
                        <span className="font-medium text-[#1E293B]">{finding.secondary_student_name || "—"}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[11px]">Protected APAAR ID</span>
                        <span className="text-slate-700 tabular-nums">{finding.secondary_masked_apaar || "—"}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Institutional Responses Thread */}
              <div className="bg-white rounded-2xl border border-[#CBD5E1] p-6 shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-bold text-[#0F2942] flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 text-slate-500" />
                    <span>Institutional explanations & dispute thread</span>
                  </h2>
                  <span className="text-xs text-[#475569]">
                    {finding.responses?.length || 0} response{(finding.responses?.length || 0) === 1 ? "" : "s"}
                  </span>
                </div>

                {finding.responses && finding.responses.length > 0 ? (
                  <div className="space-y-3">
                    {finding.responses.map((resp: FindingResponseItem) => (
                      <div key={resp.id} className="p-4 rounded-xl border border-[#CBD5E1] bg-slate-50 space-y-2 text-xs">
                        <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                          <span className="font-semibold text-[#0F2942]">{resp.institution_name || "Submitting institution"}</span>
                          <span className="text-slate-500 tabular-nums">{new Date(resp.submitted_at).toLocaleString()}</span>
                        </div>
                        <p className="text-[#1E293B] leading-relaxed">{resp.explanation}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 rounded-xl border border-dashed border-[#CBD5E1] text-xs text-slate-500 text-center bg-slate-50">
                    No institutional explanations have been submitted yet.
                  </div>
                )}
              </div>

              {/* Supporting Evidence Documents */}
              <div className="bg-white rounded-2xl border border-[#CBD5E1] p-6 shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-bold text-[#0F2942] flex items-center gap-2">
                    <FileText className="w-4 h-4 text-slate-500" />
                    <span>Uploaded verification evidence</span>
                  </h2>
                  <span className="text-xs text-[#475569]">
                    {finding.evidence_attachments?.length || 0} document{(finding.evidence_attachments?.length || 0) === 1 ? "" : "s"}
                  </span>
                </div>

                {finding.evidence_attachments && finding.evidence_attachments.length > 0 ? (
                  <div className="space-y-2">
                    {finding.evidence_attachments.map((ev: EvidenceMetadataItem) => (
                      <div key={ev.id} className="p-3.5 rounded-xl border border-[#CBD5E1] bg-slate-50 flex items-center justify-between text-xs">
                        <div>
                          <span className="font-semibold text-[#0F2942] block">{ev.original_filename}</span>
                          <span className="text-slate-500 text-[11px]">
                            {ev.evidence_category.replace(/_/g, " ").toLowerCase()} • {(ev.file_size_bytes / 1024).toFixed(1)} KB
                          </span>
                        </div>
                        <a
                          href={`/api/v1/evidence/${ev.id}`}
                          target="_blank"
                          rel="noreferrer"
                          className="btn-rounded-secondary text-xs"
                        >
                          <Download className="w-3.5 h-3.5" />
                          Download
                        </a>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 rounded-xl border border-dashed border-[#CBD5E1] text-xs text-slate-500 text-center bg-slate-50">
                    No supporting evidence documents attached to this finding.
                  </div>
                )}
              </div>
            </div>

            {/* Right Column (35%): Context Metadata & Lifecycle Workflow */}
            <div className="w-full lg:w-1/3 space-y-6">
              {/* Context Summary Card */}
              <div className="bg-white rounded-2xl border border-[#CBD5E1] p-6 shadow-xs space-y-4">
                <h2 className="text-sm font-bold text-[#0F2942] border-b border-[#E2E8F0] pb-2">Academic context</h2>
                <div className="space-y-3 text-xs">
                  <div>
                    <span className="text-slate-500 block text-[11px]">Programme context</span>
                    <span className="font-semibold text-[#0F2942]">{finding.programme_name || "General engineering / technical"}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[11px]">Academic session</span>
                    <span className="font-semibold text-[#0F2942]">{finding.academic_year_label || "2024–2025"}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[11px]">Finding category</span>
                    <span className="font-semibold text-[#0F2942]">{finding.category.toLowerCase().replace(/_/g, " ")}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[11px]">Last evaluated</span>
                    <span className="font-semibold text-[#0F2942] tabular-nums">{new Date(finding.last_detected_at).toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[11px]">Assigned reviewer</span>
                    <span className="font-semibold text-[#0F2942]">{finding.assigned_reviewer_name || "National regulatory desk (unassigned)"}</span>
                  </div>
                </div>
              </div>

              {/* Lifecycle Actions Card */}
              <div className="bg-white rounded-2xl border border-[#CBD5E1] p-6 shadow-xs space-y-4">
                <h2 className="text-sm font-bold text-[#0F2942] border-b border-[#E2E8F0] pb-2">Lifecycle management</h2>
                <p className="text-xs text-[#475569]">
                  Current status: <strong className="text-[#0F2942] capitalize">{finding.status.toLowerCase().replace(/_/g, " ")}</strong>
                </p>

                {finding.permitted_transitions && finding.permitted_transitions.length > 0 ? (
                  <div className="space-y-2 pt-1">
                    <span className="text-xs font-semibold text-[#0F2942] block">Permitted target transitions:</span>
                    <div className="flex flex-wrap gap-2">
                      {finding.permitted_transitions.map((st) => (
                        <button
                          key={st}
                          onClick={() => {
                            setTargetStatus(st);
                            setShowTransitionModal(true);
                            setTransitionError(null);
                          }}
                          className="btn-rounded-secondary text-xs capitalize"
                        >
                          {st.toLowerCase().replace(/_/g, " ")}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">No further transitions permitted from this terminal state.</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Modal: Submit Institutional Response (Clean solid overlay, no blur) */}
        {showResponseModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
            <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xl max-w-lg w-full p-6 sm:p-8 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <h3 className="text-base font-bold text-[#0F2942]">Submit institutional explanation</h3>
                <button 
                  onClick={() => setShowResponseModal(false)}
                  className="text-slate-400 hover:text-slate-600 rounded-full p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {responseError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
                  {responseError}
                </div>
              )}

              <form onSubmit={handleResponseSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-[#1E293B] mb-1">Response type</label>
                  <select
                    value={responseType}
                    onChange={(e) => setResponseType(e.target.value)}
                    className="w-full text-xs rounded-full border border-[#CBD5E1] px-4 py-2 bg-white text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                  >
                    <option value="EXPLANATION">General explanation</option>
                    <option value="TRANSFER_EVIDENCE">Transfer or withdrawal claim</option>
                    <option value="DATA_ENTRY_ERROR">Correction claim</option>
                    <option value="DISPUTE">Identity dispute</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#1E293B] mb-1">
                    Explanation statement <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    rows={4}
                    value={responseExplanation}
                    onChange={(e) => setResponseExplanation(e.target.value)}
                    placeholder="Provide a verified explanation regarding the discrepancy..."
                    className="w-full text-xs rounded-xl border border-[#CBD5E1] p-3 text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    required
                  />
                  <span className="text-[11px] text-slate-500 mt-1 block">
                    All submitted explanations are recorded in the official audit trail.
                  </span>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E2E8F0]">
                  <button
                    type="button"
                    onClick={() => setShowResponseModal(false)}
                    className="btn-rounded-secondary text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmittingResponse}
                    className="btn-rounded-primary text-xs"
                  >
                    {isSubmittingResponse ? "Submitting..." : "Record response"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Transition Lifecycle (Clean solid overlay, no blur) */}
        {showTransitionModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
            <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xl max-w-lg w-full p-6 sm:p-8 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <h3 className="text-base font-bold text-[#0F2942]">Transition finding status</h3>
                <button 
                  onClick={() => setShowTransitionModal(false)}
                  className="text-slate-400 hover:text-slate-600 rounded-full p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {transitionError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
                  {transitionError}
                </div>
              )}

              <form onSubmit={handleTransitionSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-[#1E293B] mb-1">Target state</label>
                  <select
                    value={targetStatus}
                    onChange={(e) => setTargetStatus(e.target.value)}
                    className="w-full text-xs rounded-full border border-[#CBD5E1] px-4 py-2 bg-white text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                  >
                    {finding?.permitted_transitions?.map((st) => (
                      <option key={st} value={st}>
                        {st.toLowerCase().replace(/_/g, " ")}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#1E293B] mb-1">
                    Decision rationale {["RESOLVED", "DISMISSED", "ESCALATED"].includes(targetStatus) && <span className="text-red-500">* (mandatory)</span>}
                  </label>
                  <textarea
                    rows={4}
                    value={transitionRationale}
                    onChange={(e) => setTransitionRationale(e.target.value)}
                    placeholder="Document the exact basis and verification rationale for this decision..."
                    className="w-full text-xs rounded-xl border border-[#CBD5E1] p-3 text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                  />
                  <span className="text-[11px] text-slate-500 mt-1 block">
                    A minimum of 10 characters is required for final resolution or dismissal decisions.
                  </span>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E2E8F0]">
                  <button
                    type="button"
                    onClick={() => setShowTransitionModal(false)}
                    className="btn-rounded-secondary text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmittingTransition}
                    className="btn-rounded-primary text-xs"
                  >
                    {isSubmittingTransition ? "Updating..." : "Execute transition"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Upload Supporting Evidence (Clean solid overlay, no blur) */}
        {showEvidenceModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
            <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xl max-w-lg w-full p-6 sm:p-8 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <h3 className="text-base font-bold text-[#0F2942]">Upload supporting evidence</h3>
                <button 
                  onClick={() => setShowEvidenceModal(false)}
                  className="text-slate-400 hover:text-slate-600 rounded-full p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {evidenceError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
                  {evidenceError}
                </div>
              )}

              <form onSubmit={handleEvidenceUpload} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-[#1E293B] mb-1">Evidence document category</label>
                  <select
                    value={evidenceCategory}
                    onChange={(e) => setEvidenceCategory(e.target.value)}
                    className="w-full text-xs rounded-full border border-[#CBD5E1] px-4 py-2 bg-white text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                  >
                    <option value="TRANSFER_CERTIFICATE">Transfer certificate (TC)</option>
                    <option value="MIGRATION_CERTIFICATE">Migration certificate</option>
                    <option value="ADMISSION_RECEIPT">Admission receipt / offer letter</option>
                    <option value="STUDENT_AFFIDAVIT">Student confirmation / affidavit</option>
                    <option value="CANCELLATION_NOTICE">Admission cancellation order</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#1E293B] mb-1">
                    Select file (PDF, PNG, JPG - max 10MB) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={(e) => setEvidenceFile(e.target.files?.[0] || null)}
                    className="w-full text-xs border border-[#CBD5E1] rounded-xl p-2.5 bg-slate-50"
                    required
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E2E8F0]">
                  <button
                    type="button"
                    onClick={() => setShowEvidenceModal(false)}
                    className="btn-rounded-secondary text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isUploadingEvidence}
                    className="btn-rounded-primary text-xs"
                  >
                    {isUploadingEvidence ? "Uploading..." : "Upload document"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}

export default function FindingDetailPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <React.Suspense
      fallback={
        <div className="min-h-screen bg-[#F8FAFC] p-12 text-center flex items-center justify-center">
          <div className="bg-white rounded-2xl border border-[#CBD5E1] p-8 shadow-xs">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-slate-300 border-t-[#0F2942]"></div>
            <p className="mt-3 text-xs text-[#475569]">Loading discrepancy dossier...</p>
          </div>
        </div>
      }
    >
      <FindingDetailInner params={params} />
    </React.Suspense>
  );
}
