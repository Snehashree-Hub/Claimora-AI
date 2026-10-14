from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(
    prefix="/api/eligibility",
    tags=["Eligibility Agent"]
)


class EligibilityRequest(BaseModel):
    patient_name: str
    age: int
    policy_number: str
    insurance_company: str
    hospital_name: str
    treatment: str
    claim_amount: float


@router.post("/check")
def check_eligibility(data: EligibilityRequest):

    checks = []
    score = 0

    # 1. Patient name
    if data.patient_name.strip():
        checks.append({
            "check": "Patient Information",
            "status": "Passed",
            "details": "Patient name is provided"
        })
        score += 15
    else:
        checks.append({
            "check": "Patient Information",
            "status": "Failed",
            "details": "Patient name is missing"
        })

    # 2. Age
    if 0 < data.age <= 120:
        checks.append({
            "check": "Age Validation",
            "status": "Passed",
            "details": f"Age {data.age} is valid"
        })
        score += 10
    else:
        checks.append({
            "check": "Age Validation",
            "status": "Failed",
            "details": "Invalid patient age"
        })

    # 3. Policy
    if data.policy_number.strip():
        checks.append({
            "check": "Policy Number",
            "status": "Passed",
            "details": "Policy number is available"
        })
        score += 20
    else:
        checks.append({
            "check": "Policy Number",
            "status": "Failed",
            "details": "Policy number is missing"
        })

    # 4. Insurance company
    if data.insurance_company.strip():
        checks.append({
            "check": "Insurance Provider",
            "status": "Passed",
            "details": data.insurance_company
        })
        score += 15
    else:
        checks.append({
            "check": "Insurance Provider",
            "status": "Failed",
            "details": "Insurance company is missing"
        })

    # 5. Hospital
    if data.hospital_name.strip():
        checks.append({
            "check": "Hospital",
            "status": "Passed",
            "details": data.hospital_name
        })
        score += 10
    else:
        checks.append({
            "check": "Hospital",
            "status": "Failed",
            "details": "Hospital name is missing"
        })

    # 6. Treatment
    if data.treatment.strip():
        checks.append({
            "check": "Treatment",
            "status": "Passed",
            "details": data.treatment
        })
        score += 15
    else:
        checks.append({
            "check": "Treatment",
            "status": "Failed",
            "details": "Treatment information is missing"
        })

    # 7. Claim amount
    if data.claim_amount > 0:
        checks.append({
            "check": "Claim Amount",
            "status": "Passed",
            "details": f"₹{data.claim_amount:,.2f}"
        })
        score += 15
    else:
        checks.append({
            "check": "Claim Amount",
            "status": "Failed",
            "details": "Claim amount must be greater than zero"
        })

    # Final decision
    if score >= 85:
        eligibility_status = "Eligible"
        message = (
            "Claim passed the initial eligibility checks "
            "and can proceed to further processing."
        )

    elif score >= 60:
        eligibility_status = "Manual Review"
        message = (
            "Claim requires manual review before "
            "further processing."
        )

    else:
        eligibility_status = "Not Eligible"
        message = (
            "Claim failed the initial eligibility checks."
        )

    return {
        "success": True,
        "agent": "Eligibility Agent",
        "eligibility_status": eligibility_status,
        "eligibility_score": score,
        "checks": checks,
        "message": message
    }