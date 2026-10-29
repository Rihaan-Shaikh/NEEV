import asyncio
import uuid
from datetime import datetime, date, timezone
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User, Role, Permission, UserScope, role_permissions, user_roles
from app.models.institution import Institution
from app.models.programme import AcademicYear, Programme, ProgrammeApproval, ApprovedIntakeVersion, SeatCategoryRule
from app.models.student import StudentIdentity, EnrolmentRecord, EnrolmentRecordVersion
from app.models.validation import ValidationRule
from app.core.security import hash_password, generate_apaar_fingerprint, mask_apaar_id

def utc_now():
    return datetime.now(timezone.utc)

async def seed_all_data(session_factory=None):
    factory = session_factory or AsyncSessionLocal
    async with factory() as session:
        print("Starting NEEV Phase 1 seed data insertion...")

        # 1. Validation Rules Catalog
        rules_data = [
            ("SCH-001", "Required Field Missing", "Detect missing required field values in submitted roster row", "SCHEMA", "ERROR"),
            ("SCH-002", "Invalid Date", "Date parsing failed. Expected YYYY-MM-DD format", "SCHEMA", "ERROR"),
            ("SCH-003", "Invalid Enumeration", "Field value not in supported set of values", "SCHEMA", "WARNING"),
            ("SCH-004", "Invalid Programme Reference", "Programme code does not exist or is unauthorized for institution", "SCHEMA", "ERROR"),
            ("SCH-005", "Invalid Academic Year", "Academic year is not recognized or active", "SCHEMA", "ERROR"),
            ("SCH-006", "Duplicate Row within Batch", "Multiple rows share identical student identifier within batch", "SCHEMA", "ERROR"),
            ("APA-001", "Missing APAAR ID", "Student identifier is missing. Recorded as distinct unlinked quality state", "IDENTIFIER", "WARNING"),
            ("APA-002", "Malformed APAAR ID", "Identifier format invalid. Expected 12-digit numeric APAAR", "IDENTIFIER", "ERROR"),
            ("APA-003", "Format Valid - Unverified Source", "Format valid but live external government verification unavailable/simulated", "IDENTIFIER", "WARNING"),
            ("ENR-001", "Unsupported Enrolment Status", "Status is not in ACTIVE, TRANSFERRED, WITHDRAWN, COMPLETED, SUSPENDED", "ENROLMENT", "ERROR"),
            ("INT-001", "Approved Intake Missing", "No approved intake capacity reference configured for programme", "INTAKE", "WARNING"),
            ("INT-002", "Capacity Exceeded", "Active enrolment count exceeds approved intake capacity", "INTAKE", "ERROR"),
            ("INT-003", "Reported Count Discrepancy", "Reported student total differs from calculated active count", "INTAKE", "INFO"),
        ]

        for code, name, desc, cat, sev in rules_data:
            existing = await session.execute(select(ValidationRule).where(ValidationRule.rule_code == code))
            if not existing.scalars().first():
                session.add(ValidationRule(
                    rule_code=code,
                    name=name,
                    description=desc,
                    category=cat,
                    severity=sev,
                    version="1.0.0",
                    status="ACTIVE"
                ))

        # 2. Permissions
        permissions_data = [
            ("institution.read", "Read institution records"),
            ("institution.manage", "Create and update institutions"),
            ("enrolment.read", "Read enrolment records"),
            ("enrolment.write", "Create and edit enrolments"),
            ("batch.submit", "Upload and submit roster batches"),
            ("rules.configure", "Configure validation rules"),
            ("dashboard.view", "View national or institutional dashboard"),
        ]
        perm_map = {}
        for code, desc in permissions_data:
            res = await session.execute(select(Permission).where(Permission.code == code))
            perm = res.scalars().first()
            if not perm:
                perm = Permission(code=code, description=desc)
                session.add(perm)
                await session.flush()
            perm_map[code] = perm

        # 3. Roles
        roles_data = [
            ("PLATFORM_ADMIN", "Platform Administrator", list(perm_map.values())),
            ("AICTE_ADMIN", "AICTE National Administrator", list(perm_map.values())),
            ("AICTE_OFFICER", "AICTE Regulatory Officer", [perm_map["institution.read"], perm_map["enrolment.read"], perm_map["dashboard.view"]]),
            ("INSTITUTION_ADMIN", "Institution Administrator", [perm_map["institution.read"], perm_map["enrolment.read"], perm_map["enrolment.write"], perm_map["batch.submit"], perm_map["dashboard.view"]]),
            ("INSTITUTION_OPERATOR", "Institution Data Operator", [perm_map["enrolment.read"], perm_map["batch.submit"]]),
            ("AUDITOR", "External Regulatory Auditor", [perm_map["institution.read"], perm_map["enrolment.read"], perm_map["dashboard.view"]]),
            ("VERIFIER", "Restricted Student Record Verifier", [perm_map["enrolment.read"]]),
            ("STUDENT", "Student Self-Access", []),
        ]
        role_map = {}
        for r_code, r_name, r_perms in roles_data:
            res = await session.execute(select(Role).where(Role.code == r_code))
            role = res.scalars().first()
            if not role:
                role = Role(code=r_code, name=r_name, description=f"Role for {r_name}")
                role.permissions = r_perms
                session.add(role)
                await session.flush()
            role_map[r_code] = role

        # 4. Academic Years
        ay_data = [
            ("2024-2025", date(2024, 7, 1), date(2025, 6, 30), "ACTIVE"),
            ("2023-2024", date(2023, 7, 1), date(2024, 6, 30), "HISTORICAL"),
            ("2025-2026", date(2025, 7, 1), date(2026, 6, 30), "UPCOMING"),
        ]
        ay_map = {}
        for label, s_date, e_date, ay_status in ay_data:
            res = await session.execute(select(AcademicYear).where(AcademicYear.label == label))
            ay = res.scalars().first()
            if not ay:
                ay = AcademicYear(label=label, start_date=s_date, end_date=e_date, status=ay_status)
                session.add(ay)
                await session.flush()
            ay_map[label] = ay

        active_ay = ay_map["2024-2025"]

        # 5. Synthetic Institutions
        inst_1_code = "AICTE-SYNTH-1001"
        inst_1_res = await session.execute(select(Institution).where(Institution.official_institution_code == inst_1_code))
        inst_1 = inst_1_res.scalars().first()
        if not inst_1:
            inst_1 = Institution(
                official_institution_code=inst_1_code,
                name="Delhi Institute of Technology",
                institution_type="CENTRAL_UNIVERSITY",
                state_code="DL",
                district_code="NEW_DELHI",
                address="Sector 14, Dwarka, New Delhi 110078",
                status="ACTIVE",
                source_reference="AICTE_PORTAL_SEED_2024",
                is_synthetic=True
            )
            session.add(inst_1)
            await session.flush()

        inst_2_code = "AICTE-SYNTH-2002"
        inst_2_res = await session.execute(select(Institution).where(Institution.official_institution_code == inst_2_code))
        inst_2 = inst_2_res.scalars().first()
        if not inst_2:
            inst_2 = Institution(
                official_institution_code=inst_2_code,
                name="Mumbai Technical University",
                institution_type="STATE_UNIVERSITY",
                state_code="MH",
                district_code="MUMBAI_CITY",
                address="Vidyanagari, Kalina, Santacruz East, Mumbai 400098",
                status="ACTIVE",
                source_reference="AICTE_PORTAL_SEED_2024",
                is_synthetic=True
            )
            session.add(inst_2)
            await session.flush()

        # 6. Demo Users
        users_seed = [
            # National Admin
            ("aicte.admin@neev.aicte.gov.in", "NeevAdmin@2026", "AICTE National Administrator", "active", "AICTE_ADMIN", "NATIONAL", None),
            # DIT Administrator (Scoped to Institution 1)
            ("admin@dit.synthetic.edu.in", "DitAdmin@2026", "DIT Institutional Admin", "active", "INSTITUTION_ADMIN", "INSTITUTION", inst_1.id),
            # MTU Administrator (Scoped to Institution 2)
            ("admin@mtu.synthetic.edu.in", "MtuAdmin@2026", "MTU Institutional Admin", "active", "INSTITUTION_ADMIN", "INSTITUTION", inst_2.id),
            # Suspended / Disabled User for Security testing
            ("disabled.user@neev.aicte.gov.in", "DisabledUser@2026", "Suspended User Account", "suspended", "INSTITUTION_OPERATOR", "INSTITUTION", inst_1.id),
        ]

        for email, pwd, name, status, role_code, scope_type, scoped_inst_id in users_seed:
            u_res = await session.execute(select(User).where(User.email_normalized == email))
            u = u_res.scalars().first()
            if not u:
                u = User(
                    email_normalized=email,
                    password_hash=hash_password(pwd),
                    display_name=name,
                    account_status=status
                )
                u.roles = [role_map[role_code]]
                session.add(u)
                await session.flush()

                # Add scope
                u_scope = UserScope(
                    user_id=u.id,
                    scope_type=scope_type,
                    institution_id=scoped_inst_id
                )
                session.add(u_scope)
                await session.flush()

        # 7. Programmes & Approvals & Intake
        programmes_to_seed = [
            # Inst 1 (DIT):
            (inst_1.id, "BTECH-CSE", "B.Tech Computer Science & Engineering", "UNDERGRADUATE", 120, "AICTE/EOA/2024-25/1-1001-CSE"),
            (inst_1.id, "BTECH-ECE", "B.Tech Electronics & Communication Engineering", "UNDERGRADUATE", 60, "AICTE/EOA/2024-25/1-1001-ECE"),
            (inst_1.id, "MTECH-AI", "M.Tech Artificial Intelligence", "POSTGRADUATE", None, "AICTE/EOA/2024-25/1-1001-AI"),  # Missing intake for INT-001 test
            # Inst 2 (MTU):
            (inst_2.id, "BTECH-IT", "B.Tech Information Technology", "UNDERGRADUATE", 180, "AICTE/EOA/2024-25/1-2002-IT"),
            (inst_2.id, "BTECH-MECH", "B.Tech Mechanical Engineering", "UNDERGRADUATE", 120, "AICTE/EOA/2024-25/1-2002-MECH"),
        ]

        prog_created_map = {}
        for inst_id, p_code, p_name, q_level, intake_seats, app_ref in programmes_to_seed:
            p_res = await session.execute(
                select(Programme).where(Programme.institution_id == inst_id, Programme.official_programme_code == p_code)
            )
            prog = p_res.scalars().first()
            if not prog:
                prog = Programme(
                    institution_id=inst_id,
                    official_programme_code=p_code,
                    programme_name=p_name,
                    qualification_level=q_level,
                    academic_discipline="Engineering & Technology",
                    status="APPROVED"
                )
                session.add(prog)
                await session.flush()

                # Programme approval
                app = ProgrammeApproval(
                    programme_id=prog.id,
                    academic_year_id=active_ay.id,
                    approval_reference=app_ref,
                    approval_status="APPROVED",
                    source_reference="AICTE_EOA_LETTER_2024",
                    is_synthetic=True,
                    effective_from=active_ay.start_date,
                    effective_until=active_ay.end_date,
                    version=1
                )
                session.add(app)
                await session.flush()

                # Approved intake version if configured
                if intake_seats is not None:
                    intake_v = ApprovedIntakeVersion(
                        programme_approval_id=app.id,
                        approved_intake=intake_seats,
                        source_type="AICTE_APPROVAL_LETTER",
                        source_reference=app_ref,
                        version=1,
                        effective_from=active_ay.start_date,
                        effective_until=active_ay.end_date,
                        recorded_by="AICTE_ADMIN_SYSTEM"
                    )
                    session.add(intake_v)
                    await session.flush()

            prog_created_map[(inst_id, p_code)] = prog

        # 8. Seed Enrolment Records for Reconciliation Testing
        # DIT BTECH-CSE: approved 120, active 5 synthetic sample records (within capacity)
        # DIT BTECH-ECE: approved 60, seed 62 synthetic active records to test INT-002 CAPACITY_EXCEEDED!
        dit_cse = prog_created_map[(inst_1.id, "BTECH-CSE")]
        dit_ece = prog_created_map[(inst_1.id, "BTECH-ECE")]

        # Check existing records
        existing_enr = await session.execute(
            select(EnrolmentRecord).where(EnrolmentRecord.institution_id == inst_1.id)
        )
        if not existing_enr.scalars().first():
            # Seed 5 valid records for BTECH-CSE
            sample_students_cse = [
                ("DIT-2024-CSE-001", "Aarav Sharma", "2024-07-15", "100120045001", "OPEN"),
                ("DIT-2024-CSE-002", "Diya Patel", "2024-07-16", "100120045002", "OBC"),
                ("DIT-2024-CSE-003", "Rohan Verma", "2024-07-16", "100120045003", "SC"),
                ("DIT-2024-CSE-004", "Ananya Iyer", "2024-07-18", None, "OPEN"),  # Missing APAAR (APA-001)
                ("DIT-2024-CSE-005", "Ishaan Nair", "2024-07-20", "100120045005", "EWS"),
            ]
            for s_id, s_name, s_date, apaar, cat in sample_students_cse:
                apaar_fp = generate_apaar_fingerprint(apaar) if apaar else None
                identity = StudentIdentity(
                    apaar_id_ciphertext=apaar,
                    apaar_id_fingerprint=apaar_fp,
                    apaar_validation_status="SIMULATED" if apaar else "UNAVAILABLE",
                    apaar_validation_source="SIMULATED_ADAPTER" if apaar else "NONE",
                    masked_apaar_id=mask_apaar_id(apaar)
                )
                session.add(identity)
                await session.flush()

                enr = EnrolmentRecord(
                    student_identity_id=identity.id,
                    institution_id=inst_1.id,
                    programme_id=dit_cse.id,
                    academic_year_id=active_ay.id,
                    institution_student_id=s_id,
                    student_full_name=s_name,
                    admission_date=datetime.strptime(s_date, "%Y-%m-%d").date(),
                    enrolment_status="ACTIVE",
                    admission_category=cat,
                    current_record_version=1
                )
                session.add(enr)
                await session.flush()

                session.add(EnrolmentRecordVersion(
                    enrolment_record_id=enr.id,
                    version_number=1,
                    snapshot_json='{"status": "INITIAL_SEED"}',
                    change_reason="DEMO_SEED_DATA",
                    changed_by="SYSTEM"
                ))

            # Also seed 1 historical completed student to test historical preservation
            hist_identity = StudentIdentity(
                apaar_id_ciphertext="100120045099",
                apaar_id_fingerprint=generate_apaar_fingerprint("100120045099"),
                apaar_validation_status="SIMULATED",
                apaar_validation_source="SIMULATED_ADAPTER",
                masked_apaar_id=mask_apaar_id("100120045099")
            )
            session.add(hist_identity)
            await session.flush()

            session.add(EnrolmentRecord(
                student_identity_id=hist_identity.id,
                institution_id=inst_1.id,
                programme_id=dit_cse.id,
                academic_year_id=ay_map["2023-2024"].id,
                institution_student_id="DIT-2023-CSE-999",
                student_full_name="Kavita Reddy (Alumni)",
                admission_date=date(2023, 7, 10),
                enrolment_status="COMPLETED",
                admission_category="OPEN",
                current_record_version=1
            ))

            # For BTECH-ECE: approved intake is 60. Let's seed 63 active students to exercise INT-002 capacity exceeded finding!
            for i in range(1, 64):
                num_str = f"{i:03d}"
                ece_apaar = f"90001000{num_str}1"
                ece_ident = StudentIdentity(
                    apaar_id_ciphertext=ece_apaar,
                    apaar_id_fingerprint=generate_apaar_fingerprint(ece_apaar),
                    apaar_validation_status="SIMULATED",
                    apaar_validation_source="SIMULATED_ADAPTER",
                    masked_apaar_id=mask_apaar_id(ece_apaar)
                )
                session.add(ece_ident)
                await session.flush()

                session.add(EnrolmentRecord(
                    student_identity_id=ece_ident.id,
                    institution_id=inst_1.id,
                    programme_id=dit_ece.id,
                    academic_year_id=active_ay.id,
                    institution_student_id=f"DIT-2024-ECE-{num_str}",
                    student_full_name=f"ECE Synthetic Student {i}",
                    admission_date=date(2024, 7, 20),
                    enrolment_status="ACTIVE",
                    admission_category="OPEN",
                    current_record_version=1
                ))

        # --- Phase 2: Seed Inst 2 (MTU) Enrolments for Cross-Institution Conflict Detection ---
        existing_mtu = await session.execute(
            select(EnrolmentRecord).where(EnrolmentRecord.institution_id == inst_2.id)
        )
        if not existing_mtu.scalars().first():
            mtu_it = prog_created_map.get((inst_2.id, "BTECH-IT"))
            if not mtu_it:
                p_res = await session.execute(select(Programme).where(Programme.institution_id == inst_2.id, Programme.official_programme_code == "BTECH-IT"))
                mtu_it = p_res.scalars().first()

            # Case B: DUP-002 Cross-institution active conflict
            # Aarav Sharma (APAAR 100120045001) is ACTIVE at DIT and ALSO active at MTU in the same academic year!
            mtu_conflict_ident = StudentIdentity(
                apaar_id_ciphertext="100120045001",
                apaar_id_fingerprint=generate_apaar_fingerprint("100120045001"),
                apaar_validation_status="SIMULATED",
                apaar_validation_source="SIMULATED_ADAPTER",
                masked_apaar_id=mask_apaar_id("100120045001")
            )
            session.add(mtu_conflict_ident)
            await session.flush()

            session.add(EnrolmentRecord(
                student_identity_id=mtu_conflict_ident.id,
                institution_id=inst_2.id,
                programme_id=mtu_it.id,
                academic_year_id=active_ay.id,
                institution_student_id="MTU-2024-IT-001",
                student_full_name="Aarav Sharma",
                admission_date=date(2024, 8, 1),
                enrolment_status="ACTIVE",
                admission_category="OPEN",
                current_record_version=1
            ))

            # Case A: DUP-004 Legitimate Transfer
            # Diya Patel (APAAR 100120045002) transferred from DIT to MTU
            mtu_transfer_ident = StudentIdentity(
                apaar_id_ciphertext="100120045002",
                apaar_id_fingerprint=generate_apaar_fingerprint("100120045002"),
                apaar_validation_status="SIMULATED",
                apaar_validation_source="SIMULATED_ADAPTER",
                masked_apaar_id=mask_apaar_id("100120045002")
            )
            session.add(mtu_transfer_ident)
            await session.flush()

            session.add(EnrolmentRecord(
                student_identity_id=mtu_transfer_ident.id,
                institution_id=inst_2.id,
                programme_id=mtu_it.id,
                academic_year_id=active_ay.id,
                institution_student_id="MTU-2024-IT-002",
                student_full_name="Diya Patel",
                admission_date=date(2024, 8, 5),
                enrolment_status="ACTIVE",
                admission_category="OBC",
                current_record_version=1
            ))

            await session.flush()

        # Execute Phase 2 reconciliation engine to generate findings
        from app.services.conflict_service import ConflictDetectionService
        await ConflictDetectionService.run_integrity_reconciliation(session, "SYSTEM")

        # ================= Phase 3 Oversight Seed Data =================
        print("Seeding NEEV Phase 3 oversight & regulatory case management data...")
        from app.services.risk_engine_service import RiskEngineService
        from app.models.oversight import (
            AuditCase,
            AuditCaseFinding,
            AuditCaseEvent,
            ClarificationRequest,
            AuditCaseDecision,
            ReportJob
        )
        from app.models.integrity import Finding

        # 1. Run deterministic risk calculations for DIT and MTU
        dit_risk = await RiskEngineService.calculate_institution_risk(session, inst_1.id, active_ay.id)
        mtu_risk = await RiskEngineService.calculate_institution_risk(session, inst_2.id, active_ay.id)

        # 2. Find seeded DUP-002 finding
        dup_finding = (await session.execute(
            select(Finding).where(Finding.rule_code == "DUP-002").limit(1)
        )).scalar_one_or_none()

        aicte_admin = (await session.execute(
            select(User).where(User.email_normalized == "aicte.admin@neev.aicte.gov.in")
        )).unique().scalar_one_or_none()

        dit_cse = prog_created_map.get((inst_1.id, "BTECH-CSE"))
        mtu_it = prog_created_map.get((inst_2.id, "BTECH-IT"))

        now = utc_now()
        existing_case = (await session.execute(
            select(AuditCase).where(AuditCase.case_reference == "CASE-2026-0001")
        )).scalar_one_or_none()

        if not existing_case:
            case_1 = AuditCase(
                case_reference="CASE-2026-0001",
                institution_id=inst_1.id,
                programme_id=dit_cse.id,
                academic_year_id=active_ay.id,
                case_category="CROSS_INSTITUTION_DUPLICATE",
                priority="HIGH",
                status="CLARIFICATION_REQUESTED",
                creation_rationale="Simultaneous active enrolment detected across DIT and MTU for student Aarav Sharma under rule DUP-002.",
                assigned_reviewer_id=aicte_admin.id,
                created_by_user_id=aicte_admin.id,
                created_at=now,
                updated_at=now
            )
            session.add(case_1)
            await session.flush()

            if dup_finding:
                session.add(AuditCaseFinding(
                    audit_case_id=case_1.id,
                    finding_id=dup_finding.id,
                    linked_at=now
                ))

            # Case events
            session.add(AuditCaseEvent(
                audit_case_id=case_1.id,
                event_type="CASE_CREATED",
                actor_user_id=aicte_admin.id,
                actor_name=aicte_admin.display_name,
                to_status="ASSIGNED",
                description=f"Case created and assigned to {aicte_admin.display_name} based on finding DUP-002.",
                is_internal=False,
                created_at=now
            ))
            session.add(AuditCaseEvent(
                audit_case_id=case_1.id,
                event_type="CLARIFICATION_ISSUED",
                actor_user_id=aicte_admin.id,
                actor_name=aicte_admin.display_name,
                from_status="ASSIGNED",
                to_status="CLARIFICATION_REQUESTED",
                description="Clarification request CLR-2026-0001 issued to Delhi Institute of Technology.",
                is_internal=False,
                created_at=now
            ))

            # Clarification request
            session.add(ClarificationRequest(
                audit_case_id=case_1.id,
                institution_id=inst_1.id,
                request_reference="CLR-2026-0001",
                subject="Clarification of concurrent active enrolment for Aarav Sharma",
                information_requested="Please provide certified copy of admission verification or transfer/migration documents for student Aarav Sharma (DIT-2024-CS-001).",
                status="PENDING_RESPONSE",
                issuing_officer_id=aicte_admin.id,
                created_at=now
            ))

            # Case 2: Resolved case
            case_2 = AuditCase(
                case_reference="CASE-2026-0002",
                institution_id=inst_2.id,
                programme_id=mtu_it.id,
                academic_year_id=active_ay.id,
                case_category="REGULATORY_REVIEW",
                priority="MEDIUM",
                status="RESOLVED",
                creation_rationale="Routine verification of IT programme intake configuration and admission roster.",
                assigned_reviewer_id=aicte_admin.id,
                created_by_user_id=aicte_admin.id,
                closed_at=now,
                closure_reason="Approved intake configuration verified against AICTE sanction letters.",
                created_at=now,
                updated_at=now
            )
            session.add(case_2)
            await session.flush()

            session.add(AuditCaseDecision(
                audit_case_id=case_2.id,
                decision_type="RESOLVED",
                decision_rationale="Approved intake configuration verified against AICTE sanction letters. Zero capacity discrepancy.",
                follow_up_action="Continue standard monitoring in next cycle.",
                reviewer_id=aicte_admin.id,
                decided_at=now
            ))

        # 3. Sample completed report job
        existing_report = (await session.execute(
            select(ReportJob).where(ReportJob.report_type == "ENROLMENT_RECONCILIATION")
        )).scalars().first()
        if not existing_report:
            session.add(ReportJob(
                report_type="ENROLMENT_RECONCILIATION",
                report_title="Institution-level enrolment reconciliation",
                status="COMPLETED",
                requester_user_id=aicte_admin.id,
                institution_id=inst_1.id,
                row_count=2,
                file_size_bytes=420,
                created_at=now,
                completed_at=now
            ))

        # 4. Phase 4: Integration Status Adapter Logs
        from app.models.verification import VerificationReference, VerificationAccessLog, IntegrationStatusLog
        import hashlib, json
        from datetime import timedelta

        adapters_data = [
            (
                "APAAR_DIGILOCKER",
                "APAAR / DigiLocker Verification Gateway",
                "SIMULATED",
                True,
                115.5,
                ["apaar_id", "student_name", "dob", "gender"],
                "Simulated sandbox adapter. Official production APIs require signed MeitY/MoE data-sharing agreements.",
                "PASSED"
            ),
            (
                "AISHE_PORTAL",
                "AISHE Higher Education Portal",
                "SIMULATED",
                True,
                175.0,
                ["institution_code", "survey_year", "accreditation_grade"],
                "AISHE annual census integration simulated. Real-time REST API unavailable from ministry.",
                "PASSED"
            ),
            (
                "NAD_PORTAL",
                "National Academic Depository (NAD)",
                "NOT_CONFIGURED",
                True,
                None,
                ["degree_award", "convocation_year", "transcript_hash"],
                "Requires institutional Digilocker NAD tenant onboarding and certificate credentials.",
                "SKIPPED"
            ),
            (
                "STATE_TECH_BOARD",
                "State Technical Education Examination Board",
                "SIMULATED",
                True,
                92.4,
                ["diploma_registration", "lateral_entry_sanction"],
                "Simulated interface for Delhi (BTE), Maharashtra (MSBTE), and Karnataka (DTE).",
                "PASSED"
            ),
            (
                "AICTE_APPROVAL_PORTAL",
                "AICTE Central Approval Bureau (EDB)",
                "CONFIGURED",
                True,
                108.2,
                ["intake_sanction", "approval_letter_no", "nri_supernumerary_quota"],
                "Simulated mirror of central AICTE approval portal and intake capacity versions.",
                "PASSED"
            )
        ]

        for code, name, status, is_sim, lat, claims, limits, ct_stat in adapters_data:
            existing_adapter = (await session.execute(
                select(IntegrationStatusLog).where(IntegrationStatusLog.adapter_code == code)
            )).scalars().first()
            if not existing_adapter:
                session.add(IntegrationStatusLog(
                    adapter_code=code,
                    adapter_name=name,
                    status=status,
                    is_simulated=is_sim,
                    last_checked_at=now,
                    latency_ms=lat,
                    supported_claims=json.dumps(claims),
                    known_limitations=limits,
                    contract_test_status=ct_stat,
                    created_at=now,
                    updated_at=now
                ))

        # 5. Phase 4: Sample Limited-Purpose Verification Reference
        existing_vrf = (await session.execute(
            select(VerificationReference).where(VerificationReference.public_reference_code == "VRF-2026-DIT001")
        )).scalars().first()

        dit_admin = (await session.execute(
            select(User).where(User.email_normalized == "admin@dit.synthetic.edu.in")
        )).scalars().first()
        issuing_id = dit_admin.id if dit_admin else aicte_admin.id

        aarav_enrolment = (await session.execute(
            select(EnrolmentRecord).where(EnrolmentRecord.institution_id == inst_1.id)
        )).scalars().first()

        if not existing_vrf and aarav_enrolment:
            raw_sample_token = "neev_token_aarav_sharma_sample_2026"
            token_hash = hashlib.sha256(raw_sample_token.encode("utf-8")).hexdigest()
            profile = {
                "disclose_student_name": True,
                "disclose_programme": True,
                "disclose_enrolment_status": True,
                "disclose_academic_year": True,
                "disclose_institution": True,
                "disclose_admission_date": False
            }

            vrf = VerificationReference(
                public_reference_code="VRF-2026-DIT001",
                reference_token_hash=token_hash,
                enrolment_record_id=aarav_enrolment.id,
                institution_id=inst_1.id,
                issuing_user_id=issuing_id,
                purpose="EMPLOYMENT_VERIFICATION",
                disclosure_profile=json.dumps(profile),
                status="ACTIVE",
                max_uses=5,
                use_count=1,
                expires_at=now + timedelta(days=30),
                created_at=now,
                updated_at=now
            )
            session.add(vrf)
            await session.flush()

            session.add(VerificationAccessLog(
                verification_reference_id=vrf.id,
                outcome="SUCCESS",
                disclosed_claims_json=json.dumps({
                    "student_name": "Aarav Sharma",
                    "programme_name": "Computer Science and Engineering",
                    "enrolment_status": "ACTIVE",
                    "academic_year": "2024–2025",
                    "institution_name": "Delhi Institute of Technology"
                }),
                request_ip_hash=hashlib.sha256(b"127.0.0.1").hexdigest(),
                user_agent_safe="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Verification Resolver Test",
                created_at=now
            ))

        await session.commit()
        print("NEEV Phase 1, 2, 3 & 4 seed data successfully committed!")

if __name__ == "__main__":
    asyncio.run(seed_all_data())


