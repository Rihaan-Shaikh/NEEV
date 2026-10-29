"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import { api, RiskQueueItem } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { 
  TrendingUp, 
  Search, 
  Filter, 
  ShieldAlert, 
  ArrowUpRight, 
  RefreshCw,
  FolderPlus,
  CheckCircle2,
  ChevronLeft,
  ChevronRight
} from "lucide-react";

export default function RiskQueuePage() {
  const { user } = useAuth();
  const [items, setItems] = useState<RiskQueueItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [selectedBand, setSelectedBand] = useState<string>("");
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Quick case creation state
  const [createModalInst, setCreateModalInst] = useState<RiskQueueItem | null>(null);
  const [rationale, setRationale] = useState("");
  const [priority, setPriority] = useState("HIGH");
  const [category, setCategory] = useState("REGULATORY_REVIEW");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createSuccessMsg, setCreateSuccessMsg] = useState<string | null>(null);

  const fetchQueue = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.getRiskQueue({
        risk_band: selectedBand || undefined,
        search: search.trim() || undefined,
        page,
        page_size: pageSize
      });
      setItems(res.items || []);
      setTotal(res.total || 0);
    } catch (err: any) {
      setError(err.message || "Failed to load risk review queue.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, [page, selectedBand]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchQueue();
  };

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createModalInst) return;
    if (rationale.trim().length < 10) {
      alert("Creation rationale must be at least 10 characters.");
      return;
    }
    setIsSubmitting(true);
    try {
      const newCase = await api.createCase({
        institution_id: createModalInst.institution_id,
        case_category: category,
        priority,
        creation_rationale: rationale.trim()
      });
      setCreateSuccessMsg(`Audit case ${newCase.case_reference} created successfully.`);
      setTimeout(() => {
        setCreateModalInst(null);
        setRationale("");
        setCreateSuccessMsg(null);
        fetchQueue();
      }, 1500);
    } catch (err: any) {
      alert(err.message || "Failed to create audit case.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const getBandBadge = (band: string) => {
    switch (band) {
      case "PRIORITY_REVIEW":
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 text-[11px] font-bold bg-rose-50 text-rose-700 border border-rose-200 rounded-full">Priority review</span>;
      case "REVIEW_RECOMMENDED":
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200 rounded-full">Review recommended</span>;
      case "WATCH":
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 text-[11px] font-medium bg-blue-50 text-blue-700 border border-blue-200 rounded-full">Watch</span>;
      default:
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full">Routine</span>;
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-[#0F2942] tracking-tight">
              Risk review queue
            </h1>
            <p className="text-xs text-[#475569] mt-0.5">
              Prioritized review queue based on institutional risk factors and compliance thresholds.
            </p>
          </div>
          <button
            onClick={fetchQueue}
            disabled={isLoading}
            className="btn-rounded-secondary text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-[#0F2942] ${isLoading ? "animate-spin" : ""}`} />
            Refresh queue
          </button>
        </div>

        {/* Explainability Banner */}
        <div className="p-3.5 bg-slate-50 border border-[#CBD5E1] rounded-2xl text-xs text-[#475569] flex items-start gap-2.5">
          <ShieldAlert className="w-4 h-4 text-[#0F2942] shrink-0 mt-0.5" />
          <p>
            <strong className="text-[#0F2942] font-semibold">Regulatory notice:</strong> Risk scores are transparent review-prioritization indicators calculated from verified database records. They do not constitute a finding of misconduct, fraud probability, or an automatic sanction.
          </p>
        </div>

        {/* Filters & Search */}
        <div className="bg-white p-3.5 rounded-2xl border border-[#CBD5E1] shadow-xs flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
          <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 flex-1 max-w-md">
            <div className="relative flex-1">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="text"
                placeholder="Search by institution name or code..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 border border-[#CBD5E1] rounded-full text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
              />
            </div>
            <button
              type="submit"
              className="btn-rounded-primary text-xs"
            >
              Search
            </button>
          </form>

          <div className="flex items-center gap-2">
            <span className="text-xs text-[#475569] font-medium flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-[#0F2942]" />
              Risk band:
            </span>
            <select
              value={selectedBand}
              onChange={(e) => {
                setSelectedBand(e.target.value);
                setPage(1);
              }}
              className="px-3 py-1.5 text-xs bg-slate-50 border border-[#CBD5E1] rounded-full text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
            >
              <option value="">All bands</option>
              <option value="PRIORITY_REVIEW">Priority review (&ge; 70)</option>
              <option value="REVIEW_RECOMMENDED">Review recommended (40–69)</option>
              <option value="WATCH">Watch (20–39)</option>
              <option value="ROUTINE">Routine (&lt; 20)</option>
            </select>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-800">
            {error}
          </div>
        )}

        {/* Data Table */}
        <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs neev-table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Institution</th>
                  <th>State</th>
                  <th>Risk band</th>
                  <th className="text-right">Score</th>
                  <th>Primary driver</th>
                  <th className="text-center">Unresolved findings</th>
                  <th className="text-center">Active cases</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {isLoading ? (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-[#475569]">
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-5 h-5 border-2 border-[#0F2942] border-t-transparent rounded-full animate-spin"></div>
                        <span>Evaluating deterministic risk queue...</span>
                      </div>
                    </td>
                  </tr>
                ) : items.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-[#475569]">
                      No institutions match the current queue criteria.
                    </td>
                  </tr>
                ) : (
                  items.map((item) => (
                    <tr key={item.institution_id}>
                      <td className="text-[11px] text-[#475569] tabular-nums">{item.official_code}</td>
                      <td className="font-semibold text-[#0F2942]">
                        <Link
                          href={`/institutions/${item.institution_id}/risk-profile`}
                          className="hover:underline"
                        >
                          {item.institution_name}
                        </Link>
                      </td>
                      <td className="text-[#475569]">{item.state}</td>
                      <td>
                        {getBandBadge(item.risk_band)}
                      </td>
                      <td className="text-right font-bold text-[#0F2942] tabular-nums">
                        {item.total_score !== undefined && item.total_score !== null ? item.total_score.toFixed(1) : "—"}
                        <span className="text-[10px] text-[#475569] font-normal"> / 100</span>
                      </td>
                      <td className="text-[#475569] truncate max-w-xs" title={item.primary_driver}>
                        {item.primary_driver}
                      </td>
                      <td className="text-center">
                        <span className={`whitespace-nowrap inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium tabular-nums ${item.unresolved_findings_count > 0 ? "bg-amber-50 text-amber-800 border border-amber-200" : "text-[#475569]"}`}>
                          {item.unresolved_findings_count}
                        </span>
                      </td>
                      <td className="text-center">
                        <span className={`whitespace-nowrap inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium tabular-nums ${item.active_cases_count > 0 ? "bg-blue-50 text-blue-800 border border-blue-200" : "text-[#475569]"}`}>
                          {item.active_cases_count}
                        </span>
                      </td>
                      <td className="text-right space-x-2">
                        <Link
                          href={`/institutions/${item.institution_id}/risk-profile`}
                          className="btn-rounded-secondary text-xs py-1 px-3.5"
                        >
                          Profile
                          <ArrowUpRight className="w-3.5 h-3.5 text-[#0F2942]" />
                        </Link>
                        <button
                          onClick={() => setCreateModalInst(item)}
                          className="btn-rounded-primary text-xs py-1 px-3.5"
                        >
                          <FolderPlus className="w-3.5 h-3.5 text-white" />
                          Create case
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="p-3.5 bg-slate-50 border-t border-[#CBD5E1] flex items-center justify-between text-xs text-[#475569]">
            <span>Showing {items.length} of {total} institutions</span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="btn-rounded-secondary text-xs py-1 px-3"
              >
                <ChevronLeft className="w-3.5 h-3.5 text-[#0F2942]" />
                Previous
              </button>
              <button
                disabled={page * pageSize >= total}
                onClick={() => setPage((p) => p + 1)}
                className="btn-rounded-secondary text-xs py-1 px-3"
              >
                Next
                <ChevronRight className="w-3.5 h-3.5 text-[#0F2942]" />
              </button>
            </div>
          </div>
        </div>

        {/* Modal: Create Audit Case (Clean solid overlay, no blur) */}
        {createModalInst && (
          <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
            <div className="bg-white w-full max-w-lg rounded-2xl border border-[#CBD5E1] shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
              <div className="p-5 bg-slate-50 border-b border-[#E2E8F0] flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-[#0F2942]">Create audit case</h3>
                  <p className="text-xs text-[#475569]">
                    {createModalInst.institution_name} ({createModalInst.official_code})
                  </p>
                </div>
                <button
                  onClick={() => setCreateModalInst(null)}
                  className="w-7 h-7 rounded-full flex items-center justify-center hover:bg-slate-200 text-[#475569] hover:text-[#0F2942] transition-colors text-base font-bold"
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
                <form onSubmit={handleCreateCase} className="p-5 space-y-4 text-xs">
                  <div>
                    <label className="block font-semibold text-[#0F2942] mb-1">
                      Case category <span className="text-red-600">*</span>
                    </label>
                    <select
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      className="w-full px-3.5 py-2 bg-slate-50 border border-[#CBD5E1] rounded-full text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    >
                      <option value="REGULATORY_REVIEW">Regulatory review</option>
                      <option value="CAPACITY_VIOLATION">Capacity violation</option>
                      <option value="CROSS_INSTITUTION_DUPLICATE">Cross-institution duplicate</option>
                      <option value="DATA_QUALITY_ANOMALY">Data quality anomaly</option>
                      <option value="GENERAL">General audit</option>
                    </select>
                  </div>

                  <div>
                    <label className="block font-semibold text-[#0F2942] mb-1">
                      Priority <span className="text-red-600">*</span>
                    </label>
                    <select
                      value={priority}
                      onChange={(e) => setPriority(e.target.value)}
                      className="w-full px-3.5 py-2 bg-slate-50 border border-[#CBD5E1] rounded-full text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    >
                      <option value="LOW">Low</option>
                      <option value="MEDIUM">Medium</option>
                      <option value="HIGH">High</option>
                      <option value="CRITICAL">Critical</option>
                    </select>
                  </div>

                  <div>
                    <label className="block font-semibold text-[#0F2942] mb-1">
                      Creation rationale <span className="text-red-600">* (at least 10 characters)</span>
                    </label>
                    <textarea
                      rows={3}
                      required
                      placeholder="Specify the regulatory justification and evidence basis for opening this audit case..."
                      value={rationale}
                      onChange={(e) => setRationale(e.target.value)}
                      className="w-full p-3 bg-slate-50 border border-[#CBD5E1] rounded-xl text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    />
                  </div>

                  <div className="flex justify-end gap-2.5 pt-3 border-t border-[#E2E8F0]">
                    <button
                      type="button"
                      onClick={() => setCreateModalInst(null)}
                      className="btn-rounded-secondary text-xs"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isSubmitting || rationale.trim().length < 10}
                      className="btn-rounded-primary text-xs disabled:opacity-40"
                    >
                      {isSubmitting ? "Creating..." : "Confirm case creation"}
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