import io
import re
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pypdf import PdfReader


router = APIRouter(
    prefix="/api/documents",
    tags=["Document Verification"]
)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024

MEDICAL_KEYWORDS = [
    "hospital", "patient", "medical", "insurance", "policy",
    "claim", "treatment", "diagnosis", "bill", "doctor",
    "discharge", "prescription", "appendectomy", "surgery"
]


def extract_pdf_text(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))

        if reader.is_encrypted:
            try:
                if not reader.decrypt(""):
                    return ""
            except Exception:
                return ""

        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )
    except Exception:
        return ""


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def normalize_identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def amount_found(amount: str, text: str) -> bool:
    """
    Compare an amount using numeric tokens rather than unsafe
    substring matching (for example, 500 must not match 15000).
    """
    cleaned = amount.replace(",", "").strip()

    if not cleaned:
        return False

    try:
        number = float(cleaned)
    except ValueError:
        return normalize_text(cleaned) in normalize_text(text)

    if number < 0:
        return False

    formatted = f"{number:.2f}".rstrip("0").rstrip(".")
    escaped = re.escape(formatted)

    # Accept common optional decimal zeros and comma grouping.
    pattern = (
        r"(?<![\d.])"
        + escaped.replace(r"\.", r"\.(?:0+)?")
        + r"(?!\d)"
    )

    return bool(re.search(pattern, text.replace(",", "")))




def verify_stored_document_content(
    file_bytes: bytes,
    filename: str,
    patient_name: str = "",
    policy_number: str = "",
    claim_amount: str = ""
) -> dict:
    """
    Content checks for a securely stored PDF.
    Fingerprint integrity must be verified separately.
    This function does not establish authenticity.
    """
    extension = Path(filename).suffix.lower()

    if extension != ".pdf":
        return {
            "success": True,
            "verification_status": "Review Required",
            "score": 0,
            "document_type": "Unsupported for automatic content verification",
            "failed_checks": ["PDF text verification unavailable for this file type"],
            "message": "Only PDF text extraction is implemented in this verification flow."
        }

    if not file_bytes:
        return {
            "success": True,
            "verification_status": "Review Required",
            "score": 0,
            "document_type": "Unknown",
            "failed_checks": ["Empty document"],
            "message": "The stored document is empty."
        }

    if len(file_bytes) > MAX_FILE_SIZE:
        return {
            "success": True,
            "verification_status": "Review Required",
            "score": 0,
            "document_type": "Unknown",
            "failed_checks": ["File size"],
            "message": "The stored document exceeds the configured size limit."
        }

    extracted_text = extract_pdf_text(file_bytes)
    normalized = normalize_text(extracted_text)
    score = 25
    failed = []

    keywords = [
        word for word in MEDICAL_KEYWORDS
        if word in normalized
    ]

    if not normalized:
        status = "Review Required"
        failed.append("Readable Content")
        message = "PDF text could not be extracted. Manual review or OCR is required."
    elif len(keywords) < 2:
        status = "Invalid"
        failed.append("Claim Document Relevance")
        message = "Insufficient medical/insurance keywords were detected."
    else:
        score += 25
        message = "PDF text and configured claim-detail checks completed."

        if patient_name.strip():
            if normalize_text(patient_name) in normalized:
                score += 15
            else:
                failed.append("Patient Name")

        if policy_number.strip():
            expected = normalize_identifier(policy_number)
            actual = normalize_identifier(extracted_text)
            if expected and expected in actual:
                score += 15
            else:
                failed.append("Policy Number")

        if str(claim_amount).strip():
            if amount_found(str(claim_amount), extracted_text):
                score += 20
            else:
                failed.append("Claim Amount")

        if failed:
            status = "Review Required"
            message = "One or more claim-detail checks require manual review."
        else:
            status = "Verified"
            message = (
                "Configured PDF text checks passed. This does not establish "
                "document authenticity or claim approval."
            )

    if "discharge summary" in normalized:
        document_type = "Discharge Summary"
    elif "prescription" in normalized:
        document_type = "Medical Prescription"
    elif "medical bill" in normalized or "hospital bill" in normalized:
        document_type = "Medical Bill"
    elif "insurance claim" in normalized:
        document_type = "Insurance Claim Document"
    elif "invoice" in normalized or "bill no" in normalized:
        document_type = "Medical Bill / Invoice"
    else:
        document_type = "Medical / Insurance Document"

    return {
        "success": True,
        "verification_status": status,
        "score": min(score, 100),
        "document_type": document_type,
        "failed_checks": failed,
        "extracted_text_available": bool(normalized),
        "keyword_matches": keywords[:10],
        "message": message
    }


