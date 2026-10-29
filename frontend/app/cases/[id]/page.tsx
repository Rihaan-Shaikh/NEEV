"use client";

import React, { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import {
  api,
  AuditCaseDetail,
  AuditCaseFindingItem,
  AuditCaseEventItem,
  ClarificationRequestItem,
  AuditCaseDecisionItem,
} from "@/lib/api";
import {
  ArrowLeft,
  Building2,
  Calendar,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  UserCheck,
  UserPlus,
  Send,
  FileText,
  Lock,
  MessageSquare,
  HelpCircle,
  FileCheck,
  ExternalLink,
  ChevronRight,
  RefreshCw,
  X,
  AlertCircle
} from "lucide-react";

function CaseDetailInner({ params }: { params: Promise<{ id: string }> }) {
  const unwrappedParams = use(params);
  const router = useRouter();
  const caseId = unwrappedParams.id;

  const [auditCase, setAuditCase] = useState<AuditCaseDetail | null>(null);
  const [reviewers, setReviewers] = useState<{ id: string; display_name: string; email: string; role: string }[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"findings" | "clarifications" | "decisions" | "timeline">("findings");

  // Modals state
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [assignReviewerId, setAssignReviewerId] = useState("");
  const [assignRationale, setAssignRationale] = useState("");
  const [isAssigning, setIsAssigning] = useState(false);

  const [isTransitionModalOpen, setIsTransitionModalOpen] = useState(false);
  const [targetStatus, setTargetStatus] = useState("");
  const [transitionRationale, setTransitionRationale] = useState("");
  const [isTransitioning, setIsTransitioning] = useState(false);

  const [isNoteModalOpen, setIsNoteModalOpen] = useState(false);
  const [noteText, setNoteText] = useState("");
  const [isInternalNote, setIsInternalNote] = useState(true);
  const [isAddingNote, setIsAddingNote] = useState(false);

  const [isClarificationModalOpen, setIsClarificationModalOpen] = useState(false);
  const [clarificationSubject, setClarificationSubject] = useState("");
  const [clarificationDetails, setClarificationDetails] = useState("");
  const [clarificationDeadline, setClarificationDeadline] = useState("");
  const [isIssuingClarification, setIsIssuingClarification] = useState(false);

  const [isDecisionModalOpen, setIsDecisionModalOpen] = useState(false);
  const [decisionType, setDecisionType] = useState<"RESOLVED" | "ESCALATED" | "CLOSED_NO_ACTION">("RESOLVED");
  const [decisionRationale, setDecisionRationale] = useState("");
  const [decisionFollowUp, setDecisionFollowUp] = useState("");
  const [isRecordingDecision, setIsRecordingDecision] = useState(false);

  const [selectedClarificationId, setSelectedClarificationId] = useState<string | null>(null);
  const [responseExplanation, setResponseExplanation] = useState("");
  const [isResponding, setIsResponding] = useState(false);

  const [actionMessage, setActionMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadCase = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getCaseDetail(caseId);
      setAuditCase(data);
      if (data.permitted_transitions && data.permitted_transitions.length > 0) {
        setTargetStatus(data.permitted_transitions[0]);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load audit case workspace.");
    } finally {
      setIsLoading(false);
    }
  };

  const loadReviewers = async () => {
    try {
      const revs = await api.listReviewers();
      setReviewers(revs);
      if (revs.length > 0) {
        setAssignReviewerId(revs[0].id);
      }
    } catch {
      // Non-critical if reviewers list fails to load
    }
  };

  useEffect(() => {
    if (caseId) {
      loadCase();
      loadReviewers();
    }
  }, [caseId]);

  // Handle Assign Case
  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assignReviewerId) return;
    setIsAssigning(true);
    setActionMessage(null);
    try {
      const updated = await api.assignCase(caseId, {
        reviewer_id: assignReviewerId,
        rationale: assignRationale.trim() || undefined,
      });
      setAuditCase(updated);
      setIsAssignModalOpen(false);
      setAssignRationale("");
      setActionMessage({ type: "success", text: "Reviewer assigned successfully." });
    } catch (err: any) {
      setActionMessage({ type: "error", text: err.message || "Failed to assign case." });
    } finally {
      setIsAssigning(false);
    }
  };

  // Handle State Transition
  const handleTransition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetStatus || !transitionRationale.trim()) {
      setActionMessage({ type: "error", text: "Please provide a valid transition and rationale." });
      return;
    }
    setIsTransitioning(true);
    setActionMessage(null);
    try {
      const updated = await api.transitionCase(caseId, {
        target_status: targetStatus,
        rationale: transitionRationale.trim(),
      });
      setAuditCase(updated);
      setIsTransitionModalOpen(false);
      setTransitionRationale("");
      setActionMessage({ type: "success", text: `Case transitioned to ${targetStatus.replace(/_/g, " ")}.` });
    } catch (err: any) {
      setActionMessage({ type: "error", text: err.message || "Failed to transition case." });
    } finally {
      setIsTransitioning(false);
    }
  };

  // Handle Add Note
  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!noteText.trim()) return;
    setIsAddingNote(true);
    setActionMessage(null);
    try {
      await api.addCaseNote(caseId, {
        note: noteText.trim(),
        is_internal: isInternalNote,
      });
      setIsNoteModalOpen(false);
      setNoteText("");
      setActionMessage({ type: "success", text: "Note recorded in case timeline." });
      await loadCase();
    } catch (err: any) {
      setActionMessage({ type: "error", text: err.message || "Failed to record note." });
    } finally {
      setIsAddingNote(false);
    }
  };

  // Handle Issue Clarification Request
  const handleIssueClarification = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!clarificationSubject.trim() || !clarificationDetails.trim()) {
      setActionMessage({ type: "error", text: "Subject and instructions are required." });
      return;
    }
    setIsIssuingClarification(true);
    setActionMessage(null);
    try {
      await api.createClarificationRequest(caseId, {
        subject: clarificationSubject.trim(),
        information_requested: clarificationDetails.trim(),
        response_deadline: clarificationDeadline || undefined,
      });
      setIsClarificationModalOpen(false);
      setClarificationSubject("");
      setClarificationDetails("");
      setClarificationDeadline("");
      setActionMessage({ type: "success", text: "Clarification request issued to institution." });
      await loadCase();
    } catch (err: any) {
      setActionMessage({ type: "error", text: err.message || "Failed to issue clarification request." });
    } finally {
      setIsIssuingClarification(false);
    }
  };

  // Handle Record Decision
  const handleRecordDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (decisionRationale.trim().length < 10) {
      setActionMessage({ type: "error", text: "Decision rationale must be at least 10 characters." });
      return;
    }
    setIsRecordingDecision(true);
    setActionMessage(null);
    try {
      await api.recordCaseDecision(caseId, {
        decision_type: decisionType,
        decision_rationale: decisionRationale.trim(),
        follow_up_action: decisionFollowUp.trim() || undefined,
      });
      setIsDecisionModalOpen(false);
      setDecisionRationale("");
      setDecisionFollowUp("");
      setActionMessage({ type: "success", text: `Decision recorded: ${decisionType.replace(/_/g, " ")}.` });
      await loadCase();
    } catch (err: any) {
      setActionMessage({ type: "error", text: err.message || "Failed to record decision." });
    } finally {
      setIsRecordingDecision(false);
    }
  };

  // Handle Submit Clarification Response
  const handleSubmitResponse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClarificationId || !responseExplanation.trim()) return;
    setIsResponding(true);
    setActionMessage(null);
    try {
      await api.submitClarificationResponse(selectedClarificationId, {
        explanation: responseExplanation.trim(),
      });
      setSelectedClarificationId(null);
      setResponseExplanation("");
      setActionMessage({ type: "success", text: "Clarification response submitted successfully." });
      await loadCase();
    } catch (err: any) {
      setActionMessage({ type: "error", text: err.message || "Failed to submit response." });
    } finally {
      setIsResponding(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "OPEN":
        return <span className="px-2.5 py-1 bg-amber-50 text-amber-800 border border-amber-200 text-xs font-semibold rounded">Open</span>;
      case "ASSIGNED":
        return <span className="px-2.5 py-1 bg-blue-50 text-blue-800 border border-blue-200 text-xs font-semibold rounded">Assigned</span>;
      case "UNDER_REVIEW":
        return <span className="px-2.5 py-1 bg-indigo-50 text-indigo-800 border border-indigo-200 text-xs font-semibold rounded">Under review</span>;
      case "CLARIFICATION_REQUESTED":
        return <span className="px-2.5 py-1 bg-purple-50 text-purple-800 border border-purple-200 text-xs font-semibold rounded">Clarification requested</span>;
      case "RESPONSE_RECEIVED":
        return <span className="px-2.5 py-1 bg-teal-50 text-teal-800 border border-teal-200 text-xs font-semibold rounded">Response received</span>;
      case "RESOLVED":
        return <span className="px-2.5 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-semibold rounded">Resolved</span>;
      case "ESCALATED":
        return <span className="px-2.5 py-1 bg-red-50 text-red-800 border border-red-200 text-xs font-semibold rounded">Escalated</span>;
      case "CLOSED_NO_ACTION":
        return <span className="px-2.5 py-1 bg-neutral-100 text-neutral-800 border border-neutral-300 text-xs font-semibold rounded">Closed (no action)</span>;
      default:
        return <span className="px-2.5 py-1 bg-neutral-100 text-neutral-800 border border-neutral-300 text-xs font-semibold rounded">{status.replace(/_/g, " ")}</span>;
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case "CRITICAL":
        return <span className="px-2 py-0.5 bg-red-100 text-red-900 border border-red-300 text-[11px] font-bold rounded">Critical</span>;
      case "HIGH":
        return <span className="px-2 py-0.5 bg-orange-100 text-orange-900 border border-orange-300 text-[11px] font-bold rounded">High</span>;
      case "MEDIUM":
        return <span className="px-2 py-0.5 bg-amber-100 text-amber-900 border border-amber-300 text-[11px] font-bold rounded">Medium</span>;
      default:
        return <span className="px-2 py-0.5 bg-blue-100 text-blue-900 border border-blue-300 text-[11px] font-bold rounded">Low</span>;
    }
  };

  const isTerminal = auditCase && ["RESOLVED", "ESCALATED", "CLOSED_NO_ACTION"].includes(auditCase.status);

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center gap-2 text-xs text-[#475569]">
          <Link href="/cases" className="hover:text-[#0F2942] flex items-center gap-1 transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" />
            Audit cases
          </Link>
          <ChevronRight className="w-3 h-3 text-[#0F2942]" />
          <span className="font-semibold text-[#0F2942]">
            {auditCase ? auditCase.case_reference : "Case workspace"}
          </span>
        </div>

        {actionMessage && (
          <div
            className={`p-3.5 rounded border text-xs flex items-center justify-between ${
              actionMessage.type === "success"
                ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                : "bg-red-50 border-red-200 text-red-800"
            }`}
          >
            <div className="flex items-center gap-2">
              {actionMessage.type === "success" ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
              )}
              <span>{actionMessage.text}</span>
            </div>
            <button
              onClick={() => setActionMessage(null)}
              className="text-neutral-500 hover:text-neutral-800 text-xs font-semibold"
            >
              Dismiss
            </button>
          </div>
        )}

        {isLoading ? (
          <div className="h-64 flex items-center justify-center bg-white rounded border border-[#CBD5E1]">
            <div className="flex flex-col items-center gap-2">
              <div className="w-6 h-6 border-2 border-[#0F2942] border-t-transparent rounded-full animate-spin"></div>
              <span className="text-xs text-[#475569]">Loading case workspace...</span>
            </div>
          </div>
        ) : error || !auditCase ? (
          <div className="p-6 bg-red-50 border border-red-200 rounded text-center">
            <AlertTriangle className="w-8 h-8 text-red-600 mx-auto mb-2" />
            <h2 className="text-sm font-bold text-red-900 mb-1">Failed to load case workspace</h2>
            <p className="text-xs text-red-700 mb-4">{error || "Case not found."}</p>
            <button
              onClick={loadCase}
              className="px-3 py-1.5 bg-red-800 text-white text-xs font-semibold rounded hover:bg-red-900 transition-colors"
            >
              Retry
            </button>
          </div>
        ) : (
          <>
            {/* Case Header Card */}
            <div className="bg-white p-5 rounded border border-[#CBD5E1] shadow-xs space-y-4">
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-[#E2E8F0]">
                <div className="space-y-1">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <h1 className="text-xl font-bold text-[#0F2942] tracking-tight">
                      {auditCase.case_reference}
                    </h1>
                    {getStatusBadge(auditCase.status)}
                    {getPriorityBadge(auditCase.priority)}
                    <span className="text-xs text-[#475569] px-2 py-0.5 bg-[#F8FAFC] rounded border border-[#CBD5E1]">
                      {auditCase.case_category.replace(/_/g, " ")}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-[#475569] flex-wrap pt-1">
                    <span className="flex items-center gap-1.5">
                      <Building2 className="w-3.5 h-3.5 text-[#0F2942]" />
                      <Link
                        href={`/institutions/${auditCase.institution_id}/risk-profile`}
                        className="font-medium text-[#0F2942] hover:text-[#0F2942] underline decoration-dotted"
                      >
                        {auditCase.institution_name ? auditCase.institution_name.replace(/\[DEMO-SYNTHETIC\]/gi, "").trim() : "—"}
                      </Link>
                    </span>
                    {auditCase.programme_name && (
                      <span className="flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5 text-[#0F2942]" />
                        <span>Programme: {auditCase.programme_name}</span>
                      </span>
                    )}
                    {auditCase.academic_year_label && (
                      <span className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5 text-[#0F2942]" />
                        <span>AY: {auditCase.academic_year_label}</span>
                      </span>
                    )}
                    <span className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-[#475569]" />
                      <span>Created: {new Date(auditCase.created_at).toLocaleString()}</span>
                    </span>
                  </div>
                </div>

                {/* Case Action Buttons */}
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    onClick={() => setIsAssignModalOpen(true)}
                    className="px-3 py-1.5 border border-[#CBD5E1] bg-white hover:bg-[#F8FAFC] text-[#0F2942] text-xs font-semibold rounded flex items-center gap-1.5 transition-colors"
                  >
                    <UserPlus className="w-3.5 h-3.5 text-[#0F2942]" />
                    {auditCase.assigned_reviewer_id ? "Reassign reviewer" : "Assign reviewer"}
                  </button>

                  {!isTerminal && auditCase.permitted_transitions && auditCase.permitted_transitions.length > 0 && (
                    <button
                      onClick={() => setIsTransitionModalOpen(true)}
                      className="btn-rounded-primary text-xs"
                    >
                      <RefreshCw className="w-3.5 h-3.5 text-sky-300" />
                      Update workflow status
                    </button>
                  )}

                  <button
                    onClick={() => setIsNoteModalOpen(true)}
                    className="btn-rounded-secondary text-xs"
                  >
                    <MessageSquare className="w-3.5 h-3.5 text-slate-500" />
                    Add note
                  </button>

                  {!isTerminal && (
                    <button
                      onClick={() => setIsClarificationModalOpen(true)}
                      className="btn-rounded-secondary text-xs text-amber-900 border-amber-300 bg-amber-50"
                    >
                      <HelpCircle className="w-3.5 h-3.5 text-amber-700" />
                      Request clarification
                    </button>
                  )}

                  {!isTerminal && (
                    <button
                      onClick={() => setIsDecisionModalOpen(true)}
                      className="btn-rounded-primary text-xs bg-emerald-800 hover:bg-emerald-900"
                    >
                      <FileCheck className="w-3.5 h-3.5 text-emerald-200" />
                      Record regulatory decision
                    </button>
                  )}
                </div>
              </div>

              {/* Reviewer & Rationale Strip (Clean 2-Column Split) */}
              <div className="flex flex-col md:flex-row gap-4 pt-1 text-xs">
                <div className="w-full md:w-1/3 p-4 bg-slate-50 rounded-2xl border border-slate-200 space-y-1">
                  <span className="font-semibold text-[#475569] text-xs">
                    Assigned regulatory reviewer
                  </span>
                  <div className="flex items-center gap-2 mt-1">
                    <UserCheck className="w-4 h-4 text-[#0F2942]" />
                    <span className="font-semibold text-[#0F2942]">
                      {auditCase.assigned_reviewer_name || "Unassigned"}
                    </span>
                  </div>
                </div>

                <div className="w-full md:w-2/3 p-4 bg-slate-50 rounded-2xl border border-slate-200 space-y-1">
                  <span className="font-semibold text-[#475569] text-xs">
                    Creation rationale & scope
                  </span>
                  <p className="text-[#1E293B] leading-relaxed mt-1">
                    {auditCase.creation_rationale}
                  </p>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex border-b border-[#CBD5E1] space-x-6 text-xs font-semibold">
              <button
                onClick={() => setActiveTab("findings")}
                className={`pb-3 flex items-center gap-1.5 border-b-2 transition-colors ${
                  activeTab === "findings"
                    ? "border-[#0F2942] text-[#0F2942]"
                    : "border-transparent text-[#475569] hover:text-[#0F2942]"
                }`}
              >
                <ShieldAlert className="w-3.5 h-3.5 text-[#0F2942]" />
                Linked findings ({auditCase.findings?.length || 0})
              </button>

              <button
                onClick={() => setActiveTab("clarifications")}
                className={`pb-3 flex items-center gap-1.5 border-b-2 transition-colors ${
                  activeTab === "clarifications"
                    ? "border-[#0F2942] text-[#0F2942]"
                    : "border-transparent text-[#475569] hover:text-[#0F2942]"
                }`}
              >
                <HelpCircle className="w-3.5 h-3.5 text-[#0F2942]" />
                Clarification requests ({auditCase.clarification_requests?.length || 0})
              </button>

              <button
                onClick={() => setActiveTab("decisions")}
                className={`pb-3 flex items-center gap-1.5 border-b-2 transition-colors ${
                  activeTab === "decisions"
                    ? "border-[#0F2942] text-[#0F2942]"
                    : "border-transparent text-[#475569] hover:text-[#0F2942]"
                }`}
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Recorded decisions ({auditCase.decisions?.length || 0})
              </button>

              <button
                onClick={() => setActiveTab("timeline")}
                className={`pb-3 flex items-center gap-1.5 border-b-2 transition-colors ${
                  activeTab === "timeline"
                    ? "border-[#0F2942] text-[#0F2942]"
                    : "border-transparent text-[#475569] hover:text-[#0F2942]"
                }`}
              >
                <Clock className="w-3.5 h-3.5 text-[#475569]" />
                Audit timeline ({auditCase.events?.length || 0})
              </button>
            </div>

            {/* TAB 1: LINKED FINDINGS */}
            {activeTab === "findings" && (
              <div className="bg-white rounded border border-[#CBD5E1] shadow-xs overflow-hidden">
                <div className="p-4 border-b border-[#CBD5E1] bg-[#F8FAFC] flex items-center justify-between">
                  <div>
                    <h2 className="text-xs font-bold text-[#0F2942] ">
                      Canonical integrity findings linked to this case
                    </h2>
                    <p className="text-[11px] text-[#475569] mt-0.5">
                      Deterministic discrepancy items from the integrity ledger requiring regulatory verification.
                    </p>
                  </div>
                </div>

                {auditCase.findings && auditCase.findings.length > 0 ? (
                  <div className="divide-y divide-[#E2E8F0]">
                    {auditCase.findings.map((f: AuditCaseFindingItem) => (
                      <div key={f.id} className="p-4 hover:bg-[#F8FAFC] transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                        <div className="space-y-1 max-w-3xl">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-[#0F2942] tabular-nums text-[11px] px-2 py-0.5 bg-neutral-100 rounded border border-neutral-300">
                              {f.rule_code}
                            </span>
                            <span className="px-2 py-0.5 bg-red-50 text-red-800 border border-red-200 text-[10px] font-bold rounded">
                              {f.severity}
                            </span>
                            <span className="px-2 py-0.5 bg-neutral-100 text-neutral-800 border border-neutral-300 text-[10px] rounded">
                              {f.status}
                            </span>
                          </div>
                          <p className="text-[#0F2942] font-medium leading-relaxed">
                            {f.explanation}
                          </p>
                          <span className="text-[11px] text-[#475569] block">
                            Linked at: {new Date(f.linked_at).toLocaleString()}
                          </span>
                        </div>
                        <div className="shrink-0">
                          <Link
                            href={`/findings/${f.finding_id}`}
                            className="px-3 py-1.5 border border-[#CBD5E1] hover:bg-white text-[#0F2942] text-xs font-semibold rounded flex items-center gap-1 shadow-xs transition-colors"
                          >
                            <span>Inspect finding</span>
                            <ExternalLink className="w-3 h-3 text-[#0F2942]" />
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center text-xs text-[#475569]">
                    No specific findings linked directly. This case was initiated under general programme/institutional review.
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: CLARIFICATION REQUESTS */}
            {activeTab === "clarifications" && (
              <div className="space-y-4">
                <div className="bg-white rounded border border-[#CBD5E1] shadow-xs overflow-hidden">
                  <div className="p-4 border-b border-[#CBD5E1] bg-[#F8FAFC] flex items-center justify-between">
                    <div>
                      <h2 className="text-xs font-bold text-[#0F2942] ">
                        Institutional clarification requests & responses
                      </h2>
                      <p className="text-[11px] text-[#475569] mt-0.5">
                        Authorized regulatory communications dispatched to the institution and recorded in the audit dossier.
                      </p>
                    </div>
                  </div>

                  {auditCase.clarification_requests && auditCase.clarification_requests.length > 0 ? (
                    <div className="divide-y divide-[#E2E8F0]">
                      {auditCase.clarification_requests.map((cr: ClarificationRequestItem) => (
                        <div key={cr.id} className="p-5 space-y-4">
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-[#E2E8F0]">
                            <div className="flex items-center gap-2">
                              <span className="font-bold tabular-nums text-xs text-[#0F2942] px-2 py-0.5 bg-[#F8FAFC] rounded border border-[#CBD5E1]">
                                {cr.request_reference}
                              </span>
                              <span className="font-semibold text-sm text-[#0F2942]">
                                {cr.subject}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 text-xs">
                              <span className={`px-2.5 py-0.5 rounded font-semibold text-[11px] border ${
                                cr.status === "RESPONSE_RECEIVED"
                                  ? "bg-teal-50 text-teal-800 border-teal-200"
                                  : cr.status === "PENDING_RESPONSE"
                                  ? "bg-purple-50 text-purple-800 border-purple-200"
                                  : "bg-neutral-100 text-neutral-800 border-neutral-300"
                              }`}>
                                {cr.status.replace(/_/g, " ")}
                              </span>
                              {cr.response_deadline && (
                                <span className="text-[#475569] text-[11px]">
                                  Deadline: {new Date(cr.response_deadline).toLocaleDateString()}
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="p-3.5 bg-[#F8FAFC] rounded border border-[#E2E8F0] text-xs space-y-1">
                            <span className="font-semibold text-[#475569] text-[10px]  block">
                              Information requested by officer ({cr.issuing_officer_name || "Regulatory officer"})
                            </span>
                            <p className="text-[#0F2942] whitespace-pre-line leading-relaxed">
                              {cr.information_requested}
                            </p>
                          </div>

                          {/* Response Section */}
                          {cr.status === "RESPONSE_RECEIVED" ? (
                            <div className="p-3.5 bg-teal-50/50 rounded border border-teal-200 text-xs space-y-2">
                              <div className="flex items-center justify-between text-[11px] text-teal-900 font-semibold">
                                <span className="flex items-center gap-1.5">
                                  <CheckCircle2 className="w-3.5 h-3.5 text-teal-700" />
                                  Institution response submitted by {cr.responded_by_user_name || "Institution officer"}
                                </span>
                                <span>{cr.responded_at ? new Date(cr.responded_at).toLocaleString() : ""}</span>
                              </div>
                              <p className="text-teal-950 leading-relaxed whitespace-pre-line bg-white p-3 rounded border border-teal-200/60">
                                {cr.response_explanation}
                              </p>
                            </div>
                          ) : (
                            <div className="flex items-center justify-between pt-1">
                              <span className="text-[11px] text-amber-800 font-medium">
                                Awaiting formal institutional clarification response.
                              </span>
                              <button
                                onClick={() => {
                                  setSelectedClarificationId(cr.id);
                                  setResponseExplanation("");
                                }}
                                className="btn-rounded-primary text-xs"
                              >
                                <Send className="w-3.5 h-3.5 text-white" />
                                Submit institutional response
                              </button>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-8 text-center text-xs text-[#475569]">
                      No clarification requests have been issued for this case.
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 3: REGULATORY DECISIONS */}
            {activeTab === "decisions" && (
              <div className="bg-white rounded border border-[#CBD5E1] shadow-xs overflow-hidden">
                <div className="p-4 border-b border-[#CBD5E1] bg-[#F8FAFC] flex items-center justify-between">
                  <div>
                    <h2 className="text-xs font-bold text-[#0F2942] ">
                      Authoritative regulatory decisions
                    </h2>
                    <p className="text-[11px] text-[#475569] mt-0.5">
                      Immutable review determinations with formal rationale recorded by authorized officers.
                    </p>
                  </div>
                </div>

                {auditCase.decisions && auditCase.decisions.length > 0 ? (
                  <div className="divide-y divide-[#E2E8F0]">
                    {auditCase.decisions.map((d: AuditCaseDecisionItem) => (
                      <div key={d.id} className="p-5 space-y-3">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-[#E2E8F0]">
                          <div className="flex items-center gap-2">
                            <span className={`px-2.5 py-1 text-xs font-bold rounded border ${
                              d.decision_type === "RESOLVED"
                                ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                                : d.decision_type === "ESCALATED"
                                ? "bg-red-50 text-red-800 border-red-200"
                                : "bg-neutral-100 text-neutral-800 border-neutral-300"
                            }`}>
                              Decision: {d.decision_type.replace(/_/g, " ")}
                            </span>
                            <span className="text-xs text-[#475569]">
                              Recorded by: <strong className="text-[#0F2942]">{d.reviewer_name || "Regulatory officer"}</strong>
                            </span>
                          </div>
                          <span className="text-[11px] text-[#475569]">
                            {new Date(d.decided_at).toLocaleString()}
                          </span>
                        </div>

                        <div className="p-3 bg-[#F8FAFC] rounded border border-[#E2E8F0] text-xs space-y-1">
                          <span className="font-semibold text-[#475569] text-[10px]  block">
                            Decision rationale
                          </span>
                          <p className="text-[#0F2942] whitespace-pre-line leading-relaxed">
                            {d.decision_rationale}
                          </p>
                        </div>

                        {d.follow_up_action && (
                          <div className="text-xs text-[#475569] flex items-center gap-1.5 pt-1">
                            <strong className="text-[#0F2942]">Mandated follow-up action:</strong>
                            <span>{d.follow_up_action}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center text-xs text-[#475569]">
                    No formal regulatory decisions have been recorded for this case yet.
                  </div>
                )}
              </div>
            )}

            {/* TAB 4: AUDIT TIMELINE */}
            {activeTab === "timeline" && (
              <div className="bg-white rounded border border-[#CBD5E1] shadow-xs overflow-hidden">
                <div className="p-4 border-b border-[#CBD5E1] bg-[#F8FAFC]">
                  <h2 className="text-xs font-bold text-[#0F2942] ">
                    Full case audit event stream
                  </h2>
                  <p className="text-[11px] text-[#475569] mt-0.5">
                    Immutable chronological record of all state transitions, reviewer notes, and case communications.
                  </p>
                </div>

                {auditCase.events && auditCase.events.length > 0 ? (
                  <div className="p-5 space-y-4">
                    {auditCase.events.map((ev: AuditCaseEventItem) => (
                      <div key={ev.id} className="flex items-start gap-3 text-xs">
                        <div className="mt-0.5 shrink-0">
                          {ev.is_internal ? (
                            <span className="w-6 h-6 rounded-full bg-amber-100 flex items-center justify-center border border-amber-300">
                              <Lock className="w-3 h-3 text-amber-800" />
                            </span>
                          ) : (
                            <span className="w-6 h-6 rounded-full bg-[#F8FAFC] flex items-center justify-center border border-[#CBD5E1]">
                              <Clock className="w-3 h-3 text-[#0F2942]" />
                            </span>
                          )}
                        </div>

                        <div className="flex-1 p-3.5 bg-[#F8FAFC] rounded border border-[#E2E8F0] space-y-1.5">
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-[#0F2942]">
                                {ev.event_type.replace(/_/g, " ")}
                              </span>
                              {ev.is_internal && (
                                <span className="px-1.5 py-0.2 bg-amber-100 text-amber-900 border border-amber-300 rounded text-[10px] font-bold">
                                  Confidential internal
                                </span>
                              )}
                              {ev.from_status && ev.to_status && (
                                <span className="text-[11px] text-[#475569] tabular-nums">
                                  ({ev.from_status} → {ev.to_status})
                                </span>
                              )}
                            </div>
                            <span className="text-[11px] text-[#475569]">
                              {new Date(ev.created_at).toLocaleString()}
                            </span>
                          </div>

                          <p className="text-[#0F2942] leading-relaxed whitespace-pre-line">
                            {ev.description}
                          </p>

                          <div className="text-[11px] text-[#475569]">
                            Actor: <strong className="text-[#0F2942]">{ev.actor_name || "System"}</strong>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center text-xs text-[#475569]">
                    No events logged.
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* ================= MODALS ================= */}

        {/* 1. Assign Reviewer Modal */}
        {isAssignModalOpen && (
          <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded border border-[#CBD5E1] shadow-lg max-w-md w-full p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <h3 className="text-sm font-bold text-[#0F2942]">
                  Assign regulatory reviewer
                </h3>
                <button
                  onClick={() => setIsAssignModalOpen(false)}
                  className="text-neutral-400 hover:text-neutral-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleAssign} className="space-y-4 text-xs">
                <div>
                  <label className="block font-semibold text-[#0F2942] mb-1">
                    Select reviewer <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={assignReviewerId}
                    onChange={(e) => setAssignReviewerId(e.target.value)}
                    className="w-full px-3 py-2 border border-[#CBD5E1] rounded text-xs bg-white text-[#0F2942] focus:outline-hidden focus:border-[#0F2942]"
                    required
                  >
                    <option value="">Select an active reviewer...</option>
                    {reviewers.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.display_name} ({r.role})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-[#0F2942] mb-1">
                    Assignment rationale (optional)
                  </label>
                  <textarea
                    value={assignRationale}
                    onChange={(e) => setAssignRationale(e.target.value)}
                    placeholder="Enter reason for assignment or reassignment..."
                    rows={3}
                    className="w-full px-3 py-2 border border-[#CBD5E1] rounded text-xs text-[#0F2942] focus:outline-hidden focus:border-[#0F2942]"
                  />
                </div>

                <div className="flex justify-end gap-2.5 pt-3 border-t border-[#E2E8F0]">
                  <button
                    type="button"
                    onClick={() => setIsAssignModalOpen(false)}
                    className="btn-rounded-secondary text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isAssigning || !assignReviewerId}
                    className="btn-rounded-primary text-xs disabled:opacity-50"
                  >
                    {isAssigning ? "Assigning..." : "Confirm assignment"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* 2. Transition Workflow Modal */}
        {isTransitionModalOpen && (
          <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded border border-[#CBD5E1] shadow-lg max-w-md w-full p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <h3 className="text-sm font-bold text-[#0F2942]">
                  Update workflow status
                </h3>
                <button
                  onClick={() => setIsTransitionModalOpen(false)}
                  className="text-neutral-400 hover:text-neutral-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleTransition} className="space-y-4 text-xs">
                <div>
                  <label className="block font-semibold text-[#0F2942] mb-1">
                    Target workflow status <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={targetStatus}
                    onChange={(e) => setTargetStatus(e.target.value)}
                    className="w-full px-3 py-2 border border-[#CBD5E1] rounded text-xs bg-white text-[#0F2942] focus:outline-hidden focus:border-[#0F2942]"
                    required
                  >
                    {auditCase?.permitted_transitions?.map((st) => (
                      <option key={st} value={st}>
                        {st.replace(/_/g, " ")}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-[#0F2942] mb-1">
                    Status transition rationale <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={transitionRationale}
                    onChange={(e) => setTransitionRationale(e.target.value)}
                    placeholder="Provide justification for moving to this status..."
                    rows={3}
                    className="w-full px-3 py-2 border border-[#CBD5E1] rounded text-xs text-[#0F2942] focus:outline-hidden focus:border-[#0F2942]"
                    required
                  />
                </div>

                <div className="flex justify-end gap-2.5 pt-3 border-t border-[#E2E8F0]">
                  <button
                    type="button"
                    onClick={() => setIsTransitionModalOpen(false)}
                    className="btn-rounded-secondary text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isTransitioning || !transitionRationale.trim()}
                    className="btn-rounded-primary text-xs disabled:opacity-50"
                  >
                    {isTransitioning ? "Updating..." : "Execute transition"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* 3. Add Note Modal */}
        {isNoteModalOpen && (
          <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded border border-[#CBD5E1] shadow-lg max-w-md w-full p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <h3 className="text-sm font-bold text-[#0F2942]">
                  Record reviewer note
                </h3>
                <button
                  onClick={() => setIsNoteModalOpen(false)}
                  className="text-neutral-400 hover:text-neutral-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleAddNote} className="space-y-4 text-xs">
                <div>
                  <label className="block font-semibold text-[#0F2942] mb-1">
                    Note content <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                    placeholder="Enter observation, audit note, or review comment..."
                    rows={4}
                    className="w-full px-3 py-2 border border-[#CBD5E1] rounded text-xs text-[#0F2942] focus:outline-hidden focus:border-[#0F2942]"
                    required
                  />
                </div>

                <div className="flex items-center gap-2 p-2.5 bg-[#F8FAFC] rounded border border-[#E2E8F0]">
                  <input
                    type="checkbox"
                    id="isInternalCheck"
                    checked={isInternalNote}
                    onChange={(e) => setIsInternalNote(e.target.checked)}
                    className="rounded border-[#CBD5E1] text-[#0F2942] focus:ring-0"
                  />
                  <label htmlFor="isInternalCheck" className="font-semibold text-[#0F2942] cursor-pointer">
                    Confidential internal note (hidden from institution)
                  </label>
                </div>

                <div className="flex justify-end gap-2.5 pt-3 border-t border-[#E2E8F0]">
                  <button
                    type="button"
                    onClick={() => setIsNoteModalOpen(false)}
                    className="btn-rounded-secondary text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isAddingNote || !noteText.trim()}
                    className="btn-rounded-primary text-xs disabled:opacity-50"
                  >
                    {isAddingNote ? "Recording..." : "Record note"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* 4. Issue Clarification Request Modal */}
        {isClarificationModalOpen && (
          <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded border border-[#CBD5E1] shadow-lg max-w-lg w-full p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <h3 className="text-sm font-bold text-[#0F2942]">
                  Issue institutional clarification request
                </h3>
                <button
                  onClick={() => setIsClarificationModalOpen(false)}
                  className="text-neutral-400 hover:text-neutral-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleIssueClarification} className="space-y-4 text-xs">
                <div>
                  <label className="block font-semibold text-[#0F2942] mb-1">
                    Subject <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={clarificationSubject}
                    onChange={(e) => setClarificationSubject(e.target.value)}
                    placeholder="e.g. Discrepancy explanation for approved intake mismatch"
                    className="w-full px-3 py-2 border border-[#CBD5E1] rounded text-xs text-[#0F2942] focus:outline-hidden focus:border-[#0F2942]"
                    required
                  />
                </div>

                <div>
                  <label className="block font-semibold text-[#0F2942] mb-1">
                    Information requested & instructions <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={clarificationDetails}
                    onChange={(e) => setClarificationDetails(e.target.value)}
                    placeholder="Specify exactly what evidence, explanation, or reconciliation documents are required..."
                    rows={4}
                    className="w-full px-3 py-2 border border-[#CBD5E1] rounded text-xs text-[#0F2942] focus:outline-hidden focus:border-[#0F2942]"
                    required
                  />
                </div>

                <div>
                  <label className="block font-semibold text-[#0F2942] mb-1">
                    Response deadline (optional)
                  </label>
                  <input
                    type="date"
                    value={clarificationDeadline}
                    onChange={(e) => setClarificationDeadline(e.target.value)}
                    className="w-full px-3 py-2 border border-[#CBD5E1] rounded text-xs text-[#0F2942] focus:outline-hidden focus:border-[#0F2942]"
                  />
                </div>

                <div className="flex justify-end gap-2.5 pt-3 border-t border-[#E2E8F0]">
                  <button
                    type="button"
                    onClick={() => setIsClarificationModalOpen(false)}
                    className="btn-rounded-secondary text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isIssuingClarification || !clarificationSubject.trim() || !clarificationDetails.trim()}
                    className="btn-rounded-primary text-xs disabled:opacity-50"
                  >
                    {isIssuingClarification ? "Issuing..." : "Issue clarification request"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* 5. Record Decision Modal */}
        {isDecisionModalOpen && (
          <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded border border-[#CBD5E1] shadow-lg max-w-lg w-full p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <h3 className="text-sm font-bold text-[#0F2942]">
                  Record regulatory case decision
                </h3>
                <button
                  onClick={() => setIsDecisionModalOpen(false)}
                  className="text-neutral-400 hover:text-neutral-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleRecordDecision} className="space-y-4 text-xs">
                <div>
                  <label className="block font-semibold text-[#0F2942] mb-1">
                    Decision outcome <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={decisionType}
                    onChange={(e) => setDecisionType(e.target.value as any)}
                    className="w-full px-3 py-2 border border-[#CBD5E1] rounded text-xs bg-white text-[#0F2942] focus:outline-hidden focus:border-[#0F2942]"
                    required
                  >
                    <option value="RESOLVED">Resolved (Satisfactory evidence received)</option>
                    <option value="ESCALATED">Escalated (Referred for formal regulatory committee)</option>
                    <option value="CLOSED_NO_ACTION">Closed no action (No further compliance action required)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-[#0F2942] mb-1">
                    Decision rationale <span className="text-red-500">* (at least 10 characters)</span>
                  </label>
                  <textarea
                    value={decisionRationale}
                    onChange={(e) => setDecisionRationale(e.target.value)}
                    placeholder="Enter formal justification and review findings that substantiate this decision..."
                    rows={4}
                    className="w-full px-3 py-2 border border-[#CBD5E1] rounded text-xs text-[#0F2942] focus:outline-hidden focus:border-[#0F2942]"
                    required
                  />
                </div>

                <div>
                  <label className="block font-semibold text-[#0F2942] mb-1">
                    Mandated follow-up action (optional)
                  </label>
                  <input
                    type="text"
                    value={decisionFollowUp}
                    onChange={(e) => setDecisionFollowUp(e.target.value)}
                    placeholder="e.g. Re-verification required in next academic cycle"
                    className="w-full px-3 py-2 border border-[#CBD5E1] rounded text-xs text-[#0F2942] focus:outline-hidden focus:border-[#0F2942]"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2 border-t border-[#E2E8F0]">
                  <button
                    type="button"
                    onClick={() => setIsDecisionModalOpen(false)}
                    className="px-3 py-1.5 border border-[#CBD5E1] text-[#0F2942] text-xs font-semibold rounded hover:bg-[#F8FAFC]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isRecordingDecision || decisionRationale.trim().length < 10}
                    className="px-4 py-1.5 bg-emerald-800 text-white text-xs font-semibold rounded hover:bg-emerald-900 disabled:opacity-50"
                  >
                    {isRecordingDecision ? "Recording..." : "Record formal decision"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* 6. Clarification Response Modal */}
        {selectedClarificationId && (
          <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded border border-[#CBD5E1] shadow-lg max-w-lg w-full p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <h3 className="text-sm font-bold text-[#0F2942]">
                  Submit institutional response
                </h3>
                <button
                  onClick={() => setSelectedClarificationId(null)}
                  className="text-neutral-400 hover:text-neutral-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleSubmitResponse} className="space-y-4 text-xs">
                <div>
                  <label className="block font-semibold text-[#0F2942] mb-1">
                    Formal explanation <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={responseExplanation}
                    onChange={(e) => setResponseExplanation(e.target.value)}
                    placeholder="Enter the official response on behalf of the institution..."
                    rows={5}
                    className="w-full px-3 py-2 border border-[#CBD5E1] rounded text-xs text-[#0F2942] focus:outline-hidden focus:border-[#0F2942]"
                    required
                  />
                </div>

                <div className="flex justify-end gap-2.5 pt-3 border-t border-[#E2E8F0]">
                  <button
                    type="button"
                    onClick={() => setSelectedClarificationId(null)}
                    className="btn-rounded-secondary text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isResponding || !responseExplanation.trim()}
                    className="btn-rounded-primary text-xs disabled:opacity-50"
                  >
                    {isResponding ? "Submitting..." : "Submit response"}
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

export default function CaseDetailPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <React.Suspense
      fallback={
        <div className="min-h-screen bg-[#F8FAFC] p-12 text-center flex items-center justify-center">
          <div className="bg-white rounded border border-[#CBD5E1] p-8 shadow-xs">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-[#CBD5E1] border-t-[#0F2942]"></div>
            <p className="mt-3 text-xs text-[#475569]">Loading case workspace...</p>
          </div>
        </div>
      }
    >
      <CaseDetailInner params={params} />
    </React.Suspense>
  );
}
