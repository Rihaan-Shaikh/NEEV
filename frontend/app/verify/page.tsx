"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { api, VerificationResultResponse } from "@/lib/api";
import { useLanguage } from "@/lib/language-context";
import NeevHeaderTitle from "@/components/common/NeevHeaderTitle";
import NeevEmblem from "@/components/common/NeevEmblem";
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Search,
  Clock,
  Volume2,
  FileCheck2,
  GraduationCap,
  Building,
  UserCheck
} from "lucide-react";

export default function PublicVerifyPage() {
  const { language, setLanguage, t } = useLanguage();
  const [tokenInput, setTokenInput] = useState("");
  const [result, setResult] = useState<VerificationResultResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState<string>("");
  const [fontSizeLevel, setFontSizeLevel] = useState<"small" | "normal" | "large">("normal");

  // Live IST Clock
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const options: Intl.DateTimeFormatOptions = {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: true,
      };
      setCurrentTime(now.toLocaleString("en-IN", options));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Functional Font Sizer - Font Size ONLY (No whole-page zoom)
  const handleSetFontSize = (level: "small" | "normal" | "large") => {
    setFontSizeLevel(level);
    try {
      localStorage.setItem("neev_font_size", level);
    } catch {}
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("data-font-size", level);
      document.body.setAttribute("data-font-size", level);
      const fontVal = level === "small" ? "13.5px" : level === "large" ? "17.5px" : "15px";
      document.documentElement.style.fontSize = fontVal;
      document.body.style.fontSize = fontVal;
      (document.body.style as any).zoom = "";
    }
  };

  useEffect(() => {
    try {
      const saved = localStorage.getItem("neev_font_size") as "small" | "normal" | "large" | null;
      const initial = saved || "normal";
      setFontSizeLevel(initial);
      if (typeof document !== "undefined") {
        document.documentElement.setAttribute("data-font-size", initial);
        document.body.setAttribute("data-font-size", initial);
        const fontVal = initial === "small" ? "13.5px" : initial === "large" ? "17.5px" : "15px";
        document.documentElement.style.fontSize = fontVal;
        document.body.style.fontSize = fontVal;
        (document.body.style as any).zoom = "";
      }
    } catch {}
  }, []);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tokenInput.trim()) return;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.verifyReferenceToken(tokenInput.trim());
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to verify credentials. The reference code may be expired or invalid.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col justify-between">
      {/* 1. Top Utility Bar with Left Alignment */}
      <div className="bg-[#0A1C2E] border-b border-[#16365C] pl-4 sm:pl-8 lg:pl-[12%] pr-4 sm:pr-8 lg:pr-[6%] py-1.5 flex flex-wrap items-center justify-between text-xs text-slate-200 shrink-0 select-none">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-300">
            <Clock className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span className="tabular-nums font-medium">{currentTime || "Academic session 2024–2025"}</span>
          </div>
          <span className="hidden md:inline-block w-1 h-1 rounded-full bg-slate-500"></span>
          <span className="hidden md:inline-block text-[11px] text-slate-300">
            {language === "hi" ? "सार्वजनिक साक्ष्य सत्यापन सेवा" : "Public Credential Verification Service"}
          </span>
        </div>

        <div className="flex items-center gap-3 sm:gap-4 ml-auto">
          {/* Functional Text Size: A-  A  A+ */}
          <div className="flex items-center gap-1 text-[11px]">
            <span className="text-slate-400 mr-1 hidden sm:inline">Text Size:</span>
            <button
              type="button"
              onClick={() => handleSetFontSize("small")}
              className={`px-1.5 py-0.5 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                fontSizeLevel === "small" ? "bg-amber-400 text-[#0F2942]" : "hover:bg-[#16365C] text-slate-200"
              }`}
              title="Decrease text size (A-)"
            >
              A-
            </button>
            <button
              type="button"
              onClick={() => handleSetFontSize("normal")}
              className={`px-1.5 py-0.5 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                fontSizeLevel === "normal" ? "bg-amber-400 text-[#0F2942]" : "hover:bg-[#16365C] text-slate-200"
              }`}
              title="Standard text size (A)"
            >
              A
            </button>
            <button
              type="button"
              onClick={() => handleSetFontSize("large")}
              className={`px-1.5 py-0.5 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                fontSizeLevel === "large" ? "bg-amber-400 text-[#0F2942]" : "hover:bg-[#16365C] text-slate-200"
              }`}
              title="Increase text size (A+)"
            >
              A+
            </button>
          </div>

          <span className="text-slate-600 hidden sm:inline">|</span>

          {/* Bilingual Selector */}
          <div className="flex items-center rounded-full bg-[#16365C] p-0.5 text-[11px] font-medium">
            <button
              type="button"
              onClick={() => setLanguage("en")}
              className={`px-2 py-0.5 rounded-full transition-colors cursor-pointer ${
                language === "en"
                  ? "bg-amber-400 text-[#0F2942] font-bold"
                  : "text-slate-200 hover:text-white"
              }`}
            >
              English
            </button>
            <button
              type="button"
              onClick={() => setLanguage("hi")}
              className={`px-2 py-0.5 rounded-full transition-colors cursor-pointer ${
                language === "hi"
                  ? "bg-amber-400 text-[#0F2942] font-bold"
                  : "text-slate-200 hover:text-white"
              }`}
            >
              हिन्दी
            </button>
          </div>
        </div>
      </div>

      {/* 2. Official Masthead with Circular Emblem & Indian Flag Colors */}
      <header className="bg-white border-b border-[#CBD5E1] pl-4 sm:pl-8 lg:pl-[12%] pr-4 sm:pr-8 lg:pr-[6%] py-3.5 flex items-center justify-between shrink-0 shadow-xs">
        <Link href="/login" className="group">
          <NeevHeaderTitle emblemSize={52} />
        </Link>

        {/* Clean Link back to Authorized Login */}
        <Link
          href="/login"
          className="btn-rounded-secondary text-xs flex items-center gap-1.5 cursor-pointer"
        >
          <span>{language === "hi" ? "अधिकारी प्रवेश द्वार" : "Authorized officer sign in"}</span>
          <ArrowRight className="w-3.5 h-3.5 text-[#0F2942]" />
        </Link>
      </header>

      {/* 3. Main Verification Canvas */}
      <main className="flex-1 w-full pl-4 sm:pl-8 lg:pl-[12%] pr-4 sm:pr-8 lg:pr-[6%] py-8 space-y-6">
        {/* Verification Overview Banner */}
        <div className="p-4 bg-white border border-[#CBD5E1] rounded-2xl shadow-xs space-y-1">
          <div className="flex items-center gap-2">
            <FileCheck2 className="w-4 h-4 text-[#0F2942]" />
            <h1 className="text-sm font-bold text-[#0F2942]">
              {language === "hi" ? "वैधानिक छात्र साक्ष्य एवं उपाधि सत्यापन" : "Statutory academic credential & enrolment verification"}
            </h1>
          </div>
          <p className="text-xs text-[#475569] leading-relaxed">
            Verify official student admissions, enrolment authenticity, and degree records issued by council-recognized universities and colleges.
          </p>
        </div>

        {/* Verification Form Card */}
        <div className="bg-white p-6 sm:p-8 rounded-2xl border border-[#CBD5E1] shadow-xs space-y-5">
          <div className="space-y-1 border-b border-[#E2E8F0] pb-4">
            <h2 className="text-base font-bold text-[#0F2942]">
              {language === "hi" ? "सत्यापन संदर्भ कोड दर्ज करें" : "Enter verification reference code"}
            </h2>
            <p className="text-xs text-[#475569]">
              Enter the unique reference code printed on the official academic transcript, certificate, or institutional document.
            </p>
          </div>

          <form onSubmit={handleVerify} className="space-y-4">
            <div>
              <label htmlFor="tokenField" className="block text-xs font-semibold text-[#1E293B] mb-1.5">
                {language === "hi" ? "सत्यापन संदर्भ कोड" : "Official reference code / digital token"}
              </label>
              <div className="relative">
                <input
                  id="tokenField"
                  type="text"
                  value={tokenInput}
                  onChange={(e) => setTokenInput(e.target.value)}
                  placeholder="e.g. VRF-2026-DL-88319 or credential token"
                  className="w-full pl-4 pr-10 py-2.5 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                  required
                />
                <Search className="w-4 h-4 text-slate-400 absolute right-3.5 top-3 pointer-events-none" />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || !tokenInput.trim()}
              className="btn-rounded-primary py-2.5 px-6 disabled:opacity-50 cursor-pointer flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Verifying against master registry...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4 text-white" />
                  <span>Verify credential authenticity</span>
                </>
              )}
            </button>
          </form>

          {error && (
            <div className="p-3.5 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Verification Result Dossier */}
        {result && (
          <div className="bg-white rounded-2xl border-2 border-emerald-300 shadow-sm overflow-hidden space-y-4 p-6 sm:p-8 animate-in fade-in duration-200">
            {/* Certificate Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#E2E8F0]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center shrink-0 border border-emerald-300">
                  <CheckCircle2 className="w-5 h-5 text-emerald-700" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-[#0F2942]">
                    Official Verification Dossier — Verified Record
                  </h2>
                  <p className="text-xs text-[#475569]">
                    Verified timestamp: {new Date(result.verified_at).toLocaleDateString("en-IN", {
                      day: "numeric",
                      month: "long",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit"
                    })}
                  </p>
                </div>
              </div>

              {result.public_reference_code && (
                <span className="px-3.5 py-1 bg-slate-100 text-[#0F2942] text-xs font-bold rounded-full border border-slate-300 w-fit tabular-nums">
                  Reference: {result.public_reference_code}
                </span>
              )}
            </div>

            {/* Official Confirmation Banner */}
            <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-900 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-700 shrink-0" />
              <p className="font-semibold">{result.message}</p>
            </div>

            {/* Disclosed Credential Details */}
            {result.disclosed_claims && (
              <div className="space-y-3 pt-2">
                <h3 className="text-xs font-bold text-[#0F2942] uppercase tracking-wider border-b border-[#E2E8F0] pb-1.5">
                  Verified Academic Credentials
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  {result.disclosed_claims.student_full_name && (
                    <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                      <span className="text-[11px] font-semibold text-[#64748B] block">
                        Student Full Name
                      </span>
                      <span className="font-bold text-sm text-[#0F2942]">
                        {result.disclosed_claims.student_full_name}
                      </span>
                    </div>
                  )}

                  {result.disclosed_claims.enrolment_status && (
                    <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                      <span className="text-[11px] font-semibold text-[#64748B] block">
                        Enrolment Status
                      </span>
                      <span className="inline-block px-3 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                        {result.disclosed_claims.enrolment_status}
                      </span>
                    </div>
                  )}

                  {result.disclosed_claims.institution_name && (
                    <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                      <span className="text-[11px] font-semibold text-[#64748B] block">
                        Recognized Educational Institution
                      </span>
                      <span className="font-semibold text-xs text-[#0F2942]">
                        {result.disclosed_claims.institution_name}
                      </span>
                    </div>
                  )}

                  {result.disclosed_claims.programme_name && (
                    <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                      <span className="text-[11px] font-semibold text-[#64748B] block">
                        Academic Course & Level
                      </span>
                      <span className="font-semibold text-xs text-[#0F2942]">
                        {result.disclosed_claims.programme_name}
                      </span>
                    </div>
                  )}

                  {result.disclosed_claims.academic_year && (
                    <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                      <span className="text-[11px] font-semibold text-[#64748B] block">
                        Academic Year / Session
                      </span>
                      <span className="font-semibold text-xs text-[#0F2942]">
                        {result.disclosed_claims.academic_year}
                      </span>
                    </div>
                  )}

                  {result.disclosed_claims.admission_date && (
                    <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                      <span className="text-[11px] font-semibold text-[#64748B] block">
                        Verified Admission Date
                      </span>
                      <span className="font-semibold text-xs text-[#0F2942]">
                        {result.disclosed_claims.admission_date}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="pt-3 border-t border-slate-200 text-[11px] text-[#64748B] flex items-center justify-between flex-wrap gap-2">
              <span>Verified against National Education Evidence and Verification master database.</span>
              <span className="font-semibold text-[#0F2942]">Cryptographically signed by NEEV Registry</span>
            </div>
          </div>
        )}
      </main>

      {/* 4. Footer with Circular Emblem & Left Alignment */}
      <footer className="bg-[#0F2942] text-white border-t border-[#16365C] text-xs py-6 pl-4 sm:pl-8 lg:pl-[12%] pr-4 sm:pr-8 lg:pr-[6%] mt-auto">
        <div className="w-full flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <NeevEmblem size={36} />
            <div>
              <p className="font-bold text-slate-100">राष्ट्रीय शिक्षा साक्ष्य एवं सत्यापन</p>
              <p className="text-[11px] text-slate-300">National Education Evidence and Verification</p>
            </div>
          </div>
          <p className="text-[11px] text-slate-300 text-center md:text-right">
            Designed in accordance with Council Verification Guidelines and GIGW Standards. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
