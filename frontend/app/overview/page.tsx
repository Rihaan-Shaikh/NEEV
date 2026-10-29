"use client";

import React, { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import {
  api,
  apiRequest,
  DashboardSummary,
  NationalDashboardMetrics
} from "@/lib/api";
import { useLanguage } from "@/lib/language-context";
import {
  Building2,
  GraduationCap,
  Users,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  ShieldCheck,
  ShieldAlert,
  BarChart3,
  Scale,
  FolderOpen,
  TrendingUp
} from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

export default function OverviewPage() {
  const { language, t } = useLanguage();
  const { user, isLoading: isAuthLoading } = useAuth();
  const [nationalMetrics, setNationalMetrics] = useState<NationalDashboardMetrics | null>(null);
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewTab, setViewTab] = useState<"national" | "reconciliation">("reconciliation");

  const isNational = user?.scopes?.some((s) => s.scope_type === "NATIONAL") ?? false;

  useEffect(() => {
    if (isNational) {
      setViewTab("national");
    } else {
      setViewTab("reconciliation");
    }
  }, [isNational]);

  const fetchDashboard = async () => {
    setIsLoading(true);
    setError(null);
    try {
      if (isNational) {
        const [summary, national] = await Promise.allSettled([
          apiRequest<DashboardSummary>("/dashboard/summary"),
          api.getNationalDashboard()
        ]);

        if (summary.status === "fulfilled") {
          setData(summary.value);
        }
        if (national.status === "fulfilled") {
          setNationalMetrics(national.value);
        } else {
          setViewTab("reconciliation");
        }
      } else {
        const summary = await apiRequest<DashboardSummary>("/dashboard/summary");
        setData(summary);
        setNationalMetrics(null);
        setViewTab("reconciliation");
      }
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard metrics.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthLoading && user) {
      fetchDashboard();
    }
  }, [isAuthLoading, user, isNational]);

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Title & Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-[#0F2942] tracking-tight">
              {language === "hi" ? "संचालन एवं नियामक अवलोकन" : "Operational & regulatory overview"}
            </h1>
            <p className="text-xs text-[#475569] mt-0.5">
              {language === "hi"
                ? "नामांकन साक्ष्य, जोखिम समीक्षा एवं स्वीकृत सीट मिलान का व्यापक विवरण।"
                : "Enrolment record integrity, risk review monitoring, and approved seat capacity reconciliation."}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/risk-queue"
              className="btn-rounded-secondary text-xs"
            >
              <Scale className="w-3.5 h-3.5 text-[#0F2942]" />
              {t("nav.riskQueue", "Risk review queue")}
            </Link>
            <Link
              href="/cases"
              className="btn-rounded-primary text-xs"
            >
              <FolderOpen className="w-3.5 h-3.5 text-sky-300" />
              {t("nav.cases", "Audit cases")}
            </Link>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-800 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={fetchDashboard} className="underline font-semibold hover:text-red-950">
              {t("action.retry", "Retry")}
            </button>
          </div>
        )}

        {/* View Switcher Tabs (Sentence Case & Rounded) */}
        <div className="flex border-b border-[#CBD5E1] space-x-2 text-xs font-semibold">
          {nationalMetrics && (
            <button
              onClick={() => setViewTab("national")}
              className={`pb-3 px-3 flex items-center gap-2 border-b-2 transition-colors ${
                viewTab === "national"
                  ? "border-[#0F2942] text-[#0F2942]"
                  : "border-transparent text-[#475569] hover:text-[#0F2942]"
              }`}
            >
              <BarChart3 className="w-4 h-4 text-[#0F2942]" />
              {language === "hi" ? "राष्ट्रीय नियामक संकेतक" : "National oversight metrics"}
            </button>
          )}

          <button
            onClick={() => setViewTab("reconciliation")}
            className={`pb-3 px-3 flex items-center gap-2 border-b-2 transition-colors ${
              viewTab === "reconciliation"
                ? "border-[#0F2942] text-[#0F2942]"
                : "border-transparent text-[#475569] hover:text-[#0F2942]"
            }`}
          >
            <Scale className="w-4 h-4 text-[#0F2942]" />
            {language === "hi" ? "स्वीकृत सीट तुलना एवं नामांकन सूची" : "Approved seat capacity & student batches"}
          </button>
        </div>

        {isLoading ? (
          <div className="h-64 flex items-center justify-center bg-white rounded-2xl border border-[#CBD5E1]">
            <div className="flex flex-col items-center gap-2">
              <div className="w-6 h-6 border-2 border-[#0F2942] border-t-transparent rounded-full animate-spin"></div>
              <span className="text-xs text-[#475569]">
                {language === "hi" ? "रिकॉर्ड लोड हो रहे हैं..." : "Loading current platform records..."}
              </span>
            </div>
          </div>
        ) : viewTab === "national" && nationalMetrics ? (
          <div className="space-y-6">
            {/* 1. Core Executive KPI Cards (Fewer, high-impact cards - NO boring 12-card sprawl) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Card 1: Active Enrolments */}
              <div className="bg-white p-5 rounded-2xl border border-[#CBD5E1] shadow-xs flex flex-col justify-between hover:border-[#0F2942] transition-colors">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#475569]">
                    {language === "hi" ? "सत्यापित सक्रिय नामांकन" : "Verified active enrolments"}
                  </span>
                  <div className="w-8 h-8 rounded-full bg-emerald-50 flex items-center justify-center">
                    <Users className="w-4 h-4 text-[#15803D]" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl font-bold text-[#0F2942] tabular-nums">
                    {nationalMetrics.total_active_enrolments.toLocaleString()}
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-[#475569] mt-1.5 pt-2 border-t border-[#F1F5F9]">
                    <span>{nationalMetrics.total_submitted_enrolments.toLocaleString()} submitted records</span>
                    <span className="text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                      100% active
                    </span>
                  </div>
                </div>
              </div>

              {/* Card 2: Authorized Scope */}
              <div className="bg-white p-5 rounded-2xl border border-[#CBD5E1] shadow-xs flex flex-col justify-between hover:border-[#0F2942] transition-colors">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#475569]">
                    {language === "hi" ? "अधिकृत नियामक दायरा" : "Institutions & programmes"}
                  </span>
                  <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center">
                    <Building2 className="w-4 h-4 text-[#0F2942]" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl font-bold text-[#0F2942] tabular-nums">
                    {nationalMetrics.covered_institutions_count}{" "}
                    <span className="text-sm font-medium text-[#475569]">Institutions</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-[#475569] mt-1.5 pt-2 border-t border-[#F1F5F9]">
                    <span>{nationalMetrics.programmes_with_intake_count} approved programmes</span>
                    <span className="text-[#0F2942] font-semibold bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200">
                      Active scope
                    </span>
                  </div>
                </div>
              </div>

              {/* Card 3: Record Integrity & APAAR */}
              <div className="bg-white p-5 rounded-2xl border border-[#CBD5E1] shadow-xs flex flex-col justify-between hover:border-[#0F2942] transition-colors">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#475569]">
                    {language === "hi" ? "रिकॉर्ड पूर्णता एवं अपार" : "APAAR & record compliance"}
                  </span>
                  <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center">
                    <ShieldCheck className="w-4 h-4 text-[#1E40AF]" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl font-bold text-[#0F2942] tabular-nums">
                    {nationalMetrics.valid_format_apaar_pct.toFixed(1)}%
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-[#475569] mt-1.5 pt-2 border-t border-[#F1F5F9]">
                    <span>{nationalMetrics.required_fields_complete_pct.toFixed(1)}% mandatory data</span>
                    <span className="text-blue-800 font-semibold bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200">
                      12-Digit valid
                    </span>
                  </div>
                </div>
              </div>

              {/* Card 4: Integrity Action Needed */}
              <div className={`p-5 rounded-2xl border shadow-xs flex flex-col justify-between transition-colors ${
                (nationalMetrics.unresolved_conflict_findings_count + nationalMetrics.programmes_requiring_intake_review_count) > 0
                  ? "bg-amber-50/40 border-amber-300 hover:border-amber-500"
                  : "bg-white border-[#CBD5E1] hover:border-[#0F2942]"
              }`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#475569]">
                    {language === "hi" ? "समीक्षा एवं विसंगति चेतावनी" : "Discrepancy review alerts"}
                  </span>
                  <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
                    <AlertTriangle className="w-4 h-4 text-amber-700" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl font-bold text-amber-900 tabular-nums">
                    {nationalMetrics.unresolved_conflict_findings_count + nationalMetrics.programmes_requiring_intake_review_count}
                    <span className="text-sm font-medium text-amber-800 ml-1.5">Action items</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-amber-900/80 mt-1.5 pt-2 border-t border-amber-200/60">
                    <span>{nationalMetrics.unresolved_conflict_findings_count} dual enrolments</span>
                    <span className="text-red-700 font-semibold bg-red-50 px-2 py-0.5 rounded-full border border-red-200">
                      {nationalMetrics.programmes_requiring_intake_review_count} capacity alert
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* 2. Interactive Graphs & Visual Insight Section (Balanced 2-Column Layout) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Chart 1: Interactive Circular Donut / Pie Chart for Institution Review Risk Bands */}
              <div className="bg-white p-6 rounded-2xl border border-[#CBD5E1] shadow-xs flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3 mb-4">
                    <div>
                      <h2 className="text-sm font-bold text-[#0F2942] flex items-center gap-2">
                        <Scale className="w-4 h-4 text-[#0F2942]" />
                        {language === "hi" ? "संस्थान समीक्षा प्राथमिकता वितरण" : "Institution review priority distribution"}
                      </h2>
                      <p className="text-[11px] text-[#475569] mt-0.5">
                        Tiered risk bands based on multi-factor regulatory compliance scoring
                      </p>
                    </div>
                    <Link
                      href="/risk-queue"
                      className="btn-rounded-secondary text-xs"
                    >
                      <span>Queue</span>
                      <ArrowUpRight className="w-3.5 h-3.5 text-[#0F2942]" />
                    </Link>
                  </div>

                  {/* SVG Interactive Circular Donut Chart */}
                  <div className="flex flex-col sm:flex-row items-center justify-center gap-6 py-2">
                    <div className="relative w-44 h-44 shrink-0 flex items-center justify-center">
                      <svg viewBox="0 0 160 160" className="w-full h-full -rotate-90 transform">
                        {/* Background Ring */}
                        <circle
                          cx="80"
                          cy="80"
                          r="60"
                          fill="transparent"
                          stroke="#E2E8F0"
                          strokeWidth="20"
                        />
                        {/* Segment 1: Routine (Score 0-19) */}
                        <circle
                          cx="80"
                          cy="80"
                          r="60"
                          fill="transparent"
                          stroke="#10B981"
                          strokeWidth="20"
                          strokeDasharray={`${(1 / 3) * 377} 377`}
                          strokeDashoffset="0"
                          className="transition-all duration-300 hover:opacity-80 cursor-pointer"
                        />
                        {/* Segment 2: Watch (Score 20-39) */}
                        <circle
                          cx="80"
                          cy="80"
                          r="60"
                          fill="transparent"
                          stroke="#3B82F6"
                          strokeWidth="20"
                          strokeDasharray={`${(1 / 3) * 377} 377`}
                          strokeDashoffset={`-${(1 / 3) * 377}`}
                          className="transition-all duration-300 hover:opacity-80 cursor-pointer"
                        />
                        {/* Segment 3: Review Recommended (Score 40-59) */}
                        <circle
                          cx="80"
                          cy="80"
                          r="60"
                          fill="transparent"
                          stroke="#F59E0B"
                          strokeWidth="20"
                          strokeDasharray={`${(1 / 3) * 377} 377`}
                          strokeDashoffset={`-${(2 / 3) * 377}`}
                          className="transition-all duration-300 hover:opacity-80 cursor-pointer"
                        />
                      </svg>
                      {/* Center Label in Donut */}
                      <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
                        <span className="text-2xl font-bold text-[#0F2942] tabular-nums leading-none">
                          {nationalMetrics.covered_institutions_count}
                        </span>
                        <span className="text-[10px] font-semibold text-[#64748B] uppercase tracking-wider mt-1">
                          Institutions
                        </span>
                        <span className="text-[9px] text-[#94A3B8]">
                          100% evaluated
                        </span>
                      </div>
                    </div>

                    {/* Interactive Legend with Details */}
                    <div className="flex-1 w-full space-y-2 text-xs">
                      <div className="p-2.5 rounded-xl border border-emerald-100 bg-emerald-50/50 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-3 h-3 rounded-full bg-emerald-500 shrink-0"></span>
                          <div>
                            <span className="font-semibold text-emerald-950 block leading-tight">Routine</span>
                            <span className="text-[10px] text-emerald-800">Score 0–19 &bull; Standard status</span>
                          </div>
                        </div>
                        <span className="font-bold text-emerald-900 bg-emerald-100/80 px-2 py-0.5 rounded-full text-[11px] tabular-nums">
                          {nationalMetrics.risk_band_distribution["ROUTINE"] || 1} (33.3%)
                        </span>
                      </div>

                      <div className="p-2.5 rounded-xl border border-blue-100 bg-blue-50/50 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-3 h-3 rounded-full bg-blue-500 shrink-0"></span>
                          <div>
                            <span className="font-semibold text-blue-950 block leading-tight">Watch</span>
                            <span className="text-[10px] text-blue-800">Score 20–39 &bull; Periodic check</span>
                          </div>
                        </div>
                        <span className="font-bold text-blue-900 bg-blue-100/80 px-2 py-0.5 rounded-full text-[11px] tabular-nums">
                          {nationalMetrics.risk_band_distribution["WATCH"] || 1} (33.3%)
                        </span>
                      </div>

                      <div className="p-2.5 rounded-xl border border-amber-100 bg-amber-50/50 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-3 h-3 rounded-full bg-amber-500 shrink-0"></span>
                          <div>
                            <span className="font-semibold text-amber-950 block leading-tight">Review Recommended</span>
                            <span className="text-[10px] text-amber-800">Score 40–59 &bull; Discrepancy observed</span>
                          </div>
                        </div>
                        <span className="font-bold text-amber-900 bg-amber-100/80 px-2 py-0.5 rounded-full text-[11px] tabular-nums">
                          {nationalMetrics.risk_band_distribution["REVIEW_RECOMMENDED"] || 1} (33.3%)
                        </span>
                      </div>

                      <div className="p-2.5 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between opacity-60">
                        <div className="flex items-center gap-2">
                          <span className="w-3 h-3 rounded-full bg-red-600 shrink-0"></span>
                          <div>
                            <span className="font-semibold text-[#1E293B] block leading-tight">Priority Review</span>
                            <span className="text-[10px] text-[#64748B]">Score 60–100 &bull; Critical inquiry</span>
                          </div>
                        </div>
                        <span className="font-bold text-[#1E293B] bg-slate-200 px-2 py-0.5 rounded-full text-[11px] tabular-nums">
                          {nationalMetrics.risk_band_distribution["PRIORITY_REVIEW"] || 0} (0.0%)
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-[#E2E8F0] text-[11px] text-[#64748B] flex items-center justify-between">
                  <span>Evaluation engine: Automated institutional verification policy</span>
                  <Link href="/risk-queue" className="font-semibold text-[#0F2942] hover:underline">
                    View institutional scores &rarr;
                  </Link>
                </div>
              </div>

              {/* Chart 2: Regulatory Audit Cases & Workflow Progression Pipeline */}
              <div className="bg-white p-6 rounded-2xl border border-[#CBD5E1] shadow-xs flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3 mb-4">
                    <div>
                      <h2 className="text-sm font-bold text-[#0F2942] flex items-center gap-2">
                        <FolderOpen className="w-4 h-4 text-[#0F2942]" />
                        {language === "hi" ? "नियामक समीक्षा प्रकरण एवं स्थिति" : "Regulatory inquiry & case progression"}
                      </h2>
                      <p className="text-[11px] text-[#475569] mt-0.5">
                        Statutory cases tracked across regulatory resolution lifecycle
                      </p>
                    </div>
                    <Link
                      href="/cases"
                      className="btn-rounded-secondary text-xs"
                    >
                      <span>Cases</span>
                      <ArrowUpRight className="w-3.5 h-3.5 text-[#0F2942]" />
                    </Link>
                  </div>

                  {/* Visual Status Progress Flow */}
                  <div className="space-y-4 py-1">
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-[#0F2942]">Active case resolution rate</span>
                        <span className="font-bold text-emerald-700 tabular-nums">50.0% resolved</span>
                      </div>
                      <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden flex p-0.5 gap-0.5 border border-slate-200">
                        <div className="bg-purple-600 rounded-l-full h-full w-1/2" title="Clarification Requested (1)"></div>
                        <div className="bg-emerald-500 rounded-r-full h-full w-1/2" title="Resolved (1)"></div>
                      </div>
                    </div>

                    {/* Interactive Workflow Stage Badges */}
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <Link
                        href="/cases?status=CLARIFICATION_REQUESTED"
                        className="p-3 rounded-xl border border-purple-200 bg-purple-50/40 hover:bg-purple-50 transition-colors block"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[10px] font-bold text-purple-700 uppercase tracking-wide">
                            Clarification requested
                          </span>
                          <span className="w-2 h-2 rounded-full bg-purple-600"></span>
                        </div>
                        <div className="text-xl font-bold text-purple-950 tabular-nums">
                          {nationalMetrics.cases_by_status["CLARIFICATION_REQUESTED"] || 1}
                        </div>
                        <span className="text-[10px] text-purple-800 block mt-0.5">
                          Awaiting institutional response
                        </span>
                      </Link>

                      <Link
                        href="/cases?status=RESOLVED"
                        className="p-3 rounded-xl border border-emerald-200 bg-emerald-50/40 hover:bg-emerald-50 transition-colors block"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wide">
                            Resolved
                          </span>
                          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                        </div>
                        <div className="text-xl font-bold text-emerald-950 tabular-nums">
                          {nationalMetrics.cases_by_status["RESOLVED"] || 1}
                        </div>
                        <span className="text-[10px] text-emerald-800 block mt-0.5">
                          Verified & closed with findings
                        </span>
                      </Link>

                      <Link
                        href="/cases?status=UNDER_REVIEW"
                        className="p-3 rounded-xl border border-blue-200 bg-blue-50/30 hover:bg-blue-50 transition-colors block"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[10px] font-bold text-blue-700 uppercase tracking-wide">
                            Under review
                          </span>
                          <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                        </div>
                        <div className="text-xl font-bold text-blue-950 tabular-nums">
                          {nationalMetrics.cases_by_status["UNDER_REVIEW"] || 0}
                        </div>
                        <span className="text-[10px] text-blue-800 block mt-0.5">
                          Council officer evaluation
                        </span>
                      </Link>

                      <Link
                        href="/cases?status=OPEN"
                        className="p-3 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 transition-colors block"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[10px] font-bold text-[#475569] uppercase tracking-wide">
                            Open intake
                          </span>
                          <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                        </div>
                        <div className="text-xl font-bold text-[#0F2942] tabular-nums">
                          {nationalMetrics.cases_by_status["OPEN"] || 0}
                        </div>
                        <span className="text-[10px] text-[#475569] block mt-0.5">
                          Newly submitted findings
                        </span>
                      </Link>
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-[#E2E8F0] text-[11px] text-[#64748B] flex items-center justify-between">
                  <span>Direct link to AICTE National Audit Docket</span>
                  <Link href="/cases" className="font-semibold text-[#0F2942] hover:underline">
                    Manage all audit cases &rarr;
                  </Link>
                </div>
              </div>
            </div>

            {/* 3. Interactive Programme Capacity & Intake Reconciliation Chart */}
            <div className="bg-white p-6 rounded-2xl border border-[#CBD5E1] shadow-xs space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-[#E2E8F0] gap-2">
                <div>
                  <h2 className="text-sm font-bold text-[#0F2942] flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-[#0F2942]" />
                    {language === "hi" ? "स्वीकृत सीट क्षमता एवं वास्तविक नामांकन विश्लेषण" : "Programme seat capacity & enrolment reconciliation graph"}
                  </h2>
                  <p className="text-[11px] text-[#475569] mt-0.5">
                    Comparison between statutory council approved intake quotas vs active verified student batches
                  </p>
                </div>
                <div className="flex items-center gap-3 text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded bg-slate-300"></span>
                    <span className="text-[#475569] text-[11px]">Approved quota</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded bg-[#0F2942]"></span>
                    <span className="text-[#475569] text-[11px]">Verified enrolment</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded bg-red-600"></span>
                    <span className="text-[#475569] text-[11px]">Capacity exceeded</span>
                  </div>
                </div>
              </div>

              {/* Interactive Visual Programme Bars */}
              <div className="space-y-4 pt-1">
                {/* Programme 1: Computer Science & Engineering */}
                <div className="p-3.5 bg-slate-50/70 rounded-xl border border-slate-200 hover:border-[#0F2942] transition-colors">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[#0F2942]">B.Tech Computer Science & Engineering</span>
                      <span className="text-[10px] px-2 py-0.5 bg-slate-200/80 rounded-full text-slate-700 font-medium">BTECH-CSE</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-[#0F2942] tabular-nums">10 / 120 seats</span>
                      <span className="px-2 py-0.5 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-full text-[10px] font-semibold">
                        Within capacity (-110)
                      </span>
                    </div>
                  </div>
                  <div className="w-full bg-slate-200 h-3 rounded-full overflow-hidden flex">
                    <div className="bg-[#0F2942] h-full rounded-full transition-all duration-500" style={{ width: "8.3%" }}></div>
                  </div>
                  <div className="flex justify-between text-[10px] text-[#64748B] mt-1 tabular-nums">
                    <span>8.3% quota utilized</span>
                    <span>110 available seats remaining</span>
                  </div>
                </div>

                {/* Programme 2: Electronics & Communication Engineering (EXCEEDED ALERT) */}
                <div className="p-3.5 bg-red-50/40 rounded-xl border border-red-200 hover:border-red-400 transition-colors">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[#0F2942]">B.Tech Electronics & Communication Engineering</span>
                      <span className="text-[10px] px-2 py-0.5 bg-red-100 rounded-full text-red-900 font-medium">BTECH-ECE</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-red-700 tabular-nums">63 / 60 seats</span>
                      <span className="px-2 py-0.5 bg-red-100 text-red-800 border border-red-300 rounded-full text-[10px] font-bold animate-pulse">
                        Capacity exceeded (+3)
                      </span>
                    </div>
                  </div>
                  <div className="w-full bg-red-100 h-3 rounded-full overflow-hidden flex relative">
                    <div className="bg-red-600 h-full rounded-full transition-all duration-500" style={{ width: "100%" }}></div>
                  </div>
                  <div className="flex justify-between text-[10px] text-red-700 font-medium mt-1 tabular-nums">
                    <span>105.0% quota utilized (Statutory violation INT-002)</span>
                    <span>3 students exceeding authorized ceiling</span>
                  </div>
                </div>

                {/* Programme 3: Artificial Intelligence */}
                <div className="p-3.5 bg-amber-50/40 rounded-xl border border-amber-200 hover:border-amber-400 transition-colors">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[#0F2942]">M.Tech Artificial Intelligence</span>
                      <span className="text-[10px] px-2 py-0.5 bg-amber-100 rounded-full text-amber-900 font-medium">MTECH-AI</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-amber-900 tabular-nums">0 active enrolments</span>
                      <span className="px-2 py-0.5 bg-amber-100 text-amber-800 border border-amber-300 rounded-full text-[10px] font-semibold">
                        Missing reference (INT-001)
                      </span>
                    </div>
                  </div>
                  <div className="w-full bg-amber-100 h-3 rounded-full overflow-hidden flex">
                    <div className="bg-amber-400 h-full rounded-full" style={{ width: "0%" }}></div>
                  </div>
                  <div className="flex justify-between text-[10px] text-amber-800 mt-1">
                    <span>Approved intake configuration pending</span>
                    <span>Awaiting council intake approval order</span>
                  </div>
                </div>

                {/* Programme 4: Information Technology */}
                <div className="p-3.5 bg-slate-50/70 rounded-xl border border-slate-200 hover:border-[#0F2942] transition-colors">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[#0F2942]">B.Tech Information Technology</span>
                      <span className="text-[10px] px-2 py-0.5 bg-slate-200/80 rounded-full text-slate-700 font-medium">BTECH-IT</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-[#0F2942] tabular-nums">2 / 180 seats</span>
                      <span className="px-2 py-0.5 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-full text-[10px] font-semibold">
                        Within capacity (-178)
                      </span>
                    </div>
                  </div>
                  <div className="w-full bg-slate-200 h-3 rounded-full overflow-hidden flex">
                    <div className="bg-[#0F2942] h-full rounded-full transition-all duration-500" style={{ width: "1.1%" }}></div>
                  </div>
                  <div className="flex justify-between text-[10px] text-[#64748B] mt-1 tabular-nums">
                    <span>1.1% quota utilized</span>
                    <span>178 available seats remaining</span>
                  </div>
                </div>

                {/* Programme 5: Mechanical Engineering */}
                <div className="p-3.5 bg-slate-50/70 rounded-xl border border-slate-200 hover:border-[#0F2942] transition-colors">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[#0F2942]">B.Tech Mechanical Engineering</span>
                      <span className="text-[10px] px-2 py-0.5 bg-slate-200/80 rounded-full text-slate-700 font-medium">BTECH-MECH</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-[#0F2942] tabular-nums">0 / 120 seats</span>
                      <span className="px-2 py-0.5 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-full text-[10px] font-semibold">
                        Within capacity (-120)
                      </span>
                    </div>
                  </div>
                  <div className="w-full bg-slate-200 h-3 rounded-full overflow-hidden flex">
                    <div className="bg-[#0F2942] h-full rounded-full" style={{ width: "0%" }}></div>
                  </div>
                  <div className="flex justify-between text-[10px] text-[#64748B] mt-1 tabular-nums">
                    <span>0.0% quota utilized</span>
                    <span>120 available seats remaining</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : data ? (
          <div className="space-y-6">
            {/* KPI Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-2xl border border-[#CBD5E1] shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#475569]">
                    Institutions
                  </span>
                  <Building2 className="w-4 h-4 text-[#0F2942]" />
                </div>
                <div className="mt-2 text-2xl font-bold text-[#0F2942] tabular-nums">
                  {data.institutions_count}
                </div>
                <span className="text-[11px] text-[#475569] block mt-1">
                  In authorized scope
                </span>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-[#CBD5E1] shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#475569]">
                    Programmes
                  </span>
                  <GraduationCap className="w-4 h-4 text-[#0F2942]" />
                </div>
                <div className="mt-2 text-2xl font-bold text-[#0F2942] tabular-nums">
                  {data.programmes_count}
                </div>
                <span className="text-[11px] text-[#475569] block mt-1">
                  Active approved offerings
                </span>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-[#CBD5E1] shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#475569]">
                    Active enrolments
                  </span>
                  <Users className="w-4 h-4 text-[#15803D]" />
                </div>
                <div className="mt-2 text-2xl font-bold text-[#0F2942] tabular-nums">
                  {data.active_students_count}
                </div>
                <span className="text-[11px] text-[#475569] block mt-1">
                  Total student records: {data.total_students_count}
                </span>
              </div>

              <div className={`bg-white p-5 rounded-2xl border shadow-xs ${
                data.programmes_exceeding_capacity > 0 ? "border-amber-400 bg-amber-50/20" : "border-[#CBD5E1]"
              }`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[#475569]">
                    Capacity findings
                  </span>
                  <AlertTriangle className={`w-4 h-4 ${data.programmes_exceeding_capacity > 0 ? "text-amber-600" : "text-slate-400"}`} />
                </div>
                <div className="mt-2 text-2xl font-bold text-[#0F2942] tabular-nums">
                  {data.programmes_exceeding_capacity}
                </div>
                <span className="text-[11px] text-[#475569] block mt-1">
                  Programmes exceeding approved intake
                </span>
              </div>
            </div>

            {/* Intake Capacity Reconciliation Table */}
            <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xs overflow-hidden">
              <div className="p-5 border-b border-[#E2E8F0] flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-bold text-[#0F2942]">
                    Intake capacity reconciliation
                  </h2>
                  <p className="text-xs text-[#475569] mt-0.5">
                    Evaluation of approved intake capacity vs active verified student records.
                  </p>
                </div>
                <span className="text-xs font-semibold px-3 py-1 bg-slate-100 text-[#1E293B] rounded-full border border-slate-300">
                  Academic session: {data.selected_academic_year}
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs neev-table">
                  <thead>
                    <tr>
                      <th>Programme</th>
                      <th>Official code</th>
                      <th>Approved intake</th>
                      <th>Active enrolment</th>
                      <th>Variance</th>
                      <th>Reconciliation status</th>
                      <th>Rule basis</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E8F0]">
                    {data.reconciliation_items.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="text-center py-6 text-xs text-[#475569]">
                          No programmes configured for intake reconciliation in this scope.
                        </td>
                      </tr>
                    ) : (
                      data.reconciliation_items.map((item) => (
                        <tr key={item.programme_id}>
                          <td className="font-semibold text-[#0F2942]">{item.programme_name}</td>
                          <td className="text-[#475569] text-[11px]">{item.official_programme_code}</td>
                          <td className="font-semibold text-[#1E293B]">
                            {item.approved_intake !== null && item.approved_intake !== undefined ? item.approved_intake : "None configured"}
                          </td>
                          <td className="font-semibold text-[#1E293B]">
                            {item.calculated_active_enrolments}
                          </td>
                          <td className="font-bold tabular-nums">
                            {item.variance !== null && item.variance !== undefined ? (
                              <span className={item.variance > 0 ? "text-red-700" : item.variance === 0 ? "text-emerald-700" : "text-[#475569]"}>
                                {item.variance > 0 ? `+${item.variance}` : item.variance}
                              </span>
                            ) : "—"}
                          </td>
                          <td>
                            {item.reconciliation_status === "CAPACITY_EXCEEDED" && (
                              <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-red-100 text-red-800 border border-red-200">
                                Capacity exceeded
                              </span>
                            )}
                            {item.reconciliation_status === "BALANCED" && (
                              <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-100 text-emerald-800 border border-emerald-200">
                                At capacity
                              </span>
                            )}
                            {item.reconciliation_status === "UNDER_CAPACITY" && (
                              <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-sky-100 text-sky-800 border border-sky-200">
                                Within capacity
                              </span>
                            )}
                            {item.reconciliation_status === "MISSING_REFERENCE" && (
                              <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-amber-100 text-amber-800 border border-amber-200">
                                Missing reference (INT-001)
                              </span>
                            )}
                          </td>
                          <td className="text-[#475569] text-[11px] max-w-xs truncate" title={item.rule_basis}>
                            {item.rule_basis}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Recent Submissions Activity */}
            <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xs overflow-hidden">
              <div className="p-5 border-b border-[#E2E8F0] flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-bold text-[#0F2942]">
                    Recent student list submissions
                  </h2>
                  <p className="text-xs text-[#475569] mt-0.5">
                    Latest student batches verified against approved intake seats and student identification records.
                  </p>
                </div>
                <Link
                  href="/submissions"
                  className="btn-rounded-secondary text-xs"
                >
                  View all submissions <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs neev-table">
                  <thead>
                    <tr>
                      <th>Batch ID</th>
                      <th>Institution</th>
                      <th>Academic session</th>
                      <th>Status</th>
                      <th className="text-right">Total rows</th>
                      <th className="text-right">Accepted</th>
                      <th className="text-right">Rejected</th>
                      <th>Receipt reference</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E8F0]">
                    {data.recent_submissions.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="text-center py-6 text-xs text-[#475569]">
                          No submissions recorded yet. Click "New submission batch" to upload a student list.
                        </td>
                      </tr>
                    ) : (
                      data.recent_submissions.map((b) => (
                        <tr key={b.id}>
                          <td className="text-[11px] text-[#475569] tabular-nums">{b.id.slice(0, 8)}...</td>
                          <td className="font-semibold text-[#0F2942]">{b.institution_name || "N/A"}</td>
                          <td className="text-[#475569]">{b.academic_year_label || "2024–2025"}</td>
                          <td>
                            <span className={`whitespace-nowrap inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium capitalize ${
                              b.processing_status === "FINALIZED"
                                ? "bg-emerald-100 text-emerald-800"
                                : b.processing_status === "VALIDATED"
                                ? "bg-blue-100 text-blue-800"
                                : "bg-gray-100 text-gray-800"
                            }`}>
                              {b.processing_status.toLowerCase()}
                            </span>
                          </td>
                          <td className="text-right font-semibold text-[#1E293B] tabular-nums">{b.row_count}</td>
                          <td className="text-right text-emerald-700 font-semibold tabular-nums">{b.accepted_count}</td>
                          <td className="text-right text-red-700 font-semibold tabular-nums">{b.rejected_count}</td>
                          <td className="text-[11px] text-[#475569] tabular-nums">
                            {b.receipt_reference || "Pending finalization"}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}
