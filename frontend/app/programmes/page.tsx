"use client";

import React, { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import { apiRequest, Programme, Institution, InstitutionListResponse } from "@/lib/api";
import { GraduationCap, Building2, Filter, AlertCircle, Calendar } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export default function ProgrammesPage() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const [programmes, setProgrammes] = useState<Programme[]>([]);
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [selectedInstId, setSelectedInstId] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const instData = await apiRequest<InstitutionListResponse>("/institutions?page=1&page_size=100");
      setInstitutions(instData.items);

      let url = "/programmes";
      if (selectedInstId) {
        url += `?institution_id=${selectedInstId}`;
      }
      const progData = await apiRequest<Programme[]>(url);
      setProgrammes(progData);
    } catch (err: any) {
      setError(err.message || "Failed to load programme data.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthLoading && user) {
      loadData();
    }
  }, [isAuthLoading, user, selectedInstId]);

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-[#0F2942] tracking-tight">
              Programmes and approved intake
            </h1>
            <p className="text-xs text-[#475569] mt-0.5">
              Authoritative programme registrations and AICTE approved intake capacity versions.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <span className="text-xs text-[#475569] font-medium flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-[#0F2942]" /> Institution scope:
            </span>
            <select
              value={selectedInstId}
              onChange={(e) => setSelectedInstId(e.target.value)}
              className="px-3.5 py-1.5 bg-slate-50 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
            >
              <option value="">All permitted institutions</option>
              {institutions.map((i) => (
                <option key={i.id} value={i.id}>{i.name}</option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div className="p-3.5 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-800">
            {error}
          </div>
        )}

        {/* Programmes Grid / Table */}
        <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xs overflow-hidden">
          <div className="p-4 border-b border-[#CBD5E1] bg-slate-50 flex items-center justify-between">
            <span className="text-xs font-semibold text-[#1E293B]">
              Approved academic offerings ({programmes.length})
            </span>
            <span className="text-[11px] text-[#0F2942] font-medium flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5 text-[#0F2942]" />
              Source: Regulatory council approval notification letter
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full neev-table">
              <thead>
                <tr>
                  <th>Official code</th>
                  <th>Programme name</th>
                  <th>Institution</th>
                  <th>Level / discipline</th>
                  <th>Approved intake</th>
                  <th>Active enrolments</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-xs text-[#475569]">
                      Loading approved programme directory...
                    </td>
                  </tr>
                ) : programmes.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-xs text-[#475569]">
                      No programmes found in this scope.
                    </td>
                  </tr>
                ) : (
                  programmes.map((p) => (
                    <tr key={p.id}>
                      <td className="neev-id font-semibold text-[#0F2942] tabular-nums">
                        {p.official_programme_code}
                      </td>
                      <td>
                        <div className="font-semibold text-[#0F2942]">{p.programme_name}</div>
                        <span className="text-[11px] text-[#475569] block mt-0.5">
                          {p.qualification_level}
                        </span>
                      </td>
                      <td className="text-xs text-[#1E293B] font-medium">
                        {p.institution_name}
                      </td>
                      <td className="text-xs text-[#475569]">
                        {p.academic_discipline}
                      </td>
                      <td>
                        {p.active_intake !== null && p.active_intake !== undefined ? (
                          <div className="flex items-center gap-1.5">
                            <span className="font-bold text-sm text-[#0F2942] tabular-nums">{p.active_intake}</span>
                            <span className="text-[10px] text-[#475569]">seats</span>
                          </div>
                        ) : (
                          <span className="whitespace-nowrap inline-flex items-center text-xs text-amber-700 bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200 font-medium">
                            Missing intake reference (INT-001)
                          </span>
                        )}
                      </td>
                      <td>
                        <span className="font-semibold text-sm text-[#0F2942] tabular-nums">
                          {p.active_enrolments_count}
                        </span>
                      </td>
                      <td>
                        <span className={`whitespace-nowrap inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${
                          p.status === "APPROVED"
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-slate-100 text-[#475569]"
                        }`}>
                          {p.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
