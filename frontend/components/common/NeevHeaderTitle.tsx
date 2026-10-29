import React from "react";
import NeevEmblem from "./NeevEmblem";

interface NeevHeaderTitleProps {
  emblemSize?: number;
  className?: string;
  subtitle?: string;
  center?: boolean;
}

export default function NeevHeaderTitle({
  emblemSize = 52,
  className = "",
  subtitle = "Statutory Higher Education Regulatory Portal",
  center = false,
}: NeevHeaderTitleProps) {
  return (
    <div
      className={`flex items-center gap-3.5 select-none ${
        center ? "justify-center text-left" : ""
      } ${className}`}
    >
      {/* 100% Perfect Circular Emblem - No rectangular box/shadow */}
      <NeevEmblem size={emblemSize} />

      {/* Bilingual Title Block with Indian Flag Colors on the Full Form */}
      <div className="flex flex-col">
        <span className="font-bold text-base sm:text-xl text-[#0F2942] leading-tight tracking-tight">
          राष्ट्रीय शिक्षा साक्ष्य एवं सत्यापन
        </span>
        <span className="text-xs sm:text-[14.5px] font-bold leading-tight mt-1 tracking-tight flex items-center gap-1.5 flex-wrap">
          <span className="text-[#E65100]">National Education</span>
          <span className="text-[#0F2942]">Evidence</span>
          <span className="text-[#046A38]">and Verification</span>
        </span>
        {subtitle && (
          <span className="text-[11px] text-[#64748B] font-medium hidden sm:block mt-0.5">
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
}
