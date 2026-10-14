from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator

from .excel import save_claim_to_excel, update_claim_in_excel

router = APIRouter(
    prefix="/api/v1/claims",
    tags=["Claims"],
)


class ClaimCreate(BaseModel):
    claim_id: str = Field(min_length=1)
    policy_id: str = Field(min_length=1)

    patient_name: str = Field(min_length=1)
    patient_age: Optional[int] = Field(default=None, ge=0, le=120)
    email: EmailStr

    insurance_company: str = Field(min_length=1)

    claim_amount: float = Field(gt=0, allow_inf_nan=False)
    diagnosis: str = Field(min_length=1)

    hospital_name: str = Field(default="ClaimCare", min_length=1)
    doctor_name: Optional[str] = ""

    treatment_date: Optional[str] = ""
    description: Optional[str] = ""

    status: str = "Pending"
    fraud_risk: str = "Not Checked"

    created_at: Optional[str] = ""

    documents: Optional[list[str]] = []


    @field_validator(
        "claim_id",
        "policy_id",
        "patient_name",
        "insurance_company",
        "diagnosis",
        "hospital_name",
        mode="before",
    )
    @classmethod
    def validate_required_text(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("This field is required and cannot be blank.")
        return value.strip()


class ClaimStatusUpdate(BaseModel):
    status: str


@router.post("")
def create_claim(claim: ClaimCreate):

    claim_data = claim.model_dump()

    excel_result = save_claim_to_excel(claim_data)

    return {
        "success": True,
        "message": "Claim created and stored in Excel.",
        "claim": claim_data,
        "excel": excel_result,
    }


@router.patch("/{claim_id}/status")
def update_claim_status(
    claim_id: str,
    update: ClaimStatusUpdate,
):

    valid_statuses = [
        "Pending",
        "Under Review",
        "Approved",
        "Rejected",
    ]

    if update.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid claim status.",
        )

    result = update_claim_in_excel(
        claim_id,
        {
            "status": update.status,
        },
    )

    return {
        "success": True,
        "message": f"{claim_id} status updated.",
        **result,
    }