@router.post("/verify")
async def verify_document(
    file: UploadFile = File(...),
    patient_name: str = Form(""),
    policy_number: str = Form(""),
    claim_amount: str = Form("")
):
    filename = Path(file.filename or "").name

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, JPG, JPEG and PNG files are allowed."
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size cannot exceed 10 MB."
        )

    file_size_mb = round(len(file_bytes) / (1024 * 1024), 2)
    checks = []
    score = 0
    failed_checks = []

    checks.append({
        "name": "File Type",
        "status": "Passed",
        "details": f"{extension.upper()} file accepted"
    })
    score += 15

    checks.append({
        "name": "File Size",
        "status": "Passed",
        "details": f"{file_size_mb} MB; within the 10 MB limit"
    })
    score += 10

    if extension == ".pdf":
        extracted_text = extract_pdf_text(file_bytes)
    else:
        # Image OCR is not implemented in this endpoint yet.
        extracted_text = ""

    normalized_text = normalize_text(extracted_text)

    if normalized_text:
        checks.append({
            "name": "Readable Content",
            "status": "Passed",
            "details": "Text extracted from PDF successfully"
        })
        score += 20
    elif extension == ".pdf":
        checks.append({
            "name": "Readable Content",
            "status": "Review Required",
            "details": (
                "No readable PDF text found. The PDF may be scanned, "
                "image-only, encrypted, or unreadable."
            )
        })
        failed_checks.append("Readable Content")
    else:
        checks.append({
            "name": "Readable Content",
            "status": "Review Required",
            "details": (
                "Image accepted, but OCR is not enabled. "
                "Document text must be reviewed or extracted separately."
            )
        })
        failed_checks.append("Readable Content")

    keyword_matches = [
        keyword for keyword in MEDICAL_KEYWORDS
        if keyword in normalized_text
    ]

    if len(keyword_matches) >= 2:
        checks.append({
            "name": "Claim Document Relevance",
            "status": "Passed",
            "details": (
                "Medical/insurance keywords detected: "
                + ", ".join(keyword_matches[:6])
            )
        })
        score += 20
    else:
        checks.append({
            "name": "Claim Document Relevance",
            "status": "Review Required",
            "details": (
                "Insufficient medical/insurance keywords were detected. "
                "Manual review is needed."
            )
        })
        failed_checks.append("Claim Document Relevance")

    if patient_name.strip():
        expected = normalize_text(patient_name)
        found = expected in normalized_text if normalized_text else False

        checks.append({
            "name": "Patient Name",
            "status": "Passed" if found else "Review Required",
            "details": (
                "Patient name found in extracted text."
                if found else
                "Patient name could not be matched to extracted text."
            )
        })

        if found:
            score += 15
        else:
            failed_checks.append("Patient Name")

    if policy_number.strip():
        expected = normalize_identifier(policy_number)
        actual = normalize_identifier(extracted_text)
        found = bool(expected) and expected in actual

        checks.append({
            "name": "Policy Number",
            "status": "Passed" if found else "Review Required",
            "details": (
                "Policy number found in extracted text."
                if found else
                "Policy number could not be matched to extracted text."
            )
        })

        if found:
            score += 10
        else:
            failed_checks.append("Policy Number")

    if claim_amount.strip():
        found = amount_found(claim_amount, extracted_text)

        checks.append({
            "name": "Claim Amount",
            "status": "Passed" if found else "Review Required",
            "details": (
                "Claim amount appears in extracted text."
                if found else
                "Claim amount could not be matched to extracted text."
            )
        })

        if found:
            score += 10
        else:
            failed_checks.append("Claim Amount")

    if "discharge summary" in normalized_text:
        document_type = "Discharge Summary"
    elif "prescription" in normalized_text:
        document_type = "Medical Prescription"
    elif "medical bill" in normalized_text or "hospital bill" in normalized_text:
        document_type = "Medical Bill"
    elif "insurance claim" in normalized_text:
        document_type = "Insurance Claim Document"
    elif "invoice" in normalized_text or "bill no" in normalized_text:
        document_type = "Medical Bill / Invoice"
    else:
        document_type = "Medical / Insurance Document"

    if not normalized_text:
        verification_status = "Review Required"
        message = (
            "The file passed basic upload checks, but readable content "
            "could not be confirmed. Manual review or OCR is required."
        )
    elif len(keyword_matches) < 2:
        verification_status = "Invalid"
        message = (
            "The document could not be identified as a medical or "
            "insurance claim document based on extracted text."
        )
    elif failed_checks:
        verification_status = "Review Required"
        message = (
            "Some document checks need manual review: "
            + ", ".join(failed_checks)
            + "."
        )
    else:
        verification_status = "Verified"
        message = (
            "All configured text and claim-detail checks passed. "
            "This does not establish document authenticity or claim approval."
        )

    return {
        "success": True,
        "verification_status": verification_status,
        "score": score,
        "document_type": document_type,
        "filename": filename,
        "file_size_mb": file_size_mb,
        "checks": checks,
        "failed_checks": failed_checks,
        "extracted_text_available": bool(normalized_text),
        "ocr_required": extension in {".jpg", ".jpeg", ".png"}
            or not bool(normalized_text),
        "message": message
    }
