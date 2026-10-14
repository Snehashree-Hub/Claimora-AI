import re
from pypdf import PdfReader


def extract_pdf_text(file_path: str) -> str:
    """
    Extract text from an uploaded PDF.
    """

    try:
        reader = PdfReader(file_path)

        pages = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages.append(text)

        return "\n".join(pages).strip()

    except Exception as e:
        return f"PDF extraction error: {str(e)}"


def find_value(text: str, labels):
    """
    Search for values following common field labels.
    """

    for label in labels:

        pattern = rf"{re.escape(label)}\s*[:\-]\s*(.+)"

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(1).strip()

    return None


def verify_claim_document(
    file_path: str,
    patient_name: str,
    policy_number: str,
    claim_amount: float
):
    """
    AI-style rule-based document verification agent.
    """

    text = extract_pdf_text(file_path)

    if text.startswith("PDF extraction error"):
        return {
            "verified": False,
            "status": "Failed",
            "score": 0,
            "message": text,
            "checks": []
        }

    if not text:

        return {
            "verified": False,
            "status": "Failed",
            "score": 0,
            "message": "No readable text found in PDF.",
            "checks": []
        }

    checks = []

    # -------------------------------------------------
    # CHECK 1 — Patient Name
    # -------------------------------------------------

    patient_match = patient_name.lower() in text.lower()

    checks.append({
        "check": "Patient Name",
        "status": "Passed" if patient_match else "Failed",
        "details": (
            "Patient name found in document."
            if patient_match
            else "Patient name not found in document."
        )
    })

    # -------------------------------------------------
    # CHECK 2 — Policy Number
    # -------------------------------------------------

    if policy_number:

        policy_match = policy_number.lower() in text.lower()

        checks.append({
            "check": "Policy Number",
            "status": "Passed" if policy_match else "Warning",
            "details": (
                "Policy number found in document."
                if policy_match
                else "Policy number not found in document."
            )
        })

    else:

        checks.append({
            "check": "Policy Number",
            "status": "Skipped",
            "details": "Policy number was not provided."
        })

    # -------------------------------------------------
    # CHECK 3 — Claim Amount
    # -------------------------------------------------

    amount_string = f"{claim_amount:.0f}"

    amount_match = (
        amount_string in text.replace(",", "")
    )

    checks.append({
        "check": "Claim Amount",
        "status": "Passed" if amount_match else "Warning",
        "details": (
            "Claim amount found in document."
            if amount_match
            else "Claim amount was not clearly found."
        )
    })

    # -------------------------------------------------
    # CHECK 4 — Medical keywords
    # -------------------------------------------------

    medical_keywords = [
        "hospital",
        "treatment",
        "diagnosis",
        "patient",
        "doctor",
        "medical",
        "bill",
        "claim"
    ]

    found_keywords = [
        word
        for word in medical_keywords
        if word.lower() in text.lower()
    ]

    medical_document = len(found_keywords) >= 3

    checks.append({
        "check": "Medical Document",
        "status": "Passed" if medical_document else "Warning",
        "details": (
            f"Detected medical keywords: {', '.join(found_keywords)}"
            if found_keywords
            else "Medical information could not be identified."
        )
    })

    # -------------------------------------------------
    # CHECK 5 — Required claim information
    # -------------------------------------------------

    required_fields = [
        "patient",
        "hospital",
        "treatment",
        "claim"
    ]

    found_fields = [
        field
        for field in required_fields
        if field.lower() in text.lower()
    ]

    complete_document = len(found_fields) >= 3

    checks.append({
        "check": "Required Information",
        "status": "Passed" if complete_document else "Warning",
        "details": (
            "Required claim information detected."
            if complete_document
            else "Some required claim information appears to be missing."
        )
    })

    # -------------------------------------------------
    # DOCUMENT SCORE
    # -------------------------------------------------

    passed = sum(
        1
        for check in checks
        if check["status"] == "Passed"
    )

    total = sum(
        1
        for check in checks
        if check["status"] != "Skipped"
    )

    score = int(
        (passed / total) * 100
    ) if total else 0

    # -------------------------------------------------
    # FINAL STATUS
    # -------------------------------------------------

    if score >= 80:

        status = "Verified"
        verified = True
        message = "Claim document successfully verified."

    elif score >= 50:

        status = "Review Required"
        verified = False
        message = "Document requires manual review."

    else:

        status = "Rejected"
        verified = False
        message = "Document verification failed."

    return {
        "verified": verified,
        "status": status,
        "score": score,
        "message": message,
        "checks": checks,
        "extracted_text_preview": text[:2000]
    }