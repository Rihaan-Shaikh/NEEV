import React from "react";

interface NeevEmblemProps {
  className?: string;
  size?: number;
}

export default function NeevEmblem({ className = "", size = 48 }: NeevEmblemProps) {
  // Strip any accidental box-shadows to guarantee strict circular geometry
  const sanitizedClassName = className.replace(/shadow(-\w+)?/g, "").trim();

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`rounded-full shrink-0 select-none block ${sanitizedClassName}`}
      style={{ borderRadius: "50%", overflow: "hidden" }}
      aria-label="National Education Evidence and Verification official seal"
    >
      {/* Outer Golden Border with Navy Body - True Geometric Circle */}
      <circle cx="50" cy="50" r="48" fill="#0F2942" stroke="#D97706" strokeWidth="2.5" />
      <circle cx="50" cy="50" r="44" stroke="#FDE68A" strokeWidth="1" strokeDasharray="2 2" opacity="0.6" />
      
      {/* 24-Spoke Radial Wheel of Learning */}
      <g stroke="#F59E0B" strokeWidth="0.8" opacity="0.3">
        {[
          0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165,
          180, 195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 345
        ].map((angle) => (
          <line
            key={angle}
            x1="50"
            y1="50"
            x2={50 + 40 * Math.cos((angle * Math.PI) / 180)}
            y2={50 + 40 * Math.sin((angle * Math.PI) / 180)}
          />
        ))}
      </g>
      <circle cx="50" cy="50" r="32" fill="#0A1C2E" stroke="#F59E0B" strokeWidth="1.2" />

      {/* Saffron & Green Arc Accents (Tiranga Ethos) */}
      <path d="M 22 50 A 28 28 0 0 1 50 22" stroke="#FF671F" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M 50 78 A 28 28 0 0 1 22 50" stroke="#046A38" strokeWidth="2.5" strokeLinecap="round" />

      {/* Foundation Pedestal Steps ("नींव" - 3 Tiered Plinth) */}
      <rect x="28" y="71" width="44" height="4.5" rx="1.5" fill="#F59E0B" />
      <rect x="33" y="66" width="34" height="4" rx="1" fill="#E2E8F0" />
      <rect x="38" y="62" width="24" height="3.5" rx="0.8" fill="#F59E0B" />

      {/* Open Book of Academic Evidence */}
      <path
        d="M 27 57 C 36 53, 46 54, 50 57 C 54 54, 64 53, 73 57 L 73 42 C 64 38, 54 39, 50 42 C 46 39, 36 38, 27 42 Z"
        fill="#FFFFFF"
        stroke="#0F2942"
        strokeWidth="1.2"
        strokeLinejoin="round"
      />
      {/* Book Center Fold Line */}
      <line x1="50" y1="42" x2="50" y2="57" stroke="#D97706" strokeWidth="1.5" />
      {/* Book Lines (Evidence & Records) */}
      <line x1="32" y1="46" x2="44" y2="46" stroke="#94A3B8" strokeWidth="0.8" strokeLinecap="round" />
      <line x1="32" y1="50" x2="43" y2="50" stroke="#94A3B8" strokeWidth="0.8" strokeLinecap="round" />
      <line x1="56" y1="46" x2="68" y2="46" stroke="#94A3B8" strokeWidth="0.8" strokeLinecap="round" />
      <line x1="57" y1="50" x2="68" y2="50" stroke="#94A3B8" strokeWidth="0.8" strokeLinecap="round" />

      {/* Central Column of Truth */}
      <rect x="47.5" y="27" width="5" height="15" rx="1" fill="#F59E0B" />
      {/* Capital Crown */}
      <circle cx="50" cy="24" r="5" fill="#FF671F" stroke="#FFFFFF" strokeWidth="1" />
      <circle cx="50" cy="24" r="2" fill="#FFFFFF" />

      {/* Verification Shield & Checkmark Seal */}
      <circle cx="68" cy="33" r="8" fill="#046A38" stroke="#FFFFFF" strokeWidth="1.5" />
      <path d="M 64.5 33 L 67 35.5 L 71.5 30.5" stroke="#FFFFFF" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
