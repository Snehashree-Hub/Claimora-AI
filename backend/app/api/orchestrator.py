from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .eligibility import check_eligibility
from .fraud_detection import detect_fraud, FraudRequest
from backend.security.security_service import analyze_claim_security
from backend.security.audit_service import log_security_event
from pathlib import Path
from backend.security.document_security import (
    UPLOAD_DIR,
    verify_secure_document
)
from backend.app.api.documents import verify_stored_document_content



router = APIRouter(
    prefix="/api/orchestrator",
    tags=["AI Orchestrator Agent"]
)


class OrchestratorRequest(BaseModel):
    claim_id: str = Field(default="", max_length=100)

    patient_name: str
    age: int
    policy_number: str
    insurance_company: str
    hospital_name: str
    treatment: str
    claim_amount: float

    patient_id: str = ""
    patient_email: str = ""

    document_status: str = "Not Verified"
    document_score: int = 0
    document_type: str = ""
    document_path: str = ""
    stored_filename: str = ""


@router.get("/test")
def orchestrator_test():
    return {
        "success": True,
        "agent": "AI Claim Orchestrator",
        "status": "working",

        "connected_agents": [
            "Claim Security Analyzer",
            "Document Verification Agent",
            "Eligibility Agent",
            "Fraud Detection Agent"
        ],

        "risk_gate": {
            "low": "Continue normal AI-agent claim processing.",
            "medium": "Continue with additional verification.",
            "high": "Stop automation and require manual review."
        },

        "audit_trail": {
            "enabled": True,
            "module": "Security Audit Trail"
        }
    }


