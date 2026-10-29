"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import { api, InstitutionRiskProfile } from "@/lib/api";
import { 
  ShieldAlert, 
  RefreshCw, 
  ArrowLeft, 
  History, 
  AlertTriangle, 
  Building2, 
  CheckCircle2,
  FolderKanban,
  FileCheck
} from "lucide-react";

interface PageProps {
  params: Promise<{ id: string }>;
}

function InstitutionRiskProfileInner({ params }: PageProps) {
  const resolvedParams = use(params);
  const institutionId = resolvedParams.id;

  const [profile, setProfile] = useState<InstitutionRiskProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRecalculating, setIsRecalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchProfile = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getInstitutionRiskProfile(institutionId);
      setProfile(data);
    } catch (err: any) {
      setError(err.message || "Failed to load institution risk profile.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, [institutionId]);

  const handleRecalculate = async () => {
    setIsRecalculating(true);
    setSuccessMsg(null);
    try {
      await api.recalculateRisk(institutionId);
      setSuccessMsg("Risk profile successfully recalculated against current database records.");
      await fetchProfile();
    } catch (err: any) {
      alert(err.message || "Recalculation failed.");
    } finally {
      setIsRecalculating(false);
    }
  };

  const getBandBadge = (band: string) => {
    switch (band) {
      case "PRIORITY_REVIEW":
        return <span className="px-2.5 py-1 text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200 rounded">Priority review</span>;
      case "REVIEW_RECOMMENDED":
        return <span className="px-2.5 py-1 text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 rounded">Review recommended</span>;
      case "WATCH":
        return <span className="px-2.5 py-1 text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 rounded">Watch</span>;
      default:
        return <span className="px-2.5 py-1 text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 rounded">Routine</span>;
    }
  };

  const calc = profile?.current_calculation;
  const factors = calc?.factors;

  return (
    <AppShell>
      <div className="space-y-6 max-w-6xl">
        {/* Navigation back */}
        <div className="flex items-center justify-between">
          <Link
            href="/risk-queue"
            className="inline-flex items-center gap-1.5 text-xs text-[#475569] hover:text-[#0F2942] font-medium"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to risk review queue
          </Link>
          <div className="flex gap-2">
            <Link
              href={`/cases?institution_id=${institutionId}`}
              className="btn-rounded-secondary text-xs"
            >
              <FolderKanban className="w-3.5 h-3.5 text-[#0F2942]" />
              View audit cases
            </Link>
            <button
              onClick={handleRecalculate}
              disabled={isRecalculating}
              className="btn-rounded-primary text-xs disabled:opacity-40"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-white ${isRecalculating ? "animate-spin" : ""}`} />
              {isRecalculating ? "Recalculating..." : "Recalculate risk"}
            </button>
          </div>
        </div>

        {successMsg && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            {successMsg}
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded text-xs text-red-800">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="h-64 flex items-center justify-center bg-white rounded border border-[#CBD5E1]">
            <div className="flex flex-col items-center gap-2">
              <div className="w-6 h-6 border-2 border-[#0F2942] border-t-transparent rounded-full animate-spin"></div>
              <span className="text-xs text-[#475569]">Loading institution risk profile...</span>
            </div>
          </div>
        ) : profile && calc ? (
          <>
            {/* Header Summary Card */}
            <div className="bg-white p-5 rounded border border-[#CBD5E1] shadow-xs">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 text-xs text-[#475569]">
                    <Building2 className="w-4 h-4 text-[#0F2942]" />
                    <span className="tabular-nums">{profile.official_code}</span>
                    <span>&bull;</span>
                    <span>Version {calc.calculation_version}</span>
                    <span>&bull;</span>
                    <span>{new Date(calc.calculated_at).toLocaleString()}</span>
                  </div>
                  <h1 className="text-xl font-bold text-[#0F2942] mt-1">
                    {profile.institution_name}
                  </h1>
                </div>

                <div className="flex items-center gap-4 bg-[#F8FAFC] p-3.5 rounded border border-[#CBD5E1] self-start md:self-auto">
                  <div className="text-right">
                    <span className="text-[11px] text-[#475569] block  font-semibold">
                      Review priority
                    </span>
                    <div className="mt-1">{getBandBadge(calc.risk_band)}</div>
                  </div>
                  <div className="border-l border-[#CBD5E1] pl-4">
                    <span className="text-[11px] text-[#475569] block  font-semibold">
                      Total score
                    </span>
                    <div className="text-2xl font-bold tabular-nums text-[#0F2942]">
                      {calc.total_score.toFixed(1)}
                      <span className="text-xs font-normal text-[#475569]"> / 100</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Explanatory text */}
              <div className="mt-4 pt-4 border-t border-[#CBD5E1] text-xs text-[#475569]">
                <strong className="text-[#0F2942] font-semibold">Regulatory calculation summary: </strong>
                {calc.explanation}
              </div>
            </div>

            {/* Factor Contributions Grid */}
            <div className="bg-white p-5 rounded border border-[#CBD5E1] shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-[#CBD5E1] pb-3">
                <h2 className="text-sm font-bold text-[#0F2942]">
                  Deterministic factor contributions
                </h2>
                <span className="text-xs text-[#475569]">
                  Ruleset version {calc.calculation_version}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Factor 1: Capacity Discrepancy */}
                <div className="p-3.5 bg-[#F8FAFC] rounded border border-[#CBD5E1] space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-[#0F2942]">Approved intake capacity variance</span>
                    <span className="tabular-nums font-bold text-[#0F2942]">
                      {factors?.capacity_discrepancy.toFixed(1)} <span className="text-[10px] text-[#475569] font-normal">/ 25.0</span>
                    </span>
                  </div>
                  <div className="w-full bg-[#E5E4DE] h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-[#0F2942] h-full rounded-full transition-all duration-300" 
                      style={{ width: `${Math.min(100, ((factors?.capacity_discrepancy || 0) / 25) * 100)}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-[#475569]">
                    Measures programmes exceeding approved AICTE intake sanctioned for the current cycle.
                  </p>
                </div>

                {/* Factor 2: Cross-Institution Conflicts */}
                <div className="p-3.5 bg-[#F8FAFC] rounded border border-[#CBD5E1] space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-[#0F2942]">Unresolved cross-institution conflicts</span>
                    <span className="tabular-nums font-bold text-[#0F2942]">
                      {factors?.unresolved_conflicts.toFixed(1)} <span className="text-[10px] text-[#475569] font-normal">/ 25.0</span>
                    </span>
                  </div>
                  <div className="w-full bg-[#E5E4DE] h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-[#0F2942] h-full rounded-full transition-all duration-300" 
                      style={{ width: `${Math.min(100, ((factors?.unresolved_conflicts || 0) / 25) * 100)}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-[#475569]">
                    Active duplicate enrolments where the student is simultaneously recorded in multiple institutions.
                  </p>
                </div>

                {/* Factor 3: Identifier and Data Quality */}
                <div className="p-3.5 bg-[#F8FAFC] rounded border border-[#CBD5E1] space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-[#0F2942]">Identifier & data quality defects</span>
                    <span className="tabular-nums font-bold text-[#0F2942]">
                      {factors?.data_quality.toFixed(1)} <span className="text-[10px] text-[#475569] font-normal">/ 15.0</span>
                    </span>
                  </div>
                  <div className="w-full bg-[#E5E4DE] h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-[#0F2942] h-full rounded-full transition-all duration-300" 
                      style={{ width: `${Math.min(100, ((factors?.data_quality || 0) / 15) * 100)}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-[#475569]">
                    Ratio of missing identifiers or malformed APAAR numbers in submitted student records.
                  </p>
                </div>

                {/* Factor 4: Unusual Roster Changes */}
                <div className="p-3.5 bg-[#F8FAFC] rounded border border-[#CBD5E1] space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-[#0F2942]">Student list corrections & post-admission edits</span>
                    <span className="tabular-nums font-bold text-[#0F2942]">
                      {factors?.unusual_roster_changes.toFixed(1)} <span className="text-[10px] text-[#475569] font-normal">/ 15.0</span>
                    </span>
                  </div>
                  <div className="w-full bg-[#E5E4DE] h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-[#0F2942] h-full rounded-full transition-all duration-300" 
                      style={{ width: `${Math.min(100, ((factors?.unusual_roster_changes || 0) / 15) * 100)}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-[#475569]">
                    Tracked version modifications and historical replacements performed on finalized records.
                  </p>
                </div>

                {/* Factor 5: Source Reconciliation Gap */}
                <div className="p-3.5 bg-[#F8FAFC] rounded border border-[#CBD5E1] space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-[#0F2942]">External source reconciliation gap</span>
                    <span className="tabular-nums font-bold text-[#0F2942]">
                      {factors?.source_reconciliation_gap.toFixed(1)} <span className="text-[10px] text-[#475569] font-normal">/ 10.0</span>
                    </span>
                  </div>
                  <div className="w-full bg-[#E5E4DE] h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-[#0F2942] h-full rounded-full transition-all duration-300" 
                      style={{ width: `${Math.min(100, ((factors?.source_reconciliation_gap || 0) / 10) * 100)}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-[#475569]">
                    Simulated or unverified registry references where authoritative verification is pending.
                  </p>
                </div>

                {/* Factor 6: Repeated Prior Findings */}
                <div className="p-3.5 bg-[#F8FAFC] rounded border border-[#CBD5E1] space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-[#0F2942]">Repeated unresolved prior findings</span>
                    <span className="tabular-nums font-bold text-[#0F2942]">
                      {factors?.repeated_prior_findings.toFixed(1)} <span className="text-[10px] text-[#475569] font-normal">/ 10.0</span>
                    </span>
                  </div>
                  <div className="w-full bg-[#E5E4DE] h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-[#0F2942] h-full rounded-full transition-all duration-300" 
                      style={{ width: `${Math.min(100, ((factors?.repeated_prior_findings || 0) / 10) * 100)}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-[#475569]">
                    Historical integrity discrepancies remaining in response-overdue status.
                  </p>
                </div>
              </div>
            </div>

            {/* Input Snapshot & Historical Calculations */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Snapshot Details */}
              <div className="bg-white p-4 rounded border border-[#CBD5E1] shadow-xs space-y-3">
                <h3 className="text-xs font-bold text-[#0F2942] flex items-center gap-1.5 border-b border-[#CBD5E1] pb-2">
                  <FileCheck className="w-3.5 h-3.5 text-[#0F2942]" />
                  Calculation input snapshot
                </h3>
                <div className="bg-[#F8FAFC] p-3 rounded tabular-nums text-[11px] text-[#0F2942] overflow-x-auto border border-[#CBD5E1]">
                  <pre>{JSON.stringify(calc.input_snapshot, null, 2)}</pre>
                </div>
              </div>

              {/* Versioned History */}
              <div className="bg-white p-4 rounded border border-[#CBD5E1] shadow-xs space-y-3">
                <h3 className="text-xs font-bold text-[#0F2942] flex items-center gap-1.5 border-b border-[#CBD5E1] pb-2">
                  <History className="w-3.5 h-3.5 text-[#0F2942]" />
                  Preserved calculation history ({profile.history.length})
                </h3>
                <div className="space-y-2">
                  {profile.history.map((h) => (
                    <div key={h.id} className="p-2.5 bg-[#F8FAFC] border border-[#CBD5E1] rounded flex items-center justify-between text-xs">
                      <div>
                        <span className="tabular-nums font-medium text-[#0F2942]">
                          Score: {h.total_score.toFixed(1)}
                        </span>
                        <span className="text-[11px] text-[#475569] ml-2">
                          {new Date(h.calculated_at).toLocaleString()}
                        </span>
                      </div>
                      <div>
                        {getBandBadge(h.risk_band)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}

export default function InstitutionRiskProfilePage({ params }: PageProps) {
  return (
    <React.Suspense
      fallback={
        <div className="min-h-screen bg-[#F8FAFC] p-12 text-center flex items-center justify-center">
          <div className="bg-white rounded border border-[#CBD5E1] p-8 shadow-xs">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-[#CBD5E1] border-t-[#0F2942]"></div>
            <p className="mt-3 text-xs text-[#475569]">Loading institution risk profile...</p>
          </div>
        </div>
      }
    >
      <InstitutionRiskProfileInner params={params} />
    </React.Suspense>
  );
}
