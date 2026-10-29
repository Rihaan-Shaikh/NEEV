import json
import time
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.verification import IntegrationStatusLog

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class IntegrationService:
    @staticmethod
    async def list_adapters(session: AsyncSession) -> List[Dict[str, Any]]:
        """
        Lists all external source adapters with current simulation status, claims, and limitations.
        """
        q = select(IntegrationStatusLog).order_by(IntegrationStatusLog.adapter_name.asc())
        rows = (await session.execute(q)).scalars().all()
        result = []
        for r in rows:
            result.append({
                "adapter_code": r.adapter_code,
                "adapter_name": r.adapter_name,
                "status": r.status,
                "is_simulated": r.is_simulated,
                "last_checked_at": r.last_checked_at,
                "latency_ms": r.latency_ms,
                "supported_claims": json.loads(r.supported_claims) if r.supported_claims else [],
                "known_limitations": r.known_limitations,
                "contract_test_status": r.contract_test_status,
                "error_code": r.error_code
            })
        return result

    @staticmethod
    async def get_adapter(session: AsyncSession, adapter_code: str) -> Dict[str, Any]:
        """
        Retrieves status metadata for a specific adapter.
        """
        q = select(IntegrationStatusLog).where(IntegrationStatusLog.adapter_code == adapter_code.upper())
        r = (await session.execute(q)).scalar_one_or_none()
        if not r:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Integration adapter '{adapter_code}' not found."
            )
        return {
            "adapter_code": r.adapter_code,
            "adapter_name": r.adapter_name,
            "status": r.status,
            "is_simulated": r.is_simulated,
            "last_checked_at": r.last_checked_at,
            "latency_ms": r.latency_ms,
            "supported_claims": json.loads(r.supported_claims) if r.supported_claims else [],
            "known_limitations": r.known_limitations,
            "contract_test_status": r.contract_test_status,
            "error_code": r.error_code
        }

    @staticmethod
    async def test_contract(session: AsyncSession, adapter_code: str) -> Dict[str, Any]:
        """
        Executes a simulated contract test probe against the specified adapter.
        """
        q = select(IntegrationStatusLog).where(IntegrationStatusLog.adapter_code == adapter_code.upper())
        r = (await session.execute(q)).scalar_one_or_none()
        if not r:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Integration adapter '{adapter_code}' not found."
            )

        start_time = time.time()
        # Simulated probe latency between 50ms and 150ms
        simulated_latency = 75.0 + (hash(adapter_code) % 50)
        now = utc_now()

        r.latency_ms = simulated_latency
        r.last_checked_at = now
        r.contract_test_status = "PASSED"
        r.updated_at = now
        await session.commit()

        return {
            "adapter_code": r.adapter_code,
            "contract_test_status": "PASSED",
            "latency_ms": simulated_latency,
            "checked_at": now,
            "message": f"Simulated contract test for {r.adapter_name} passed successfully in {simulated_latency:.1f}ms."
        }
