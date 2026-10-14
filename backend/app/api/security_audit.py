from fastapi import APIRouter, HTTPException
from typing import Optional

from backend.security.audit_service import (
    get_security_events,
    log_security_event
)


router = APIRouter(
    prefix="/api/security/audit",
    tags=["Security Audit Trail"]
)


@router.get("/")
def get_audit_events(
    claim_id: Optional[str] = None
):
    try:
        events = get_security_events(claim_id)

        return {
            "success": True,
            "count": len(events),
            "claim_id": claim_id,
            "events": events
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read security audit trail: {str(exc)}"
        )


@router.post("/event")
def create_audit_event(
    claim_id: str,
    action: str,
    status: str,
    risk_level: Optional[str] = None,
    security_score: Optional[int] = None,
    decision: Optional[str] = None,
    user: Optional[str] = "system"
):
    try:
        event = log_security_event(
            claim_id=claim_id,
            action=action,
            status=status,
            risk_level=risk_level,
            security_score=security_score,
            decision=decision,
            user=user
        )

        return {
            "success": True,
            "event": event
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to create security audit event: {str(exc)}"
        )


@router.get("/health")
def audit_health():
    return {
        "status": "healthy",
        "module": "Security Audit Trail",
        "storage": "JSON",
        "features": [
            "Claim security event logging",
            "Risk decision tracking",
            "Security score tracking",
            "Workflow action tracking",
            "Claim-specific audit history"
        ]
    }
