"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { apiRequest } from "@/lib/api";
import { useLanguage } from "@/lib/language-context";
import { Eye, EyeOff, ShieldAlert, CheckCircle2, ArrowLeft } from "lucide-react";
import NeevHeaderTitle from "@/components/common/NeevHeaderTitle";
import NeevEmblem from "@/components/common/NeevEmblem";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const tokenFromUrl = searchParams.get("token") || "";
  const { language, t } = useLanguage();

  const [token, setToken] = useState(tokenFromUrl);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!token.trim()) {
      setErrorMsg("A valid password recovery token is required.");
      return;
    }

    if (newPassword.length < 8) {
      setErrorMsg("Password must be at least 8 characters long.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setErrorMsg("Passwords do not match. Please verify both fields.");
      return;
    }

    setIsSubmitting(true);
    try {
      await apiRequest<{ message: string }>("/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ token: token.trim(), new_password: newPassword }),
      });
      setSuccess(true);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to reset password. The link may have expired.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white py-8 px-6 sm:px-8 shadow-sm border border-[#CBD5E1] rounded-2xl">
      <h2 className="text-base font-semibold text-[#0F2942] mb-1">
        {language === "hi" ? "नया पासवर्ड सेट करें" : "Set new account password"}
      </h2>
      <p className="text-xs text-[#475569] mb-5 border-b border-[#E2E8F0] pb-3">
        {language === "hi"
          ? "कार्यक्षेत्र में सुरक्षित प्रवेश के लिए अपना नया पासवर्ड दर्ज करें।"
          : "Enter your new secure password below to regain workspace access."}
      </p>

      {errorMsg && (
        <div className="mb-5 p-3.5 bg-red-50 border border-red-200 rounded-xl flex items-start gap-2.5 text-xs text-red-700">
          <ShieldAlert className="w-4 h-4 shrink-0 text-red-600 mt-0.5" />
          <div>
            <span className="font-semibold block">Validation error</span>
            {errorMsg}
          </div>
        </div>
      )}

      {success ? (
        <div className="space-y-4">
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-900 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-[#15803D] shrink-0 mt-0.5" />
            <div className="leading-relaxed">
              <span className="font-semibold block text-sm mb-1">
                {language === "hi" ? "पासवर्ड अद्यतन हुआ" : "Password updated"}
              </span>
              {language === "hi"
                ? "आपका पासवर्ड सफलतापूर्वक बदल दिया गया है।"
                : "Your password has been successfully reset. All active sessions have been terminated."}
            </div>
          </div>

          <div className="pt-4 border-t border-[#E2E8F0]">
            <Link
              href="/login"
              className="w-full btn-rounded-primary py-2.5"
            >
              {language === "hi" ? "नए पासवर्ड से साइन इन करें" : "Sign in with new password"}
            </Link>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {!tokenFromUrl && (
            <div>
              <label htmlFor="reset-token" className="block text-xs font-semibold text-[#1E293B] mb-1">
                {language === "hi" ? "पुनर्प्राप्ति टोकन" : "Recovery token"}
              </label>
              <input
                id="reset-token"
                type="text"
                required
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Paste your reset token"
                className="block w-full px-4 py-2 bg-white border border-[#CBD5E1] rounded-full text-sm text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
              />
            </div>
          )}

          <div>
            <label htmlFor="new-password" className="block text-xs font-semibold text-[#1E293B] mb-1">
              {language === "hi" ? "नया पासवर्ड" : "New password (min 8 characters)"}
            </label>
            <div className="relative">
              <input
                id="new-password"
                type={showPassword ? "text" : "password"}
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="block w-full px-4 py-2.5 bg-white border border-[#CBD5E1] rounded-full text-sm text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942] pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-700"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div>
            <label htmlFor="confirm-password" className="block text-xs font-semibold text-[#1E293B] mb-1">
              {language === "hi" ? "पासवर्ड की पुष्टि करें" : "Confirm new password"}
            </label>
            <input
              id="confirm-password"
              type={showPassword ? "text" : "password"}
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="block w-full px-4 py-2.5 bg-white border border-[#CBD5E1] rounded-full text-sm text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full btn-rounded-primary py-2.5 mt-2"
          >
            {isSubmitting
              ? (language === "hi" ? "अद्यतन हो रहा है..." : "Updating password...")
              : (language === "hi" ? "नया पासवर्ड सहेजें" : "Update password")}
          </button>

          <div className="pt-4 border-t border-[#E2E8F0] text-center">
            <Link
              href="/login"
              className="inline-flex items-center gap-1.5 text-xs text-[#475569] hover:text-[#0F2942] transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              {language === "hi" ? "साइन इन पर वापस जाएं" : "Return to sign in"}
            </Link>
          </div>
        </form>
      )}
    </div>
  );
}

export default function ResetPasswordPage() {
  const { language, setLanguage, t } = useLanguage();
  const [fontSize, setFontSize] = useState<"small" | "normal" | "large">("normal");

  const handleSetFontSize = (size: "small" | "normal" | "large") => {
    setFontSize(size);
    document.documentElement.setAttribute("data-font-size", size);
    document.body.setAttribute("data-font-size", size);
    const fontVal = size === "small" ? "13.5px" : size === "large" ? "17.5px" : "15px";
    document.documentElement.style.fontSize = fontVal;
    document.body.style.fontSize = fontVal;
    (document.body.style as any).zoom = "";
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col justify-between">
      {/* Top Utility Bar */}
      <div className="bg-[#F1F5F9] border-b border-[#CBD5E1] px-4 sm:px-8 lg:px-[12%] py-1.5 flex items-center justify-between text-xs text-[#475569]">
        <span className="font-medium text-[#1E293B]">
          {t("header.academicYear", "Academic session: 2024–2025")}
        </span>
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-1 text-[11px] text-[#475569]">
            <span className="mr-1">{t("header.textSize", "Text Size")}:</span>
            <button
              onClick={() => handleSetFontSize("small")}
              className={`w-6 h-6 rounded flex items-center justify-center font-bold text-xs transition-colors ${
                fontSize === "small" ? "bg-[#0F2942] text-white" : "hover:bg-slate-200 text-[#1E293B]"
              }`}
              title="Small text"
            >
              A-
            </button>
            <button
              onClick={() => handleSetFontSize("normal")}
              className={`w-6 h-6 rounded flex items-center justify-center font-bold text-xs transition-colors ${
                fontSize === "normal" ? "bg-[#0F2942] text-white" : "hover:bg-slate-200 text-[#1E293B]"
              }`}
              title="Standard text"
            >
              A
            </button>
            <button
              onClick={() => handleSetFontSize("large")}
              className={`w-6 h-6 rounded flex items-center justify-center font-bold text-xs transition-colors ${
                fontSize === "large" ? "bg-[#0F2942] text-white" : "hover:bg-slate-200 text-[#1E293B]"
              }`}
              title="Large text"
            >
              A+
            </button>
          </div>

          <div className="flex items-center rounded-full bg-slate-200/90 p-0.5 text-xs font-medium">
            <button
              type="button"
              onClick={() => setLanguage("en")}
              className={`px-3 py-0.5 rounded-full transition-colors ${
                language === "en" ? "bg-[#0F2942] text-white font-semibold" : "text-[#334155]"
              }`}
            >
              English
            </button>
            <button
              type="button"
              onClick={() => setLanguage("hi")}
              className={`px-3 py-0.5 rounded-full transition-colors ${
                language === "hi" ? "bg-[#0F2942] text-white font-semibold" : "text-[#334155]"
              }`}
            >
              हिन्दी
            </button>
          </div>
        </div>
      </div>

      <div className="py-10 px-4 sm:px-6 lg:px-8 flex-1 flex flex-col justify-center">
        {/* Official Masthead */}
        <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-6">
          <NeevHeaderTitle emblemSize={54} center={true} />
        </div>

        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <Suspense fallback={
            <div className="p-8 text-center bg-white rounded-2xl border border-slate-200">
              <span className="text-xs text-slate-500">Loading form...</span>
            </div>
          }>
            <ResetPasswordForm />
          </Suspense>
        </div>
      </div>

      <footer className="w-full bg-[#F1F5F9] border-t border-[#CBD5E1] py-4 text-center text-[11px] text-[#475569]">
        <div className="flex items-center justify-center gap-2 mb-1">
          <NeevEmblem size={18} />
          <span className="font-semibold text-[#0F2942]">
            National Education Evidence and Verification
          </span>
        </div>
        <p>
          Statutory Regulatory Portal &bull; Institutional Authentication &bull; Ministry of Education
        </p>
      </footer>
    </div>
  );
}