@router.post("/process")
def process_claim(data: OrchestratorRequest):

    claim_id = data.claim_id or "UNASSIGNED"

    try:

        # ==========================================================
        # 1. CLAIM RECEIVED
        # ==========================================================

        log_security_event(
            claim_id=claim_id,
            action="CLAIM_RECEIVED",
            status="RECEIVED",
            user=data.patient_email or "system",
            details={
                "patient_name": data.patient_name,
                "policy_number": data.policy_number,
                "insurance_company": data.insurance_company,
                "hospital_name": data.hospital_name,
                "treatment": data.treatment,
                "claim_amount": data.claim_amount
            }
        )


        # ==========================================================
        # 2. SECURITY ANALYSIS
        # ==========================================================

        security_result = analyze_claim_security(
            {
                "claim_id": claim_id,
                "patient_name": data.patient_name,
                "patient_id": data.patient_id,
                "patient_email": data.patient_email,

                "age": data.age,
                "policy_number": data.policy_number,
                "insurance_company": data.insurance_company,

                "hospital": data.hospital_name,
                "hospital_name": data.hospital_name,

                "treatment": data.treatment,
                "claim_amount": data.claim_amount,

                "document_path": data.document_path
            }
        )


        security_info = security_result.get(
            "security",
            {}
        )

        security_score = security_info.get(
            "security_score",
            0
        )

        risk_level = security_info.get(
            "risk_level",
            "HIGH"
        )

        security_decision = security_info.get(
            "decision",
            "REVIEW_REQUIRED"
        )


        # ==========================================================
        # 3. AUDIT SECURITY SCAN
        # ==========================================================

        log_security_event(
            claim_id=claim_id,
            action="SECURITY_SCAN",
            status="COMPLETED",
            risk_level=risk_level,
            security_score=security_score,
            decision=security_decision,
            user="security_analyzer",
            details={
                "security_reasons": security_info.get(
                    "reasons",
                    []
                )
            }
        )


        # ==========================================================
        # 4. HIGH RISK Ã¢â€ â€™ STOP AUTOMATION
        # ==========================================================

        if risk_level == "HIGH":

            log_security_event(
                claim_id=claim_id,
                action="RISK_GATE",
                status="BLOCKED",
                risk_level="HIGH",
                security_score=security_score,
                decision="MANUAL_REVIEW",
                user="security_gate",
                details={
                    "automation_status": "STOPPED",
                    "reason": (
                        "High security risk detected. "
                        "Automated claim processing stopped."
                    )
                }
            )


            log_security_event(
                claim_id=claim_id,
                action="AUTOMATION",
                status="STOPPED",
                risk_level="HIGH",
                security_score=security_score,
                decision="MANUAL_REVIEW",
                user="security_gate"
            )


            log_security_event(
                claim_id=claim_id,
                action="MANUAL_REVIEW",
                status="REQUIRED",
                risk_level="HIGH",
                security_score=security_score,
                decision="MANUAL_REVIEW",
                user="system"
            )


            return {
                "success": True,
                "agent": "AI Claim Orchestrator",

                "claim_information": {
                    "claim_id": claim_id,
                    "patient_name": data.patient_name,
                    "age": data.age,
                    "policy_number": data.policy_number,
                    "insurance_company": data.insurance_company,
                    "hospital_name": data.hospital_name,
                    "treatment": data.treatment,
                    "claim_amount": data.claim_amount
                },

                "agents": {

                    "security_analyzer": security_result,

                    "document_verification_agent": {
                        "status": "NOT_STARTED",
                        "score": 0,
                        "document_type": data.document_type
                    },

                    "eligibility_agent": {
                        "status": "NOT_STARTED",
                        "score": 0,
                        "checks": []
                    },

                    "fraud_detection_agent": {
                        "status": "NOT_STARTED",
                        "prediction": "NOT_RUN",
                        "risk_level": "NOT_RUN",
                        "fraud_probability": 0
                    }
                },

                "risk_gate": {
                    "security_score": security_score,
                    "risk_level": "HIGH",
                    "decision": "MANUAL_REVIEW",
                    "automation_status": "STOPPED",
                    "reason": (
                        "High security risk detected. "
                        "Automated claim processing has been "
                        "stopped and manual review is required."
                    )
                },

                "assessment": {
                    "status": "Manual Review",
                    "message": (
                        "Claim was stopped by the security risk "
                        "gate before automated eligibility and "
                        "fraud processing."
                    )
                },

                "routing": {
                    "processing_type": "Manual Review",
                    "department": "Insurance Security and Claims Review"
                },

                "final_status": "Manual Review",

                "message": (
                    "Claim security screening triggered "
                    "the high-risk automation gate."
                )
            }


        # ==========================================================
        # 5. DOCUMENT INFORMATION
        # ==========================================================

        # ==========================================================
        # 5. REQUIRED-FIELD VALIDATION
        # Runs after the high-security-risk gate and before
        # document, eligibility and fraud workflow processing.
        # ==========================================================

        required_fields = {
            "patient_name": data.patient_name,
            "policy_number": data.policy_number,
            "insurance_company": data.insurance_company,
            "hospital_name": data.hospital_name,
            "treatment": data.treatment,
        }

        missing_fields = [
            field_name
            for field_name, value in required_fields.items()
            if not isinstance(value, str) or not value.strip()
        ]

        invalid_fields = []

        if not 0 < data.age <= 120:
            invalid_fields.append({
                "field": "age",
                "reason": "Age must be between 1 and 120."
            })

        if data.claim_amount <= 0:
            invalid_fields.append({
                "field": "claim_amount",
                "reason": "Claim amount must be greater than zero."
            })

        validation_passed = (
            not missing_fields and not invalid_fields
        )

        log_security_event(
            claim_id=claim_id,
            action="MISSING_FIELD_VALIDATION",
            status="PASSED" if validation_passed else "NEEDS_INFORMATION",
            risk_level=risk_level,
            security_score=security_score,
            decision=(
                "CONTINUE"
                if validation_passed
                else "ADDITIONAL_INFORMATION_REQUIRED"
            ),
            user="claim_validation_agent",
            details={
                "missing_fields": missing_fields,
                "invalid_fields": invalid_fields,
                "validation_passed": validation_passed
            }
        )

        if not validation_passed:
            log_security_event(
                claim_id=claim_id,
                action="CLAIM_PROCESSING",
                status="PAUSED",
                risk_level=risk_level,
                security_score=security_score,
                decision="ADDITIONAL_INFORMATION_REQUIRED",
                user="system",
                details={
                    "reason": (
                        "Required claim information is missing "
                        "or invalid."
                    )
                }
            )

            return {
                "success": True,
                "agent": "AI Claim Orchestrator",
                "claim_information": {
                    "claim_id": claim_id,
                    "patient_name": data.patient_name,
                    "policy_number": data.policy_number,
                    "insurance_company": data.insurance_company,
                    "hospital_name": data.hospital_name,
                    "treatment": data.treatment,
                    "claim_amount": data.claim_amount
                },
                "agents": {
                    "security_analyzer": {
                        "status": "COMPLETED",
                        "risk_level": risk_level,
                        "security_score": security_score,
                        "decision": security_decision
                    },
                    "missing_field_validation": {
                        "status": "NEEDS_INFORMATION",
                        "missing_fields": missing_fields,
                        "invalid_fields": invalid_fields
                    },
                    "document_verification": {
                        "status": "NOT_STARTED"
                    },
                    "eligibility": {
                        "status": "NOT_STARTED"
                    },
                    "fraud_detection": {
                        "status": "NOT_RUN"
                    }
                },
                "risk_gate": {
                    "status": "PAUSED",
                    "risk_level": risk_level,
                    "reason": "Missing or invalid claim information."
                },
                "assessment": {
                    "status": "Additional Information Required",
                    "missing_fields": missing_fields,
                    "invalid_fields": invalid_fields
                },
                "final_status": "Additional Information Required",
                "message": (
                    "Please correct or complete the listed claim "
                    "fields before automated processing continues."
                )
            }

        # ==========================================================
        # 5. SECURE DOCUMENT INTEGRITY + CONTENT VERIFICATION
        # ==========================================================

        if not data.claim_id or not data.stored_filename:
            document_status = "Review Required"
            document_score = 0
            document_type = "Not supplied"
            reason = (
                "A real claim ID and stored_filename from the secure "
                "upload response are required."
            )
            integrity_result = {
                "status": "NOT_CHECKED",
                "message": reason
            }
            content_result = {
                "verification_status": "Review Required",
                "message": reason,
                "failed_checks": ["Secure document reference missing"]
            }
            verified_path = ""

        else:
            integrity_result = verify_secure_document(
                data.claim_id,
                data.stored_filename
            )

            verified_path = str(
                Path(UPLOAD_DIR) / data.claim_id / data.stored_filename
            )

            if integrity_result.get("status") == "VERIFIED":
                try:
                    file_bytes = Path(verified_path).read_bytes()
                    content_result = verify_stored_document_content(
                        file_bytes=file_bytes,
                        filename=data.stored_filename,
                        patient_name=data.patient_name,
                        policy_number=data.policy_number,
                        claim_amount=str(data.claim_amount)
                    )
                except OSError:
                    content_result = {
                        "verification_status": "Review Required",
                        "score": 0,
                        "document_type": "Unreadable",
                        "failed_checks": ["Stored file could not be read"],
                        "message": "Stored file could not be read for content verification."
                    }
            else:
                content_result = {
                    "verification_status": "Review Required",
                    "score": 0,
                    "document_type": "Untrusted document",
                    "failed_checks": ["Integrity verification did not pass"],
                    "message": integrity_result.get(
                        "message",
                        "Document integrity could not be verified."
                    )
                }

        content_status = content_result.get(
            "verification_status", "Review Required"
        )
        document_type = content_result.get("document_type", "Unknown")
        document_score = int(content_result.get("score", 0) or 0)

        if (
            integrity_result.get("status") == "VERIFIED"
            and content_status == "Verified"
        ):
            document_status = "Verified"
        elif content_status == "Invalid":
            document_status = "Invalid"
        else:
            document_status = "Review Required"

        # Fail closed: any unsuccessful secure-document integrity check
        # must be classified as HIGH risk and sent for manual review.
        integrity_passed = (
            integrity_result.get("success") is True
            and integrity_result.get("status") == "VERIFIED"
        )

        if not integrity_passed:
            risk_level = "HIGH"
            security_decision = "MANUAL_REVIEW"

        log_security_event(
            claim_id=claim_id,
            action="DOCUMENT_INTEGRITY_AND_CONTENT_VERIFICATION",
            status=document_status.upper().replace(" ", "_"),
            risk_level=risk_level,
            security_score=security_score,
            user="document_verification_agent",
            details={
                "integrity_status": integrity_result.get("status"),
                "integrity_message": integrity_result.get("message", ""),
                "content_status": content_status,
                "document_score": document_score,
                "document_type": document_type,
                "stored_filename": data.stored_filename,
                "failed_checks": content_result.get("failed_checks", [])
            }
        )

        # Never continue to eligibility or fraud scoring when the
        # secure document is missing, modified, unreadable, or unverified.
        if document_status != "Verified":
            log_security_event(
                claim_id=claim_id,
                action="CLAIM_PROCESSING_PAUSED",
                status="PAUSED",
                risk_level=risk_level,
                security_score=security_score,
                user="document_security_gate",
                details={
                    "document_status": document_status,
                    "integrity_status": integrity_result.get("status"),
                    "integrity_message": integrity_result.get("message", ""),
                    "reason": (
                        integrity_result.get("message")
                        or "Secure document integrity verification did not pass."
                    )
                }
            )

            return {
                "success": True,
                "claim_id": claim_id,
                "security": {
                    "risk_level": risk_level,
                    "security_score": security_score,
                    "document_integrity": integrity_result
                },
                "document_verification_agent": {
                    "status": document_status,
                    "score": document_score,
                    "document_type": document_type,
                    "integrity": integrity_result,
                    "content_verification": content_result
                },
                "eligibility_agent": {"status": "NOT_RUN"},
                "fraud_detection_agent": {"status": "NOT_RUN"},
                "risk_gate": {
                    "status": "PAUSED",
                    "risk_level": risk_level,
                    "reason": "Secure document verification must pass before automated claim analysis."
                },
                "assessment": {
                    "status": (
                        "Document Rejected"
                        if document_status == "Invalid"
                        else "Document Review"
                    ),
                    "failed_checks": content_result.get("failed_checks", [])
                },
                "final_status": (
                    "Document Rejected"
                    if document_status == "Invalid"
                    else "Document Review"
                ),
                "message": (
                    "Document verification failed. Manual review is required. "
                    "No claim approval has been made."
                )
            }

        # Use the server-resolved path only after integrity verification.
        # Do not trust document_status, score, or type sent by the client.
        data.document_path = verified_path

        # Re-run security analysis with the server-verified document path.
        # The earlier analysis may have run before the file path was resolved.
        security_result = analyze_claim_security(
            {
                "claim_id": claim_id,
                "patient_name": data.patient_name,
                "patient_id": data.patient_id,
                "patient_email": data.patient_email,
                "age": data.age,
                "policy_number": data.policy_number,
                "insurance_company": data.insurance_company,
                "hospital": data.hospital_name,
                "hospital_name": data.hospital_name,
                "treatment": data.treatment,
                "claim_amount": data.claim_amount,
                "document_path": verified_path
            }
        )

        security_info = security_result.get("security", {})
        security_score = security_info.get("security_score", 0)
        risk_level = str(security_info.get("risk_level", "HIGH")).upper()
        security_decision = security_info.get("decision", "REVIEW_REQUIRED")

        # Require the security analyzer's own integrity check to confirm
        # that it checked the server-resolved file.
        analyzer_checks = security_result.get("checks", {})
        analyzer_integrity = analyzer_checks.get("document_integrity", {})

        analyzer_integrity_passed = (
            analyzer_integrity.get("checked") is True
            and analyzer_integrity.get("status") == "VERIFIED"
            and bool(analyzer_integrity.get("hash"))
        )

        log_security_event(
            claim_id=claim_id,
            action="SECURITY_RECHECK_WITH_VERIFIED_DOCUMENT",
            status="COMPLETED" if analyzer_integrity_passed else "BLOCKED",
            risk_level=risk_level,
            security_score=security_score,
            decision=security_decision,
            user="security_analyzer",
            details={
                "integrity_status": analyzer_integrity.get("status", "NOT_CHECKED"),
                "integrity_checked": analyzer_integrity.get("checked", False),
                "document_path_resolved": True
            }
        )

        # Fail closed if the analyzer cannot confirm document integrity.
        if not analyzer_integrity_passed:
            log_security_event(
                claim_id=claim_id,
                action="CLAIM_PROCESSING_PAUSED",
                status="PAUSED",
                risk_level="HIGH",
                security_score=security_score,
                decision="MANUAL_REVIEW",
                user="document_security_gate",
                details={
                    "reason": "Security analyzer did not confirm document integrity."
                }
            )

            return {
                "success": True,
                "claim_id": claim_id,
                "agents": {
                    "security_analyzer": security_result,
                    "document_verification_agent": {
                        "status": document_status,
                        "score": document_score,
                        "document_type": document_type,
                        "integrity": integrity_result,
                        "content_verification": content_result
                    },
                    "eligibility_agent": {"status": "NOT_RUN"},
                    "fraud_detection_agent": {"status": "NOT_RUN"}
                },
                "risk_gate": {
                    "status": "PAUSED",
                    "risk_level": "HIGH",
                    "decision": "MANUAL_REVIEW",
                    "reason": "The security analyzer did not confirm document integrity."
                },
                "final_status": "Document Review",
                "message": "Processing paused. Manual review is required; no claim approval has been made."
            }

        # Reapply the high-risk gate using the updated analysis.
        if risk_level == "HIGH":
            log_security_event(
                claim_id=claim_id,
                action="RISK_GATE",
                status="BLOCKED",
                risk_level="HIGH",
                security_score=security_score,
                decision="MANUAL_REVIEW",
                user="security_gate",
                details={
                    "reason": "High risk detected during the post-verification security analysis."
                }
            )

            return {
                "success": True,
                "claim_id": claim_id,
                "agents": {
                    "security_analyzer": security_result,
                    "document_verification_agent": {
                        "status": document_status,
                        "score": document_score,
                        "document_type": document_type,
                        "integrity": integrity_result,
                        "content_verification": content_result
                    },
                    "eligibility_agent": {"status": "NOT_RUN"},
                    "fraud_detection_agent": {"status": "NOT_RUN"}
                },
                "risk_gate": {
                    "status": "STOPPED",
                    "risk_level": "HIGH",
                    "decision": "MANUAL_REVIEW",
                    "automation_status": "STOPPED",
                    "reason": "High security risk detected after document verification."
                },
                "final_status": "Manual Review Required",
                "message": "Automated processing stopped because high security risk was detected. No claim approval has been made."
            }

        # 6. ELIGIBILITY AGENT
        # ==========================================================

        eligibility_request = type(
            "EligibilityData",
            (),
            {
                "patient_name": data.patient_name,
                "age": data.age,
                "policy_number": data.policy_number,
                "insurance_company": data.insurance_company,
                "hospital_name": data.hospital_name,
                "treatment": data.treatment,
                "claim_amount": data.claim_amount
            }
        )()


        eligibility_result = check_eligibility(
            eligibility_request
        )


        eligibility_status = eligibility_result[
            "eligibility_status"
        ]

        eligibility_score = eligibility_result[
            "eligibility_score"
        ]


        log_security_event(
            claim_id=claim_id,
            action="ELIGIBILITY_ANALYSIS",
            status="COMPLETED",
            risk_level=risk_level,
            security_score=security_score,
            user="eligibility_agent",
            details={
                "eligibility_status": eligibility_status,
                "eligibility_score": eligibility_score
            }
        )


        # ==========================================================
        # 7. FRAUD DETECTION AGENT
        # ==========================================================

        fraud_request = FraudRequest(
            patient_name=data.patient_name,
            age=data.age,
            policy_number=data.policy_number,
            insurance_company=data.insurance_company,
            hospital_name=data.hospital_name,
            treatment=data.treatment,
            claim_amount=data.claim_amount
        )


        fraud_result = detect_fraud(
            fraud_request
        )


        fraud_prediction = fraud_result[
            "prediction"
        ]

        fraud_risk = fraud_result[
            "risk_level"
        ]

        fraud_probability = fraud_result[
            "fraud_probability"
        ]


        log_security_event(
            claim_id=claim_id,
            action="FRAUD_ANALYSIS",
            status="COMPLETED",
            risk_level=risk_level,
            security_score=security_score,
            user="fraud_detection_agent",
            details={
                "prediction": fraud_prediction,
                "fraud_risk": fraud_risk,
                "fraud_probability": fraud_probability
            }
        )


        # ==========================================================
        # 8. DOCUMENT / ELIGIBILITY / FRAUD ASSESSMENT
        # ==========================================================

        if document_status == "Invalid":

            assessment_status = "Document Rejected"

            final_message = (
                "Claim cannot proceed because the uploaded "
                "document failed verification."
            )

        elif fraud_risk == "High":

            assessment_status = "Fraud Investigation"

            final_message = (
                "Potential fraud detected. "
                "Manual investigation is required."
            )

        elif eligibility_status == "Not Eligible":

            assessment_status = "Eligibility Review Required"

            final_message = (
                "The claim failed the initial eligibility checks. "
                "Manual review is required before a claim decision."
            )

        elif eligibility_status == "Manual Review":

            assessment_status = "Manual Review"

            final_message = (
                "The eligibility result requires manual review "
                "before further claim processing."
            )

        elif document_status == "Review Required":

            assessment_status = "Document Review"

            final_message = (
                "Claim requires additional document review."
            )

        elif fraud_risk == "Medium":

            assessment_status = "Manual Review"

            final_message = (
                "Claim requires additional verification "
                "before processing."
            )

        else:

            assessment_status = "Ready for Processing"

            final_message = (
                "Claim passed the initial configured checks. "
                "This is not a claim approval."
            )


        # 9. COMBINED SECURITY, FRAUD AND ASSESSMENT GATE
        # ==========================================================

        fraud_risk_normalized = str(fraud_risk).strip().upper()
        security_risk_normalized = str(risk_level).strip().upper()

        manual_review_required = (
            security_risk_normalized == "HIGH"
            or fraud_risk_normalized == "HIGH"
            or assessment_status in {
                "Document Rejected",
                "Fraud Investigation",
                "Eligibility Review Required",
                "Manual Review",
            }
        )

        additional_verification_required = (
            not manual_review_required
            and (
                security_risk_normalized == "MEDIUM"
                or fraud_risk_normalized == "MEDIUM"
                or assessment_status != "Ready for Processing"
            )
        )

        if manual_review_required:
            gate_decision = "MANUAL_REVIEW"
            automation_status = "RESTRICTED"
            gate_status = "MANUAL_REVIEW_REQUIRED"
            processing_status = "MANUAL_REVIEW"
            gate_reason = (
                "Fraud risk or another claim assessment requires "
                "manual review. No claim approval has been made."
            )

        elif additional_verification_required:
            gate_decision = "ADDITIONAL_VERIFICATION"
            automation_status = "RESTRICTED"
            gate_status = "RESTRICTED"
            processing_status = "ADDITIONAL_VERIFICATION"
            gate_reason = (
                "Additional verification is required before "
                "normal processing. No claim approval has been made."
            )

        else:
            gate_decision = "CONTINUE"
            automation_status = "NORMAL"
            gate_status = "PASSED"
            processing_status = "READY"
            gate_reason = (
                "Configured initial checks passed. "
                "This is not an insurer approval."
            )

        audit_risk_level = (
            "HIGH"
            if "HIGH" in {security_risk_normalized, fraud_risk_normalized}
            else "MEDIUM"
            if "MEDIUM" in {security_risk_normalized, fraud_risk_normalized}
            else "LOW"
        )
        log_security_event(
            claim_id=claim_id,
            action="RISK_GATE",
            status=gate_status,
            risk_level=audit_risk_level,
            security_score=security_score,
            decision=gate_decision,
            user="security_gate",
            details={
                "automation_status": automation_status,
                "fraud_risk": fraud_risk,
                "assessment_status": assessment_status,
                "reason": gate_reason,
            },
        )

        # 10. CLAIM ROUTING
        # ==========================================================

        if data.insurance_company.strip().lower() == "claimcare":
            processing_type = "Internal Processing"
            department = "ClaimCare Internal Insurance Department"
        else:
            processing_type = "External Insurance Processing"
            department = (
                f"{data.insurance_company} Claims Department"
            )

        # 11. CLAIM PROCESSING AUDIT
        # ==========================================================

        log_security_event(
            claim_id=claim_id,
            action="CLAIM_PROCESSING",
            status=processing_status,
            risk_level=audit_risk_level,
            security_score=security_score,
            decision=gate_decision,
            user="orchestrator",
            details={
                "fraud_risk": fraud_risk,
                "assessment_status": assessment_status,
            },
        )

        # 12. FINAL RESPONSE
        # ==========================================================

        return {

            "success": True,

            "agent": "AI Claim Orchestrator",

            "claim_information": {

                "claim_id": claim_id,

                "patient_name": data.patient_name,

                "age": data.age,

                "policy_number": data.policy_number,

                "insurance_company": data.insurance_company,

                "hospital_name": data.hospital_name,

                "treatment": data.treatment,

                "claim_amount": data.claim_amount
            },

            "agents": {

                "security_analyzer": security_result,

                "document_verification_agent": {
                    "status": document_status,
                    "score": document_score,
                    "document_type": document_type
                },

                "eligibility_agent": {

                    "status": eligibility_status,

                    "score": eligibility_score,

                    "checks": eligibility_result[
                        "checks"
                    ]
                },

                "fraud_detection_agent": {

                    "prediction": fraud_prediction,

                    "risk_level": fraud_risk,

                    "fraud_probability": fraud_probability,

                    "recommendation": fraud_result[
                        "recommendation"
                    ]
                }
            },

            "risk_gate": {

                "security_score": security_score,

                "risk_level": risk_level,

                "decision": gate_decision,

                "automation_status": automation_status,

                "status": gate_status,

                "reason": gate_reason,

                "fraud_risk": fraud_risk,

                "assessment_status": assessment_status
            },

            "assessment": {

                "status": assessment_status,

                "message": final_message
            },

            "routing": {

                "processing_type": processing_type,

                "department": department
            },

            "final_status": assessment_status,

            "message": (
                "Claim processed through the "
                "AI Agent Orchestrator with security "
                "risk gating and audit tracking."
            )
        }


    except Exception as e:

        log_security_event(
            claim_id=claim_id,
            action="ORCHESTRATOR_ERROR",
            status="FAILED",
            user="orchestrator",
            details={
                "error": str(e)
            }
        )

        print()
        print("=" * 70)
        print("ORCHESTRATOR ERROR")
        print("=" * 70)
        print(str(e))
        print("=" * 70)

        raise HTTPException(
            status_code=500,
            detail=(
                "Orchestrator processing failed: "
                f"{str(e)}"
            )
        )



