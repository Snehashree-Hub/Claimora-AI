from fastapi import APIRouter
from pathlib import Path
import pandas as pd

router = APIRouter(
    prefix="/api/datasets",
    tags=["Dataset Analytics"]
)

BASE_DIR = Path(__file__).resolve().parents[2]

CLAIMS_FILE = BASE_DIR / "datasets" / "health_insurance_claims.csv.csv"
FRAUD_FILE = BASE_DIR / "ml_models" / "health_insurance_claims_fraud.csv.csv"


@router.get("/summary")
def dataset_summary():

    result = {
        "success": True,
        "data": {
            "claims_dataset": {},
            "fraud_dataset": {}
        }
    }

    # Claims dataset
    if CLAIMS_FILE.exists():
        df = pd.read_csv(CLAIMS_FILE)

        fraud_count = 0
        normal_count = 0

        if "Is_Fraudulent" in df.columns:
            fraud_count = int(
                pd.to_numeric(
                    df["Is_Fraudulent"],
                    errors="coerce"
                ).fillna(0).sum()
            )
            normal_count = len(df) - fraud_count

        avg_amount = 0

        if "Claim_Amount" in df.columns:
            avg_amount = float(
                pd.to_numeric(
                    df["Claim_Amount"],
                    errors="coerce"
                ).fillna(0).mean()
            )

        result["data"]["claims_dataset"] = {
            "records": int(len(df)),
            "columns": int(len(df.columns)),
            "fraudulent_claims": fraud_count,
            "normal_claims": normal_count,
            "average_claim_amount": round(avg_amount, 2),
            "columns_list": df.columns.tolist(),
            "file": str(CLAIMS_FILE)
        }

    else:
        result["data"]["claims_dataset"] = {
            "records": 0,
            "columns": 0,
            "fraudulent_claims": 0,
            "normal_claims": 0,
            "average_claim_amount": 0,
            "columns_list": [],
            "file": str(CLAIMS_FILE),
            "error": "Claims dataset not found"
        }

    # Fraud dataset
    if FRAUD_FILE.exists():
        fraud_df = pd.read_csv(FRAUD_FILE)

        fraud_count = 0
        normal_count = 0

        if "fraud_label" in fraud_df.columns:
            labels = pd.to_numeric(
                fraud_df["fraud_label"],
                errors="coerce"
            ).fillna(0)

            fraud_count = int((labels == 1).sum())
            normal_count = int((labels == 0).sum())

        avg_amount = 0

        if "claim_amount" in fraud_df.columns:
            avg_amount = float(
                pd.to_numeric(
                    fraud_df["claim_amount"],
                    errors="coerce"
                ).fillna(0).mean()
            )

        result["data"]["fraud_dataset"] = {
            "records": int(len(fraud_df)),
            "columns": int(len(fraud_df.columns)),
            "fraud_records": fraud_count,
            "normal_records": normal_count,
            "average_claim_amount": round(avg_amount, 2),
            "columns_list": fraud_df.columns.tolist(),
            "file": str(FRAUD_FILE)
        }

    else:
        result["data"]["fraud_dataset"] = {
            "records": 0,
            "columns": 0,
            "fraud_records": 0,
            "normal_records": 0,
            "average_claim_amount": 0,
            "columns_list": [],
            "file": str(FRAUD_FILE),
            "error": "Fraud dataset not found"
        }

    return result
