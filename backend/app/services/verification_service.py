import hashlib
import json
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.verification import VerificationReference, VerificationAccessLog
from app.models.student import EnrolmentRecord
from app.models.user import User
from app.models.institution import Institution
from app.services.audit_service import log_audit_event
from app.policies.authorization import enforce_institution_scope

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class VerificationService:
    @staticmethod
    def hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()

    @staticmethod
    async def issue_reference(
        session: AsyncSession,
        current_user: User,
        enrolment_record_id: str,
        purpose: str,
        disclosure_profile: Dict[str, bool],
        expires_in_days: int = 30,
        max_uses: Optional[int] = None
    ) -> Tuple[VerificationReference, str]:
        """
        Issues an opaque, limited-purpose verification reference for an enrolment record.
        Enforces tenant authorization. Raw token is returned strictly once and never stored plaintext.
        """
        # 1. Fetch enrolment record with eager loads
        q = (
            select(EnrolmentRecord)
            .options(
                selectinload(EnrolmentRecord.institution),
                selectinload(EnrolmentRecord.programme),
                selectinload(EnrolmentRecord.academic_year)
            )
            .where(EnrolmentRecord.id == enrolment_record_id)
        )
        enrolment = (await session.execute(q)).scalar_one_or_none()
        if not enrolment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrolment record '{enrolment_record_id}' not found."
            )

        # 2. Enforce scope: User must have access to the institution
        enforce_institution_scope(current_user, enrolment.institution_id)

        # 3. Generate high-entropy bearer token & tracking code
        raw_token = f"neev_vrf_{secrets.token_hex(20)}"
        token_hash = VerificationService.hash_token(raw_token)
        public_code = f"VRF-2026-{secrets.token_hex(4).upper()}"

        # 4. Safe sanitized disclosure profile (allowlist only, NO APAAR permitted)
        allowed_profile_keys = {
            "disclose_student_name": True,
            "disclose_programme": True,
            "disclose_enrolment_status": True,
            "disclose_academic_year": True,
            "disclose_institution": True,
            "disclose_admission_date": False
        }
        sanitized_profile = {
            k: bool(disclosure_profile.get(k, allowed_profile_keys[k]))
            for k in allowed_profile_keys
        }

        expires_at = utc_now() + timedelta(days=expires_in_days)

        vrf = VerificationReference(
            public_reference_code=public_code,
            reference_token_hash=token_hash,
            enrolment_record_id=enrolment.id,
            institution_id=enrolment.institution_id,
            issuing_user_id=current_user.id,
            purpose=purpose.strip()[:100],
            disclosure_profile=json.dumps(sanitized_profile),
            status="ACTIVE",
            max_uses=max_uses if max_uses and max_uses > 0 else None,
            use_count=0,
            expires_at=expires_at,
            created_at=utc_now(),
            updated_at=utc_now()
        )
        session.add(vrf)
        await session.flush()

        # Audit
        await log_audit_event(
            session,
            action="VERIFICATION_REFERENCE_ISSUED",
            target_type="VERIFICATION_REFERENCE",
            target_id=vrf.id,
            actor_user_id=current_user.id,
            actor_email=current_user.email_normalized,
            metadata={
                "public_code": public_code,
                "purpose": purpose,
                "expires_at": expires_at.isoformat(),
                "max_uses": max_uses,
                "institution_id": enrolment.institution_id
            }
        )
        await session.commit()
        return vrf, raw_token, enrolment

    @staticmethod
    async def revoke_reference(
        session: AsyncSession,
        current_user: User,
        reference_id: str,
        revocation_reason: str
    ) -> VerificationReference:
        """
        Revokes an active verification reference with an immutable audit event.
        """
        q = (
            select(VerificationReference)
            .options(
                selectinload(VerificationReference.enrolment_record).selectinload(EnrolmentRecord.programme),
                selectinload(VerificationReference.enrolment_record).selectinload(EnrolmentRecord.academic_year),
                selectinload(VerificationReference.institution),
                selectinload(VerificationReference.issuing_user),
                selectinload(VerificationReference.access_logs)
            )
            .where(VerificationReference.id == reference_id)
        )
        vrf = (await session.execute(q)).scalar_one_or_none()
        if not vrf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Verification reference '{reference_id}' not found."
            )

        enforce_institution_scope(current_user, vrf.institution_id)

        if vrf.status == "REVOKED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification reference is already revoked."
            )

        vrf.status = "REVOKED"
        vrf.revoked_at = utc_now()
        vrf.revoked_by_user_id = current_user.id
        vrf.revocation_reason = revocation_reason.strip()[:255]
        vrf.updated_at = utc_now()

        await log_audit_event(
            session,
            action="VERIFICATION_REFERENCE_REVOKED",
            target_type="VERIFICATION_REFERENCE",
            target_id=vrf.id,
            actor_user_id=current_user.id,
            actor_email=current_user.email_normalized,
            metadata={
                "public_code": vrf.public_reference_code,
                "reason": vrf.revocation_reason,
                "institution_id": vrf.institution_id
            }
        )
        await session.commit()
        return vrf

    @staticmethod
    async def verify_reference_token(
        session: AsyncSession,
        raw_token: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resolves a limited-purpose verification reference against the database.
        Uses row locking to guarantee atomic use limit enforcement under concurrency.
        Returns minimal permitted claims with synthetic disclaimer.
        """
        token_hash = VerificationService.hash_token(raw_token)
        now = utc_now()
        ip_hash = hashlib.sha256(client_ip.encode("utf-8")).hexdigest() if client_ip else None
        safe_ua = (user_agent or "")[:255]

        # 1. Query with row lock
        q = (
            select(VerificationReference)
            .options(
                selectinload(VerificationReference.enrolment_record).selectinload(EnrolmentRecord.institution),
                selectinload(VerificationReference.enrolment_record).selectinload(EnrolmentRecord.programme),
                selectinload(VerificationReference.enrolment_record).selectinload(EnrolmentRecord.academic_year),
                selectinload(VerificationReference.institution)
            )
            .where(VerificationReference.reference_token_hash == token_hash)
            .with_for_update(of=VerificationReference)
        )
        vrf = (await session.execute(q)).scalar_one_or_none()

        if not vrf:
            return {
                "outcome": "INVALID_TOKEN",
                "public_reference_code": None,
                "verified_at": now,
                "purpose": None,
                "disclosed_claims": None,
                "synthetic_disclaimer": "Synthetic demonstration — not an official APAAR verification.",
                "message": "The presented verification reference token is invalid or unrecognized."
            }

        # 2. Check Revocation
        if vrf.status == "REVOKED" or vrf.revoked_at is not None:
            access_log = VerificationAccessLog(
                verification_reference_id=vrf.id,
                outcome="REVOKED",
                disclosed_claims_json=None,
                request_ip_hash=ip_hash,
                user_agent_safe=safe_ua,
                created_at=now
            )
            session.add(access_log)
            await session.commit()
            return {
                "outcome": "REVOKED",
                "public_reference_code": vrf.public_reference_code,
                "verified_at": now,
                "purpose": vrf.purpose,
                "disclosed_claims": None,
                "synthetic_disclaimer": "Synthetic demonstration — not an official APAAR verification.",
                "message": f"This verification reference was revoked by the issuing institution on {vrf.revoked_at.strftime('%Y-%m-%d')}."
            }

        # 3. Check Expiry
        if vrf.expires_at < now or vrf.status == "EXPIRED":
            vrf.status = "EXPIRED"
            access_log = VerificationAccessLog(
                verification_reference_id=vrf.id,
                outcome="EXPIRED",
                disclosed_claims_json=None,
                request_ip_hash=ip_hash,
                user_agent_safe=safe_ua,
                created_at=now
            )
            session.add(access_log)
            await session.commit()
            return {
                "outcome": "EXPIRED",
                "public_reference_code": vrf.public_reference_code,
                "verified_at": now,
                "purpose": vrf.purpose,
                "disclosed_claims": None,
                "synthetic_disclaimer": "Synthetic demonstration — not an official APAAR verification.",
                "message": f"This verification reference expired on {vrf.expires_at.strftime('%Y-%m-%d')}."
            }

        # 4. Check Use Limit
        if vrf.max_uses is not None and vrf.use_count >= vrf.max_uses:
            vrf.status = "EXHAUSTED"
            access_log = VerificationAccessLog(
                verification_reference_id=vrf.id,
                outcome="USE_LIMIT_EXCEEDED",
                disclosed_claims_json=None,
                request_ip_hash=ip_hash,
                user_agent_safe=safe_ua,
                created_at=now
            )
            session.add(access_log)
            await session.commit()
            return {
                "outcome": "USE_LIMIT_EXCEEDED",
                "public_reference_code": vrf.public_reference_code,
                "verified_at": now,
                "purpose": vrf.purpose,
                "disclosed_claims": None,
                "synthetic_disclaimer": "Synthetic demonstration — not an official APAAR verification.",
                "message": f"This reference has reached its maximum authorized verification limit ({vrf.max_uses} uses)."
            }

        # 5. Check Enrolment Record eligibility
        enrolment = vrf.enrolment_record
        if not enrolment:
            return {
                "outcome": "RECORD_INELIGIBLE",
                "public_reference_code": vrf.public_reference_code,
                "verified_at": now,
                "purpose": vrf.purpose,
                "disclosed_claims": None,
                "synthetic_disclaimer": "Synthetic demonstration — not an official APAAR verification.",
                "message": "The underlying student record is no longer eligible for verification."
            }

        # 6. Success: Increment use count & resolve minimal claims
        vrf.use_count += 1
        if vrf.max_uses is not None and vrf.use_count >= vrf.max_uses:
            vrf.status = "EXHAUSTED"
        vrf.updated_at = now

        profile = json.loads(vrf.disclosure_profile)
        claims: Dict[str, Any] = {}

        if profile.get("disclose_student_name"):
            claims["student_full_name"] = enrolment.student_full_name
        if profile.get("disclose_institution"):
            claims["institution_name"] = enrolment.institution.name if enrolment.institution else "Delhi Institute of Technology"
            claims["institution_code"] = enrolment.institution.official_institution_code if enrolment.institution else "AICTE-SYNTH-1001"
        if profile.get("disclose_programme") and enrolment.programme:
            claims["programme_name"] = enrolment.programme.programme_name
            claims["programme_code"] = enrolment.programme.official_programme_code
        if profile.get("disclose_enrolment_status"):
            claims["enrolment_status"] = enrolment.enrolment_status
        if profile.get("disclose_academic_year") and enrolment.academic_year:
            claims["academic_year"] = enrolment.academic_year.label
        if profile.get("disclose_admission_date"):
            claims["admission_date"] = enrolment.admission_date.isoformat() if enrolment.admission_date else None

        # Log access
        access_log = VerificationAccessLog(
            verification_reference_id=vrf.id,
            outcome="SUCCESS",
            disclosed_claims_json=json.dumps(claims),
            request_ip_hash=ip_hash,
            user_agent_safe=safe_ua,
            created_at=now
        )
        session.add(access_log)

        await log_audit_event(
            session,
            action="VERIFICATION_RESOLVED",
            target_type="VERIFICATION_REFERENCE",
            target_id=vrf.id,
            actor_user_id=vrf.issuing_user_id,
            actor_email="system@neev.verification",
            metadata={
                "public_code": vrf.public_reference_code,
                "use_count": vrf.use_count,
                "outcome": "SUCCESS",
                "institution_id": vrf.institution_id
            }
        )
        await session.commit()

        return {
            "outcome": "SUCCESS",
            "public_reference_code": vrf.public_reference_code,
            "verified_at": now,
            "purpose": vrf.purpose,
            "disclosed_claims": claims,
            "synthetic_disclaimer": "Synthetic demonstration — not an official APAAR verification.",
            "message": "Record successfully verified against NEEV canonical registry."
        }
