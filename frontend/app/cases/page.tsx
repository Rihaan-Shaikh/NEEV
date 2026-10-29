"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import { api, AuditCaseListItem, Institution } from "@/lib/api";
import { useLanguage } from "@/lib/language-context";
import { useAuth } from "@/lib/auth-context";
import { 
  FolderKanban, 
  Search, 
  Filter, 
  FolderPlus, 
  CheckCircle2, 
  Clock, 
  ArrowUpRight, 
  RefreshCw,
  Building2
} from "lucide-react";

export default function AuditCasesPage() {
  const { language, t } = useLanguage();
  const { user, isLoading: isAuthLoading } = useAuth();
  const [cases, setCases] = useState<AuditCaseListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create Case Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [selectedInstId, setSelectedInstId] = useState("");
  const [caseCategory, setCaseCategory] = useState("REGULATORY_REVIEW");
  const [casePriority, setCasePriority] = useState("HIGH");
  const [caseRationale, setCaseRationale] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createSuccessMsg, setCreateSuccessMsg] = useState<string | null>(null);

  const fetchCases = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.listCases({
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
        search: search.trim() || undefined,
        page,
        page_size: pageSize
      });
      setCases(res.items || []);
      setTotal(res.total || 0);
    } catch (err: any) {
      setError(err.message || "Failed to load audit cases.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthLoading && user) {
      fetchCases();
    }
  }, [isAuthLoading, user, page, statusFilter, priorityFilter]);

  const loadInstitutions = async () => {
    try {
      const res = await api.getRiskQueue({ page_size: 100 });
      setInstitutions(
        res.items.map((i) => ({
          id: i.institution_id,
          official_institution_code: i.official_code,
          name: i.institution_name,
        } as any))
      );
      if (res.items.length > 0 && !selectedInstId) {
        setSelectedInstId(res.items[0].institution_id);
      }
    } catch {}
  };

  const handleOpenCreateModal = () => {
    loadInstitutions();
    setShowCreateModal(true);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (caseRationale.trim().length < 10) {
      alert("Creation rationale must be at least 10 characters.");
      return;
    }
    setIsSubmitting(true);
    try {
      const created = await api.createCase({
        institution_id: selectedInstId,
        case_category: caseCategory,
        priority: casePriority,
        creation_rationale: caseRationale.trim()
      });
      setCreateSuccessMsg(`Audit case ${created.case_reference} created successfully.`);
      setTimeout(() => {
        setShowCreateModal(false);
        setCaseRationale("");
        setCreateSuccessMsg(null);
        fetchCases();
      }, 1500);
    } catch (err: any) {
      alert(err.message || "Failed to create audit case.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "RESOLVED":
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 text-[11px] font-medium bg-emerald-100 text-emerald-800 border border-emerald-300 rounded-full">Resolved</span>;
      case "UNDER_REVIEW":
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 text-[11px] font-medium bg-blue-100 text-blue-800 border border-blue-300 rounded-full">Under review</span>;
      case "CLARIFICATION_REQUESTED":
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 text-[11px] font-medium bg-purple-100 text-purple-800 border border-purple-300 rounded-full">Clarification requested</span>;
      case "RESPONSE_RECEIVED":
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 text-[11px] font-medium bg-amber-100 text-amber-800 border border-amber-300 rounded-full">Response received</span>;
      case "ESCALATED":
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 text-[11px] font-medium bg-red-100 text-red-800 border border-red-300 rounded-full">Escalated</span>;
      case "ASSIGNED":
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 text-[11px] font-medium bg-slate-100 text-slate-800 border border-slate-300 rounded-full">Assigned</span>;
      default:
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200 rounded-full capitalize">{status.replace(/_/g, " ").toLowerCase()}</span>;
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case "CRITICAL":
      case "HIGH":
        return <span className="text-[11px] font-semibold text-red-700">{priority}</span>;
      case "MEDIUM":
        return <span className="text-[11px] font-medium text-amber-700">{priority}</span>;
      default:
        return <span className="text-[11px] text-[#475569]">{priority}</span>;
    }
  };

  return (
    <AppShell>
      <div className="space-y-6 max-w-7xl mx-auto pb-12">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#CBD5E1] pb-4">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-[#0F2942] tracking-tight">
              {language === "hi" ? "विनियामक समीक्षा प्रकरण" : "Regulatory audit cases"}
            </h1>
            <p className="text-xs text-[#475569] mt-0.5">
              {language === "hi"
                ? "अधिकृत विनियामक समीक्षा, संस्थागत स्पष्टीकरण एवं अनुपालन प्रकरण।"
                : "Regulatory review records, institutional inquiries, and compliance dossiers."}
            </p>
          </div>
          <div className="flex gap-2 self-start sm:self-auto">
            <button
              onClick={fetchCases}
              disabled={isLoading}
              className="btn-rounded-secondary text-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${isLoading ? "animate-spin" : ""}`} />
              Refresh
            </button>
            <button
              onClick={handleOpenCreateModal}
              className="btn-rounded-primary text-xs"
            >
              <FolderPlus className="w-3.5 h-3.5 text-sky-300" />
              Create review case
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white p-4 rounded-2xl border border-[#CBD5E1] shadow-xs flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
          <form onSubmit={(e) => { e.preventDefault(); setPage(1); fetchCases(); }} className="flex items-center gap-2 flex-1 max-w-md">
            <div className="relative flex-1">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search reference or institution..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-[#CBD5E1] rounded-full text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
              />
            </div>
            <button
              type="submit"
              className="btn-rounded-secondary text-xs"
            >
              Search
            </button>
          </form>

          <div className="flex flex-wrap items-center gap-2.5">
            <div className="flex items-center gap-1.5 text-xs text-[#475569]">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <span>Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
                className="px-3 py-1.5 text-xs bg-slate-50 border border-[#CBD5E1] rounded-full text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
              >
                <option value="">All statuses</option>
                <option value="OPEN">Open</option>
                <option value="ASSIGNED">Assigned</option>
                <option value="UNDER_REVIEW">Under review</option>
                <option value="CLARIFICATION_REQUESTED">Clarification requested</option>
                <option value="RESPONSE_RECEIVED">Response received</option>
                <option value="RESOLVED">Resolved</option>
                <option value="ESCALATED">Escalated</option>
                <option value="CLOSED_NO_ACTION">Closed (no action)</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5 text-xs text-[#475569]">
              <span>Priority:</span>
              <select
                value={priorityFilter}
                onChange={(e) => { setPriorityFilter(e.target.value); setPage(1); }}
                className="px-3 py-1.5 text-xs bg-slate-50 border border-[#CBD5E1] rounded-full text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
              >
                <option value="">All priorities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-800">
            {error}
          </div>
        )}

        {/* Cases Table */}
        <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs neev-table">
              <thead>
                <tr>
                  <th>Case reference</th>
                  <th>Institution</th>
                  <th>Category</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Assigned reviewer</th>
                  <th className="text-center">Linked findings</th>
                  <th>Created date</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {isLoading ? (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-[#475569]">
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-5 h-5 border-2 border-[#0F2942] border-t-transparent rounded-full animate-spin"></div>
                        <span>Loading audit cases...</span>
                      </div>
                    </td>
                  </tr>
                ) : cases.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-[#475569]">
                      No audit cases found matching current filters.
                    </td>
                  </tr>
                ) : (
                  cases.map((c) => (
                    <tr key={c.id}>
                      <td className="font-semibold text-[#0F2942] tabular-nums">
                        <Link href={`/cases/${c.id}`} className="hover:underline flex items-center gap-1">
                          {c.case_reference}
                        </Link>
                      </td>
                      <td className="font-medium text-[#1E293B]">
                        {c.institution_name ? c.institution_name.replace(/\[DEMO-SYNTHETIC\]/gi, "").trim() : "—"}
                      </td>
                      <td className="text-[#475569] capitalize">
                        {c.case_category.replace(/_/g, " ").toLowerCase()}
                      </td>
                      <td>
                        {getPriorityBadge(c.priority)}
                      </td>
                      <td>
                        {getStatusBadge(c.status)}
                      </td>
                      <td className="text-[#475569]">
                        {c.assigned_reviewer_name || <span className="text-slate-400 italic">Unassigned</span>}
                      </td>
                      <td className="text-center">
                        <span className="px-2.5 py-0.5 bg-slate-100 border border-slate-300 rounded-full text-[11px] font-medium tabular-nums">
                          {c.linked_findings_count}
                        </span>
                      </td>
                      <td className="text-[#475569] tabular-nums">
                        {new Date(c.created_at).toLocaleDateString()}
                      </td>
                      <td className="text-right">
                        <Link
                          href={`/cases/${c.id}`}
                          className="btn-rounded-secondary text-xs py-1 px-3"
                        >
                          Workspace
                          <ArrowUpRight className="w-3 h-3 text-slate-400" />
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="p-4 bg-slate-50 border-t border-[#CBD5E1] flex items-center justify-between text-xs text-[#475569]">
            <span>Showing <strong className="tabular-nums text-[#1E293B]">{cases.length}</strong> of <strong className="tabular-nums text-[#1E293B]">{total}</strong> cases</span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="btn-rounded-secondary text-xs disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={page * pageSize >= total}
                onClick={() => setPage((p) => p + 1)}
                className="btn-rounded-secondary text-xs disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </div>

        {/* Modal: Create Audit Case (Clean solid overlay, no blur) */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
            <div className="bg-white w-full max-w-lg rounded-2xl border border-[#CBD5E1] shadow-xl overflow-hidden">
              <div className="p-5 bg-slate-50 border-b border-[#E2E8F0] flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-[#0F2942]">Create review case</h3>
                  <p className="text-xs text-[#475569]">Initiate formal institutional inquiry.</p>
                </div>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-slate-400 hover:text-slate-600 rounded-full p-1"
                >
                  &times;
                </button>
              </div>

              {createSuccessMsg ? (
                <div className="p-6 text-center space-y-2">
                  <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
                  <p className="text-sm font-semibold text-[#0F2942]">{createSuccessMsg}</p>
                </div>
              ) : (
                <form onSubmit={handleCreateSubmit} className="p-6 space-y-4 text-xs">
                  <div>
                    <label className="block font-semibold text-[#1E293B] mb-1">
                      Target institution <span className="text-rose-500">*</span>
                    </label>
                    <select
                      value={selectedInstId}
                      onChange={(e) => setSelectedInstId(e.target.value)}
                      required
                      className="w-full px-4 py-2 bg-slate-50 border border-[#CBD5E1] rounded-full text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    >
                      {institutions.map((inst) => (
                        <option key={inst.id} value={inst.id}>
                          {inst.name} ({inst.official_institution_code})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block font-semibold text-[#1E293B] mb-1">Case category</label>
                      <select
                        value={caseCategory}
                        onChange={(e) => setCaseCategory(e.target.value)}
                        className="w-full px-4 py-2 bg-slate-50 border border-[#CBD5E1] rounded-full text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                      >
                        <option value="REGULATORY_REVIEW">Regulatory review</option>
                        <option value="CAPACITY_AUDIT">Capacity audit</option>
                        <option value="DISCREPANCY_INQUIRY">Discrepancy inquiry</option>
                        <option value="ROUTINE_INSPECTION">Routine inspection</option>
                      </select>
                    </div>

                    <div>
                      <label className="block font-semibold text-[#1E293B] mb-1">Priority</label>
                      <select
                        value={casePriority}
                        onChange={(e) => setCasePriority(e.target.value)}
                        className="w-full px-4 py-2 bg-slate-50 border border-[#CBD5E1] rounded-full text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                      >
                        <option value="CRITICAL">Critical</option>
                        <option value="HIGH">High</option>
                        <option value="MEDIUM">Medium</option>
                        <option value="LOW">Low</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block font-semibold text-[#1E293B] mb-1">
                      Creation rationale & scope <span className="text-rose-500">*</span>
                    </label>
                    <textarea
                      rows={3}
                      value={caseRationale}
                      onChange={(e) => setCaseRationale(e.target.value)}
                      placeholder="Specify the regulatory basis and objectives for this case..."
                      required
                      className="w-full p-3 bg-slate-50 border border-[#CBD5E1] rounded-xl text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    />
                    <span className="text-[11px] text-slate-500 mt-0.5 block">
                      A clear administrative rationale is required for official records.
                    </span>
                  </div>

                  <div className="pt-3 border-t border-[#E2E8F0] flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setShowCreateModal(false)}
                      className="btn-rounded-secondary text-xs"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="btn-rounded-primary text-xs"
                    >
                      {isSubmitting ? "Creating case..." : "Create case"}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
