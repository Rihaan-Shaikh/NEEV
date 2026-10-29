"use client";

import React, { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import { api, IntegrationStatusItem } from "@/lib/api";
import {
  Network,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Zap,
  RefreshCw,
  ShieldCheck,
  Info,
  Server,
  Lock,
  ExternalLink
} from "lucide-react";

export default function IntegrationsPage() {
  const [adapters, setAdapters] = useState<IntegrationStatusItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [probingCode, setProbingCode] = useState<string | null>(null);
  const [probeResults, setProbeResults] = useState<Record<string, { success: boolean; message: string }>>({});

  const loadAdapters = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listIntegrationStatuses();
      setAdapters(data);
    } catch (err: any) {
      setError(err.message || "Failed to load integration adapters.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAdapters();
  }, []);

  const handleTestContract = async (adapterCode: string) => {
    setProbingCode(adapterCode);
    try {
      const res = await api.testIntegrationContract(adapterCode);
      setProbeResults((prev) => ({
        ...prev,
        [adapterCode]: {
          success: res.contract_test_status === "PASSED",
          message: res.message
        }
      }));
      // Update local item
      setAdapters((prev) =>
        prev.map((a) =>
          a.adapter_code === adapterCode
            ? {
              ...a,
              last_checked_at: res.checked_at,
              latency_ms: res.latency_ms,
              contract_test_status: res.contract_test_status
            }
            : a
        )
      );
    } catch (err: any) {
      setError(err.message || `Failed to probe contract for ${adapterCode}.`);
    } finally {
      setProbingCode(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "SIMULATED":
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 bg-purple-50 text-purple-900 border border-purple-200 text-xs font-semibold rounded-full">Simulated</span>;
      case "CONFIGURED":
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 bg-emerald-50 text-emerald-900 border border-emerald-200 text-xs font-semibold rounded-full">Configured</span>;
      case "NOT_CONFIGURED":
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 bg-slate-100 text-[#475569] border border-[#CBD5E1] text-xs font-semibold rounded-full">Not configured</span>;
      case "UNAVAILABLE":
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 bg-red-50 text-red-900 border border-red-200 text-xs font-semibold rounded-full">Unavailable</span>;
      default:
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 bg-slate-100 text-[#1E293B] text-xs rounded-full">{status}</span>;
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Title & Refresh */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-[#0F2942] tracking-tight">
              External source integration status & reliability
            </h1>
            <p className="text-xs text-[#475569] mt-0.5">
              Health metrics, verification response status, and interoperability protocols for regulatory registries.
            </p>
          </div>
          <button
            onClick={loadAdapters}
            disabled={isLoading}
            className="btn-rounded-secondary text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-[#0F2942] ${isLoading ? "animate-spin" : ""}`} />
            <span>Refresh status</span>
          </button>
        </div>
        {error && (
          <div className="p-3.5 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-800 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={loadAdapters} className="underline font-semibold hover:text-red-950">
              Retry
            </button>
          </div>
        )}

        {/* Adapters Grid */}
        {isLoading ? (
          <div className="h-64 flex items-center justify-center bg-white rounded-2xl border border-[#CBD5E1]">
            <div className="flex flex-col items-center gap-2">
              <div className="w-6 h-6 border-2 border-[#0F2942] border-t-transparent rounded-full animate-spin"></div>
              <span className="text-xs text-[#475569]">Verifying connection status with gateway adapters...</span>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {adapters.map((a) => {
              const probe = probeResults[a.adapter_code];
              return (
                <div
                  key={a.adapter_code}
                  className="bg-white p-5 rounded-2xl border border-[#CBD5E1] shadow-xs flex flex-col justify-between space-y-4 hover:border-[#0F2942] transition-colors"
                >
                  <div className="space-y-3">
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2 border-b border-[#E2E8F0] pb-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Server className="w-4 h-4 text-[#0F2942]" />
                          <h3 className="text-sm font-bold text-[#0F2942]">
                            {a.adapter_name}
                          </h3>
                        </div>
                        <span className="text-[11px] tabular-nums text-[#475569] px-2 py-0.5 bg-slate-100 rounded-full border border-slate-200">
                          {a.adapter_code}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {getStatusBadge(a.status)}
                      </div>
                    </div>

                    {/* Latency and Last Probe */}
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-0.5">
                        <span className="text-xs font-semibold text-[#475569] block">
                          Response latency
                        </span>
                        <div className="flex items-center gap-1 tabular-nums font-bold text-[#0F2942]">
                          <Zap className="w-3.5 h-3.5 text-[#0F2942]" />
                          <span>{a.latency_ms !== null && a.latency_ms !== undefined ? `${a.latency_ms.toFixed(1)} ms` : "—"}</span>
                        </div>
                      </div>

                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-0.5">
                        <span className="text-xs font-semibold text-[#475569] block">
                          Protocol test
                        </span>
                        <div className="flex items-center gap-1 font-semibold text-emerald-800">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                          <span>{a.contract_test_status}</span>
                        </div>
                      </div>
                    </div>

                    {/* Supported Claims */}
                    <div className="space-y-1 text-xs">
                      <span className="text-xs font-semibold text-[#475569] block">
                        Supported verification claims:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {a.supported_claims.map((claim: string) => (
                          <span
                            key={claim}
                            className="px-2.5 py-0.5 bg-slate-100 text-[#1E293B] tabular-nums text-[10px] font-medium rounded-full border border-slate-200"
                          >
                            {claim}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Known Limitations */}
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1">
                      <span className="text-xs font-semibold text-[#475569] block">
                        Governance & integration limitations:
                      </span>
                      <p className="text-[#1E293B] leading-relaxed text-[11px]">
                        {a.known_limitations}
                      </p>
                    </div>

                    {probe && (
                      <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-900 flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                        <span>{probe.message}</span>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="pt-3 border-t border-[#E2E8F0] flex items-center justify-between text-xs">
                    <span className="text-[11px] text-[#475569]">
                      Last verified: {new Date(a.last_checked_at).toLocaleTimeString()}
                    </span>

                    <button
                      onClick={() => handleTestContract(a.adapter_code)}
                      disabled={probingCode === a.adapter_code}
                      className="btn-rounded-primary text-xs disabled:opacity-50"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 text-white ${probingCode === a.adapter_code ? "animate-spin" : ""}`} />
                      <span>{probingCode === a.adapter_code ? "Verifying..." : "Test protocol"}</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AppShell>
  );
}