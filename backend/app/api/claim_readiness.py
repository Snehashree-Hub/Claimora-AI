import re
from io import BytesIO
from datetime import datetime, timezone
import pymupdf
from fastapi import APIRouter, File, Form, HTTPException, UploadFile


router = APIRouter(
    prefix="/api/claim-readiness",
    tags=["Claim Readiness Twin"],
)

MAX_FILE_SIZE = 10 * 1024 * 1024

POLICY_CHECKS = {
    "waiting_period": {
        "label": "Waiting period",
        "keywords": [
            "waiting period",
            "initial waiting",
            "specific waiting",
            "pre-existing disease",
            "pre existing disease",
        ],
        "action": (
            "Ask the insurer to confirm whether the waiting period "
            "applies to the planned treatment."
        ),
    },
    "exclusions": {
        "label": "Policy exclusions",
        "keywords": [
            "exclusion",
            "excluded treatment",
            "not covered",
            "permanent exclusion",
        ],
        "action": (
            "Review the applicable exclusion clause with the insurer "
            "before relying on coverage."
        ),
    },
    "sub_limits": {
        "label": "Sub-limits and expense limits",
        "keywords": [
            "sub-limit",
            "sub limit",
            "room rent",
            "limit per hospitalization",
            "maximum payable",
            "specified limit",
        ],
        "action": (
            "Confirm the applicable limit and possible out-of-pocket "
            "expenses with the insurer."
        ),
    },
    "copayment": {
        "label": "Co-payment and deductible",
        "keywords": [
            "co-payment",
            "copayment",
            "co payment",
            "deductible",
        ],
        "action": (
            "Confirm any applicable co-payment or deductible and "
            "your estimated share of expenses."
        ),
    },
    "pre_authorisation": {
        "label": "Pre-authorisation",
        "keywords": [
            "pre-authorisation",
            "pre authorisation",
            "pre-authorization",
            "pre authorization",
            "cashless authorization",
            "cashless authorisation",
        ],
        "action": (
            "Ask the hospital and insurer whether pre-authorisation "
            "is required for this treatment."
        ),
    },
}


def extract_policy_pages(pdf_bytes: bytes):
    pages = []

    try:
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as document:
            if document.is_encrypted:
                raise HTTPException(
                    status_code=400,
                    detail="Password-protected PDFs are not supported yet.",
                )

            if document.page_count == 0:
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded PDF has no pages.",
                )

            for page_index, page in enumerate(document):
                text = page.get_text("text").strip()

                pages.append({
                    "page": page_index + 1,
                    "text": text,
                })

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to read this PDF: {str(exc)}",
        ) from exc

    return pages


def find_policy_evidence(pages, keywords):
    matches = []

    for page in pages:
        text = page["text"]

        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
            sentence = sentence.strip()

            if not sentence:
                continue

            lowered = sentence.casefold()

            if any(keyword in lowered for keyword in keywords):
                matches.append({
                    "page": page["page"],
                    "excerpt": sentence[:500],
                })

                if len(matches) >= 5:
                    return matches

    return matches


@router.get("/health")
def claim_readiness_health():
    return {
        "success": True,
        "module": "Claimora AI Claim Readiness Twin",
        "status": "healthy",
        "policy_pdf_analysis": True,
        "page_references": True,
        "rule_engine": "keyword-based preliminary screening",
    }


@router.post("/analyze")
async def analyze_claim_readiness(
    policy_pdf: UploadFile = File(...),
    planned_treatment: str = Form(...),
    hospital_name: str = Form(...),
    city: str = Form(""),
    estimated_expense: float = Form(0),
):
    filename = (policy_pdf.filename or "").strip()

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a policy PDF file.",
        )

    if not planned_treatment.strip() or not hospital_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Treatment and hospital name are required.",
        )

    if estimated_expense < 0:
        raise HTTPException(
            status_code=400,
            detail="Estimated expense cannot be negative.",
        )

    pdf_bytes = await policy_pdf.read(MAX_FILE_SIZE + 1)

    if not pdf_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF is empty.",
        )

    if len(pdf_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="PDF size must not exceed 10 MB.",
        )

    if not pdf_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file does not appear to be a valid PDF.",
        )

    pages = extract_policy_pages(pdf_bytes)
    extracted_text = "\n".join(page["text"] for page in pages).strip()

    if not extracted_text:
        raise HTTPException(
            status_code=422,
            detail=(
                "No readable text was extracted. This PDF may be scanned. "
                "OCR support is required before policy analysis."
            ),
        )

    findings = []
    evidence_count = 0

    for check_id, config in POLICY_CHECKS.items():
        evidence = find_policy_evidence(
            pages,
            config["keywords"],
        )

        if evidence:
            evidence_count += 1
            findings.append({
                "check_id": check_id,
                "label": config["label"],
                "status": "REVIEW_REQUIRED",
                "message": (
                    "Related wording was found. Its actual applicability "
                    "to this treatment has not been determined."
                ),
                "evidence": evidence,
                "next_action": config["action"],
            })
        else:
            findings.append({
                "check_id": check_id,
                "label": config["label"],
                "status": "NOT_IDENTIFIED",
                "message": (
                    "No matching wording was identified by this "
                    "keyword-based scan. This does not mean the "
                    "condition is absent from the policy."
                ),
                "evidence": [],
                "next_action": config["action"],
            })

    if any(page["text"] for page in pages):
        extraction_status = "TEXT_EXTRACTED"
    else:
        extraction_status = "NO_READABLE_TEXT"

    return {
        "success": True,
        "module": "Claimora AI Claim Readiness Twin",
        "analysis_id": datetime.now(timezone.utc).strftime(
            "RDY-%Y%m%dT%H%M%S-%fZ"
        ),
        "readiness_status": "NEEDS_REVIEW",
        "decision_notice": (
            "This is a preliminary document screening, not a coverage "
            "decision, medical opinion, pre-authorisation, or guarantee "
            "of claim approval."
        ),
        "inputs": {
            "policy_filename": filename,
            "planned_treatment": planned_treatment.strip(),
            "hospital_name": hospital_name.strip(),
            "city": city.strip(),
            "estimated_expense": estimated_expense,
            "currency": "INR",
        },
        "document_analysis": {
            "status": extraction_status,
            "pages_read": len(pages),
            "characters_extracted": len(extracted_text),
            "matching_categories": evidence_count,
            "analysis_method": "PDF text extraction and keyword screening",
        },
        "findings": findings,
        "next_actions": [
            {
                "priority": "HIGH",
                "action": (
                    "Confirm treatment coverage, applicable waiting "
                    "periods and exclusions with the insurer."
                ),
                "responsible_party": "User / Insurer",
                "status": "PENDING",
            },
            {
                "priority": "HIGH",
                "action": (
                    "Confirm pre-authorisation requirements and hospital "
                    "network status with the hospital and insurer."
                ),
                "responsible_party": "User / Hospital / Insurer",
                "status": "PENDING",
            },
            {
                "priority": "MEDIUM",
                "action": (
                    "Request a written estimate and confirm applicable "
                    "limits, co-payment and required documents."
                ),
                "responsible_party": "User / Hospital / Insurer",
                "status": "PENDING",
            },
        ],
        "limitations": [
            (
                "This initial version uses keyword matching; it does not "
                "yet interpret every policy clause using the Groq LLM."
            ),
            (
                "It does not independently verify current insurer rules, "
                "network status, waiting-period completion or claim eligibility."
            ),
            (
                "Scanned PDFs require OCR. Only readable extracted text "
                "can be analysed."
            ),
        ],
    }

