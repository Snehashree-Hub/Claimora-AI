# ============================================================
# MAIL PROCESSING API
# AI Agent for Health Insurance Claim Assistance
# File: backend/app/api/mail.py
# ============================================================

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from backend.app.mail_service import send_claim_email


# ------------------------------------------------------------
# ROUTER
# ------------------------------------------------------------

router = APIRouter(
    prefix="/api/mail",
    tags=["Mail Processing"]
)


# ============================================================
# REQUEST MODEL
# ============================================================

class MailProcessRequest(BaseModel):
    """
    Request body received from the frontend
    when a claim email needs to be sent.
    """

    claim_id: str

    insurer_name: str

    recipient_email: EmailStr

    patient_name: str

    patient_age: Optional[int] = None

    policy_id: str

    claim_amount: float

    diagnosis: str

    hospital_name: str

    doctor_name: str

    treatment_date: Optional[str] = None

    description: Optional[str] = ""

    attachment_paths: Optional[List[str]] = []


# ============================================================
# RESPONSE MODEL
# ============================================================

class MailProcessResponse(BaseModel):
    success: bool
    status: str
    claim_id: str
    insurer_name: str
    recipient_email: str
    subject: str
    processed_at: str
    message: str


# ============================================================
# POST /api/mail/process
# ============================================================

@router.post(
    "/process",
    response_model=MailProcessResponse
)
async def process_claim_mail(request: MailProcessRequest):
    """
    Send a health insurance claim email to the
    selected insurance company.

    Workflow:

        Frontend
            ↓
        /api/mail/process
            ↓
        SMTP
            ↓
        Insurance Company
    """

    # --------------------------------------------------------
    # Validate claim ID
    # --------------------------------------------------------

    if not request.claim_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Claim ID is required."
        )

    # --------------------------------------------------------
    # Validate insurer
    # --------------------------------------------------------

    if not request.insurer_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Insurance company name is required."
        )

    # --------------------------------------------------------
    # Validate patient
    # --------------------------------------------------------

    if not request.patient_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Patient name is required."
        )

    # --------------------------------------------------------
    # Validate policy ID
    # --------------------------------------------------------

    if not request.policy_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Policy ID is required."
        )

    # --------------------------------------------------------
    # Validate claim amount
    # --------------------------------------------------------

    if request.claim_amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Claim amount must be greater than 0."
        )

    # --------------------------------------------------------
    # Create email subject
    # --------------------------------------------------------

    subject = (
        f"Health Insurance Claim Submission - "
        f"{request.claim_id}"
    )

    # --------------------------------------------------------
    # Create professional email body
    # --------------------------------------------------------

    body = f"""
Dear Claims Team,

A new health insurance claim has been submitted through the
AI Agent for Health Insurance Claim Assistance system.

Please review the claim details and process the claim according
to the applicable policy and verification procedures.

============================================================
HEALTH INSURANCE CLAIM DETAILS
============================================================

Claim ID:
{request.claim_id}

Insurance Company:
{request.insurer_name}

------------------------------------------------------------
PATIENT INFORMATION
------------------------------------------------------------

Patient Name:
{request.patient_name}

Patient Age:
{request.patient_age if request.patient_age is not None else "Not Provided"}

Policy ID:
{request.policy_id}

------------------------------------------------------------
CLAIM INFORMATION
------------------------------------------------------------

Claim Amount:
₹{request.claim_amount:,.2f}

Diagnosis:
{request.diagnosis}

Hospital Name:
{request.hospital_name}

Doctor Name:
{request.doctor_name}

Treatment Date:
{request.treatment_date if request.treatment_date else "Not Provided"}

------------------------------------------------------------
DESCRIPTION
------------------------------------------------------------

{request.description if request.description else "No additional description provided."}

------------------------------------------------------------
DOCUMENTS
------------------------------------------------------------

Number of attached documents:
{len(request.attachment_paths or [])}

------------------------------------------------------------

The claim has been submitted for verification and processing.

Please review the submitted information and supporting documents
before making the final claim decision.

This email was generated automatically by the
AI Agent for Health Insurance Claim Assistance system.

Regards,

AI Agent for Health Insurance Claim Assistance
ClaimCare
"""


    # ========================================================
    # SEND EMAIL
    # ========================================================

    try:

        send_claim_email(
            recipient_email=str(request.recipient_email),
            subject=subject,
            body=body,
            attachment_paths=request.attachment_paths or []
        )

    except ValueError as error:

        # Configuration error
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "status": "Failed",
                "claim_id": request.claim_id,
                "message": str(error)
            }
        )

    except Exception as error:

        # SMTP or other email error
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "status": "Failed",
                "claim_id": request.claim_id,
                "message": (
                    "Unable to send claim email. "
                    f"Email service error: {str(error)}"
                )
            }
        )


    # ========================================================
    # SUCCESS RESPONSE
    # ========================================================

    processed_at = datetime.now().isoformat()

    return MailProcessResponse(
        success=True,
        status="Sent",
        claim_id=request.claim_id,
        insurer_name=request.insurer_name,
        recipient_email=str(request.recipient_email),
        subject=subject,
        processed_at=processed_at,
        message=(
            "Claim email sent successfully to the "
            "insurance company."
        )
    )


# ============================================================
# GET /api/mail/test
# ============================================================

@router.get("/test")
async def test_mail_api():
    """
    Simple API health check for Mail Processing.
    Does NOT send an email.
    """

    return {
        "success": True,
        "service": "Mail Processing",
        "status": "Ready",
        "endpoint": "POST /api/mail/process",
        "message": "Mail processing API is working."
    }