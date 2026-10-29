"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useLanguage } from "@/lib/language-context";
import { api } from "@/lib/api";
import NeevEmblem from "@/components/common/NeevEmblem";
import NeevHeaderTitle from "@/components/common/NeevHeaderTitle";
import { 
  Bell, 
  LogOut, 
  ShieldCheck, 
  Volume2, 
  Clock, 
  Menu, 
  X, 
  VolumeX, 
  CheckCircle2, 
  ExternalLink,
  ChevronDown,
  Inbox,
  AlertTriangle,
  Info
} from "lucide-react";

interface AppShellProps {
  children: React.ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, isLoading } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const [unreadCount, setUnreadCount] = useState(0);
  const [fontSizeLevel, setFontSizeLevel] = useState<"small" | "normal" | "large">("normal");
  const [currentTime, setCurrentTime] = useState<string>("");
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [showScreenReaderModal, setShowScreenReaderModal] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  // Notifications Popover State (No background polling interval!)
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [recentNotifications, setRecentNotifications] = useState<any[]>([]);
  const [isLoadingNotifications, setIsLoadingNotifications] = useState(false);
  const notificationsDropdownRef = useRef<HTMLDivElement>(null);

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

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
    setIsNotificationsOpen(false);
  }, [pathname]);

  // Accessibility Text Size scaling (A-, A, A+) - Font Size ONLY (No whole-page zoom)
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

  // Notifications toggle: fetches only when opened on demand (no timed polling interval)
  const handleToggleNotifications = async () => {
    const nextOpen = !isNotificationsOpen;
    setIsNotificationsOpen(nextOpen);
    if (nextOpen) {
      setIsLoadingNotifications(true);
      try {
        const items = await api.listNotifications({ limit: 5 });
        setRecentNotifications(items);
        const unread = items.filter((i: any) => !i.is_read).length;
        setUnreadCount(unread);
      } catch {
        // Silently handle
      } finally {
        setIsLoadingNotifications(false);
      }
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      setRecentNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch {}
  };

  // Close notifications popover on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        notificationsDropdownRef.current &&
        !notificationsDropdownRef.current.contains(e.target as Node)
      ) {
        setIsNotificationsOpen(false);
      }
    };
    if (isNotificationsOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isNotificationsOpen]);

  // Web Speech API for Screen Reader / Audio Assistance
  const handleSpeakPage = () => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      alert("Audio speech synthesis is not supported on this browser.");
      return;
    }

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    const heading = document.querySelector("h1")?.textContent || "National Education Evidence and Verification portal";
    const sub = document.querySelector("p")?.textContent || "";
    const activeRouteText = `Current section is ${pathname.replace("/", "") || "overview"}.`;
    const fullText = `${heading}. ${sub}. ${activeRouteText}. Authorized session active.`;

    const utterance = new SpeechSynthesisUtterance(fullText);
    utterance.rate = 0.95;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
    setIsSpeaking(true);
  };

  const handleStopSpeech = () => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  };

  if (isLoading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-[#F8FAFC]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-[#0F2942] border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm font-medium text-[#475569]">
            {language === "hi" ? "कार्यक्षेत्र लोड किया जा रहा है..." : "Loading regulatory workspace..."}
          </span>
        </div>
      </div>
    );
  }

  if (!user && pathname !== "/login" && pathname !== "/register" && pathname !== "/verify") {
    if (typeof window !== "undefined") {
      router.push("/login");
    }
    return null;
  }

  // Simplified non-tech plain terms: Notifications removed from navigation bar as requested
  const navItems = [
    { label: t("nav.overview", "Overview"), href: "/overview" },
    { label: t("nav.riskQueue", "Review priorities"), href: "/risk-queue" },
    { label: t("nav.cases", "Review cases"), href: "/cases" },
    { label: t("nav.reports", "Regulatory reports"), href: "/reports" },
    { label: t("nav.verificationReferences", "Verification"), href: "/verification-references" },
    { label: t("nav.integrations", "External registries"), href: "/integrations" },
    { label: t("nav.institutions", "Institutions"), href: "/institutions" },
    { label: t("nav.programmes", "Courses & seats"), href: "/programmes" },
    { label: t("nav.submissions", "Student lists"), href: "/submissions" },
    { label: t("nav.enrolments", "Enrolled students"), href: "/enrolments" },
    { label: t("nav.findings", "Compliance alerts"), href: "/findings" },
  ];

  return (
    <div className="min-h-screen w-screen flex flex-col bg-[#F8FAFC]">
      {/* 1. Official Utility Bar (AICTE Style) with 10-15% left alignment */}
      <div className="bg-[#0A1C2E] border-b border-[#16365C] px-4 sm:px-6 lg:pl-[12%] lg:pr-10 py-1.5 flex flex-wrap items-center justify-between text-xs text-slate-200 shrink-0 select-none">
        {/* Left: Live IST Clock & Screen Reader Access */}
        <div className="flex items-center gap-3 sm:gap-4 flex-wrap">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-300">
            <Clock className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span className="tabular-nums font-medium">{currentTime || "Academic session 2024–2025"}</span>
          </div>

          <span className="hidden md:inline-block w-1 h-1 rounded-full bg-slate-500"></span>

          {/* Screen Reader Access button */}
          <button
            onClick={() => setShowScreenReaderModal(true)}
            className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded hover:bg-[#16365C] text-slate-200 text-[11px] font-medium transition-colors cursor-pointer"
            title="Screen Reader Access information and guidelines"
          >
            <Volume2 className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span>Screen Reader Access</span>
          </button>
        </div>

        {/* Right: Functional Text Sizing, Language selector, and Sign out */}
        <div className="flex items-center gap-3 sm:gap-4 ml-auto">
          {/* Functional Text Size Controls: A- (Small)  A (Normal)  A+ (Large) */}
          <div className="flex items-center gap-1 text-[11px]">
            <span className="text-slate-400 mr-1 hidden sm:inline">Text Size:</span>
            <button
              onClick={() => handleSetFontSize("small")}
              className={`px-1.5 py-0.5 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                fontSizeLevel === "small" ? "bg-amber-400 text-[#0F2942]" : "hover:bg-[#16365C] text-slate-200"
              }`}
              title="Decrease text size and assets (A-)"
              aria-label="Decrease font size"
            >
              A-
            </button>
            <button
              onClick={() => handleSetFontSize("normal")}
              className={`px-1.5 py-0.5 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                fontSizeLevel === "normal" ? "bg-amber-400 text-[#0F2942]" : "hover:bg-[#16365C] text-slate-200"
              }`}
              title="Default text size (A)"
              aria-label="Default font size"
            >
              A
            </button>
            <button
              onClick={() => handleSetFontSize("large")}
              className={`px-1.5 py-0.5 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                fontSizeLevel === "large" ? "bg-amber-400 text-[#0F2942]" : "hover:bg-[#16365C] text-slate-200"
              }`}
              title="Increase text size and assets (A+)"
              aria-label="Increase font size"
            >
              A+
            </button>
          </div>

          <span className="text-slate-600 hidden sm:inline">|</span>

          {/* Bilingual Selector: English | हिन्दी */}
          <div className="flex items-center rounded-full bg-[#16365C] p-0.5 text-[11px] font-medium">
            <button
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

          {/* User Sign out button */}
          <button
            onClick={() => logout()}
            title={t("header.signOut", "Sign out")}
            aria-label="Sign out"
            className="inline-flex items-center gap-1 px-2.5 py-0.5 bg-red-950/70 hover:bg-red-900 border border-red-700/60 text-white rounded text-[11px] font-medium transition-colors cursor-pointer"
          >
            <LogOut className="w-3 h-3 text-red-300" />
            <span className="hidden sm:inline">{t("header.signOut", "Sign out")}</span>
          </button>
        </div>
      </div>

      {/* 2. Official Institutional Masthead with 10-15% left alignment */}
      <header className="bg-white border-b border-[#CBD5E1] pl-4 sm:pl-8 lg:pl-[12%] pr-4 sm:pr-8 lg:pr-[6%] py-3.5 flex items-center justify-between shrink-0 shadow-xs">
        <Link href="/overview" className="group">
          <NeevHeaderTitle emblemSize={52} />
        </Link>

        {/* Right Masthead Controls */}
        <div className="flex items-center gap-3">
          {/* Session Tag */}
          <div className="hidden lg:flex flex-col text-right text-xs">
            <span className="text-[11px] text-[#64748B] font-medium">Session Status</span>
            <span className="font-semibold text-[#0F2942]">Academic Session 2024–2025</span>
          </div>

          {/* Notification Bell with Smooth Animated Dropdown Popup (No timed polling!) */}
          <div className="relative" ref={notificationsDropdownRef}>
            <button
              onClick={handleToggleNotifications}
              className="relative p-2 text-[#475569] hover:text-[#0F2942] hover:bg-slate-100 rounded-full transition-colors cursor-pointer"
              title="Notifications"
              aria-label="View notifications popup"
              aria-expanded={isNotificationsOpen}
            >
              <Bell className="w-5 h-5 text-[#0F2942]" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 w-4 h-4 bg-[#B91C1C] text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-pulse">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              )}
            </button>

            {/* Smooth Animated Notification Popup */}
            {isNotificationsOpen && (
              <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-2xl border border-[#CBD5E1] shadow-2xl p-4 z-50 animate-in fade-in zoom-in-95 duration-150 space-y-3">
                <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2.5">
                  <div className="flex items-center gap-2">
                    <Bell className="w-4 h-4 text-[#0F2942]" />
                    <span className="font-bold text-xs text-[#0F2942]">Official notifications</span>
                  </div>
                  {recentNotifications.some((n) => !n.is_read) && (
                    <button
                      onClick={handleMarkAllRead}
                      className="text-[11px] font-semibold text-[#1E40AF] hover:underline cursor-pointer"
                    >
                      Mark all as read
                    </button>
                  )}
                </div>

                {isLoadingNotifications ? (
                  <div className="py-6 flex flex-col items-center justify-center gap-2 text-xs text-[#475569]">
                    <div className="w-5 h-5 border-2 border-[#0F2942] border-t-transparent rounded-full animate-spin"></div>
                    <span>Checking notifications...</span>
                  </div>
                ) : recentNotifications.length === 0 ? (
                  <div className="py-6 text-center text-xs text-[#475569] space-y-1">
                    <Inbox className="w-6 h-6 text-slate-300 mx-auto" />
                    <p className="font-medium text-[#1E293B]">No new notifications</p>
                    <p className="text-[11px] text-slate-400">Your regulatory inbox is up to date.</p>
                  </div>
                ) : (
                  <div className="divide-y divide-[#E2E8F0] max-h-64 overflow-y-auto sidebar-scroll">
                    {recentNotifications.map((notif: any) => (
                      <div
                        key={notif.id}
                        className={`py-2.5 px-2 rounded-lg transition-colors flex items-start gap-2.5 ${
                          notif.is_read ? "opacity-75 hover:bg-slate-50" : "bg-blue-50/40 hover:bg-blue-50/80"
                        }`}
                      >
                        <div className="mt-0.5 shrink-0">
                          {notif.severity === "CRITICAL" || notif.severity === "ERROR" ? (
                            <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
                          ) : (
                            <Info className="w-3.5 h-3.5 text-[#0F2942]" />
                          )}
                        </div>
                        <div className="flex-1 text-xs">
                          <p className="font-semibold text-[#0F2942] leading-tight">
                            {notif.title}
                          </p>
                          <p className="text-[11px] text-[#475569] mt-0.5 line-clamp-2">
                            {notif.body}
                          </p>
                          <span className="text-[10px] text-slate-400 mt-1 block">
                            {new Date(notif.created_at).toLocaleDateString("en-IN", {
                              day: "numeric",
                              month: "short",
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                        </div>
                        {!notif.is_read && (
                          <span className="w-2 h-2 rounded-full bg-blue-600 shrink-0 mt-1"></span>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                <div className="pt-2 border-t border-[#E2E8F0] flex justify-between items-center text-xs">
                  <span className="text-[11px] text-slate-400">Regulatory dispatch channel</span>
                  <Link
                    href="/notifications"
                    onClick={() => setIsNotificationsOpen(false)}
                    className="font-bold text-xs text-[#0F2942] hover:text-[#1E40AF] hover:underline"
                  >
                    View all notifications →
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Mobile hamburger menu button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="lg:hidden p-2 text-[#0F2942] hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
            aria-label="Toggle navigation menu"
          >
            {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </header>

      {/* 3. Primary HORIZONTAL Navigation Bar (Deep Navy Blue Stripe) with 10-15% left alignment */}
      <nav className="bg-[#0F2942] text-white shadow-md sticky top-0 z-40 shrink-0 border-y border-[#16365C]">
        <div className="w-full pl-4 sm:pl-8 lg:pl-[12%] pr-4 sm:pr-8 lg:pr-[6%]">
          {/* Desktop Horizontal Navigation Links */}
          <div className="hidden lg:flex items-center justify-start space-x-1 overflow-x-auto sidebar-scroll py-0.5">
            {navItems.map((item) => {
              const isActive = pathname === item.href || (item.href !== "/overview" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-3 py-2 text-xs font-semibold whitespace-nowrap transition-all border-b-2 ${
                    isActive
                      ? "bg-[#16365C] text-white border-amber-400 font-bold shadow-xs"
                      : "text-slate-100 border-transparent hover:bg-[#16365C]/80 hover:text-white hover:border-slate-300"
                  }`}
                >
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>

          {/* Mobile Navigation Drawer */}
          {isMobileMenuOpen && (
            <div className="lg:hidden py-3 border-t border-[#16365C] space-y-1">
              {navItems.map((item) => {
                const isActive = pathname === item.href || (item.href !== "/overview" && pathname.startsWith(item.href));
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`flex items-center justify-between px-3 py-2 rounded-md text-xs font-semibold ${
                      isActive
                        ? "bg-[#16365C] text-white border-l-4 border-amber-400"
                        : "text-slate-200 hover:bg-[#16365C]/70 hover:text-white"
                    }`}
                  >
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </nav>

      {/* 4. Official Breadcrumb / Active Workspace Banner with 10-15% left alignment */}
      <div className="bg-[#F1F5F9] border-b border-[#CBD5E1] pl-4 sm:pl-8 lg:pl-[12%] pr-4 sm:pr-8 lg:pr-[6%] py-2 flex flex-wrap items-center justify-between text-xs text-[#475569] shrink-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[#64748B] font-medium">Active workspace:</span>
          <span className="font-semibold text-[#0F2942]">
            {user?.display_name || user?.email_normalized}
          </span>
          <span className="text-slate-400">|</span>
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-slate-200 text-[#1E293B] font-medium border border-slate-300 text-[11px]">
            <ShieldCheck className="w-3 h-3 text-[#0F2942]" />
            <span>{user?.roles?.[0]?.replace(/_/g, " ").toLowerCase() || "Authorized officer"}</span>
          </span>
        </div>

        <div className="hidden sm:flex items-center gap-2 text-[11px] text-[#64748B]">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>Verified Institutional Gateway • Council Approved</span>
        </div>
      </div>

      {/* 5. Main Canvas: Genuinely Left-Aligned with ~10-15% Left Margin (No max-width cap so 30% zoom stays left-aligned) */}
      <main className="flex-1 w-full bg-[#F8FAFC]">
        <div className="w-full pl-4 sm:pl-8 lg:pl-[12%] pr-4 sm:pr-8 lg:pr-[6%] py-6 sm:py-8">
          {children}
        </div>
      </main>

      {/* 6. Official Institutional Footer with Circular NEEV Emblem & Left Alignment */}
      <footer className="bg-[#0F2942] text-white border-t border-[#16365C] text-xs py-6 pl-4 sm:pl-8 lg:pl-[12%] pr-4 sm:pr-8 lg:pr-[6%] mt-auto">
        <div className="w-full flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            {/* 100% Perfect Circular NEEV Emblem */}
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

      {/* Screen Reader Accessibility Modal */}
      {showScreenReaderModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-2xl max-w-lg w-full p-6 space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
              <div className="flex items-center gap-2">
                <Volume2 className="w-5 h-5 text-[#0F2942]" />
                <h3 className="text-base font-bold text-[#0F2942]">
                  Screen Reader Access & Assistance
                </h3>
              </div>
              <button
                onClick={() => setShowScreenReaderModal(false)}
                className="w-7 h-7 rounded-full flex items-center justify-center hover:bg-slate-100 text-[#475569] hover:text-[#0F2942] cursor-pointer"
                aria-label="Close modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-[#475569] leading-relaxed">
              This portal complies with the Guidelines for Indian Government Websites (GIGW) and World Wide Web Consortium (W3C) Web Content Accessibility Guidelines (WCAG) 2.1 Level AA.
            </p>

            {/* Audio Reader Trigger */}
            <div className="p-4 bg-slate-50 border border-[#CBD5E1] rounded-xl flex items-center justify-between gap-3">
              <div>
                <span className="font-bold text-xs text-[#0F2942] block">Browser Audio Assistant</span>
                <span className="text-[11px] text-[#475569] block">Listen to active page summary via speech synthesis</span>
              </div>
              {isSpeaking ? (
                <button
                  onClick={handleStopSpeech}
                  className="btn-rounded text-xs bg-red-700 hover:bg-red-800 text-white cursor-pointer"
                >
                  <VolumeX className="w-3.5 h-3.5" />
                  Stop
                </button>
              ) : (
                <button
                  onClick={handleSpeakPage}
                  className="btn-rounded-primary text-xs cursor-pointer"
                >
                  <Volume2 className="w-3.5 h-3.5 text-white" />
                  Listen
                </button>
              )}
            </div>

            {/* Compatible Screen Readers Table */}
            <div className="space-y-2">
              <span className="text-xs font-bold text-[#0F2942] block">Supported Assistive Technologies:</span>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg">
                  <span className="font-semibold block text-[#0F2942]">NVDA</span>
                  <span className="text-[11px] text-[#64748B]">NonVisual Desktop Access (Free)</span>
                </div>
                <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg">
                  <span className="font-semibold block text-[#0F2942]">JAWS</span>
                  <span className="text-[11px] text-[#64748B]">Job Access With Speech</span>
                </div>
                <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg">
                  <span className="font-semibold block text-[#0F2942]">Windows Narrator</span>
                  <span className="text-[11px] text-[#64748B]">Built-in (Win + Ctrl + Enter)</span>
                </div>
                <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg">
                  <span className="font-semibold block text-[#0F2942]">VoiceOver</span>
                  <span className="text-[11px] text-[#64748B]">Apple macOS & iOS</span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-[#E2E8F0] flex justify-end">
              <button
                onClick={() => setShowScreenReaderModal(false)}
                className="btn-rounded-primary text-xs cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
