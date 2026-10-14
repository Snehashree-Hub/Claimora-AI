from pathlib import Path
import pandas as pd


# ============================================================
# DATASET PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

CLAIMS_DATASET = (
    BASE_DIR
    / "datasets"
    / "health_insurance_claims.csv.csv"
)

FRAUD_DATASET = (
    BASE_DIR
    / "ml_models"
    / "health_insurance_claims_fraud.csv.csv"
)


# ============================================================
# LOAD CLAIMS DATASET
# ============================================================

def load_claims_dataset():

    if not CLAIMS_DATASET.exists():
        raise FileNotFoundError(
            f"Claims dataset not found: {CLAIMS_DATASET}"
        )

    return pd.read_csv(CLAIMS_DATASET)


# ============================================================
# LOAD FRAUD DATASET
# ============================================================

def load_fraud_dataset():

    if not FRAUD_DATASET.exists():
        raise FileNotFoundError(
            f"Fraud dataset not found: {FRAUD_DATASET}"
        )

    return pd.read_csv(FRAUD_DATASET)


# ============================================================
# DATASET SUMMARY
# ============================================================

def get_dataset_summary():

    claims_df = load_claims_dataset()
    fraud_df = load_fraud_dataset()

    # --------------------------------------------------------
    # Claims dataset fraud statistics
    # --------------------------------------------------------

    fraudulent_claims = 0
    normal_claims = 0

    if "Is_Fraudulent" in claims_df.columns:

        fraud_values = (
            claims_df["Is_Fraudulent"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        fraudulent_claims = int(
            fraud_values.isin(
                ["true", "1", "yes"]
            ).sum()
        )

        normal_claims = int(
            fraud_values.isin(
                ["false", "0", "no"]
            ).sum()
        )

    # --------------------------------------------------------
    # Fraud dataset statistics
    # --------------------------------------------------------

    fraud_records = 0
    normal_records = 0

    if "fraud_label" in fraud_df.columns:

        fraud_records = int(
            (fraud_df["fraud_label"] == 1).sum()
        )

        normal_records = int(
            (fraud_df["fraud_label"] == 0).sum()
        )

    # --------------------------------------------------------
    # Average claim amount
    # --------------------------------------------------------

    average_claim_amount = 0

    if "Claim_Amount" in claims_df.columns:

        average_claim_amount = round(
            float(
                pd.to_numeric(
                    claims_df["Claim_Amount"],
                    errors="coerce"
                ).mean()
            ),
            2
        )

    fraud_average_amount = 0

    if "claim_amount" in fraud_df.columns:

        fraud_average_amount = round(
            float(
                pd.to_numeric(
                    fraud_df["claim_amount"],
                    errors="coerce"
                ).mean()
            ),
            2
        )

    return {

        "claims_dataset": {

            "records": len(claims_df),

            "columns": len(
                claims_df.columns
            ),

            "fraudulent_claims":
                fraudulent_claims,

            "normal_claims":
                normal_claims,

            "average_claim_amount":
                average_claim_amount,

            "columns_list":
                claims_df.columns.tolist()
        },

        "fraud_dataset": {

            "records": len(fraud_df),

            "columns": len(
                fraud_df.columns
            ),

            "fraud_records":
                fraud_records,

            "normal_records":
                normal_records,

            "average_claim_amount":
                fraud_average_amount,

            "columns_list":
                fraud_df.columns.tolist()
        }
    }


# ============================================================
# GET CLAIM RECORDS
# ============================================================

def get_claims(
    limit=100,
    offset=0
):

    df = load_claims_dataset()

    df = df.iloc[
        offset:
        offset + limit
    ]

    df = df.where(
        pd.notnull(df),
        None
    )

    return df.to_dict(
        orient="records"
    )


# ============================================================
# GET FRAUD RECORDS
# ============================================================

def get_fraud_records(
    limit=100,
    offset=0
):

    df = load_fraud_dataset()

    df = df.iloc[
        offset:
        offset + limit
    ]

    df = df.where(
        pd.notnull(df),
        None
    )

    return df.to_dict(
        orient="records"
    )


# ============================================================
# FIND FRAUD CLAIM
# ============================================================

def find_fraud_claim(
    claim_id
):

    df = load_fraud_dataset()

    if "claim_id" not in df.columns:
        return None

    result = df[
        df["claim_id"]
        .astype(str)
        .str.lower()
        ==
        str(claim_id).lower()
    ]

    if result.empty:
        return None

    row = result.iloc[0]

    row = row.where(
        pd.notnull(row),
        None
    )

    return row.to_dict()


# ============================================================
# FRAUD RISK CALCULATION
# ============================================================

def calculate_fraud_risk(
    claim_amount=0,
    previous_claims=0,
    submission_delay=0,
    high_risk_procedure=0,
    document_mismatch=0,
    anomaly_score=0
):

    score = 0

    # --------------------------------------------------------
    # Claim amount
    # --------------------------------------------------------

    if claim_amount >= 1000000:

        score += 20

    elif claim_amount >= 500000:

        score += 10

    # --------------------------------------------------------
    # Previous claims
    # --------------------------------------------------------

    if previous_claims >= 8:

        score += 15

    elif previous_claims >= 5:

        score += 8

    # --------------------------------------------------------
    # Submission delay
    # --------------------------------------------------------

    if submission_delay >= 30:

        score += 15

    elif submission_delay >= 15:

        score += 8

    # --------------------------------------------------------
    # High-risk procedure
    # --------------------------------------------------------

    if int(high_risk_procedure) == 1:

        score += 20

    # --------------------------------------------------------
    # Document mismatch
    # --------------------------------------------------------

    if int(document_mismatch) == 1:

        score += 20

    # --------------------------------------------------------
    # Anomaly score
    # --------------------------------------------------------

    try:

        anomaly = float(
            anomaly_score
        )

        if anomaly >= 0.75:

            score += 20

        elif anomaly >= 0.50:

            score += 10

    except Exception:

        pass

    # Maximum 100
    score = min(
        score,
        100
    )

    # --------------------------------------------------------
    # Risk level
    # --------------------------------------------------------

    if score >= 60:

        risk = "High"

    elif score >= 30:

        risk = "Medium"

    else:

        risk = "Low"

    return {

        "risk": risk,

        "score": score
    }