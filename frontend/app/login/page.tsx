"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useLanguage } from "@/lib/language-context";
import NeevEmblem from "@/components/common/NeevEmblem";
import NeevHeaderTitle from "@/components/common/NeevHeaderTitle";
import { 
  Eye, 
  EyeOff, 
  ShieldAlert, 
  KeyRound, 
  Building, 
  Lock, 
  Clock, 
  ShieldCheck, 
  AlertOctagon,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  ExternalLink,
  Info
} from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentTime, setCurrentTime] = useState<string>("");
  const [fontSizeLevel, setFontSizeLevel] = useState<"small" | "normal" | "large">("normal");

  // Platform Demo Slides for Showcase
  const demoScreenshots = [
    {
      src: "/demo/14_screen_overview.png",
      title: "National Regulatory Overview",
      subtitle: "AICTE national-level intelligence, capacity distribution & institutional coverage metrics",
      tag: "Council Dashboard"
    },
    {
      src: "/demo/16_screen_enrolments.png",
      title: "Student Enrolment Register",
      subtitle: "Deterministic reconciliation against sanctioned intake and supernumerary caps",
      tag: "Integrity Core"
    },
    {
      src: "/demo/18_screen_findings.png",
      title: "Automated Discrepancy Findings",
      subtitle: "Real-time detection of intake overflows, missing APAARs & cross-college duplicates",
      tag: "Verification Engine"
    },
    {
      src: "/demo/20_screen_risk_queue.png",
      title: "AICTE Prioritized Risk Queue",
      subtitle: "Explainable regulatory indicators routing high-priority audits without black-box scores",
      tag: "Audit Queue"
    },
    {
      src: "/demo/25_screen_reports.png",
      title: "National Policy & Regulatory Reports",
      subtitle: "Policy-grade analytics, institutional compliance logs & verifiable audit trails",
      tag: "Policy Analytics"
    }
  ];

  const [activeSlide, setActiveSlide] = useState(0);

  // Auto-advance showcase every 4.5 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveSlide((prev) => (prev + 1) % demoScreenshots.length);
    }, 4500);
    return () => clearInterval(timer);
  }, [demoScreenshots.length]);


  // Rate Limiting Cooldown State
  const [cooldownSeconds, setCooldownSeconds] = useState<number>(0);
  const [isRateLimited, setIsRateLimited] = useState<boolean>(false);

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

  // Cooldown countdown timer
  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      if (params.get("session_expired") === "1") {
        setErrorMsg(
          language === "hi"
            ? "आपका सत्र समाप्त हो गया है। कृपया जारी रखने के लिए पुनः प्रवेश करें।"
            : "Your session has expired. Please sign in again to continue."
        );
      }
    }
  }, [language]);

  useEffect(() => {
    if (cooldownSeconds <= 0) {
      if (isRateLimited) {
        setIsRateLimited(false);
        setErrorMsg(null);
      }
      return;
    }
    const timer = setTimeout(() => {
      setCooldownSeconds((prev) => prev - 1);
    }, 1000);
    return () => clearTimeout(timer);
  }, [cooldownSeconds, isRateLimited]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (cooldownSeconds > 0) return;

    setErrorMsg(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      router.push("/overview");
    } catch (err: any) {
      // Check for 429 Too Many Requests / Rate Limit
      const is429 = 
        err.status === 429 ||
        err.message?.includes("429") ||
        err.message?.toLowerCase().includes("too many requests") ||
        err.message?.toLowerCase().includes("rate limit");

      if (is429) {
        setIsRateLimited(true);
        setCooldownSeconds(60);
        setErrorMsg(
          language === "hi"
            ? "प्रयास सीमा समाप्त। सुरक्षा कारणों से प्रणाली 60 सेकंड के लिए अस्थायी रूप से लॉक की गई है।"
            : "Rate limit exceeded. For regulatory security, login attempts are temporarily throttled. Please try again after the cooldown finishes."
        );
      } else {
        setErrorMsg(err.message || (language === "hi" ? "अमान्य ईमेल अथवा पासवर्ड" : "Invalid authorized email or password."));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const setDemoCredentials = (demoEmail: string, demoPass: string) => {
    if (cooldownSeconds > 0) return;
    setEmail(demoEmail);
    setPassword(demoPass);
    setErrorMsg(null);
  };

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

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col justify-between">
      {/* 1. Official Citizen & Officer Top Utility Bar (AICTE Style) */}
      <div className="bg-[#0A1C2E] border-b border-[#16365C] pl-4 sm:pl-8 lg:pl-[12%] pr-4 sm:pr-8 lg:pr-[6%] py-1.5 flex flex-wrap items-center justify-between text-xs text-slate-200 shrink-0 select-none">
        {/* Left: Live IST Clock */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-300">
            <Clock className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span className="tabular-nums font-medium">{currentTime || "Academic session 2024–2025"}</span>
          </div>
          <span className="hidden md:inline-block w-1 h-1 rounded-full bg-slate-500"></span>
          <span className="hidden md:inline-block text-[11px] text-slate-300">
            {language === "hi" ? "सत्यापन एवं नियामक नियंत्रण प्रणाली" : "Evidence and Regulatory Oversight Gateway"}
          </span>
        </div>

        {/* Right: Functional Text Size scaling and Language selector */}
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

          {/* Bilingual Selector: English | हिन्दी */}
          <div className="flex items-center rounded-full bg-[#16365C] p-0.5 text-[11px] font-medium">
            <button
              type="button"
              onClick={() => setLanguage("en")}
              className={`px-2 py-0.5 rounded-full transition-colors cursor-pointer ${
                language === "en"
                  ? "bg-amber-400 text-[#0F2942] font-bold"
                  : "text-slate-200 hover:text-white"
              }`}
              aria-label="Switch to English"
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
              aria-label="हिंदी में बदलें"
            >
              हिन्दी
            </button>
          </div>
        </div>
      </div>

      {/* 2. Official Masthead with Bespoke Circular NEEV Emblem & Indian Flag Colors */}
      <header className="bg-white border-b border-[#CBD5E1] pl-4 sm:pl-8 lg:pl-[12%] pr-4 sm:pr-8 lg:pr-[6%] py-3.5 flex items-center justify-between shrink-0 shadow-xs">
        <NeevHeaderTitle emblemSize={52} />

        <Link
          href="/verify"
          className="btn-rounded-secondary text-xs hidden sm:inline-flex cursor-pointer"
        >
          <span>Public verification portal</span>
          <ExternalLink className="w-3.5 h-3.5 text-[#0F2942]" />
        </Link>
      </header>

      {/* 3. Main Form Canvas */}
            {/* 3. Main Split Canvas (55% Demo Showcase : 45% Right-Aligned Login) */}
      <main className="flex-1 w-full flex flex-col lg:flex-row items-center justify-between py-6 lg:py-8 pl-4 sm:pl-8 lg:pl-[6%] pr-4 sm:pr-6 lg:pr-[5%] gap-8 lg:gap-12 w-full">
        {/* Left 55%: Interactive Platform Showcase & Animated Transition Carousel */}
        <div className="w-full lg:w-[55%] flex flex-col justify-center space-y-4 py-2">
          {/* Header Title & Single Line Description */}
          <div className="space-y-1.5">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#0F2942] tracking-tight">
              Evidence-based student enrolment integrity for AICTE
            </h1>
            <p className="text-xs sm:text-sm text-[#475569] whitespace-normal xl:whitespace-nowrap leading-relaxed">
              Preview our live regulatory workspaces, canonical student registers, and explainable audit workflows across AICTE-approved institutions.
            </p>
          </div>

          {/* Clean Image Showcase Frame - Pure Image & Description Only */}
          <div className="relative rounded-2xl bg-white border border-[#CBD5E1] shadow-lg overflow-hidden flex flex-col transition-all duration-300">
            {/* Slides Image Showcase (Crossfade Animation) */}
            <div className="relative w-full aspect-[16/10] bg-slate-950 overflow-hidden group">
              {demoScreenshots.map((item, idx) => (
                <div
                  key={item.src}
                  className={`absolute inset-0 transition-all duration-700 ease-in-out ${
                    idx === activeSlide
                      ? "opacity-100 scale-100 z-10"
                      : "opacity-0 scale-98 z-0 pointer-events-none"
                  }`}
                >
                  <img
                    src={item.src}
                    alt={item.title}
                    className="w-full h-full object-cover object-top"
                  />
                  {/* Clean dark gradient overlay at bottom for title & description */}
                  <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950/95 via-slate-950/50 to-transparent p-4 sm:p-5 flex flex-col justify-end text-white">
                    <h3 className="text-sm sm:text-base font-bold text-white leading-snug">
                      {item.title}
                    </h3>
                    <p className="text-[11px] sm:text-xs text-slate-200 mt-0.5 leading-relaxed">
                      {item.subtitle}
                    </p>
                  </div>
                </div>
              ))}

              {/* Prev / Next controls on hover */}
              <button
                type="button"
                onClick={() => setActiveSlide((prev) => (prev - 1 + demoScreenshots.length) % demoScreenshots.length)}
                aria-label="Previous slide"
                className="absolute left-2.5 top-1/2 -translate-y-1/2 z-20 w-8 h-8 rounded-full bg-slate-900/60 hover:bg-slate-900/90 text-white flex items-center justify-center backdrop-blur-xs transition-colors cursor-pointer border border-white/20 opacity-0 group-hover:opacity-100"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => setActiveSlide((prev) => (prev + 1) % demoScreenshots.length)}
                aria-label="Next slide"
                className="absolute right-2.5 top-1/2 -translate-y-1/2 z-20 w-8 h-8 rounded-full bg-slate-900/60 hover:bg-slate-900/90 text-white flex items-center justify-center backdrop-blur-xs transition-colors cursor-pointer border border-white/20 opacity-0 group-hover:opacity-100"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Right 45%: Login Card pushed further to the right */}
        <div className="w-full lg:w-[45%] flex justify-end lg:pr-8 xl:pr-14 2xl:pr-20">

        <div className="bg-white py-8 px-6 sm:px-8 shadow-sm border border-[#CBD5E1] rounded-2xl space-y-6 w-full max-w-lg">
          {/* Form Header */}
          <div className="border-b border-[#E2E8F0] pb-4">
            <div className="flex items-center gap-2">
              <Lock className="w-4 h-4 text-[#0F2942]" />
              <h2 className="text-base font-bold text-[#0F2942]">
                {language === "hi" ? "अधिकृत नियामक प्रवेश द्वार" : "Authorized regulatory sign-in"}
              </h2>
            </div>
            <p className="text-xs text-[#475569] mt-1">
              {language === "hi"
                ? "यह पोर्टल केवल अधिकृत नियामक एवं संस्थागत अधिकारियों के उपयोग हेतु है।"
                : "Authorized access for council regulatory officers and affiliated institutional administrators."}
            </p>
          </div>

          {/* Rate Limit Lockout Banner */}
          {isRateLimited && (
            <div className="p-4 bg-amber-50 border-2 border-amber-300 rounded-xl flex items-start gap-3 text-xs text-amber-900 animate-in fade-in duration-200">
              <AlertOctagon className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-bold text-sm text-amber-900 block">
                  {language === "hi" ? "प्रणाली सुरक्षा कूलडाउन सक्रिय" : "Security rate limit active"}
                </span>
                <p className="leading-relaxed">
                  {errorMsg}
                </p>
                <div className="inline-flex items-center gap-2 mt-2 px-3 py-1 bg-amber-100 rounded-full font-bold text-amber-900 tabular-nums">
                  <Clock className="w-3.5 h-3.5" />
                  <span>Cooldown remaining: {cooldownSeconds}s</span>
                </div>
              </div>
            </div>
          )}

          {/* General Error Message */}
          {errorMsg && !isRateLimited && (
            <div className="p-3.5 bg-red-50 border border-red-200 rounded-xl flex items-start gap-2.5 text-xs text-red-800">
              <ShieldAlert className="w-4 h-4 shrink-0 text-red-600 mt-0.5" />
              <div>
                <span className="font-bold block">
                  {language === "hi" ? "सत्यापन विफल" : "Authentication failed"}
                </span>
                <p className="mt-0.5">{errorMsg}</p>
              </div>
            </div>
          )}

          {/* Form Controls */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="login-email" className="block text-xs font-semibold text-[#1E293B] mb-1">
                {language === "hi" ? "अधिकृत ईमेल" : "Authorized institutional email"}
              </label>
              <input
                id="login-email"
                type="email"
                required
                disabled={cooldownSeconds > 0}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="officer@institution.gov.in"
                className="block w-full px-4 py-2.5 bg-white border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0F2942] focus:border-transparent transition-all disabled:bg-slate-100 disabled:cursor-not-allowed"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label htmlFor="login-password" className="block text-xs font-semibold text-[#1E293B]">
                  {language === "hi" ? "पासवर्ड" : "Password"}
                </label>
                <Link
                  href="/forgot-password"
                  className="text-xs font-medium text-[#1E40AF] hover:underline"
                >
                  {language === "hi" ? "पासवर्ड भूल गए?" : "Forgot password?"}
                </Link>
              </div>
              <div className="relative">
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  required
                  disabled={cooldownSeconds > 0}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full px-4 py-2.5 bg-white border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0F2942] focus:border-transparent transition-all pr-10 disabled:bg-slate-100 disabled:cursor-not-allowed"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-500 hover:text-slate-700"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting || cooldownSeconds > 0}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-full text-xs font-bold text-white bg-[#0F2942] hover:bg-[#16365C] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#0F2942] transition-colors disabled:opacity-50 shadow-xs cursor-pointer"
            >
              {cooldownSeconds > 0 ? (
                <>
                  <Clock className="w-4 h-4 animate-spin" />
                  <span>Security cooldown ({cooldownSeconds}s)...</span>
                </>
              ) : isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>{language === "hi" ? "सत्यापन किया जा रहा है..." : "Authenticating session..."}</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>{language === "hi" ? "कार्यक्षेत्र में प्रवेश करें" : "Sign in to workspace"}</span>
                </>
              )}
            </button>
          </form>

          {/* New Institution / Register Route Link */}
          <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between text-xs">
            <div>
              <span className="font-bold text-[#0F2942] block">
                {language === "hi" ? "नई संस्था अथवा नोडल अधिकारी?" : "New institution or officer?"}
              </span>
              <span className="text-[11px] text-[#475569]">
                {language === "hi" ? "आधिकारिक संस्थागत पंजीकरण फॉर्म भरें" : "Submit institutional onboarding request"}
              </span>
            </div>
            <Link
              href="/register"
              className="btn-rounded-primary text-xs py-1.5 px-3 flex items-center gap-1.5"
            >
              <span>{language === "hi" ? "पंजीकरण" : "Register"}</span>
              <ArrowRight className="w-3.5 h-3.5 text-white" />
            </Link>
          </div>

          {/* Statutory Security Disclaimer */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-[11px] text-[#475569] flex items-start gap-2">
            <Lock className="w-3.5 h-3.5 text-[#0F2942] shrink-0 mt-0.5" />
            <span>
              This is a protected national education regulatory portal. Automated login attempts and rate limit violations are logged under the Information Technology Act.
            </span>
          </div>

          {/* Quick-Fill Demonstration Profiles */}
          <div className="pt-4 border-t border-[#E2E8F0] space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-[#475569]">
                {language === "hi" ? "त्वरित परीक्षण साख-पत्र (डेमो)" : "Institutional test accounts (demonstration):"}
              </span>
              <span className="text-[10px] text-slate-500 font-medium">Click to populate</span>
            </div>

            <div className="space-y-2">
              <button
                type="button"
                onClick={() => setDemoCredentials("aicte.admin@neev.aicte.gov.in", "NeevAdmin@2026")}
                className="w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 flex items-center justify-between text-xs transition-colors"
              >
                <div>
                  <span className="font-semibold text-[#0F2942] flex items-center gap-1.5">
                    <KeyRound className="w-3.5 h-3.5 text-[#0F2942]" />
                    National regulatory reviewer
                  </span>
                  <span className="text-[11px] text-slate-500">aicte.admin@neev.aicte.gov.in</span>
                </div>
                <span className="text-[11px] bg-white px-2 py-0.5 rounded-full border border-slate-200 font-medium text-slate-700">
                  National
                </span>
              </button>

              <button
                type="button"
                onClick={() => setDemoCredentials("admin@dit.synthetic.edu.in", "DitAdmin@2026")}
                className="w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 flex items-center justify-between text-xs transition-colors"
              >
                <div>
                  <span className="font-semibold text-[#0F2942] flex items-center gap-1.5">
                    <Building className="w-3.5 h-3.5 text-[#0F2942]" />
                    Delhi Institute of Technology admin
                  </span>
                  <span className="text-[11px] text-slate-500">admin@dit.institution.edu.in</span>
                </div>
                <span className="text-[11px] bg-white px-2 py-0.5 rounded-full border border-slate-200 font-medium text-slate-700">
                  Institution 1
                </span>
              </button>

              <button
                type="button"
                onClick={() => setDemoCredentials("admin@mtu.synthetic.edu.in", "MtuAdmin@2026")}
                className="w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 flex items-center justify-between text-xs transition-colors"
              >
                <div>
                  <span className="font-semibold text-[#0F2942] flex items-center gap-1.5">
                    <Building className="w-3.5 h-3.5 text-[#0F2942]" />
                    Mumbai Technical University admin
                  </span>
                  <span className="text-[11px] text-slate-500">admin@mtu.institution.edu.in</span>
                </div>
                <span className="text-[11px] bg-white px-2 py-0.5 rounded-full border border-slate-200 font-medium text-slate-700">
                  Institution 2
                </span>
              </button>
            </div>
          </div>
        </div>
              </div>
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
            {language === "hi"
              ? "राष्ट्रीय शिक्षा साक्ष्य एवं सत्यापन — सर्वाधिकार सुरक्षित। GIGW दिशानिर्देशों के अनुरूप अभिकल्पित।"
              : "National Education Evidence and Verification — All rights reserved. Designed in accordance with GIGW Standards."}
          </p>
        </div>
      </footer>
    </div>
  );
}
