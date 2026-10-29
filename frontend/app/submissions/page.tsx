"use client";

import React, { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import { 
  apiRequest, 
  Institution, 
  InstitutionListResponse, 
  AcademicYear, 
  Programme, 
  Batch, 
  BatchPreview,
  RowPreviewItem
} from "@/lib/api";
import { useLanguage } from "@/lib/language-context";
import { 
  UploadCloud, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  ShieldCheck, 
  FileCheck2,
  ChevronDown,
  ChevronUp,
  Info
} from "lucide-react";
import Link from "next/link";

export default function SubmissionsPage() {
  const { language, t } = useLanguage();
  // Step state: 1 (Context), 2 (Upload), 3 (Preview & Validate), 4 (Receipt)
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);

  // References
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [programmes, setProgrammes] = useState<Programme[]>([]);

  // Selection
  const [selectedInstId, setSelectedInstId] = useState("");
  const [selectedAyId, setSelectedAyId] = useState("");
  const [selectedProgId, setSelectedProgId] = useState("");
  const [submissionType, setSubmissionType] = useState("REGULAR_ENROLMENT");

  // Batch & Processing
  const [currentBatch, setCurrentBatch] = useState<Batch | null>(null);
  const [previewData, setPreviewData] = useState<BatchPreview | null>(null);
  const [receiptData, setReceiptData] = useState<any | null>(null);

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [filterRowsStatus, setFilterRowsStatus] = useState<string>("ALL");
  const [expandedRows, setExpandedRows] = useState<Record<number, boolean>>({});
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  useEffect(() => {
    const loadInitData = async () => {
      try {
        const instRes = await apiRequest<InstitutionListResponse>("/institutions?page=1&page_size=100");
        setInstitutions(instRes.items);
        if (instRes.items.length > 0) {
          setSelectedInstId(instRes.items[0].id);
        }

        const ayRes = await apiRequest<AcademicYear[]>("/academic-years");
        setAcademicYears(ayRes);
        const activeAy = ayRes.find(a => a.status === "ACTIVE") || ayRes[0];
        if (activeAy) {
          setSelectedAyId(activeAy.id);
        }
      } catch (err: any) {
        setErrorMsg(err.message || "Failed to load references");
      }
    };
    loadInitData();
  }, []);

  // Load programmes when institution changes
  useEffect(() => {
    if (selectedInstId) {
      apiRequest<Programme[]>(`/institutions/${selectedInstId}/programmes`)
        .then(setProgrammes)
        .catch(() => setProgrammes([]));
    }
  }, [selectedInstId]);

  // Step 1: Create Batch
  const handleCreateBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const batch = await apiRequest<Batch>("/batches", {
        method: "POST",
        body: JSON.stringify({
          institution_id: selectedInstId,
          academic_year_id: selectedAyId,
          programme_id: selectedProgId || null,
          submission_type: submissionType
        })
      });
      setCurrentBatch(batch);
      setStep(2);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to create batch context");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Step 2: Upload CSV
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !currentBatch) return;

    if (!file.name.toLowerCase().endsWith(".csv")) {
      setErrorMsg("Please upload a valid .csv student list file.");
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      await apiRequest<Batch>(`/batches/${currentBatch.id}/file`, {
        method: "POST",
        body: formData,
      });

      const preview = await apiRequest<BatchPreview>(`/batches/${currentBatch.id}/preview`);
      setPreviewData(preview);
      setStep(3);
    } catch (err: any) {
      setErrorMsg(err.message || "Error uploading and validating student list file.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Step 3: Finalize Batch
  const handleFinalizeBatch = async () => {
    if (!currentBatch) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    setShowConfirmModal(false);

    try {
      const receipt = await apiRequest<any>(`/batches/${currentBatch.id}/finalize`, {
        method: "POST"
      });
      setReceiptData(receipt);
      setStep(4);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to finalize batch.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleRowExpand = (rowNum: number) => {
    setExpandedRows(prev => ({ ...prev, [rowNum]: !prev[rowNum] }));
  };

  const stepsList = [
    { num: 1, label: language === "hi" ? "सत्र एवं संस्थान चयन" : "Select context" },
    { num: 2, label: language === "hi" ? "छात्र सूची अपलोड" : "Upload student list" },
    { num: 3, label: language === "hi" ? "पूर्वावलोकन एवं सत्यापन" : "Preview & validate" },
    { num: 4, label: language === "hi" ? "पावती" : "Receipt" }
  ];

  const filteredPreviewRows = previewData?.rows.filter(r => {
    if (filterRowsStatus === "ALL") return true;
    return r.processing_status === filterRowsStatus;
  }) || [];

  const selectedInst = institutions.find(i => i.id === (currentBatch?.institution_id || selectedInstId));
  const selectedAy = academicYears.find(a => a.id === (currentBatch?.academic_year_id || selectedAyId));
  const selectedProg = programmes.find(p => p.id === (currentBatch?.programme_id || selectedProgId));

  return (
    <AppShell>
      <div className="space-y-6 pb-12">
        {/* Header & Steps Indicator */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-[#CBD5E1] pb-4">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-[#0F2942] tracking-tight">
              {language === "hi" ? "छात्र सूची प्रस्तुति प्रक्रिया" : "Student list submission workflow"}
            </h1>
            <p className="text-xs text-[#475569] mt-0.5">
              {language === "hi"
                ? "संस्थागत छात्र सूची सत्यापन, क्षमता मिलान एवं आधिकारिक पावती जारी करना।"
                : "Student list upload, verification against approved seats, and official receipt issuance."}
            </p>
          </div>

          {/* Stepper (Rounded Pills) */}
          <nav aria-label="Submission stages" className="flex items-center gap-2 bg-white px-4 py-2 rounded-full border border-[#CBD5E1] shadow-xs">
            {stepsList.map((s) => (
              <div key={s.num} className="flex items-center gap-1.5">
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-bold ${
                  step === s.num
                    ? "bg-[#0F2942] text-white"
                    : step > s.num
                    ? "bg-[#15803D] text-white"
                    : "bg-slate-200 text-[#475569]"
                }`}>
                  {step > s.num ? "✓" : s.num}
                </span>
                <span className={`text-xs ${step === s.num ? "font-bold text-[#0F2942]" : "text-[#475569]"}`}>
                  {s.label}
                </span>
                {s.num < 4 && <span className="text-[#CBD5E1] mx-1">›</span>}
              </div>
            ))}
          </nav>
        </div>

        {errorMsg && (
          <div className="p-3.5 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800 flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold block">Submission notice</span>
              {errorMsg}
            </div>
          </div>
        )}

        {/* STEP 1: CONTEXT SELECTION (Clean 2-Column Split: 65% + 35% - NO 3-COLUMN LAYOUT) */}
        {step === 1 && (
          <div className="flex flex-col lg:flex-row gap-6">
            <div className="w-full lg:w-2/3 bg-white rounded-2xl border border-[#CBD5E1] shadow-xs p-6 sm:p-8">
              <h2 className="text-sm font-bold text-[#0F2942] border-b border-[#E2E8F0] pb-3 mb-4 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-[#0F2942]" />
                Step 1: Select submission context
              </h2>

              <form onSubmit={handleCreateBatch} className="space-y-4">
                <div>
                  <label htmlFor="select-institution" className="block text-xs font-semibold text-[#1E293B] mb-1">
                    Institution (Authorized scope)
                  </label>
                  <select
                    id="select-institution"
                    required
                    value={selectedInstId}
                    onChange={(e) => setSelectedInstId(e.target.value)}
                    className="w-full px-4 py-2 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942] bg-white"
                  >
                    {institutions.map(inst => (
                      <option key={inst.id} value={inst.id}>
                        {inst.name} ({inst.official_institution_code})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="select-academic-year" className="block text-xs font-semibold text-[#1E293B] mb-1">
                      Academic session
                    </label>
                    <select
                      id="select-academic-year"
                      required
                      value={selectedAyId}
                      onChange={(e) => setSelectedAyId(e.target.value)}
                      className="w-full px-4 py-2 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942] bg-white"
                    >
                      {academicYears.map(ay => (
                        <option key={ay.id} value={ay.id}>
                          {ay.label} ({ay.status})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label htmlFor="select-programme" className="block text-xs font-semibold text-[#1E293B] mb-1">
                      Programme (Optional filter)
                    </label>
                    <select
                      id="select-programme"
                      value={selectedProgId}
                      onChange={(e) => setSelectedProgId(e.target.value)}
                      className="w-full px-4 py-2 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942] bg-white"
                    >
                      <option value="">All approved programmes</option>
                      {programmes.map(prog => (
                        <option key={prog.id} value={prog.id}>
                          {prog.programme_name} ({prog.official_programme_code})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label htmlFor="submission-type" className="block text-xs font-semibold text-[#1E293B] mb-1">
                    Submission type
                  </label>
                  <select
                    id="submission-type"
                    value={submissionType}
                    onChange={(e) => setSubmissionType(e.target.value)}
                    className="w-full px-4 py-2 border border-[#CBD5E1] rounded-full text-xs text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#0F2942] bg-white"
                  >
                    <option value="REGULAR_ENROLMENT">Regular annual enrolment</option>
                    <option value="LATERAL_ENTRY">Lateral entry admissions</option>
                    <option value="TRANSFER_ADJUSTMENT">Transfer adjustments</option>
                  </select>
                </div>

                <div className="pt-3 border-t border-[#E2E8F0] flex justify-end">
                  <button
                    type="submit"
                    disabled={isSubmitting || !selectedInstId || !selectedAyId}
                    className="btn-rounded-primary text-xs"
                  >
                    {isSubmitting ? "Creating batch..." : "Proceed to upload →"}
                  </button>
                </div>
              </form>
            </div>

            {/* Sidebar Guide (35% width - 2-column pattern) */}
            <div className="w-full lg:w-1/3 bg-slate-50 rounded-2xl border border-[#CBD5E1] p-6 space-y-3">
              <div className="text-xs font-semibold text-[#0F2942] border-b border-[#E2E8F0] pb-2 flex items-center gap-1.5">
                <Info className="w-4 h-4 text-[#0F2942]" />
                Institutional submission standards
              </div>
              <p className="text-xs text-[#475569] leading-relaxed">
                Student list submissions must be valid CSV files. Each record is verified against approved course capacities and student identification records.
              </p>
              <div className="bg-white p-3.5 rounded-xl border border-[#CBD5E1] text-xs text-[#1E293B] space-y-1">
                <div className="font-semibold text-xs text-[#0F2942] mb-1">Required CSV fields:</div>
                <div>• institution_student_id</div>
                <div>• student_full_name</div>
                <div>• admission_date (YYYY-MM-DD)</div>
                <div>• programme_code</div>
                <div>• enrolment_status (ACTIVE/INACTIVE)</div>
                <div>• apaar_id (12 digits, optional)</div>
              </div>
            </div>
          </div>
        )}

        {/* STEP 2: CSV UPLOAD (Clean 2-Column Split: 65% + 35% - NO 3-COLUMN LAYOUT) */}
        {step === 2 && currentBatch && (
          <div className="flex flex-col lg:flex-row gap-6">
            <div className="w-full lg:w-2/3 bg-white rounded-2xl border border-[#CBD5E1] shadow-xs p-6 sm:p-8 space-y-5">
              <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
                <div>
                  <h2 className="text-sm font-bold text-[#0F2942]">Step 2: Upload student list CSV</h2>
                  <span className="text-xs text-[#475569] tabular-nums">Batch reference: {currentBatch.id.slice(0, 8)}...</span>
                </div>
                <button
                  onClick={() => setStep(1)}
                  className="btn-rounded-secondary text-xs"
                >
                  Change context
                </button>
              </div>

              {/* Upload Dropzone */}
              <div className="border-2 border-dashed border-[#CBD5E1] rounded-2xl p-10 text-center bg-slate-50 hover:bg-white transition-colors">
                <UploadCloud className="w-10 h-10 text-[#0F2942] mx-auto mb-2" />
                <p className="text-xs font-semibold text-[#0F2942]">
                  Select CSV student list to upload and verify
                </p>
                <p className="text-[11px] text-[#475569] mt-1 mb-5">
                  Supported format: Comma-Separated Values (.csv), UTF-8 encoded, maximum 10MB
                </p>

                <label className="cursor-pointer btn-rounded-primary text-xs shadow-xs">
                  <span>{isSubmitting ? "Uploading and verifying..." : "Browse and upload CSV"}</span>
                  <input
                    type="file"
                    accept=".csv"
                    disabled={isSubmitting}
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </label>
              </div>
            </div>

            {/* Persistent Context Card */}
            <div className="w-full lg:w-1/3 bg-slate-50 rounded-2xl border border-[#CBD5E1] p-6 space-y-3">
              <div className="text-xs font-semibold text-[#0F2942] border-b border-[#E2E8F0] pb-2">
                Active submission context
              </div>
              <div className="space-y-2 text-xs">
                <div>
                  <span className="text-[#475569] block text-[11px]">Institution:</span>
                  <strong className="text-[#0F2942]">{selectedInst?.name || "Selected institution"}</strong>
                </div>
                <div>
                  <span className="text-[#475569] block text-[11px]">Academic session:</span>
                  <strong className="text-[#0F2942]">{selectedAy?.label || "2024–2025"}</strong>
                </div>
                <div>
                  <span className="text-[#475569] block text-[11px]">Programme scope:</span>
                  <strong className="text-[#0F2942]">{selectedProg?.programme_name || "All institution programmes"}</strong>
                </div>
                <div>
                  <span className="text-[#475569] block text-[11px]">Verification standard:</span>
                  <span className="text-[#15803D] font-semibold">Enrolment Integrity Standards v1.0</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* STEP 3: PREVIEW & VALIDATE */}
        {step === 3 && previewData && (
          <div className="space-y-6">
            {/* Context & Summary Bar (4-Column Linear Stats) */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-white p-4 rounded-2xl border border-[#CBD5E1] shadow-xs">
                <span className="text-xs text-[#475569] font-medium">Total student records</span>
                <div className="text-2xl font-bold text-[#0F2942] mt-1 tabular-nums">{previewData.total_rows}</div>
              </div>
              <div className="bg-white p-4 rounded-2xl border border-emerald-200 bg-emerald-50/20 shadow-xs">
                <span className="text-xs text-emerald-800 font-medium">Verified valid</span>
                <div className="text-2xl font-bold text-[#15803D] mt-1 tabular-nums">{previewData.valid_rows}</div>
              </div>
              <div className="bg-white p-4 rounded-2xl border border-amber-200 bg-amber-50/20 shadow-xs">
                <span className="text-xs text-amber-800 font-medium">Flagged warnings</span>
                <div className="text-2xl font-bold text-amber-700 mt-1 tabular-nums">{previewData.warning_rows}</div>
              </div>
              <div className="bg-white p-4 rounded-2xl border border-red-200 bg-red-50/20 shadow-xs">
                <span className="text-xs text-red-800 font-medium">Flagged errors</span>
                <div className="text-2xl font-bold text-red-700 mt-1 tabular-nums">{previewData.error_rows}</div>
              </div>
            </div>

            {/* Filter & Rows Table */}
            <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xs overflow-hidden">
              <div className="p-4 border-b border-[#E2E8F0] flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-[#475569]">Filter view:</span>
                  <div className="flex rounded-full border border-[#CBD5E1] overflow-hidden text-xs">
                    {["ALL", "VALID", "WARNING", "ERROR"].map((status) => (
                      <button
                        key={status}
                        onClick={() => setFilterRowsStatus(status)}
                        className={`px-3 py-1 font-medium transition-colors ${
                          filterRowsStatus === status
                            ? "bg-[#0F2942] text-white"
                            : "bg-white text-[#475569] hover:bg-slate-100"
                        }`}
                      >
                        {status === "ALL" ? "All rows" : status === "VALID" ? "Valid" : status === "WARNING" ? "Warnings" : "Errors"}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="text-xs text-[#475569]">
                  Showing <strong className="tabular-nums">{filteredPreviewRows.length}</strong> of <strong className="tabular-nums">{previewData.total_rows}</strong> rows
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full neev-table text-xs">
                  <thead>
                    <tr>
                      <th>Row</th>
                      <th>Student ID</th>
                      <th>Full name</th>
                      <th>Admission date</th>
                      <th>Programme code</th>
                      <th>Status</th>
                      <th>Identity verification</th>
                      <th>Outcome</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E8F0]">
                    {filteredPreviewRows.map((r) => {
                      const isExpanded = !!expandedRows[r.row_number];
                      const hasIssues = r.errors.length > 0 || r.warnings.length > 0;
                      return (
                        <React.Fragment key={r.row_number}>
                          <tr>
                            <td className="text-xs font-semibold text-[#475569] tabular-nums">
                              #{r.row_number}
                            </td>
                            <td className="font-semibold text-[#0F2942] tabular-nums">
                              {r.raw_data.institution_student_id || <span className="text-red-600 italic">Missing</span>}
                            </td>
                            <td className="text-[#1E293B]">{r.raw_data.student_full_name || <span className="text-red-600 italic">Missing</span>}</td>
                            <td className="text-[#475569] tabular-nums">{r.raw_data.admission_date || "—"}</td>
                            <td className="text-[#475569] text-xs">{r.raw_data.programme_code || "—"}</td>
                            <td className="text-xs">{r.raw_data.enrolment_status || "—"}</td>
                            <td>
                              {r.normalized_data?.apaar_validation_status === "SIMULATED" && (
                                <span className="text-[10px] bg-sky-50 text-sky-800 px-2 py-0.5 rounded-full border border-sky-200">
                                  Simulated
                                </span>
                              )}
                              {r.normalized_data?.apaar_validation_status === "UNAVAILABLE" && (
                                <span className="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full border border-slate-200">
                                  Unavailable
                                </span>
                              )}
                              {r.errors.some(e => e.rule_code === "APA-002") && (
                                <span className="text-[10px] bg-red-100 text-red-800 px-2 py-0.5 rounded-full border border-red-200">
                                  Invalid format
                                </span>
                              )}
                            </td>
                            <td>
                              {r.processing_status === "ERROR" && (
                                <span className="inline-flex items-center gap-1 text-xs font-semibold text-red-700">
                                  <XCircle className="w-3.5 h-3.5" /> {r.errors.length} error{r.errors.length > 1 ? "s" : ""}
                                </span>
                              )}
                              {r.processing_status === "WARNING" && (
                                <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-700">
                                  <AlertTriangle className="w-3.5 h-3.5" /> Warning
                                </span>
                              )}
                              {r.processing_status === "VALID" && (
                                <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700">
                                  <CheckCircle2 className="w-3.5 h-3.5" /> Verified
                                </span>
                              )}
                            </td>
                            <td>
                              {hasIssues && (
                                <button
                                  onClick={() => toggleRowExpand(r.row_number)}
                                  className="btn-rounded-secondary text-xs py-1 px-2.5"
                                >
                                  {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                                  {isExpanded ? "Hide" : "Inspect"}
                                </button>
                              )}
                            </td>
                          </tr>

                          {/* Expanded Actionable Error Box */}
                          {isExpanded && hasIssues && (
                            <tr className="bg-red-50/50">
                              <td colSpan={9} className="p-3 border-b border-[#CBD5E1]">
                                <div className="space-y-1.5 pl-4">
                                  {r.errors.map((err, i) => (
                                    <div key={i} className="text-xs text-red-800 flex items-start gap-2">
                                      <span className="font-semibold bg-red-100 px-2 py-0.5 rounded-full border border-red-200 text-[11px]">
                                        {err.rule_code}
                                      </span>
                                      <span>
                                        <strong>Field '{err.field_name}':</strong> {err.explanation}
                                      </span>
                                    </div>
                                  ))}
                                  {r.warnings.map((warn, i) => (
                                    <div key={i} className="text-xs text-amber-800 flex items-start gap-2">
                                      <span className="font-semibold bg-amber-100 px-2 py-0.5 rounded-full border border-amber-200 text-[11px]">
                                        {warn.rule_code}
                                      </span>
                                      <span>
                                        <strong>Field '{warn.field_name}':</strong> {warn.explanation}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Action Bar */}
              <div className="p-4 border-t border-[#E2E8F0] bg-slate-50 flex flex-wrap items-center justify-between gap-4">
                <div className="text-xs text-[#475569]">
                  <strong>Policy:</strong> Only valid and warning rows ({previewData.valid_rows}) will be saved to the national enrolment registry. Flagged error rows ({previewData.error_rows}) will remain uncommitted.
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => setStep(2)}
                    className="btn-rounded-secondary text-xs"
                  >
                    Upload corrected file
                  </button>
                  <button
                    onClick={() => setShowConfirmModal(true)}
                    disabled={isSubmitting || previewData.valid_rows === 0}
                    className="btn-rounded-primary text-xs disabled:opacity-50"
                  >
                    <FileCheck2 className="w-4 h-4 text-sky-300" />
                    {isSubmitting ? "Finalizing submission..." : `Finalize submission (${previewData.valid_rows} records)`}
                  </button>
                </div>
              </div>
            </div>

            {/* Finalization Confirmation Modal (No blur, clean solid overlay) */}
            {showConfirmModal && (
              <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center p-4 z-50">
                <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-lg max-w-md w-full p-6 sm:p-8 space-y-4">
                  <h3 className="text-base font-bold text-[#0F2942] flex items-center gap-2">
                    <ShieldCheck className="w-5 h-5 text-[#0F2942]" />
                    Confirm submission finalization
                  </h3>
                  <p className="text-xs text-[#475569] leading-relaxed">
                    You are committing <strong className="text-[#0F2942] tabular-nums">{previewData.valid_rows}</strong> valid enrolment records into the canonical registry. Once finalized, an official submission receipt will be issued and this batch cannot be re-uploaded.
                  </p>
                  <div className="flex justify-end gap-3 pt-3 border-t border-[#E2E8F0]">
                    <button
                      onClick={() => setShowConfirmModal(false)}
                      className="btn-rounded-secondary text-xs"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleFinalizeBatch}
                      disabled={isSubmitting}
                      className="btn-rounded-primary text-xs"
                    >
                      {isSubmitting ? "Committing records..." : "Confirm and commit"}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* STEP 4: SUBMISSION RECEIPT */}
        {step === 4 && receiptData && (
          <div className="bg-white rounded-2xl border border-[#CBD5E1] shadow-xs p-8 max-w-xl mx-auto space-y-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-emerald-100 text-[#15803D] rounded-full flex items-center justify-center mx-auto mb-3">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h2 className="text-lg font-bold text-[#0F2942]">Official submission receipt</h2>
              <p className="text-xs text-[#475569] mt-1">
                Your batch has been finalized and student enrolment records have been recorded in the registry.
              </p>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2.5 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-200">
                <span className="text-[#475569]">Receipt reference:</span>
                <span className="font-semibold text-[#0F2942] tabular-nums">{receiptData.receipt_reference}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-200">
                <span className="text-[#475569]">Processing status:</span>
                <span className="font-medium text-emerald-800">{receiptData.status}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-200">
                <span className="text-[#475569]">Enrolments recorded:</span>
                <span className="font-semibold text-emerald-700 tabular-nums">{receiptData.accepted_count}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-200">
                <span className="text-[#475569]">Flagged / uncommitted rows:</span>
                <span className="font-semibold text-red-700 tabular-nums">{receiptData.rejected_count}</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-[#475569]">Issued timestamp:</span>
                <span className="tabular-nums text-slate-700">{new Date(receiptData.issued_at).toLocaleString()}</span>
              </div>
            </div>

            <div className="flex justify-center gap-3 pt-2">
              <Link
                href="/enrolments"
                className="btn-rounded-primary text-xs"
              >
                Inspect enrolment registry
              </Link>
              <button
                onClick={() => {
                  setStep(1);
                  setCurrentBatch(null);
                  setPreviewData(null);
                  setReceiptData(null);
                }}
                className="btn-rounded-secondary text-xs"
              >
                Start new batch
              </button>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
