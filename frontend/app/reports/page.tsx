"use client";

import React, { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import {
  api,
  ReportDefinition,
  ReportJobItem
} from "@/lib/api";
import {
  FileSpreadsheet,
  Download,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Building2,
  ShieldCheck,
  ArrowRight,
  X,
  AlertCircle
} from "lucide-react";

export default function ReportsPage() {
  const [definitions, setDefinitions] = useState<ReportDefinition[]>([]);
  const [jobs, setJobs] = useState<ReportJobItem[]>([]);
  const [institutions, setInstitutions] = useState<{ id: string; name: string; official_institution_code: string }[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshingJobs, setIsRefreshingJobs] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Generate Report Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedDefinition, setSelectedDefinition] = useState<ReportDefinition | null>(null);
  const [institutionId, setInstitutionId] = useState("");
  const [stateCode, setStateCode] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [defsData, jobsData, instsData] = await Promise.all([
        api.listReportDefinitions(),
        api.listReportJobs(),
        api.listInstitutions({ page_size: 100 })
      ]);
      setDefinitions(defsData);
      setJobs(jobsData);
      setInstitutions(instsData.items || []);
    } catch (err: any) {
      setError(err.message || "Failed to load reports catalog.");
    } finally {
      setIsLoading(false);
    }
  };

  const refreshJobs = async () => {
    setIsRefreshingJobs(true);
    try {
      const jobsData = await api.listReportJobs();
      setJobs(jobsData);
    } catch {
      // Non-blocking refresh
    } finally {
      setIsRefreshingJobs(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      refreshJobs();
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleOpenGenerateModal = (def: ReportDefinition) => {
    setSelectedDefinition(def);
    setInstitutionId("");
    setStateCode("");
    setDateFrom("");
    setDateTo("");
    setModalError(null);
    setIsModalOpen(true);
  };

  const handleGenerateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDefinition) return;

    if (selectedDefinition.requires_institution_scope && !institutionId) {
      setModalError("This report requires selecting a specific institution.");
      return;
    }

    setIsSubmitting(true);
    setModalError(null);
    try {
      const job = await api.createReportJob({
        report_type: selectedDefinition.report_type,
        institution_id: institutionId || undefined,
        state: stateCode.trim().toUpperCase() || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      });

      setIsModalOpen(false);
      setNotification({
        type: "success",
        text: `Report generation job for "${selectedDefinition.title}" queued successfully.`,
      });
      setJobs((prev) => [job, ...prev]);
    } catch (err: any) {
      setModalError(err.message || "Failed to initiate report job.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return (
          <span className="whitespace-nowrap inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-semibold rounded-full">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            Completed
          </span>
        );
      case "RUNNING":
        return (
          <span className="whitespace-nowrap inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-blue-50 text-blue-800 border border-blue-200 text-xs font-semibold rounded-full">
            <RefreshCw className="w-3.5 h-3.5 text-blue-600 animate-spin shrink-0" />
            Running
          </span>
        );
      case "QUEUED":
        return (
          <span className="whitespace-nowrap inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-amber-50 text-amber-800 border border-amber-200 text-xs font-semibold rounded-full">
            <Clock className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            Queued
          </span>
        );
      case "FAILED":
        return (
          <span className="whitespace-nowrap inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-red-50 text-red-800 border border-red-200 text-xs font-semibold rounded-full">
            <AlertTriangle className="w-3.5 h-3.5 text-red-600 shrink-0" />
            Failed
          </span>
        );
      default:
        return (
          <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 bg-slate-100 text-[#1E293B] border border-[#CBD5E1] text-xs font-semibold rounded-full">
            {status}
          </span>
        );
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Title and Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-[#0F2942] tracking-tight">
              Regulatory reporting center
            </h1>
            <p className="text-xs text-[#475569] mt-0.5">
              Authorized regulatory reports and compliance data exports.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={refreshJobs}
              disabled={isRefreshingJobs}
              className="btn-rounded-secondary text-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-[#0F2942] ${isRefreshingJobs ? "animate-spin" : ""}`} />
              Refresh job status
            </button>
          </div>
        </div>

        {notification && (
          <div
            className={`p-3.5 rounded-2xl border text-xs flex items-center justify-between ${
              notification.type === "success"
                ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                : "bg-red-50 border-red-200 text-red-800"
            }`}
          >
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{notification.text}</span>
            </div>
            <button
              onClick={() => setNotification(null)}
              className="text-slate-500 hover:text-slate-800 font-semibold text-xs"
            >
              Dismiss
            </button>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-800 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={loadData} className="underline font-semibold hover:text-red-950">
              Retry
            </button>
          </div>
        )}

        {/* Section 1: Recent Report Jobs */}
        <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xs overflow-hidden">
          <div className="p-4 border-b border-[#CBD5E1] bg-slate-50 flex items-center justify-between">
            <div>
              <h2 className="text-xs font-bold text-[#0F2942]">
                Recent report generation jobs
              </h2>
              <p className="text-[11px] text-[#475569] mt-0.5">
                Real-time status of generated CSV artifacts with tenant-isolated downloads.
              </p>
            </div>
            <span className="text-[11px] text-[#475569]">
              {jobs.length} {jobs.length === 1 ? "job" : "jobs"} logged
            </span>
          </div>

          {isLoading ? (
            <div className="p-8 text-center text-xs text-[#475569]">
              <div className="w-5 h-5 border-2 border-[#0F2942] border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
              Loading report jobs from database...
            </div>
          ) : jobs.length === 0 ? (
            <div className="p-8 text-center text-xs text-[#475569]">
              No report generation jobs initiated yet. Select a report definition below to generate one.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs neev-table">
                <thead>
                  <tr>
                    <th>Report title</th>
                    <th>Scope</th>
                    <th>Status</th>
                    <th className="text-right">Rows</th>
                    <th className="text-right">File size</th>
                    <th>Requested at</th>
                    <th className="text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E2E8F0]">
                  {jobs.map((job) => (
                    <tr key={job.id}>
                      <td className="font-semibold text-[#0F2942]">
                        <div className="flex items-center gap-2">
                          <FileSpreadsheet className="w-4 h-4 text-[#0F2942] shrink-0" />
                          <span>{job.report_title}</span>
                        </div>
                      </td>
                      <td className="text-[#475569]">
                        {job.institution_name ? (
                          <span className="flex items-center gap-1 font-medium text-[#0F2942]">
                            <Building2 className="w-3.5 h-3.5 text-[#0F2942]" />
                            {job.institution_name}
                          </span>
                        ) : (
                          <span className="text-[11px] px-2 py-0.5 bg-slate-100 rounded-full text-slate-700 font-medium">
                            National aggregate
                          </span>
                        )}
                      </td>
                      <td>
                        {getStatusBadge(job.status)}
                      </td>
                      <td className="text-right tabular-nums text-[#0F2942] font-semibold">
                        {job.row_count !== null && job.row_count !== undefined ? job.row_count.toLocaleString() : "—"}
                      </td>
                      <td className="text-right text-[#475569] tabular-nums text-[11px]">
                        {job.file_size_bytes ? `${(job.file_size_bytes / 1024).toFixed(1)} KB` : "—"}
                      </td>
                      <td className="text-[#475569] text-[11px]">
                        {new Date(job.created_at).toLocaleString()}
                      </td>
                      <td className="text-right">
                        {job.status === "COMPLETED" ? (
                          <a
                            href={api.getReportDownloadUrl(job.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn-rounded-primary text-xs py-1 px-3.5"
                          >
                            <Download className="w-3.5 h-3.5 text-white" />
                            Download CSV
                          </a>
                        ) : job.status === "FAILED" ? (
                          <span
                            title={job.error_message || "Generation error"}
                            className="text-[11px] text-red-600 font-semibold cursor-help underline decoration-dotted"
                          >
                            Error details
                          </span>
                        ) : (
                          <span className="text-[11px] text-[#475569]">Processing...</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Section 2: Catalog of Available Reports */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-[#0F2942]">
                Regulatory report catalogue
              </h2>
              <p className="text-xs text-[#475569] mt-0.5">
                Deterministic compliance and intake reports approved under regulatory verification guidelines.
              </p>
            </div>
          </div>

          {isLoading ? (
            <div className="h-48 flex items-center justify-center bg-white rounded-2xl border border-[#CBD5E1]">
              <div className="w-5 h-5 border-2 border-[#0F2942] border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {definitions.map((def) => (
                <div
                  key={def.report_type}
                  className="bg-white p-5 rounded-2xl border border-[#CBD5E1] shadow-xs flex flex-col justify-between hover:border-[#0F2942] transition-colors"
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2.5">
                        <FileSpreadsheet className="w-4 h-4 text-[#0F2942] shrink-0" />
                        <h3 className="text-xs font-bold text-[#0F2942]">
                          {def.title}
                        </h3>
                      </div>
                      <span className="px-2.5 py-0.5 bg-slate-100 text-[#475569] border border-[#CBD5E1] text-[10px] font-medium rounded-full shrink-0">
                        CSV
                      </span>
                    </div>

                    <p className="text-xs text-[#475569] leading-relaxed">
                      {def.description}
                    </p>
                  </div>

                  <div className="pt-4 mt-3 border-t border-[#E2E8F0] flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] px-2 py-0.5 bg-slate-100 text-slate-700 rounded-full border border-slate-200">
                        {def.data_classification}
                      </span>
                      {def.requires_institution_scope && (
                        <span className="text-[10px] px-2 py-0.5 bg-amber-50 text-amber-800 rounded-full border border-amber-200">
                          Institution scope required
                        </span>
                      )}
                    </div>

                    <button
                      onClick={() => handleOpenGenerateModal(def)}
                      className="btn-rounded-primary text-xs py-1 px-3.5"
                    >
                      <span>Generate</span>
                      <ArrowRight className="w-3.5 h-3.5 text-white" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Generate Report Modal */}
        {isModalOpen && selectedDefinition && (
          <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xl max-w-lg w-full p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <div className="flex items-center gap-2">
                  <FileSpreadsheet className="w-4 h-4 text-[#0F2942]" />
                  <h3 className="text-sm font-bold text-[#0F2942]">
                    Generate {selectedDefinition.title}
                  </h3>
                </div>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="w-7 h-7 rounded-full flex items-center justify-center hover:bg-slate-100 text-[#475569] hover:text-[#0F2942]"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {modalError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
                  <span>{modalError}</span>
                </div>
              )}

              <form onSubmit={handleGenerateReport} className="space-y-4 text-xs">
                <div>
                  <label className="block font-semibold text-[#0F2942] mb-1">
                    Report scope & institution {selectedDefinition.requires_institution_scope && <span className="text-red-500">*</span>}
                  </label>
                  <select
                    value={institutionId}
                    onChange={(e) => setInstitutionId(e.target.value)}
                    className="w-full px-3.5 py-2 border border-[#CBD5E1] rounded-full text-xs bg-slate-50 text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    required={selectedDefinition.requires_institution_scope}
                  >
                    <option value="">
                      {selectedDefinition.requires_institution_scope
                        ? "Select an institution (required)..."
                        : "All authorized institutions (National aggregate)"}
                    </option>
                    {institutions.map((inst) => (
                      <option key={inst.id} value={inst.id}>
                        {inst.name} ({inst.official_institution_code})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-semibold text-[#0F2942] mb-1">
                      State code (optional)
                    </label>
                    <input
                      type="text"
                      maxLength={2}
                      value={stateCode}
                      onChange={(e) => setStateCode(e.target.value)}
                      placeholder="e.g. DL, MH, KA"
                      className="w-full px-4 py-2 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] uppercase focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-[#0F2942] mb-1">
                      Export format
                    </label>
                    <input
                      type="text"
                      value="CSV (Formula-sanitized)"
                      readOnly
                      className="w-full px-4 py-2 border border-[#CBD5E1] rounded-full text-xs text-[#475569] bg-slate-100 cursor-not-allowed"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-semibold text-[#0F2942] mb-1">
                      Date from (optional)
                    </label>
                    <input
                      type="date"
                      value={dateFrom}
                      onChange={(e) => setDateFrom(e.target.value)}
                      className="w-full px-4 py-2 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-[#0F2942] mb-1">
                      Date to (optional)
                    </label>
                    <input
                      type="date"
                      value={dateTo}
                      onChange={(e) => setDateTo(e.target.value)}
                      className="w-full px-4 py-2 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    />
                  </div>
                </div>

                <div className="p-3.5 bg-slate-50 rounded-xl border border-[#CBD5E1] text-[11px] text-[#475569] space-y-1">
                  <div className="font-semibold text-[#0F2942] flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-700" />
                    Data protection and sanitization enabled
                  </div>
                  <p>
                    Exported files are sanitized in compliance with statutory digital security and data protection standards.
                  </p>
                </div>

                <div className="flex justify-end gap-2.5 pt-3 border-t border-[#E2E8F0]">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="btn-rounded-secondary text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="btn-rounded-primary text-xs disabled:opacity-50"
                  >
                    {isSubmitting ? "Queueing..." : "Queue report generation"}
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