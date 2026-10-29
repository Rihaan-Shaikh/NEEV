"use client";

import React, { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import { apiRequest, Institution, InstitutionListResponse } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { 
  Building2, 
  Search, 
  Plus, 
  X, 
  GraduationCap, 
  Users, 
  MapPin,
  ChevronLeft,
  ChevronRight
} from "lucide-react";

export default function InstitutionsPage() {
  const { hasPermission, user, isLoading: isAuthLoading } = useAuth();
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newCode, setNewCode] = useState("");
  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState("CENTRAL_UNIVERSITY");
  const [newState, setNewState] = useState("DL");
  const [newDistrict, setNewDistrict] = useState("NEW_DELHI");
  const [newAddress, setNewAddress] = useState("");
  const [modalError, setModalError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchInstitutions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      let url = `/institutions?page=${page}&page_size=${pageSize}`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;

      const res = await apiRequest<InstitutionListResponse>(url);
      setInstitutions(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages || 1);
    } catch (err: any) {
      setError(err.message || "Failed to load institutions.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthLoading && user) {
      fetchInstitutions();
    }
  }, [isAuthLoading, user, page, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchInstitutions();
  };

  const handleCreateInstitution = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);
    setIsSubmitting(true);
    try {
      await apiRequest<Institution>("/institutions", {
        method: "POST",
        body: JSON.stringify({
          official_institution_code: newCode.trim().toUpperCase(),
          name: newName.trim(),
          institution_type: newType,
          state_code: newState.trim().toUpperCase(),
          district_code: newDistrict.trim().toUpperCase(),
          address: newAddress.trim() || null,
          status: "ACTIVE",
          is_synthetic: true
        }),
      });
      setIsModalOpen(false);
      setNewCode("");
      setNewName("");
      setNewAddress("");
      fetchInstitutions();
    } catch (err: any) {
      setModalError(err.message || "Failed to register institution.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-[#0F2942] tracking-tight">
              Institutions
            </h1>
            <p className="text-xs text-[#475569] mt-0.5">
              Approved educational institutions within your regulatory or tenant scope.
            </p>
          </div>
          {hasPermission("institution.manage") && (
            <button
              onClick={() => setIsModalOpen(true)}
              className="btn-rounded-primary text-xs self-start sm:self-auto"
            >
              <Plus className="w-3.5 h-3.5 text-white" />
              Register institution
            </button>
          )}
        </div>

        {/* Filters */}
        <div className="bg-white p-3.5 rounded-2xl border border-[#CBD5E1] shadow-xs flex flex-wrap items-center justify-between gap-3">
          <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 flex-1 max-w-md">
            <div className="relative w-full">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by institution name or code..."
                className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
              />
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3.5 top-3" />
            </div>
            <button
              type="submit"
              className="btn-rounded-primary text-xs"
            >
              Search
            </button>
          </form>

          <div className="flex items-center gap-3">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-3.5 py-1.5 bg-slate-50 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
            >
              <option value="">All statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="SUSPENDED">Suspended</option>
            </select>
          </div>
        </div>

        {error && (
          <div className="p-3.5 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-800">
            {error}
          </div>
        )}

        {/* Table View */}
        <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full neev-table">
              <thead>
                <tr>
                  <th>Official code</th>
                  <th>Institution name</th>
                  <th>Type</th>
                  <th>State / district</th>
                  <th>Status</th>
                  <th>Programmes</th>
                  <th>Enrolments</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-xs text-[#475569]">
                      Loading institutional directory...
                    </td>
                  </tr>
                ) : institutions.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-xs text-[#475569]">
                      No institutions found matching your scope and criteria.
                    </td>
                  </tr>
                ) : (
                  institutions.map((inst) => (
                    <tr key={inst.id}>
                      <td className="neev-id font-semibold text-[#0F2942] tabular-nums">
                        {inst.official_institution_code}
                      </td>
                      <td>
                        <div className="font-semibold text-[#0F2942]">{inst.name}</div>
                        <span className="whitespace-nowrap inline-flex items-center mt-0.5 text-[10px] text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 font-medium">
                          Recognized institution
                        </span>
                      </td>
                      <td className="text-xs text-[#475569]">
                        {inst.institution_type.replace(/_/g, " ")}
                      </td>
                      <td className="text-xs text-[#475569]">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-[#0F2942]" />
                          {inst.state_code} — {inst.district_code}
                        </span>
                      </td>
                      <td>
                        <span className={`whitespace-nowrap inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${
                          inst.status === "ACTIVE"
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-red-100 text-red-800"
                        }`}>
                          {inst.status === "ACTIVE" ? "Active" : "Suspended"}
                        </span>
                      </td>
                      <td>
                        <span className="flex items-center gap-1.5 font-semibold text-[#0F2942] tabular-nums">
                          <GraduationCap className="w-3.5 h-3.5 text-[#0F2942]" />
                          {inst.programmes_count}
                        </span>
                      </td>
                      <td>
                        <span className="flex items-center gap-1.5 font-semibold text-[#0F2942] tabular-nums">
                          <Users className="w-3.5 h-3.5 text-[#0F2942]" />
                          {inst.enrolments_count}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-4 py-3 border-t border-[#CBD5E1] bg-slate-50 flex items-center justify-between text-xs text-[#475569]">
            <span>
              Showing {institutions.length > 0 ? (page - 1) * pageSize + 1 : 0} to {Math.min(page * pageSize, total)} of {total} institutions
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="btn-rounded-secondary text-xs py-1 px-3"
                aria-label="Previous page"
              >
                <ChevronLeft className="w-3.5 h-3.5 text-[#0F2942]" />
                Previous
              </button>
              <span className="font-semibold text-[#0F2942] tabular-nums">
                Page {page} of {totalPages}
              </span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                className="btn-rounded-secondary text-xs py-1 px-3"
                aria-label="Next page"
              >
                Next
                <ChevronRight className="w-3.5 h-3.5 text-[#0F2942]" />
              </button>
            </div>
          </div>
        </div>

        {/* Create Institution Modal */}
        {isModalOpen && (
          <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xl max-w-lg w-full p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <h3 className="text-sm font-bold text-[#0F2942]">Register new institution</h3>
                <button onClick={() => setIsModalOpen(false)} className="w-7 h-7 rounded-full flex items-center justify-center hover:bg-slate-100 text-[#475569] hover:text-[#0F2942]">
                  <X className="w-4 h-4" />
                </button>
              </div>

              {modalError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
                  {modalError}
                </div>
              )}

              <form onSubmit={handleCreateInstitution} className="space-y-4">
                <div>
                  <label htmlFor="inst-code" className="block text-xs font-semibold text-[#0F2942] mb-1">
                    Official institution code
                  </label>
                  <input
                    id="inst-code"
                    type="text"
                    required
                    value={newCode}
                    onChange={(e) => setNewCode(e.target.value.toUpperCase())}
                    placeholder="e.g. AICTE-1-98765432"
                    className="block w-full px-3.5 py-2 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] tabular-nums focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                  />
                </div>

                <div>
                  <label htmlFor="inst-name" className="block text-xs font-semibold text-[#0F2942] mb-1">
                    Institution name
                  </label>
                  <input
                    id="inst-name"
                    type="text"
                    required
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="e.g. Bangalore Institute of Technology"
                    className="block w-full px-3.5 py-2 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="state-code" className="block text-xs font-semibold text-[#0F2942] mb-1">
                      State code
                    </label>
                    <input
                      id="state-code"
                      type="text"
                      required
                      value={newState}
                      onChange={(e) => setNewState(e.target.value.toUpperCase())}
                      placeholder="KA"
                      className="block w-full px-3.5 py-2 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    />
                  </div>
                  <div>
                    <label htmlFor="district-code" className="block text-xs font-semibold text-[#0F2942] mb-1">
                      District code
                    </label>
                    <input
                      id="district-code"
                      type="text"
                      required
                      value={newDistrict}
                      onChange={(e) => setNewDistrict(e.target.value.toUpperCase())}
                      placeholder="BANGALORE_URBAN"
                      className="block w-full px-3.5 py-2 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="inst-type" className="block text-xs font-semibold text-[#0F2942] mb-1">
                    Institution type
                  </label>
                  <select
                    id="inst-type"
                    value={newType}
                    onChange={(e) => setNewType(e.target.value)}
                    className="block w-full px-3.5 py-2 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942] bg-white"
                  >
                    <option value="CENTRAL_UNIVERSITY">Central University</option>
                    <option value="STATE_UNIVERSITY">State University</option>
                    <option value="PRIVATE_AIDED">Private Aided</option>
                    <option value="PRIVATE_UNAIDED">Private Unaided</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="inst-address" className="block text-xs font-semibold text-[#0F2942] mb-1">
                    Address
                  </label>
                  <input
                    id="inst-address"
                    type="text"
                    value={newAddress}
                    onChange={(e) => setNewAddress(e.target.value)}
                    placeholder="Campus address"
                    className="block w-full px-3.5 py-2 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                  />
                </div>

                <div className="pt-3 flex justify-end gap-2.5 border-t border-[#E2E8F0]">
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
                    {isSubmitting ? "Registering..." : "Register institution"}
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
