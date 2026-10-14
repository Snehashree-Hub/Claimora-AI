from fastapi import APIRouter

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin Demo Claims"]
)


# ============================================================
# 50 DEMO CLAIMS
# ADMIN DASHBOARD ONLY
# ============================================================

TREATMENTS = [
    "General Surgery",
    "Cardiology Consultation",
    "Orthopedic Treatment",
    "Diabetes Care",
    "Fever and Infection",
    "Maternity Care",
    "ENT Treatment",
    "Neurology Consultation",
    "Gastroenterology",
    "Emergency Treatment",
]

INSURANCE_COMPANIES = [
    "Star Health",
    "Niva Bupa",
    "Aditya Birla Health",
    "HDFC ERGO",
    "ICICI Lombard",
    "Care Health",
    "Bajaj Allianz",
    "SBI General",
]

DEMO_STATUSES = [
    "Demo - Under Review",
    "Demo - Document Review",
    "Demo - Eligibility Review",
    "Demo - Pending",
]


def create_demo_claims():

    claims = []

    for i in range(1, 51):

        is_external = i % 2 == 0

        if is_external:

            insurance_type = "External"

            insurance_company = (
                INSURANCE_COMPANIES[
                    (i - 1) % len(INSURANCE_COMPANIES)
                ]
            )

            policy_number = f"DEMO-POL-{i:03d}"

        else:

            insurance_type = "ClaimCare Insurance"

            insurance_company = (
                "ClaimCare Insurance"
            )

            policy_number = (
                f"DEMO-RKH-{i:03d}"
            )

        claim = {

            "id": f"DEMO-{i:03d}",

            "claim_number": (
                f"DEMO-CLM-{i:03d}"
            ),

            "policy_number": policy_number,

            "user_id": None,

            "patient_name": (
                f"Demo Patient {i:02d}"
            ),

            "age": 22 + ((i * 3) % 54),

            "insurance_type": insurance_type,

            "insurance_company": insurance_company,

            "hospital_name": "ClaimCare",

            "treatment": (
                TREATMENTS[
                    (i - 1) % len(TREATMENTS)
                ]
            ),

            "claim_amount": (
                15000 + (i * 2750)
            ),

            "eligibility_status": (
                "Pending Review"
            ),

            "document_status": "Pending",

            "fraud_risk": "Not Screened",

            "assessment_status": "Pending",

            "email_status": "Not Sent",

            "overall_status": (
                DEMO_STATUSES[
                    (i - 1) % len(DEMO_STATUSES)
                ]
            ),

            "remarks": (
                "Illustrative demo record — "
                "not a real insurance claim."
            ),

            "is_demo": True
        }

        claims.append(claim)

    return claims


from fastapi import APIRouter
from typing import List, Dict

router = APIRouter(
    prefix="/api/demo-claims",
    tags=["Demo Claims"]
)

INSURERS = [
    "Star Health",
    "Niva Bupa",
    "Aditya Birla Health",
    "HDFC ERGO",
    "ICICI Lombard",
    "Care Health",
    "Bajaj Allianz",
    "SBI General"
]

TREATMENTS = [
    "General Consultation",
    "General Surgery",
    "Orthopaedic Care",
    "Cardiology",
    "Diabetes Management",
    "ENT Treatment",
    "Maternity Care",
    "Emergency Care"
]

STATUSES = [
    "Demo - Under Review",
    "Demo - Document Review",
    "Demo - Eligibility Review",
    "Demo - Pending"
]

DEMO_CLAIMS: List[Dict] = []

for i in range(1, 51):

    is_external = i % 2 == 0

    DEMO_CLAIMS.append({
        "id": f"DEMO-{i:03d}",
        "claim_number": f"DEMO-CLM-{i:03d}",
        "policy_number": f"DEMO-POL-{i:03d}",

        "user_id": None,

        "patient_name": f"Demo Patient {i:02d}",
        "age": 22 + ((i * 3) % 54),

        "insurance_type": (
            "External Insurance"
            if is_external
            else "ClaimCare Insurance"
        ),

        "insurance_company": (
            INSURERS[(i - 1) % len(INSURERS)]
            if is_external
            else "ClaimCare Insurance"
        ),

        "hospital_name": "ClaimCare",

        "treatment": TREATMENTS[
            (i - 1) % len(TREATMENTS)
        ],

        "claim_amount": 25000 + (i * 1750),

        "eligibility_status": "Pending Review",
        "document_status": "Pending",
        "fraud_risk": "Not Screened",
        "assessment_status": "Pending",
        "email_status": "Not Sent",

        "overall_status": STATUSES[
            (i - 1) % len(STATUSES)
        ],

        "remarks": (
            "Illustrative demo record — "
            "not a real insurance claim."
        ),

        "demo": True
    })


@router.get("/")
def get_demo_claims():

    return {
        "success": True,
        "count": len(DEMO_CLAIMS),
        "demo": True,
        "message": (
            "These 50 records are illustrative demo data "
            "for the Admin Dashboard only."
        ),
        "claims": DEMO_CLAIMS
    }


@router.get("/summary")
def get_demo_claim_summary():

    status_counts = {}

    for claim in DEMO_CLAIMS:
        status = claim["overall_status"]

        if status not in status_counts:
            status_counts[status] = 0

        status_counts[status] += 1

    return {
        "success": True,
        "total_demo_claims": len(DEMO_CLAIMS),
        "status_counts": status_counts
    }