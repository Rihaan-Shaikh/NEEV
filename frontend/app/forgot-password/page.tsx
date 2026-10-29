"use client";

import React, { useState } from "react";
import Link from "next/link";
import { apiRequest } from "@/lib/api";
import { useLanguage } from "@/lib/language-context";
import { ArrowLeft, CheckCircle2, ShieldAlert } from "lucide-react";
import NeevHeaderTitle from "@/components/common/NeevHeaderTitle";
import NeevEmblem from "@/components/common/NeevEmblem";

export default function ForgotPasswordPage() {
  const { language, setLanguage, t } = useLanguage();
  const [fontSize, setFontSize] = useState<"small" | "normal" | "large">("normal");
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);
  const [devResetToken, setDevResetToken] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSetFontSize = (size: "small" | "normal" | "large") => {
    setFontSize(size);
    document.documentElement.setAttribute("data-font-size", size);
    document.body.setAttribute("data-font-size", size);
    const fontVal = size === "small" ? "13.5px" : size === "large" ? "17.5px" : "15px";
    document.documentElement.style.fontSize = fontVal;
    document.body.style.fontSize = fontVal;
    (document.body.style as any).zoom = "";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const res = await apiRequest<{ message: string; dev_reset_token?: string }>(
        "/auth/forgot-password",
        {
          method: "POST",
          body: JSON.stringify({ email: email.trim().toLowerCase() }),
        }
      );
      setSubmitted(true);
      setFeedbackMessage(res.message);
      if (res.dev_reset_token) {
        setDevResetToken(res.dev_reset_token);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to process password recovery request.");
    } finally {
      setIsSubmitting(false);
    }
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
          <div className="bg-white py-8 px-6 sm:px-8 shadow-sm border border-[#CBD5E1] rounded-2xl">
            <h2 className="text-base font-semibold text-[#0F2942] mb-1">
              {language === "hi" ? "खाता पुनर्प्राप्ति" : "Recover account access"}
            </h2>
            <p className="text-xs text-[#475569] mb-5 border-b border-[#E2E8F0] pb-3">
              {language === "hi"
                ? "पासवर्ड रीसेट निर्देश प्राप्त करने के लिए अपना अधिकृत ईमेल दर्ज करें।"
                : "Enter your authorized email address to receive secure password recovery instructions."}
            </p>

            {errorMsg && (
              <div className="mb-5 p-3.5 bg-red-50 border border-red-200 rounded-xl flex items-start gap-2.5 text-xs text-red-700">
                <ShieldAlert className="w-4 h-4 shrink-0 text-red-600 mt-0.5" />
                <div>
                  <span className="font-semibold block">Request failed</span>
                  {errorMsg}
                </div>
              </div>
            )}

            {submitted ? (
              <div className="space-y-4">
                <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-900 flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-[#15803D] shrink-0 mt-0.5" />
                  <div className="leading-relaxed">
                    <span className="font-semibold block text-sm mb-1">
                      {language === "hi" ? "पुनर्प्राप्ति आरंभ की गई" : "Recovery initiated"}
                    </span>
                    {feedbackMessage}
                  </div>
                </div>

                {devResetToken && (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900">
                    <span className="font-semibold block mb-1">Demonstration helper link:</span>
                    <Link
                      href={`/reset-password?token=${devResetToken}`}
                      className="inline-flex items-center gap-1 font-semibold text-[#0F2942] hover:underline break-all"
                    >
                      Open password reset form →
                    </Link>
                  </div>
                )}

                <div className="pt-4 border-t border-[#E2E8F0]">
                  <Link
                    href="/login"
                    className="w-full btn-rounded-secondary text-xs py-2.5"
                  >
                    <ArrowLeft className="w-4 h-4 text-slate-500" />
                    {language === "hi" ? "साइन इन पर वापस जाएं" : "Return to sign in"}
                  </Link>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="recovery-email" className="block text-xs font-semibold text-[#1E293B] mb-1">
                    {language === "hi" ? "अधिकृत ईमेल" : "Authorized email"}
                  </label>
                  <input
                    id="recovery-email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="officer@institution.edu.in"
                    className="block w-full px-4 py-2.5 bg-white border border-[#CBD5E1] rounded-full text-sm text-[#1E293B] placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0F2942] focus:border-transparent transition-all"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full btn-rounded-primary py-2.5 mt-2"
                >
                  {isSubmitting
                    ? (language === "hi" ? "निर्देश तैयार किए जा रहे हैं..." : "Processing request...")
                    : (language === "hi" ? "पासवर्ड पुनर्प्राप्ति लिंक भेजें" : "Send recovery instructions")}
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
