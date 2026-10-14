from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from backend.security.security_service import analyze_claim_security


router = APIRouter(
    prefix="/api/security",
    tags=["Claim Security"]
)


class SecurityAnalysisRequest(BaseModel):
    claim_id: Optional[str] = Field(default="", max_length=100)
    patient_name: Optional[str] = Field(default="", max_length=200)
    patient_id: Optional[str] = Field(default="", max_length=200)
    patient_email: Optional[str] = Field(default="", max_length=200)
    treatment: Optional[str] = Field(default="", max_length=200)
    hospital: Optional[str] = Field(default="", max_length=300)
    claim_amount: float = Field(default=0, ge=0)
    document_path: Optional[str] = Field(default="", max_length=1000)
    extra_data: Optional[Dict[str, Any]] = None


@router.post("/analyze")
def analyze_security(request: SecurityAnalysisRequest):
    try:
        claim_data = request.model_dump()

        extra_data = claim_data.pop("extra_data", None)

        if isinstance(extra_data, dict):
            claim_data.update(extra_data)

        result = analyze_claim_security(claim_data)

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Security analysis failed: {str(exc)}"
        )


@router.get("/health")
def security_health():
    return {
        "status": "healthy",
        "module": "Claim Security Analyzer",
        "features": [
            "Duplicate claim screening",
            "Claim amount anomaly screening",
            "Claim data consistency",
            "Document integrity fingerprinting",
            "Fraud analysis integration",
            "Security score",
            "Risk classification",
            "Risk-based workflow decision"
        ]
    }
