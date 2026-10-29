"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import { api, FindingItem } from "@/lib/api";
import { useLanguage } from "@/lib/language-context";
import { useAuth } from "@/lib/auth-context";
import { 
  RefreshCw, 
  ChevronRight, 
  Building2, 
  User, 
  Clock, 
  CheckCircle2, 
  XCircle,
  FileText,
  Filter
} from "lucide-react";

export default function FindingsInboxPage() {
  const { language, t } = useLanguage();
  const { user, isLoading: isAuthLoading } = useAuth();
  const [findings, setFindings] = useState<FindingItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [isLoading, setIsLoading] = useState(true);
  const [isReconciling, setIsReconciling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [ruleCodeFilter, setRuleCodeFilter] = useState<string>("");

  const loadFindings = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.listFindings({
        page,
        page_size: pageSize,
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
        rule_code: ruleCodeFilter || undefined,
      });
      setFindings(res.items || []);
      setTotal(res.total || 0);
    } catch (err: any) {
      setError(err.message || "Failed to load findings.");
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, statusFilter, severityFilter, ruleCodeFilter]);

  useEffect(() => {
    if (!isAuthLoading && user) {
      loadFindings();
    }
  }, [loadFindings, isAuthLoading, user]);

  const handleRunReconciliation = async () => {
    setIsReconciling(true);
    setSuccessMessage(null);
    setError(null);
    try {
      const res = await api.triggerReconciliation();
      setSuccessMessage(res.message || "Enrolment discrepancy scan completed successfully.");
      await loadFindings();
    } catch (err: any) {
      setError(err.message || "Scan failed.");
    } finally {
      setIsReconciling(false);
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "CRITICAL":
        return "bg-rose-50 text-rose-800 border-rose-300";
      case "ERROR":
        return "bg-red-50 text-red-700 border-red-200";
      case "WARNING":
        return "bg-amber-50 text-amber-800 border-amber-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "OPEN":
        return "bg-amber-100 text-amber-800 border-amber-300";
      case "AWAITING_INSTITUTION_RESPONSE":
        return "bg-blue-50 text-blue-800 border-blue-200";
      case "RESPONSE_RECEIVED":
        return "bg-purple-50 text-purple-800 border-purple-200";
      case "UNDER_REVIEW":
        return "bg-indigo-50 text-indigo-800 border-indigo-200";
      case "RESOLVED":
        return "bg-emerald-50 text-emerald-800 border-emerald-200";
      case "DISMISSED":
        return "bg-slate-100 text-slate-700 border-slate-300";
      case "ESCALATED":
        return "bg-rose-50 text-rose-800 border-rose-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  const formatStatus = (s: string) => s.replace(/_/g, " ").toLowerCase();

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-6 pb-12">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#CBD5E1] pb-4">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-[#0F2942] tracking-tight">
              {language === "hi" ? "विसंगति एवं दोहरे नामांकन इनबॉक्स" : "Enrolment discrepancies & findings"}
            </h1>
            <p className="text-xs text-[#475569] mt-0.5">
              {language === "hi"
                ? "सक्रिय दोहरे नामांकन, संस्थागत विवाद एवं समाधान हेतु लंबित प्रकरण।"
                : "Active dual enrolment alerts, institutional discrepancy cases, and pending responses."}
            </p>
          </div>
          <button
            onClick={handleRunReconciliation}
            disabled={isReconciling}
            className="btn-rounded-primary text-xs disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isReconciling ? "animate-spin text-sky-300" : ""}`} />
            {isReconciling ? "Scanning enrolment records..." : "Scan for discrepancies"}
          </button>
        </div>

        {/* Notices */}
        {successMessage && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-xs text-emerald-800 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              {successMessage}
            </span>
            <button onClick={() => setSuccessMessage(null)} className="text-emerald-700 hover:text-emerald-900 text-xs font-semibold">
              Dismiss
            </button>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-800 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <XCircle className="w-4 h-4 text-red-600 shrink-0" />
              {error}
            </span>
            <button onClick={() => setError(null)} className="text-red-700 hover:text-red-900 text-xs font-semibold">
              Dismiss
            </button>
          </div>
        )}

        {/* Filter Toolbar */}
        <div className="bg-white p-4 rounded-2xl border border-[#CBD5E1] shadow-xs flex flex-wrap gap-3 items-center justify-between">
          <div className="flex flex-wrap gap-2.5 items-center flex-1">
            <div className="flex items-center gap-1.5 text-xs text-[#475569] font-medium mr-1">
              <Filter className="w-3.5 h-3.5" />
              <span>Filters:</span>
            </div>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="text-xs px-3 py-1.5 bg-slate-50 border border-[#CBD5E1] rounded-full text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
              aria-label="Filter by lifecycle status"
            >
              <option value="">All statuses</option>
              <option value="OPEN">Open</option>
              <option value="AWAITING_INSTITUTION_RESPONSE">Awaiting institution response</option>
              <option value="RESPONSE_RECEIVED">Response received</option>
              <option value="UNDER_REVIEW">Under review</option>
              <option value="RESOLVED">Resolved</option>
              <option value="DISMISSED">Dismissed</option>
              <option value="ESCALATED">Escalated</option>
            </select>

            {/* Severity Filter */}
            <select
              value={severityFilter}
              onChange={(e) => { setSeverityFilter(e.target.value); setPage(1); }}
              className="text-xs px-3 py-1.5 bg-slate-50 border border-[#CBD5E1] rounded-full text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
              aria-label="Filter by severity"
            >
              <option value="">All severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="ERROR">Error</option>
              <option value="WARNING">Warning</option>
              <option value="INFO">Info</option>
            </select>

            {/* Rule Code Filter */}
            <select
              value={ruleCodeFilter}
              onChange={(e) => { setRuleCodeFilter(e.target.value); setPage(1); }}
              className="text-xs px-3 py-1.5 bg-slate-50 border border-[#CBD5E1] rounded-full text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
              aria-label="Filter by rule code"
            >
              <option value="">All rules</option>
              <option value="DUP-001">DUP-001 (Intra-institution duplicate)</option>
              <option value="DUP-002">DUP-002 (Cross-institution active conflict)</option>
              <option value="DUP-003">DUP-003 (Potential duplicate review)</option>
              <option value="DUP-004">DUP-004 (Documented transfer / historical)</option>
            </select>
          </div>

          <div className="text-xs text-[#475569]">
            Showing <strong className="text-[#0F2942] tabular-nums">{findings.length}</strong> of <strong className="text-[#0F2942] tabular-nums">{total}</strong> findings
          </div>
        </div>

        {/* Findings Table */}
        <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xs overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center text-xs text-[#475569]">
              <div className="w-6 h-6 border-2 border-[#0F2942] border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
              Loading integrity findings...
            </div>
          ) : findings.length === 0 ? (
            <div className="p-12 text-center space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
              <p className="text-sm font-semibold text-[#0F2942]">No active discrepancies found</p>
              <p className="text-xs text-[#475569] max-w-sm mx-auto">
                No active discrepancies meet the current filter criteria. Run an integrity scan to check enrolment records.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[980px] text-left text-xs neev-table">
                <thead>
                  <tr>
                    <th className="w-48">Rule & severity</th>
                    <th className="min-w-[320px] max-w-md">Explanation</th>
                    <th className="min-w-[260px]">Involved institutions & students</th>
                    <th className="w-32">Status</th>
                    <th className="w-28">Detected</th>
                    <th className="w-32 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E2E8F0]">
                  {findings.map((f) => (
                    <tr key={f.id}>
                      <td className="align-top whitespace-nowrap w-48 cell-nowrap">
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-semibold px-2 py-0.5 bg-[#0F2942] text-white rounded-full">
                            {f.rule_code}
                          </span>
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${getSeverityBadge(f.severity)}`}>
                            {f.severity}
                          </span>
                        </div>
                        <span className="text-[11px] text-[#475569] block mt-1">v{f.rule_version} • {f.category.toLowerCase().replace(/_/g, " ")}</span>
                      </td>

                      <td className="align-top min-w-[320px] max-w-md whitespace-normal break-words cell-wrap">
                        <p className="text-xs text-[#1E293B] font-medium leading-relaxed whitespace-normal break-words">
                          {f.explanation}
                        </p>
                        {f.responses_count > 0 && (
                          <span className="inline-flex items-center gap-1 text-[11px] text-purple-700 font-semibold mt-1.5 whitespace-nowrap">
                            <FileText className="w-3 h-3" />
                            {f.responses_count} institutional response{f.responses_count > 1 ? "s" : ""}
                          </span>
                        )}
                      </td>

                      <td className="align-top min-w-[260px] text-xs space-y-1.5 whitespace-normal cell-wrap">
                        <div className="flex items-center gap-1.5 text-[#0F2942]">
                          <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                          <span className="font-semibold text-xs leading-snug" title={f.primary_institution_name || ""}>
                            {f.primary_institution_name}
                          </span>
                        </div>
                        {f.secondary_institution_name && (
                          <div className="flex items-center gap-1.5 text-[#475569]">
                            <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                            <span className="text-xs leading-snug" title={f.secondary_institution_name}>
                              {f.secondary_institution_name}
                            </span>
                          </div>
                        )}
                        {f.primary_student_name && (
                          <div className="flex items-center gap-1.5 text-[#475569] text-[11px]">
                            <User className="w-3 h-3 shrink-0" />
                            <span className="font-medium text-[#1E293B]">{f.primary_student_name}</span>
                            {f.primary_masked_apaar && <span className="tabular-nums text-slate-500">({f.primary_masked_apaar})</span>}
                          </div>
                        )}
                      </td>

                      <td className="align-top whitespace-nowrap w-32 cell-nowrap">
                        <span className={`whitespace-nowrap inline-flex items-center text-[11px] font-medium px-2.5 py-0.5 rounded-full border capitalize ${getStatusBadge(f.status)}`}>
                          {formatStatus(f.status)}
                        </span>
                      </td>

                      <td className="align-top whitespace-nowrap text-xs text-[#475569] w-28 cell-nowrap">
                        <div className="flex items-center gap-1 tabular-nums">
                          <Clock className="w-3 h-3 text-slate-400" />
                          <span>{new Date(f.last_detected_at).toLocaleDateString()}</span>
                        </div>
                      </td>

                      <td className="align-top text-right whitespace-nowrap w-32 cell-nowrap">
                        <Link
                          href={`/findings/${f.id}`}
                          className="btn-rounded-secondary text-xs"
                        >
                          View details
                          <ChevronRight className="w-3 h-3 text-slate-400" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
