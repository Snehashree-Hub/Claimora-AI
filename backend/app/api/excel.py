from pathlib import Path
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/excel", tags=["Excel"])

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
EXCEL_FILE = DATA_DIR / "claims.xlsx"

DATA_DIR.mkdir(parents=True, exist_ok=True)

COLUMNS = [
    "claim_id",
    "policy_id",
    "patient_name",
    "patient_age",
    "email",
    "insurance_company",
    "claim_amount",
    "diagnosis",
    "hospital_name",
    "doctor_name",
    "treatment_date",
    "description",
    "status",
    "fraud_risk",
    "created_at",
    "documents",
    "eligibility_status",
    "document_status",
    "email_status",
]

ALIASES = {
    "claim_id": ["Claim ID"],
    "policy_id": ["Policy ID", "Policy Number", "policy_number"],
    "patient_name": ["Patient Name"],
    "patient_age": ["Age", "Patient Age"],
    "email": ["Email", "Email Address"],
    "insurance_company": ["Insurance Company", "Insurer"],
    "claim_amount": ["Claim Amount", "Amount"],
    "diagnosis": ["Treatment", "Diagnosis"],
    "hospital_name": ["Hospital Name", "Hospital"],
    "doctor_name": ["Doctor Name"],
    "treatment_date": ["Treatment Date"],
    "description": ["Description"],
    "status": ["Overall Status", "Claim Status", "Status"],
    "fraud_risk": ["Fraud Risk"],
    "created_at": ["Submitted Date", "Created At"],
    "documents": ["Documents"],
    "eligibility_status": ["Eligibility"],
    "document_status": ["Document Status", "Documents Status"],
    "email_status": ["Email Status"],
}


def clean_value(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return value


def normalize_claim(claim: dict):
    return {
        column: clean_value(claim.get(column, ""))
        for column in COLUMNS
    }


def normalize_dataframe(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=COLUMNS)

    normalized_rows = []

    for _, row in df.iterrows():
        source = row.to_dict()
        result = {}

        for column in COLUMNS:
            value = clean_value(source.get(column, ""))

            if value == "":
                for alias in ALIASES.get(column, []):
                    candidate = clean_value(source.get(alias, ""))
                    if candidate != "":
                        value = candidate
                        break

            result[column] = value

        # Skip completely empty spreadsheet rows.
        if not any(str(value).strip() for value in result.values()):
            continue

        # Recover the clearly shifted legacy claim row when its
        # values can be identified by their formats.
        legacy_name = str(clean_value(source.get("Patient Name", "")))
        legacy_age = str(clean_value(source.get("Age", "")))

        if (
            legacy_name.startswith("CLM-")
            and legacy_age.startswith("POL-")
        ):
            result["claim_id"] = legacy_name
            result["policy_id"] = legacy_age
            result["patient_name"] = clean_value(
                source.get("Insurance Company", "")
            )
            result["patient_age"] = clean_value(
                source.get("Hospital Name", "")
            )
            result["insurance_company"] = clean_value(
                source.get("Claim Amount", "")
            )
            result["hospital_name"] = clean_value(
                source.get("Eligibility", "")
            )
            result["diagnosis"] = clean_value(
                source.get("Documents", "")
            )
            result["claim_amount"] = clean_value(
                source.get("Fraud Risk", "")
            )
            result["status"] = clean_value(
                source.get("Overall Status", "")
            )
            result["created_at"] = clean_value(
                source.get("Unnamed: 18", "")
            )
            result["eligibility_status"] = clean_value(
                source.get("Email Status", "")
            )
            result["document_status"] = clean_value(
                source.get("Unnamed: 16", "")
            )

        normalized_rows.append(result)

    return pd.DataFrame(normalized_rows, columns=COLUMNS)


def read_claims():
    if not EXCEL_FILE.exists():
        return pd.DataFrame(columns=COLUMNS)

    try:
        raw_df = pd.read_excel(EXCEL_FILE)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read claims Excel file: {exc}",
        )

    return normalize_dataframe(raw_df)


def write_claims(df):
    try:
        normalize_dataframe(df).to_excel(EXCEL_FILE, index=False)
    except PermissionError:
        raise HTTPException(
            status_code=503,
            detail="Close claims.xlsx in Excel and retry.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to save claims Excel file: {exc}",
        )


def ensure_excel():
    if not EXCEL_FILE.exists():
        write_claims(pd.DataFrame(columns=COLUMNS))


def save_claim_to_excel(claim: dict):
    ensure_excel()
    df = read_claims()
    new_row = normalize_claim(claim)

    claim_id = str(new_row["claim_id"])
    if not claim_id.strip():
        raise HTTPException(
            status_code=400,
            detail="claim_id is required.",
        )

    if not df.empty:
        existing_ids = df["claim_id"].fillna("").astype(str).str.strip()
        if existing_ids.str.casefold().eq(claim_id.strip().casefold()).any():
            raise HTTPException(
                status_code=409,
                detail=f"Claim ID '{claim_id}' already exists. Use a unique claim ID.",
            )

    df = pd.concat(
        [df, pd.DataFrame([new_row])],
        ignore_index=True,
    )

    write_claims(df)

    return {
        "success": True,
        "claim_id": claim_id,
        "file": str(EXCEL_FILE),
        "records": len(df),
    }


def update_claim_in_excel(claim_id: str, updates: dict):
    ensure_excel()
    df = read_claims()

    mask = df["claim_id"].astype(str) == str(claim_id)

    if not mask.any():
        raise HTTPException(
            status_code=404,
            detail=f"Claim {claim_id} not found in Excel.",
        )

    for key, value in updates.items():
        if key not in COLUMNS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported claim field: {key}",
            )

        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)

        df.loc[mask, key] = clean_value(value)

        if key == "status":
            df.loc[mask, "status"] = value

    write_claims(df)

    return {
        "success": True,
        "claim_id": claim_id,
        "updated": updates,
    }


@router.get("/status")
def excel_status():
    ensure_excel()

    try:
        df = read_claims()
        return {
            "connected": True,
            "file": str(EXCEL_FILE),
            "records": len(df),
            "columns": len(COLUMNS),
            "last_modified": datetime.fromtimestamp(
                EXCEL_FILE.stat().st_mtime
            ).isoformat(),
        }
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/claims")
def excel_claims():
    ensure_excel()
    df = read_claims()
    df = df.fillna("")

    return {
        "success": True,
        "records": df.to_dict(orient="records"),
    }
