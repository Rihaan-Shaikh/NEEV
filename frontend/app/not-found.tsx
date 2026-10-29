"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Home, ShieldAlert } from "lucide-react";
import NeevHeaderTitle from "@/components/common/NeevHeaderTitle";

export default function NotFound() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col justify-center items-center px-4 py-12 sm:px-6 lg:px-8">
      {/* Official Masthead */}
      <div className="text-center mb-8">
        <NeevHeaderTitle emblemSize={56} center={true} />
      </div>

      {/* 404 Card */}
      <div className="bg-white p-8 sm:p-10 rounded-2xl border border-[#CBD5E1] shadow-sm max-w-md w-full text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 border border-slate-300 text-slate-800 text-xs font-semibold mb-4">
          <ShieldAlert className="w-3.5 h-3.5 text-slate-600" />
          Page not found (404)
        </div>

        <h2 className="text-xl font-bold text-[#0F2942] tracking-tight">
          Resource not located
        </h2>
        
        <p className="text-xs sm:text-sm text-[#475569] mt-2 mb-6 leading-relaxed">
          The requested application route or record workspace does not exist or has been relocated within the registry.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/overview"
            className="btn-rounded-primary py-2.5 px-5 text-xs"
          >
            <Home className="w-4 h-4 text-sky-300" />
            Return to overview
          </Link>

          <button
            type="button"
            onClick={() => router.back()}
            className="btn-rounded-secondary py-2.5 px-5 text-xs"
          >
            <ArrowLeft className="w-4 h-4 text-slate-600" />
            Go back
          </button>
        </div>

        <div className="mt-8 pt-4 border-t border-[#E2E8F0] text-xs text-[#475569]">
          Platform status: <span className="font-semibold text-[#15803D]">Operational</span> · Evidence-based integrity
        </div>
      </div>
    </div>
  );
}
