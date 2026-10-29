"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useLanguage } from "@/lib/language-context";
import NeevEmblem from "@/components/common/NeevEmblem";
import NeevHeaderTitle from "@/components/common/NeevHeaderTitle";
import { 
  Building2, 
  ShieldCheck, 
  User, 
  Mail, 
  Phone, 
  FileText, 
  CheckCircle2, 
  ArrowLeft, 
  Clock, 
  AlertCircle,
  HelpCircle,
  Lock,
  ArrowRight
} from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const { language, setLanguage } = useLanguage();
  const [currentTime, setCurrentTime] = useState<string>("");
  const [fontSizeLevel, setFontSizeLevel] = useState<"small" | "normal" | "large">("normal");

  // Form fields
  const [institutionCode, setInstitutionCode] = useState("");
  const [institutionName, setInstitutionName] = useState("");
  const [institutionType, setInstitutionType] = useState("CENTRAL_UNIVERSITY");
  const [stateCode, setStateCode] = useState("DL");
  const [district, setDistrict] = useState("");
  const [campusAddress, setCampusAddress] = useState("");
  const [officerName, setOfficerName] = useState("");
  const [officerDesignation, setOfficerDesignation] = useState("Registrar");
  const [officerEmail, setOfficerEmail] = useState("");
  const [officerPhone, setOfficerPhone] = useState("");
  const [councilLetterRef, setCouncilLetterRef] = useState("");
  const [hasDeclared, setHasDeclared] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successDossier, setSuccessDossier] = useState<{
    referenceCode: string;
    submittedAt: string;
  } | null>(null);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!hasDeclared) {
      setErrorMsg(
        language === "hi"
          ? "कृपया अधिकृत घोषणा पत्र पर सहमति प्रदान करें।"
          : "Please check and affirm the statutory declaration to proceed."
      );
      return;
    }

    if (!officerEmail.includes("@")) {
      setErrorMsg("Please provide a valid institutional email address.");
      return;
    }

    setIsSubmitting(true);
    try {
      // Simulate registration submission with rate-limit and latency safety
      await new Promise((resolve) => setTimeout(resolve, 800));

      const trackingCode = `REG-2026-${Math.floor(100000 + Math.random() * 900000)}`;
      setSuccessDossier({
        referenceCode: trackingCode,
        submittedAt: new Date().toLocaleString("en-IN", {
          day: "numeric",
          month: "long",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        }),
      });
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to submit institutional onboarding application.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col justify-between">
      {/* 1. Official Utility Bar */}
      <div className="bg-[#0A1C2E] border-b border-[#16365C] pl-4 sm:pl-8 lg:pl-[12%] pr-4 sm:pr-8 lg:pr-[6%] py-1.5 flex flex-wrap items-center justify-between text-xs text-slate-200 shrink-0 select-none">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-300">
            <Clock className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span className="tabular-nums font-medium">{currentTime || "Academic session 2024–2025"}</span>
          </div>
          <span className="hidden md:inline-block w-1 h-1 rounded-full bg-slate-500"></span>
          <span className="hidden md:inline-block text-[11px] text-slate-300">
            {language === "hi" ? "संस्थागत ऑनबोर्डिंग एवं अधिकृत पंजीकरण" : "Institutional Onboarding and Officer Registration"}
          </span>
        </div>

        <div className="flex items-center gap-3 sm:gap-4 ml-auto">
          {/* Text Size: A-  A  A+ */}
          <div className="flex items-center gap-1 text-[11px]">
            <span className="text-slate-400 mr-1 hidden sm:inline">Text Size:</span>
            <button
              type="button"
              onClick={() => handleSetFontSize("small")}
              className={`px-1.5 py-0.5 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                fontSizeLevel === "small" ? "bg-amber-400 text-[#0F2942]" : "hover:bg-[#16365C] text-slate-200"
              }`}
              title="Decrease text size"
            >
              A-
            </button>
            <button
              type="button"
              onClick={() => handleSetFontSize("normal")}
              className={`px-1.5 py-0.5 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                fontSizeLevel === "normal" ? "bg-amber-400 text-[#0F2942]" : "hover:bg-[#16365C] text-slate-200"
              }`}
              title="Standard text size"
            >
              A
            </button>
            <button
              type="button"
              onClick={() => handleSetFontSize("large")}
              className={`px-1.5 py-0.5 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                fontSizeLevel === "large" ? "bg-amber-400 text-[#0F2942]" : "hover:bg-[#16365C] text-slate-200"
              }`}
              title="Increase text size"
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

      {/* 2. Official Masthead with Circular NEEV Emblem & Indian Flag Colors */}
      <header className="bg-white border-b border-[#CBD5E1] pl-4 sm:pl-8 lg:pl-[12%] pr-4 sm:pr-8 lg:pr-[6%] py-3.5 flex items-center justify-between shrink-0 shadow-xs">
        <Link href="/login" className="group">
          <NeevHeaderTitle emblemSize={52} />
        </Link>

        <Link
          href="/login"
          className="btn-rounded-secondary text-xs flex items-center gap-1.5 cursor-pointer"
        >
          <ArrowLeft className="w-3.5 h-3.5 text-[#0F2942]" />
          <span>{language === "hi" ? "प्रवेश पृष्ठ पर वापस" : "Back to sign in"}</span>
        </Link>
      </header>

      {/* 3. Main Form Container */}
      <main className="py-8 px-4 sm:px-6 lg:px-8 flex-1 max-w-3xl mx-auto w-full">
        {successDossier ? (
          /* Submission Acknowledgment Card */
          <div className="bg-white p-6 sm:p-8 rounded-2xl border border-[#CBD5E1] shadow-sm space-y-6 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center gap-3 pb-4 border-b border-[#E2E8F0]">
              <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                <CheckCircle2 className="w-6 h-6 text-emerald-700" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-[#0F2942]">
                  {language === "hi" ? "संस्थागत ऑनबोर्डिंग आवेदन सफलतापूर्वक दर्ज" : "Institutional registration application registered"}
                </h2>
                <p className="text-xs text-[#475569] mt-0.5">
                  Your formal request for institutional portal access has been recorded in the regulatory clearance queue.
                </p>
              </div>
            </div>

            {/* Application Dossier Card */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <span className="text-[#64748B] block text-[11px]">Application Tracking Code</span>
                  <span className="font-bold text-sm text-[#0F2942] tabular-nums block mt-0.5">
                    {successDossier.referenceCode}
                  </span>
                </div>
                <div>
                  <span className="text-[#64748B] block text-[11px]">Submission Timestamp</span>
                  <span className="font-semibold text-[#1E293B] block mt-0.5">
                    {successDossier.submittedAt}
                  </span>
                </div>
                <div>
                  <span className="text-[#64748B] block text-[11px]">Institution Code & Name</span>
                  <span className="font-semibold text-[#1E293B] block mt-0.5">
                    {institutionCode} — {institutionName}
                  </span>
                </div>
                <div>
                  <span className="text-[#64748B] block text-[11px]">Authorized Officer</span>
                  <span className="font-semibold text-[#1E293B] block mt-0.5">
                    {officerName} ({officerDesignation})
                  </span>
                </div>
              </div>
            </div>

            {/* Verification Process Notice */}
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-900 space-y-2">
              <span className="font-bold block">Next regulatory verification steps:</span>
              <ol className="list-decimal pl-5 space-y-1 text-[11px] leading-relaxed text-blue-800">
                <li>Council regulatory review officers verify your institutional affiliation letter against the master directory.</li>
                <li>An official activation link and cryptographic access credentials will be securely dispatched to <strong>{officerEmail}</strong>.</li>
                <li>Your designated nodal officer will complete multi-factor verification before uploading student enrolment lists.</li>
              </ol>
            </div>

            <div className="pt-2 flex justify-end">
              <Link
                href="/login"
                className="btn-rounded-primary text-xs py-2 px-5 flex items-center gap-2"
              >
                <span>Return to authorized sign-in</span>
                <ArrowRight className="w-3.5 h-3.5 text-white" />
              </Link>
            </div>
          </div>
        ) : (
          /* Registration Form */
          <div className="bg-white p-6 sm:p-8 rounded-2xl border border-[#CBD5E1] shadow-sm space-y-6">
            <div>
              <div className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-[#0F2942]" />
                <h1 className="text-lg font-bold text-[#0F2942]">
                  {language === "hi" ? "संस्थागत ऑनबोर्डिंग एवं नोडल अधिकारी पंजीकरण" : "Institutional onboarding & officer registration"}
                </h1>
              </div>
              <p className="text-xs text-[#475569] mt-1">
                Statutory registration gateway for recognized higher education institutions, deemed universities, and autonomous colleges.
              </p>
            </div>

            {errorMsg && (
              <div className="p-3.5 bg-red-50 border border-red-200 rounded-xl flex items-start gap-2.5 text-xs text-red-800">
                <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Section 1: Institution Master Details */}
              <div className="space-y-4">
                <h2 className="text-xs font-bold text-[#0F2942] uppercase tracking-wider border-b border-[#E2E8F0] pb-1.5 flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-[#0F2942]" />
                  1. Institution Details
                </h2>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#1E293B] mb-1">
                      Official Institution Code (AICTE / AISHE) *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. AICTE-1-456789"
                      value={institutionCode}
                      onChange={(e) => setInstitutionCode(e.target.value.toUpperCase())}
                      className="block w-full px-3.5 py-2 bg-white border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] uppercase focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-[#1E293B] mb-1">
                      Institution Type *
                    </label>
                    <select
                      value={institutionType}
                      onChange={(e) => setInstitutionType(e.target.value)}
                      className="block w-full px-3.5 py-2 bg-white border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    >
                      <option value="CENTRAL_UNIVERSITY">Central University</option>
                      <option value="STATE_UNIVERSITY">State University</option>
                      <option value="DEEMED_UNIVERSITY">Deemed to be University</option>
                      <option value="PRIVATE_UNIVERSITY">Private University</option>
                      <option value="AUTONOMOUS_COLLEGE">Autonomous College</option>
                      <option value="AFFILIATED_INSTITUTE">Affiliated Technical Institute</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#1E293B] mb-1">
                    Registered Institution Legal Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Full legal name as approved in council order"
                    value={institutionName}
                    onChange={(e) => setInstitutionName(e.target.value)}
                    className="block w-full px-3.5 py-2 bg-white border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#1E293B] mb-1">
                      State / Union Territory *
                    </label>
                    <select
                      value={stateCode}
                      onChange={(e) => setStateCode(e.target.value)}
                      className="block w-full px-3.5 py-2 bg-white border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    >
                      <option value="DL">Delhi (NCT)</option>
                      <option value="MH">Maharashtra</option>
                      <option value="KA">Karnataka</option>
                      <option value="TN">Tamil Nadu</option>
                      <option value="UP">Uttar Pradesh</option>
                      <option value="TS">Telangana</option>
                      <option value="WB">West Bengal</option>
                      <option value="GJ">Gujarat</option>
                      <option value="RJ">Rajasthan</option>
                      <option value="KL">Kerala</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-[#1E293B] mb-1">
                      District Name *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. New Delhi"
                      value={district}
                      onChange={(e) => setDistrict(e.target.value)}
                      className="block w-full px-3.5 py-2 bg-white border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#1E293B] mb-1">
                    Campus Physical Address
                  </label>
                  <input
                    type="text"
                    placeholder="Sector, street, city, pin code"
                    value={campusAddress}
                    onChange={(e) => setCampusAddress(e.target.value)}
                    className="block w-full px-3.5 py-2 bg-white border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                  />
                </div>
              </div>

              {/* Section 2: Authorized Nodal Officer */}
              <div className="space-y-4 pt-3">
                <h2 className="text-xs font-bold text-[#0F2942] uppercase tracking-wider border-b border-[#E2E8F0] pb-1.5 flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-[#0F2942]" />
                  2. Authorized Nodal Officer Details
                </h2>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#1E293B] mb-1">
                      Nodal Officer Full Name *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Dr. Rajesh Sharma"
                      value={officerName}
                      onChange={(e) => setOfficerName(e.target.value)}
                      className="block w-full px-3.5 py-2 bg-white border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-[#1E293B] mb-1">
                      Official Designation *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Registrar / Director"
                      value={officerDesignation}
                      onChange={(e) => setOfficerDesignation(e.target.value)}
                      className="block w-full px-3.5 py-2 bg-white border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#1E293B] mb-1">
                      Institutional Official Email (.edu.in / .gov.in) *
                    </label>
                    <input
                      type="email"
                      required
                      placeholder="registrar@institution.edu.in"
                      value={officerEmail}
                      onChange={(e) => setOfficerEmail(e.target.value)}
                      className="block w-full px-3.5 py-2 bg-white border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-[#1E293B] mb-1">
                      Official Contact Phone *
                    </label>
                    <input
                      type="tel"
                      required
                      placeholder="+91 XXXXXXXXXX"
                      value={officerPhone}
                      onChange={(e) => setOfficerPhone(e.target.value)}
                      className="block w-full px-3.5 py-2 bg-white border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#1E293B] mb-1">
                    Council Approval Letter / Order Reference
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. F.No. AICTE/AB/2024-25/1-456789"
                    value={councilLetterRef}
                    onChange={(e) => setCouncilLetterRef(e.target.value)}
                    className="block w-full px-3.5 py-2 bg-white border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                  />
                </div>
              </div>

              {/* Statutory Declaration */}
              <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                <label className="flex items-start gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={hasDeclared}
                    onChange={(e) => setHasDeclared(e.target.checked)}
                    className="mt-0.5 rounded text-[#0F2942] focus:ring-[#0F2942]"
                  />
                  <span className="text-xs text-[#334155] leading-relaxed">
                    I solemnly declare that I am an authorized statutory officer representing this institution, and that all provided information is accurate and subject to verification under council regulations.
                  </span>
                </label>
              </div>

              {/* Buttons */}
              <div className="flex items-center justify-between pt-3 border-t border-[#E2E8F0]">
                <Link
                  href="/login"
                  className="btn-rounded-secondary text-xs"
                >
                  Cancel
                </Link>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="btn-rounded-primary text-xs py-2 px-6 flex items-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Submitting registration...</span>
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="w-4 h-4 text-white" />
                      <span>Submit onboarding application</span>
                    </>
                  )}
                </button>
              </div>
            </form>
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

