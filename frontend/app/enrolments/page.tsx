"use client";

import React, { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import { 
  apiRequest, 
  api, 
  EnrolmentRecord, 
  EnrolmentHistory 
} from "@/lib/api";
import { useLanguage } from "@/lib/language-context";
import { useAuth } from "@/lib/auth-context";
import { 
  Search, 
  ChevronLeft, 
  ChevronRight, 
  ShieldCheck, 
  Eye, 
  X, 
  History, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  Send 
} from "lucide-react";

interface EnrolmentListResponse {
  items: EnrolmentRecord[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export default function EnrolmentsPage() {
  const { language, t } = useLanguage();
  const { user, isLoading: isAuthLoading } = useAuth();
  const [enrolments, setEnrolments] = useState<EnrolmentRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Detail view modal
  const [selectedRecord, setSelectedRecord] = useState<EnrolmentRecord | null>(null);

  // History & Correction modal
  const [historyRecord, setHistoryRecord] = useState<EnrolmentRecord | null>(null);
  const [historyData, setHistoryData] = useState<EnrolmentHistory | null>(null);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);

  // Correction form state
  const [correctionReason, setCorrectionReason] = useState("");
  const [corrStatus, setCorrStatus] = useState("");
  const [corrAdmissionDate, setCorrAdmissionDate] = useState("");
  const [corrAdmissionCategory, setCorrAdmissionCategory] = useState("");
  const [isSubmittingCorrection, setIsSubmittingCorrection] = useState(false);
  const [correctionFeedback, setCorrectionFeedback] = useState<string | null>(null);
  const [correctionError, setCorrectionError] = useState<string | null>(null);

  const fetchEnrolments = async () => {
    setIsLoading(true);
    setError(null);
    try {
      let url = `/enrolments?page=${page}&page_size=${pageSize}`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (statusFilter) url += `&enrolment_status=${encodeURIComponent(statusFilter)}`;

      const res = await apiRequest<EnrolmentListResponse>(url);
      setEnrolments(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages || 1);
    } catch (err: any) {
      setError(err.message || "Failed to load enrolment records.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthLoading && user) {
      fetchEnrolments();
    }
  }, [isAuthLoading, user, page, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchEnrolments();
  };

  const openHistoryModal = async (record: EnrolmentRecord) => {
    setHistoryRecord(record);
    setIsHistoryLoading(true);
    setCorrectionFeedback(null);
    setCorrectionError(null);
    setCorrectionReason("");
    setCorrStatus(record.enrolment_status);
    setCorrAdmissionDate(record.admission_date || "");
    setCorrAdmissionCategory(record.admission_category || "GENERAL");

    try {
      const res = await api.getEnrolmentHistory(record.id);
      setHistoryData(res);
    } catch (err: any) {
      setCorrectionError(err.message || "Failed to load version history.");
    } finally {
      setIsHistoryLoading(false);
    }
  };

  const handleCorrectionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!historyRecord || !historyData) return;

    if (!correctionReason.trim() || correctionReason.trim().length < 5) {
      setCorrectionError("Please enter a valid administrative reason (at least 5 characters).");
      return;
    }

    setIsSubmittingCorrection(true);
    setCorrectionFeedback(null);
    setCorrectionError(null);

    try {
      const res = await api.submitEnrolmentCorrection(historyRecord.id, {
        expected_version: historyData.current_version,
        correction_reason: correctionReason.trim(),
        enrolment_status: corrStatus,
        admission_date: corrAdmissionDate || undefined,
        admission_category: corrAdmissionCategory || undefined,
      });

      setCorrectionFeedback(`Record updated to revision v${res.new_version}. Changes saved successfully.`);
      const updatedHistory = await api.getEnrolmentHistory(historyRecord.id);
      setHistoryData(updatedHistory);
      setCorrectionReason("");
      fetchEnrolments();
    } catch (err: any) {
      setCorrectionError(err.message || "Failed to apply correction.");
    } finally {
      setIsSubmittingCorrection(false);
    }
  };

  return (
    <AppShell>
      <div className="space-y-6 max-w-7xl mx-auto pb-12">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#CBD5E1]">
          <div>
            <div className="flex items-center gap-2 text-xs text-[#475569] mb-1">
              <span className="font-medium text-[#0F2942]">
                {language === "hi" ? "राष्ट्रीय नामांकन पंजी" : "National enrolment registry"}
              </span>
              <span>•</span>
              <span>{language === "hi" ? "सत्यापित छात्र विवरण" : "Student records"}</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-[#0F2942]">
              {language === "hi" ? "छात्र नामांकन रिकॉर्ड" : "Student enrolment records"}
            </h1>
            <p className="text-xs text-[#475569] mt-0.5">
              {language === "hi"
                ? "संरक्षित पहचान मिलान एवं संस्थागत साक्ष्य युक्त अधिकृत छात्र रिकॉर्ड।"
                : "Auditable student enrolment records with protected identifiers and institutional provenance."}
            </p>
          </div>
        </div>

        {/* Filter bar */}
        <div className="bg-white p-4 rounded-2xl border border-[#CBD5E1] shadow-xs flex flex-wrap items-center justify-between gap-3">
          <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 flex-1 max-w-md">
            <div className="relative w-full">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={language === "hi" ? "छात्र आईडी अथवा नाम से खोजें..." : "Search by student ID or name..."}
                className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
              />
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            </div>
            <button
              type="submit"
              className="btn-rounded-secondary text-xs"
            >
              {t("action.search", "Search")}
            </button>
          </form>

          <div className="flex items-center gap-3">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-4 py-2 bg-white border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
            >
              <option value="">All enrolment statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="TRANSFERRED">Transferred</option>
              <option value="WITHDRAWN">Withdrawn</option>
              <option value="COMPLETED">Completed</option>
              <option value="SUSPENDED">Suspended</option>
            </select>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800">
            {error}
          </div>
        )}

        {/* Table View */}
        <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left neev-table">
              <thead>
                <tr>
                  <th>Student ID</th>
                  <th>Student name</th>
                  <th>Protected APAAR ID</th>
                  <th>Programme</th>
                  <th>Academic session</th>
                  <th>Admission date</th>
                  <th>Status</th>
                  <th>Verification</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {isLoading ? (
                  <tr>
                    <td colSpan={9} className="text-center py-8 text-xs text-[#475569]">
                      {language === "hi" ? "रिकॉर्ड लोड हो रहे हैं..." : "Loading enrolment records..."}
                    </td>
                  </tr>
                ) : enrolments.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="text-center py-8 text-xs text-[#475569]">
                      No enrolment records found matching your filters.
                    </td>
                  </tr>
                ) : (
                  enrolments.map((enr) => (
                    <tr key={enr.id}>
                      <td className="font-semibold text-[#0F2942] tabular-nums">
                        {enr.institution_student_id}
                      </td>
                      <td className="font-medium text-[#1E293B]">
                        {enr.student_full_name}
                      </td>
                      <td className="text-slate-600 tabular-nums">
                        {enr.masked_apaar_id || "Unlinked identifier"}
                      </td>
                      <td>
                        <span className="block font-medium text-[#0F2942]">{enr.programme_name}</span>
                        <span className="text-[11px] text-[#475569]">{enr.official_programme_code}</span>
                      </td>
                      <td className="text-[#475569]">
                        {enr.academic_year_label}
                      </td>
                      <td className="text-[#475569] tabular-nums">
                        {enr.admission_date || "—"}
                      </td>
                      <td>
                        <span className={`whitespace-nowrap inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium capitalize ${
                          enr.enrolment_status === "ACTIVE"
                            ? "bg-emerald-100 text-emerald-800"
                            : enr.enrolment_status === "TRANSFERRED"
                            ? "bg-blue-100 text-blue-800"
                            : "bg-slate-100 text-slate-800"
                        }`}>
                          {enr.enrolment_status.toLowerCase()}
                        </span>
                      </td>
                      <td>
                        <span className={`inline-flex items-center gap-1 text-[11px] font-medium ${
                          enr.apaar_validation_status === "VERIFIED"
                            ? "text-[#15803D]"
                            : enr.apaar_validation_status === "VALID_SYNTAX"
                            ? "text-sky-700"
                            : "text-[#B45309]"
                        }`}>
                          {enr.apaar_validation_status === "VERIFIED" && <ShieldCheck className="w-3.5 h-3.5" />}
                          {enr.apaar_validation_status === "VALID_SYNTAX" ? "Format verified" : enr.apaar_validation_status}
                        </span>
                      </td>
                      <td className="text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => setSelectedRecord(enr)}
                            title="View student evidence dossier"
                            className="p-1.5 text-slate-600 hover:text-[#0F2942] hover:bg-slate-100 rounded-full transition-colors"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => openHistoryModal(enr)}
                            title="View revision history & corrections"
                            className="p-1.5 text-slate-600 hover:text-[#0F2942] hover:bg-slate-100 rounded-full transition-colors"
                          >
                            <History className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-5 py-3.5 bg-slate-50 border-t border-[#CBD5E1] flex items-center justify-between text-xs text-[#475569]">
            <span>
              Showing <strong className="text-[#1E293B] tabular-nums">{enrolments.length}</strong> of{" "}
              <strong className="text-[#1E293B] tabular-nums">{total}</strong> records
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="btn-rounded-secondary text-xs disabled:opacity-40"
              >
                <ChevronLeft className="w-3.5 h-3.5" /> Previous
              </button>
              <span className="px-2 font-medium tabular-nums">
                Page {page} of {totalPages}
              </span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="btn-rounded-secondary text-xs disabled:opacity-40"
              >
                Next <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Record Detail Modal (No backdrop blur, clean solid overlay) */}
        {selectedRecord && (
          <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xl max-w-lg w-full p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-[#0F2942]" />
                  <h3 className="text-sm font-bold text-[#0F2942]">Enrolment record details</h3>
                </div>
                <button onClick={() => setSelectedRecord(null)} className="text-slate-400 hover:text-slate-600 rounded-full p-1">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-3 text-xs">
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Student full name:</span>
                    <strong className="text-[#1E293B]">{selectedRecord.student_full_name}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Institution student ID:</span>
                    <span className="font-semibold text-[#0F2942] tabular-nums">{selectedRecord.institution_student_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Protected APAAR ID:</span>
                    <span className="text-[#1E293B] tabular-nums">{selectedRecord.masked_apaar_id || "Unlinked identifier"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Identity validation status:</span>
                    <span className="font-medium text-[#1E40AF]">{selectedRecord.apaar_validation_status}</span>
                  </div>
                </div>

                {/* 2-Column Details (Compliant with Rule 2: Avoid 3-column layouts) */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-white rounded-xl border border-slate-200">
                    <span className="text-slate-500 block text-[11px]">Institution</span>
                    <div className="font-semibold text-[#0F2942] mt-0.5">{selectedRecord.institution_name}</div>
                  </div>
                  <div className="p-3 bg-white rounded-xl border border-slate-200">
                    <span className="text-slate-500 block text-[11px]">Academic session</span>
                    <div className="font-semibold text-[#0F2942] mt-0.5">{selectedRecord.academic_year_label}</div>
                  </div>
                </div>

                <div className="p-3 bg-white rounded-xl border border-slate-200">
                  <span className="text-slate-500 block text-[11px]">Programme details</span>
                  <div className="font-semibold text-[#0F2942] mt-0.5">{selectedRecord.programme_name}</div>
                  <span className="text-[11px] text-[#475569] block">{selectedRecord.official_programme_code}</span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-slate-600">
                  <div>Admission date: <strong className="text-[#1E293B] tabular-nums">{selectedRecord.admission_date}</strong></div>
                  <div>Category: <strong className="text-[#1E293B]">{selectedRecord.admission_category}</strong></div>
                </div>
              </div>

              <div className="pt-3 border-t border-[#E2E8F0] flex justify-end">
                <button
                  onClick={() => setSelectedRecord(null)}
                  className="btn-rounded-primary text-xs"
                >
                  {t("action.close", "Close")}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal: Record Version History & Corrections (No blur, clean 2-column form) */}
        {historyRecord && (
          <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xl max-w-2xl w-full p-6 sm:p-8 space-y-5 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <div className="flex items-center gap-2.5">
                  <History className="w-5 h-5 text-[#0F2942]" />
                  <div>
                    <h3 className="text-base font-bold text-[#0F2942]">Record revision history & corrections</h3>
                    <p className="text-xs text-[#475569]">
                      {historyRecord.student_full_name} ({historyRecord.institution_student_id})
                    </p>
                  </div>
                </div>
                <button onClick={() => setHistoryRecord(null)} className="text-slate-400 hover:text-slate-600 rounded-full p-1">
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Feedback banners */}
              {correctionFeedback && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>{correctionFeedback}</span>
                </div>
              )}

              {correctionError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
                  <span>{correctionError}</span>
                </div>
              )}

              {/* Version Timeline */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-[#0F2942]">
                    Record revision history (Current: revision v{historyData?.current_version || 1})
                  </h4>
                  <span className="text-[11px] text-slate-500">
                    Identifier: {historyData?.masked_apaar_id || "Unlinked"}
                  </span>
                </div>

                {isHistoryLoading ? (
                  <div className="p-6 text-center text-xs text-slate-500">Loading version history...</div>
                ) : historyData?.versions && historyData.versions.length > 0 ? (
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {historyData.versions.map((ver) => {
                      let parsedSnapshot: any = {};
                      try {
                        parsedSnapshot = JSON.parse(ver.snapshot_json);
                      } catch {}

                      return (
                        <div key={ver.id} className="p-3 rounded-xl border border-slate-200 bg-slate-50 text-xs space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-[#0F2942] bg-white px-2 py-0.5 rounded-full border border-slate-200 tabular-nums">
                              Revision v{ver.version_number}
                            </span>
                            <span className="text-slate-500 text-[11px] flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {new Date(ver.changed_at).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-[#1E293B] font-medium pt-1">
                            Reason: <span className="text-slate-700 font-normal">{ver.change_reason}</span>
                          </p>
                          <div className="text-[11px] text-slate-500 flex flex-wrap gap-3 pt-0.5">
                            <span>Status: <strong className="text-slate-700">{parsedSnapshot.enrolment_status || "ACTIVE"}</strong></span>
                            <span>Admission date: <strong className="text-slate-700">{parsedSnapshot.admission_date || "N/A"}</strong></span>
                            <span>Category: <strong className="text-slate-700">{parsedSnapshot.admission_category || "GENERAL"}</strong></span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="p-4 rounded-xl border border-slate-200 text-xs text-slate-500 bg-slate-50">
                    Initial enrolment record (Revision 1). No historical modifications have been made.
                  </div>
                )}
              </div>

              {/* Controlled Correction Form (Clean 2-Column layout - NO 3-column layout) */}
              <div className="pt-3 border-t border-[#E2E8F0] space-y-3">
                <h4 className="text-xs font-bold text-[#0F2942]">
                  Submit official record correction
                </h4>
                <p className="text-[11px] text-slate-500">
                  Record corrections require a formal justification and automatically update status across the registry.
                </p>

                <form onSubmit={handleCorrectionSubmit} className="space-y-3 bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-slate-700 font-semibold mb-1">Enrolment status</label>
                      <select
                        value={corrStatus}
                        onChange={(e) => setCorrStatus(e.target.value)}
                        className="w-full rounded-full border border-[#CBD5E1] p-2 bg-white text-[#1E293B]"
                      >
                        <option value="ACTIVE">Active</option>
                        <option value="TRANSFERRED">Transferred</option>
                        <option value="WITHDRAWN">Withdrawn</option>
                        <option value="COMPLETED">Completed</option>
                        <option value="SUSPENDED">Suspended</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-slate-700 font-semibold mb-1">Effective admission date</label>
                      <input
                        type="date"
                        value={corrAdmissionDate}
                        onChange={(e) => setCorrAdmissionDate(e.target.value)}
                        className="w-full rounded-full border border-[#CBD5E1] p-2 bg-white text-[#1E293B]"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">Admission category</label>
                    <input
                      type="text"
                      value={corrAdmissionCategory}
                      onChange={(e) => setCorrAdmissionCategory(e.target.value)}
                      placeholder="GENERAL, OBC, SC, ST..."
                      className="w-full rounded-full border border-[#CBD5E1] p-2 bg-white text-[#1E293B]"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">
                      Correction reason / justification <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      rows={2}
                      value={correctionReason}
                      onChange={(e) => setCorrectionReason(e.target.value)}
                      placeholder="Specify the official administrative reason for this correction..."
                      className="w-full rounded-xl border border-[#CBD5E1] p-2.5 bg-white text-[#1E293B]"
                      required
                    />
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[11px] text-slate-500">
                      Target revision: <strong className="tabular-nums">v{historyData?.current_version || 1}</strong>
                    </span>
                    <button
                      type="submit"
                      disabled={isSubmittingCorrection}
                      className="btn-rounded-primary text-xs"
                    >
                      <Send className="w-3.5 h-3.5 text-sky-300" />
                      <span>{isSubmittingCorrection ? "Saving..." : "Submit correction"}</span>
                    </button>
                  </div>
                </form>
              </div>

              <div className="pt-2 border-t border-[#E2E8F0] flex justify-end">
                <button
                  type="button"
                  onClick={() => setHistoryRecord(null)}
                  className="btn-rounded-secondary text-xs"
                >
                  {t("action.close", "Close")}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
