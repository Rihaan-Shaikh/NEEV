import pytest
from app.rules.validation_engine import DeterministicValidationEngine

def test_sch_001_required_field_missing():
    # Missing admission_date and enrolment_status
    row = {
        "institution_student_id": "TEST-001",
        "student_full_name": "Test Student",
        "admission_date": "",
        "enrolment_status": None,
        "programme_code": "BTECH-CSE"
    }
    seen = set()
    res = DeterministicValidationEngine.validate_row(1, row, seen, {"BTECH-CSE"})
    assert not res.is_valid
    error_codes = [e.rule_code for e in res.errors]
    assert "SCH-001" in error_codes
    fields = [e.field_name for e in res.errors if e.rule_code == "SCH-001"]
    assert "admission_date" in fields
    assert "enrolment_status" in fields

def test_sch_002_invalid_date():
    row = {
        "institution_student_id": "TEST-002",
        "student_full_name": "Test Student",
        "admission_date": "INVALID_DATE_FORMAT",
        "enrolment_status": "ACTIVE",
        "programme_code": "BTECH-CSE"
    }
    seen = set()
    res = DeterministicValidationEngine.validate_row(1, row, seen, {"BTECH-CSE"})
    assert not res.is_valid
    assert any(e.rule_code == "SCH-002" for e in res.errors)

def test_sch_004_invalid_programme_reference():
    row = {
        "institution_student_id": "TEST-003",
        "student_full_name": "Test Student",
        "admission_date": "2024-07-15",
        "enrolment_status": "ACTIVE",
        "programme_code": "UNAPPROVED_PROG_CODE"
    }
    seen = set()
    res = DeterministicValidationEngine.validate_row(1, row, seen, {"BTECH-CSE", "BTECH-ECE"})
    assert not res.is_valid
    assert any(e.rule_code == "SCH-004" for e in res.errors)

def test_sch_006_duplicate_row_within_batch():
    row1 = {
        "institution_student_id": "TEST-DUP",
        "student_full_name": "Student One",
        "admission_date": "2024-07-15",
        "enrolment_status": "ACTIVE",
        "programme_code": "BTECH-CSE"
    }
    row2 = {
        "institution_student_id": "TEST-DUP",
        "student_full_name": "Student Two",
        "admission_date": "2024-07-16",
        "enrolment_status": "ACTIVE",
        "programme_code": "BTECH-CSE"
    }
    seen = set()
    res1 = DeterministicValidationEngine.validate_row(1, row1, seen, {"BTECH-CSE"})
    assert res1.is_valid
    res2 = DeterministicValidationEngine.validate_row(2, row2, seen, {"BTECH-CSE"})
    assert not res2.is_valid
    assert any(e.rule_code == "SCH-006" for e in res2.errors)

def test_apa_001_missing_apaar():
    row = {
        "institution_student_id": "TEST-004",
        "student_full_name": "Test Student",
        "admission_date": "2024-07-15",
        "enrolment_status": "ACTIVE",
        "programme_code": "BTECH-CSE",
        "apaar_id": ""
    }
    seen = set()
    res = DeterministicValidationEngine.validate_row(1, row, seen, {"BTECH-CSE"})
    # Missing APAAR is a warning, not a fatal rejection of student
    assert res.is_valid
    assert any(w.rule_code == "APA-001" for w in res.warnings)

def test_apa_002_malformed_apaar():
    row = {
        "institution_student_id": "TEST-005",
        "student_full_name": "Test Student",
        "admission_date": "2024-07-15",
        "enrolment_status": "ACTIVE",
        "programme_code": "BTECH-CSE",
        "apaar_id": "12345ABC"  # Malformed: not 12 digits
    }
    seen = set()
    res = DeterministicValidationEngine.validate_row(1, row, seen, {"BTECH-CSE"})
    assert not res.is_valid
    assert any(e.rule_code == "APA-002" for e in res.errors)

def test_apa_003_valid_format_unverified_source():
    row = {
        "institution_student_id": "TEST-006",
        "student_full_name": "Test Student",
        "admission_date": "2024-07-15",
        "enrolment_status": "ACTIVE",
        "programme_code": "BTECH-CSE",
        "apaar_id": "123456789012"  # 12-digit numeric
    }
    seen = set()
    res = DeterministicValidationEngine.validate_row(1, row, seen, {"BTECH-CSE"})
    assert res.is_valid
    # APA-003 warning: format valid but government source simulated
    assert any(w.rule_code == "APA-003" for w in res.warnings)

def test_enr_001_unsupported_enrolment_status():
    row = {
        "institution_student_id": "TEST-007",
        "student_full_name": "Test Student",
        "admission_date": "2024-07-15",
        "enrolment_status": "RANDOM_CUSTOM_STATUS",
        "programme_code": "BTECH-CSE"
    }
    seen = set()
    res = DeterministicValidationEngine.validate_row(1, row, seen, {"BTECH-CSE"})
    assert not res.is_valid
    assert any(e.rule_code == "ENR-001" for e in res.errors)
