from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, date
import re

VALID_ENROLMENT_STATUSES = {"ACTIVE", "TRANSFERRED", "WITHDRAWN", "COMPLETED", "SUSPENDED"}
VALID_ADMISSION_CATEGORIES = {"OPEN", "OBC", "SC", "ST", "EWS", "NRI", "MANAGEMENT"}
REQUIRED_FIELDS = ["institution_student_id", "student_full_name", "admission_date", "enrolment_status"]

class ValidationFindingItem:
    def __init__(self, rule_code: str, severity: str, explanation: str, field_name: Optional[str] = None, raw_value: Optional[str] = None):
        self.rule_code = rule_code
        self.severity = severity  # "ERROR", "WARNING", "INFO"
        self.explanation = explanation
        self.field_name = field_name
        self.raw_value = str(raw_value) if raw_value is not None else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_code": self.rule_code,
            "field_name": self.field_name,
            "severity": self.severity,
            "explanation": self.explanation,
            "raw_value": self.raw_value
        }

class ValidationResult:
    def __init__(self, row_number: int, raw_data: Dict[str, Any]):
        self.row_number = row_number
        self.raw_data = raw_data
        self.normalized_data: Dict[str, Any] = {}
        self.errors: List[ValidationFindingItem] = []
        self.warnings: List[ValidationFindingItem] = []
        self.is_valid: bool = True

    def add_error(self, rule_code: str, explanation: str, field_name: Optional[str] = None, raw_value: Optional[str] = None):
        self.errors.append(ValidationFindingItem(rule_code, "ERROR", explanation, field_name, raw_value))
        self.is_valid = False

    def add_warning(self, rule_code: str, explanation: str, field_name: Optional[str] = None, raw_value: Optional[str] = None):
        self.warnings.append(ValidationFindingItem(rule_code, "WARNING", explanation, field_name, raw_value))

class DeterministicValidationEngine:
    RULESET_VERSION = "1.0.0"

    @classmethod
    def validate_row(
        cls,
        row_number: int,
        raw_row: Dict[str, Any],
        seen_student_ids: Set[str],
        valid_programme_codes: Set[str],
        selected_programme_code: Optional[str] = None
    ) -> ValidationResult:
        """
        Deterministically evaluates a single roster row against Phase 1 validation rules.
        """
        result = ValidationResult(row_number, raw_row)
        normalized: Dict[str, Any] = {}

        # 1. SCH-001: Required field check
        for field in REQUIRED_FIELDS:
            val = raw_row.get(field)
            if val is None or str(val).strip() == "":
                result.add_error(
                    "SCH-001",
                    f"Required field '{field}' is missing or empty in row {row_number}.",
                    field_name=field,
                    raw_value=val
                )
            else:
                normalized[field] = str(val).strip()

        # Extract normalized values
        student_id = normalized.get("institution_student_id")
        student_name = normalized.get("student_full_name")
        adm_date_str = normalized.get("admission_date")
        status_val = normalized.get("enrolment_status")

        # 2. SCH-006: Intra-batch duplicate detection
        if student_id:
            if student_id.upper() in seen_student_ids:
                result.add_error(
                    "SCH-006",
                    f"Duplicate student identifier '{student_id}' detected within this batch at row {row_number}.",
                    field_name="institution_student_id",
                    raw_value=student_id
                )
            else:
                seen_student_ids.add(student_id.upper())

        # 3. SCH-002: Date parsing
        if adm_date_str:
            parsed_date = None
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    parsed_date = datetime.strptime(adm_date_str, fmt).date()
                    break
                except ValueError:
                    continue
            if parsed_date:
                normalized["admission_date"] = parsed_date.isoformat()
            else:
                result.add_error(
                    "SCH-002",
                    f"Invalid date format for 'admission_date': '{adm_date_str}'. Expected YYYY-MM-DD.",
                    field_name="admission_date",
                    raw_value=adm_date_str
                )

        # 4. SCH-003 & ENR-001: Enrolment status enumeration check
        if status_val:
            normalized_status = status_val.upper()
            if normalized_status not in VALID_ENROLMENT_STATUSES:
                result.add_error(
                    "ENR-001",
                    f"Unsupported enrolment status '{status_val}'. Permitted values: {', '.join(sorted(VALID_ENROLMENT_STATUSES))}.",
                    field_name="enrolment_status",
                    raw_value=status_val
                )
            else:
                normalized["enrolment_status"] = normalized_status

        # 5. Admission category enumeration check
        adm_cat = raw_row.get("admission_category", "OPEN")
        if adm_cat:
            normalized_cat = str(adm_cat).strip().upper()
            if normalized_cat not in VALID_ADMISSION_CATEGORIES:
                result.add_warning(
                    "SCH-003",
                    f"Non-standard admission category '{adm_cat}'. Defaulting to 'OPEN'.",
                    field_name="admission_category",
                    raw_value=adm_cat
                )
                normalized["admission_category"] = "OPEN"
            else:
                normalized["admission_category"] = normalized_cat
        else:
            normalized["admission_category"] = "OPEN"

        # 6. SCH-004: Programme reference validation
        prog_code = raw_row.get("programme_code") or selected_programme_code
        if prog_code:
            norm_prog = str(prog_code).strip()
            if norm_prog not in valid_programme_codes:
                result.add_error(
                    "SCH-004",
                    f"Invalid programme reference '{norm_prog}'. Programme is not approved for this institution.",
                    field_name="programme_code",
                    raw_value=norm_prog
                )
            else:
                normalized["programme_code"] = norm_prog
        elif not selected_programme_code:
            result.add_error(
                "SCH-004",
                "Programme reference missing from row and no batch-level programme specified.",
                field_name="programme_code",
                raw_value=None
            )

        # 7. APAAR identifier checks (APA-001, APA-002, APA-003)
        apaar_raw = raw_row.get("apaar_id")
        if apaar_raw is None or str(apaar_raw).strip() == "":
            result.add_warning(
                "APA-001",
                f"Missing APAAR identifier for student '{student_name or student_id or row_number}'. Record marked as unlinked.",
                field_name="apaar_id",
                raw_value=None
            )
            normalized["apaar_id"] = None
            normalized["apaar_validation_status"] = "UNAVAILABLE"
        else:
            cleaned_apaar = str(apaar_raw).strip().replace("-", "").replace(" ", "")
            # APA-002: Format validation - standard APAAR is a 12-digit numeric identifier
            if re.fullmatch(r"\d{12}", cleaned_apaar):
                normalized["apaar_id"] = cleaned_apaar
                # APA-003: Format is valid but no live government integration authorized in Phase 1
                normalized["apaar_validation_status"] = "SIMULATED"
                result.add_warning(
                    "APA-003",
                    f"APAAR format valid (12-digit numeric), but live external verification source is currently SIMULATED/UNAVAILABLE.",
                    field_name="apaar_id",
                    raw_value=str(apaar_raw)
                )
            else:
                result.add_error(
                    "APA-002",
                    f"Malformed APAAR identifier '{apaar_raw}'. APAAR must be a 12-digit numeric identifier.",
                    field_name="apaar_id",
                    raw_value=str(apaar_raw)
                )
                normalized["apaar_id"] = None
                normalized["apaar_validation_status"] = "MALFORMED"

        # Supernumerary category optional
        super_cat = raw_row.get("supernumerary_category")
        if super_cat and str(super_cat).strip():
            normalized["supernumerary_category"] = str(super_cat).strip().upper()
        else:
            normalized["supernumerary_category"] = None

        result.normalized_data = normalized
        return result
