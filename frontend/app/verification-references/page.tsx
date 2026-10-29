"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import {
  api,
  VerificationReferenceItem,
  VerificationReferenceCreatedResponse,
  EnrolmentRecord
} from "@/lib/api";
import {
  QrCode,
  ShieldCheck,
  Plus,
  Search,
  Copy,
  Check,
  X,
  ExternalLink,
  AlertCircle
} from "lucide-react";

export default function VerificationReferencesPage() {
  const [references, setReferences] = useState<VerificationReferenceItem[]>([]);
  const [enrolments, setEnrolments] = useState<EnrolmentRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  // Issue Reference Modal
  const [isIssueModalOpen, setIsIssueModalOpen] = useState(false);
  const [selectedEnrolmentId, setSelectedEnrolmentId] = useState("");
  const [purpose, setPurpose] = useState("EMPLOYMENT_VERIFICATION");
  const [expiresInDays, setExpiresInDays] = useState(30);
  const [maxUses, setMaxUses] = useState<number | "">("");
  const [discloseName, setDiscloseName] = useState(true);
  const [discloseInst, setDiscloseInst] = useState(true);
  const [discloseProg, setDiscloseProg] = useState(true);
  const [discloseStatus, setDiscloseStatus] = useState(true);
  const [discloseAy, setDiscloseAy] = useState(true);
  const [discloseAdmissionDate, setDiscloseAdmissionDate] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [issueError, setIssueError] = useState<string | null>(null);

  // One-time Token Reveal Modal
  const [createdRef, setCreatedRef] = useState<VerificationReferenceCreatedResponse | null>(null);
  const [copied, setCopied] = useState(false);

  // Revoke Modal
  const [revokeModalRef, setRevokeModalRef] = useState<VerificationReferenceItem | null>(null);
  const [revocationReason, setRevocationReason] = useState("");
  const [isRevoking, setIsRevoking] = useState(false);
  const [revokeError, setRevokeError] = useState<string | null>(null);

  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [refsRes, enrolmentsRes] = await Promise.all([
        api.listVerificationReferences({
          search: search.trim() || undefined,
          status: statusFilter || undefined,
          page_size: 50
        }),
        api.listEnrolments({ page_size: 100 })
      ]);
      setReferences(refsRes.items || []);
      setEnrolments(enrolmentsRes.items || []);
      if (enrolmentsRes.items?.length > 0) {
        setSelectedEnrolmentId(enrolmentsRes.items[0].id);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load verification references.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  const handleIssueReference = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEnrolmentId) {
      setIssueError("Please select a student enrolment record.");
      return;
    }

    setIsSubmitting(true);
    setIssueError(null);

    try {
      const res = await api.issueVerificationReference({
        enrolment_record_id: selectedEnrolmentId,
        purpose,
        expires_in_days: Number(expiresInDays),
        max_uses: maxUses ? Number(maxUses) : null,
        disclosure_profile: {
          disclose_student_name: discloseName,
          disclose_institution: discloseInst,
          disclose_programme: discloseProg,
          disclose_enrolment_status: discloseStatus,
          disclose_academic_year: discloseAy,
          disclose_admission_date: discloseAdmissionDate
        }
      });

      setIsIssueModalOpen(false);
      setCreatedRef(res);
      setReferences((prev) => [res, ...prev]);
      setNotification({
        type: "success",
        text: `Verification reference ${res.public_reference_code} generated successfully.`
      });
    } catch (err: any) {
      setIssueError(err.message || "Failed to issue verification reference.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRevokeReference = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!revokeModalRef || revocationReason.trim().length < 5) {
      setRevokeError("Revocation reason must be at least 5 characters.");
      return;
    }

    setIsRevoking(true);
    setRevokeError(null);

    try {
      const updated = await api.revokeVerificationReference(revokeModalRef.id, {
        revocation_reason: revocationReason.trim()
      });
      setRevokeModalRef(null);
      setRevocationReason("");
      setReferences((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      setNotification({
        type: "success",
        text: `Reference ${updated.public_reference_code} revoked successfully.`
      });
    } catch (err: any) {
      setRevokeError(err.message || "Failed to revoke verification reference.");
    } finally {
      setIsRevoking(false);
    }
  };

  const copyTokenToClipboard = () => {
    if (!createdRef) return;
    navigator.clipboard.writeText(createdRef.raw_bearer_token);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "ACTIVE":
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-semibold rounded-full">Active</span>;
      case "REVOKED":
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 bg-red-50 text-red-800 border border-red-200 text-xs font-semibold rounded-full">Revoked</span>;
      case "EXPIRED":
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 bg-slate-100 text-[#475569] border border-[#CBD5E1] text-xs font-semibold rounded-full">Expired</span>;
      case "EXHAUSTED":
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 bg-amber-50 text-amber-800 border border-amber-200 text-xs font-semibold rounded-full">Limit reached</span>;
      default:
        return <span className="whitespace-nowrap inline-flex items-center px-2.5 py-0.5 bg-slate-100 text-[#1E293B] text-xs rounded-full">{status}</span>;
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Title and Top Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-[#0F2942] tracking-tight">
              Limited-purpose verification references
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/verify"
              className="btn-rounded-secondary text-xs"
            >
              <ExternalLink className="w-3.5 h-3.5 text-[#0F2942]" />
              <span>Public verification resolver</span>
            </Link>
            <button
              onClick={() => {
                setIssueError(null);
                setIsIssueModalOpen(true);
              }}
              className="btn-rounded-primary text-xs"
            >
              <Plus className="w-3.5 h-3.5 text-white" />
              <span>Issue verification reference</span>
            </button>
          </div>
        </div>

        {notification && (
          <div
            className={`p-3.5 rounded-2xl border text-xs flex items-center justify-between ${notification.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : "bg-red-50 border-red-200 text-red-800"
              }`}
          >
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{notification.text}</span>
            </div>
            <button
              onClick={() => setNotification(null)}
              className="text-slate-500 hover:text-slate-800 text-xs font-semibold"
            >
              Dismiss
            </button>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-800 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={loadData} className="underline font-semibold hover:text-red-950">
              Retry
            </button>
          </div>
        )}

        {/* Informational Banner */}
        <div className="p-3.5 bg-slate-50 border border-[#CBD5E1] rounded-2xl text-xs text-[#475569] flex items-start gap-2.5">
          <ShieldCheck className="w-4 h-4 text-[#0F2942] shrink-0 mt-0.5" />
          <div>
            <strong className="text-[#0F2942] font-semibold">Privacy-preserving reference design:</strong> Verification references provide third parties (employers, banks, universities) limited, time-bound, and audited proof of enrolment without disclosing sensitive identifiers like APAAR ID or national ID numbers.
          </div>
        </div>

        {/* Filters and Search Bar */}
        <div className="bg-white p-3.5 rounded-2xl border border-[#CBD5E1] shadow-xs flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
          <form onSubmit={handleSearch} className="flex-1 max-w-md relative flex items-center gap-2">
            <div className="relative flex-1">
              <input
                type="text"
                placeholder="Search by tracking code or student name..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] bg-slate-50 focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
              />
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3.5 top-3" />
            </div>
            <button
              type="submit"
              className="btn-rounded-primary text-xs"
            >
              Search
            </button>
          </form>

          <div className="flex items-center gap-2">
            <span className="text-xs text-[#475569] font-medium">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3.5 py-1.5 border border-[#CBD5E1] rounded-full text-xs bg-slate-50 text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
            >
              <option value="">All statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="REVOKED">Revoked</option>
              <option value="EXPIRED">Expired</option>
              <option value="EXHAUSTED">Limit reached</option>
            </select>
          </div>
        </div>

        {/* Main Reference List Table */}
        <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xs overflow-hidden">
          <div className="p-4 border-b border-[#CBD5E1] bg-slate-50 flex items-center justify-between">
            <div>
              <h2 className="text-xs font-bold text-[#0F2942]">
                Issued verification references
              </h2>
              <p className="text-[11px] text-[#475569] mt-0.5">
                Audit trail of active and archived bearer tokens generated for external verification.
              </p>
            </div>
            <span className="text-[11px] text-[#475569]">
              {references.length} {references.length === 1 ? "reference" : "references"} found
            </span>
          </div>

          {isLoading ? (
            <div className="p-12 text-center text-xs text-[#475569]">
              <div className="w-5 h-5 border-2 border-[#0F2942] border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
              Loading verification references...
            </div>
          ) : references.length === 0 ? (
            <div className="p-12 text-center text-xs text-[#475569]">
              No verification references found. Click "Issue verification reference" to generate one.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs neev-table">
                <thead>
                  <tr>
                    <th>Public code</th>
                    <th>Student</th>
                    <th>Institution</th>
                    <th>Purpose</th>
                    <th>Status</th>
                    <th className="text-center">Uses</th>
                    <th>Expires</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E2E8F0]">
                  {references.map((r) => (
                    <tr key={r.id}>
                      <td className="tabular-nums font-bold text-[#0F2942]">
                        <div className="flex items-center gap-1.5">
                          <QrCode className="w-3.5 h-3.5 text-[#0F2942]" />
                          <span>{r.public_reference_code}</span>
                        </div>
                      </td>
                      <td className="font-semibold text-[#0F2942]">
                        {r.student_full_name}
                      </td>
                      <td className="text-[#475569]">
                        {r.institution_name}
                      </td>
                      <td>
                        <span className="text-[11px] px-2.5 py-0.5 bg-slate-100 rounded-full border border-slate-200 text-[#1E293B]">
                          {r.purpose.replace(/_/g, " ").toLowerCase()}
                        </span>
                      </td>
                      <td>
                        {getStatusBadge(r.status)}
                      </td>
                      <td className="text-center tabular-nums">
                        <span className="font-bold text-[#0F2942]">{r.use_count}</span>
                        <span className="text-[#475569]"> / {r.max_uses !== null ? r.max_uses : "∞"}</span>
                      </td>
                      <td className="text-[#475569] text-[11px]">
                        {new Date(r.expires_at).toLocaleDateString()}
                      </td>
                      <td className="text-right">
                        {r.status === "ACTIVE" ? (
                          <button
                            onClick={() => {
                              setRevokeModalRef(r);
                              setRevocationReason("");
                              setRevokeError(null);
                            }}
                            className="btn-rounded-secondary text-xs py-1 px-3 text-red-700 border-red-200 hover:bg-red-50"
                          >
                            Revoke
                          </button>
                        ) : (
                          <span className="text-[11px] text-slate-400">
                            {r.status === "REVOKED" ? "Revoked" : "Inactive"}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* 1. Issue Reference Modal */}
        {isIssueModalOpen && (
          <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xl max-w-lg w-full p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <div className="flex items-center gap-2">
                  <QrCode className="w-4 h-4 text-[#0F2942]" />
                  <h3 className="text-sm font-bold text-[#0F2942]">
                    Issue verification reference
                  </h3>
                </div>
                <button
                  onClick={() => setIsIssueModalOpen(false)}
                  className="w-7 h-7 rounded-full flex items-center justify-center hover:bg-slate-100 text-[#475569] hover:text-[#0F2942]"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {issueError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
                  <span>{issueError}</span>
                </div>
              )}

              <form onSubmit={handleIssueReference} className="space-y-4 text-xs">
                <div>
                  <label className="block font-semibold text-[#0F2942] mb-1">
                    Select student enrolment record <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={selectedEnrolmentId}
                    onChange={(e) => setSelectedEnrolmentId(e.target.value)}
                    className="w-full px-3.5 py-2 border border-[#CBD5E1] rounded-full text-xs bg-slate-50 text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    required
                  >
                    {enrolments.map((enr) => (
                      <option key={enr.id} value={enr.id}>
                        {enr.student_full_name} — {enr.programme_name} ({enr.institution_name})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-semibold text-[#0F2942] mb-1">
                      Verification purpose <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={purpose}
                      onChange={(e) => setPurpose(e.target.value)}
                      className="w-full px-3.5 py-2 border border-[#CBD5E1] rounded-full text-xs bg-slate-50 text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    >
                      <option value="EMPLOYMENT_VERIFICATION">Employment verification</option>
                      <option value="HIGHER_STUDIES_ADMISSION">Higher studies admission</option>
                      <option value="BANK_LOAN_BACKGROUND">Bank loan background</option>
                      <option value="VISA_BACKGROUND_CHECK">Visa background check</option>
                      <option value="GENERAL">General verification</option>
                    </select>
                  </div>

                  <div>
                    <label className="block font-semibold text-[#0F2942] mb-1">
                      Token validity (days)
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={365}
                      value={expiresInDays}
                      onChange={(e) => setExpiresInDays(Number(e.target.value))}
                      className="w-full px-3.5 py-2 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block font-semibold text-[#0F2942] mb-1">
                    Maximum uses (leave blank for unlimited)
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={maxUses}
                    onChange={(e) => setMaxUses(e.target.value === "" ? "" : Number(e.target.value))}
                    placeholder="Unlimited"
                    className="w-full px-3.5 py-2 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                  />
                </div>

                <div className="space-y-2 pt-2 border-t border-[#E2E8F0]">
                  <span className="font-semibold text-[#0F2942] text-[11px] block">
                    Selective disclosure profile:
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <label className="flex items-center gap-2 text-[#475569]">
                      <input
                        type="checkbox"
                        checked={discloseName}
                        onChange={(e) => setDiscloseName(e.target.checked)}
                        className="rounded text-[#0F2942]"
                      />
                      Disclose student name
                    </label>
                    <label className="flex items-center gap-2 text-[#475569]">
                      <input
                        type="checkbox"
                        checked={discloseInst}
                        onChange={(e) => setDiscloseInst(e.target.checked)}
                        className="rounded text-[#0F2942]"
                      />
                      Disclose institution
                    </label>
                    <label className="flex items-center gap-2 text-[#475569]">
                      <input
                        type="checkbox"
                        checked={discloseProg}
                        onChange={(e) => setDiscloseProg(e.target.checked)}
                        className="rounded text-[#0F2942]"
                      />
                      Disclose programme
                    </label>
                    <label className="flex items-center gap-2 text-[#475569]">
                      <input
                        type="checkbox"
                        checked={discloseStatus}
                        onChange={(e) => setDiscloseStatus(e.target.checked)}
                        className="rounded text-[#0F2942]"
                      />
                      Disclose enrolment status
                    </label>
                    <label className="flex items-center gap-2 text-[#475569]">
                      <input
                        type="checkbox"
                        checked={discloseAy}
                        onChange={(e) => setDiscloseAy(e.target.checked)}
                        className="rounded text-[#0F2942]"
                      />
                      Disclose academic session
                    </label>
                    <label className="flex items-center gap-2 text-[#475569]">
                      <input
                        type="checkbox"
                        checked={discloseAdmissionDate}
                        onChange={(e) => setDiscloseAdmissionDate(e.target.checked)}
                        className="rounded text-[#0F2942]"
                      />
                      Disclose admission date
                    </label>
                  </div>
                </div>

                <div className="flex justify-end gap-2.5 pt-3 border-t border-[#E2E8F0]">
                  <button
                    type="button"
                    onClick={() => setIsIssueModalOpen(false)}
                    className="btn-rounded-secondary text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="btn-rounded-primary text-xs disabled:opacity-50"
                  >
                    {isSubmitting ? "Generating..." : "Generate reference"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* 2. One-Time Token Reveal Modal */}
        {createdRef && (
          <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xl max-w-md w-full p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <div className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-600" />
                  <h3 className="text-sm font-bold text-[#0F2942]">
                    Verification reference generated
                  </h3>
                </div>
                <button
                  onClick={() => setCreatedRef(null)}
                  className="w-7 h-7 rounded-full flex items-center justify-center hover:bg-slate-100 text-[#475569] hover:text-[#0F2942]"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 space-y-1">
                <p className="font-bold">One-time bearer token notice:</p>
                <p>
                  Copy this token now. For security and data protection, this token is issued once and cannot be retrieved again after this session.
                </p>
              </div>

              <div className="space-y-1.5 text-xs">
                <span className="font-semibold text-[#0F2942] block">
                  Public tracking code:
                </span>
                <span className="px-3.5 py-1.5 bg-slate-50 rounded-full border border-[#CBD5E1] tabular-nums text-xs font-bold text-[#0F2942] block">
                  {createdRef.public_reference_code}
                </span>
              </div>

              <div className="space-y-1.5 text-xs">
                <span className="font-semibold text-[#0F2942] block">
                  Verification bearer token (to deliver to recipient):
                </span>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    readOnly
                    value={createdRef.raw_bearer_token}
                    className="flex-1 px-3.5 py-2 bg-slate-50 border border-[#CBD5E1] rounded-full tabular-nums text-xs text-[#1E293B]"
                  />
                  <button
                    onClick={copyTokenToClipboard}
                    className="btn-rounded-primary text-xs shrink-0"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-white" />}
                    <span>{copied ? "Copied" : "Copy"}</span>
                  </button>
                </div>
              </div>

              <div className="pt-3 border-t border-[#E2E8F0] flex justify-end">
                <button
                  onClick={() => setCreatedRef(null)}
                  className="btn-rounded-primary text-xs"
                >
                  Done
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 3. Revoke Reference Modal */}
        {revokeModalRef && (
          <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xl max-w-md w-full p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <h3 className="text-sm font-bold text-red-900">
                  Revoke verification reference
                </h3>
                <button
                  onClick={() => setRevokeModalRef(null)}
                  className="w-7 h-7 rounded-full flex items-center justify-center hover:bg-slate-100 text-[#475569] hover:text-[#0F2942]"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {revokeError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
                  <span>{revokeError}</span>
                </div>
              )}

              <form onSubmit={handleRevokeReference} className="space-y-4 text-xs">
                <p className="text-[#475569]">
                  Revoking reference <strong className="text-[#0F2942] tabular-nums">{revokeModalRef.public_reference_code}</strong> for {revokeModalRef.student_full_name} will immediately deactivate all verification queries.
                </p>

                <div>
                  <label className="block font-semibold text-[#0F2942] mb-1">
                    Revocation rationale <span className="text-red-600">* (at least 5 characters)</span>
                  </label>
                  <textarea
                    value={revocationReason}
                    onChange={(e) => setRevocationReason(e.target.value)}
                    placeholder="Enter reason for deactivation or student record change..."
                    rows={3}
                    className="w-full px-3.5 py-2.5 border border-[#CBD5E1] rounded-xl text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942]"
                    required
                  />
                </div>

                <div className="flex justify-end gap-2.5 pt-3 border-t border-[#E2E8F0]">
                  <button
                    type="button"
                    onClick={() => setRevokeModalRef(null)}
                    className="btn-rounded-secondary text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isRevoking || revocationReason.trim().length < 5}
                    className="btn-rounded-primary text-xs bg-red-700 hover:bg-red-800 disabled:opacity-50"
                  >
                    {isRevoking ? "Revoking..." : "Confirm revocation"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
