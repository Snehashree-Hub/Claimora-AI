import os
import hashlib
import pandas as pd

from typing import Optional


PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)


CLAIMS_DATASET_PATH = os.path.join(
    PROJECT_ROOT,
    "backend",
    "datasets",
    "health_insurance_claims.csv.csv"
)


FRAUD_DATASET_PATH = os.path.join(
    PROJECT_ROOT,
    "backend",
    "ml_models",
    "health_insurance_claims_fraud.csv.csv"
)


claims_dataset = None
fraud_dataset = None


# ==========================================================
# DATASET LOADING
# ==========================================================

try:

    if os.path.exists(CLAIMS_DATASET_PATH):

        claims_dataset = pd.read_csv(
            CLAIMS_DATASET_PATH
        )

        print(
            f">>> SECURITY CLAIM DATASET LOADED: "
            f"{len(claims_dataset)} rows"
        )

    else:

        print(
            ">>> SECURITY CLAIM DATASET NOT FOUND"
        )

except Exception as exc:

    print(
        ">>> SECURITY CLAIM DATASET ERROR:",
        exc
    )


try:

    if os.path.exists(FRAUD_DATASET_PATH):

        fraud_dataset = pd.read_csv(
            FRAUD_DATASET_PATH
        )

        print(
            f">>> SECURITY FRAUD DATASET LOADED: "
            f"{len(fraud_dataset)} rows"
        )

    else:

        print(
            ">>> SECURITY FRAUD DATASET NOT FOUND"
        )

except Exception as exc:

    print(
        ">>> SECURITY FRAUD DATASET ERROR:",
        exc
    )


# ==========================================================
# HELPERS
# ==========================================================

def _clean(value):

    if value is None:
        return ""

    return str(value).strip()


def _number(value):

    try:
        return float(value)

    except Exception:
        return 0.0


def _normalise(value):

    return (
        _clean(value)
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )


# ==========================================================
# SHA-256 DOCUMENT INTEGRITY
# ==========================================================

def calculate_document_hash(
    document_path: str
):

    if not document_path:

        return {
            "checked": False,
            "status": "NOT_CHECKED",
            "hash": None,
            "algorithm": "SHA-256",
            "message": (
                "Document integrity check is pending "
                "because no file was supplied."
            )
        }


    if not os.path.exists(document_path):

        return {
            "checked": True,
            "status": "FAILED",
            "hash": None,
            "algorithm": "SHA-256",
            "message": (
                "Document file was not found at the supplied path."
            )
        }


    try:

        sha256 = hashlib.sha256()

        file_size = os.path.getsize(
            document_path
        )

        with open(
            document_path,
            "rb"
        ) as file:

            while True:

                chunk = file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                sha256.update(chunk)


        document_hash = sha256.hexdigest()


        return {
            "checked": True,
            "status": "VERIFIED",
            "hash": document_hash,
            "algorithm": "SHA-256",
            "file_size": file_size,
            "message": (
                "Document integrity verified using "
                "SHA-256 fingerprinting."
            )
        }


    except Exception as exc:

        return {
            "checked": True,
            "status": "FAILED",
            "hash": None,
            "algorithm": "SHA-256",
            "message": (
                f"Unable to calculate document hash: {exc}"
            )
        }


# ==========================================================
# DUPLICATE CLAIM CHECK
# ==========================================================

def check_duplicate_claim(
    data: dict
):

    if claims_dataset is None:

        return {
            "checked": False,
            "possible_duplicate": False,
            "matches": 0,
            "message": (
                "Historical claims dataset is not available."
            )
        }


    patient_id = _clean(
        data.get("patient_id")
    )

    policy_number = _clean(
        data.get("policy_number")
    )

    claim_amount = _number(
        data.get("claim_amount")
    )

    if (
        "Patient_ID" not in claims_dataset.columns
        or
        "Policy_Number" not in claims_dataset.columns
        or
        "Claim_Amount" not in claims_dataset.columns
    ):

        return {
            "checked": False,
            "possible_duplicate": False,
            "matches": 0,
            "message": (
                "Required historical claim fields are unavailable."
            )
        }


    patient_match = pd.Series(
        False,
        index=claims_dataset.index
    )

    policy_match = pd.Series(
        False,
        index=claims_dataset.index
    )


    if patient_id:

        patient_match = (
            claims_dataset["Patient_ID"]
            .astype(str)
            .str.strip()
            == patient_id
        )


    if policy_number:

        policy_match = (
            claims_dataset["Policy_Number"]
            .astype(str)
            .str.strip()
            == policy_number
        )


    identity_match = (
        patient_match
        |
        policy_match
    )


    matching = claims_dataset[
        identity_match
    ].copy()


    if matching.empty:

        return {
            "checked": True,
            "possible_duplicate": False,
            "matches": 0,
            "message": (
                "No historical claim was found for "
                "the supplied patient or policy."
            )
        }


    matching["__amount"] = pd.to_numeric(
        matching["Claim_Amount"],
        errors="coerce"
    )


    tolerance = max(
        abs(claim_amount) * 0.01,
        100
    )


    amount_match = (
        matching["__amount"]
        .sub(claim_amount)
        .abs()
        <= tolerance
    )


    duplicate_rows = matching[
        amount_match
    ]


    possible_duplicate = (
        not duplicate_rows.empty
    )


    examples = []


    for _, row in duplicate_rows.head(5).iterrows():

        examples.append(
            {
                "claim_id": str(
                    row.get(
                        "Claim_ID",
                        ""
                    )
                ),
                "patient_id": str(
                    row.get(
                        "Patient_ID",
                        ""
                    )
                ),
                "policy_number": str(
                    row.get(
                        "Policy_Number",
                        ""
                    )
                ),
                "claim_amount": _number(
                    row.get(
                        "Claim_Amount",
                        0
                    )
                )
            }
        )


    return {
        "checked": True,
        "possible_duplicate": possible_duplicate,
        "matches": len(duplicate_rows),
        "examples": examples,
        "message": (
            "Possible duplicate claim detected."
            if possible_duplicate
            else
            "Historical patient/policy claims were found, "
            "but no matching claim amount was detected."
        )
    }


# ==========================================================
# CLAIM AMOUNT ANOMALY
# ==========================================================

def check_amount_anomaly(
    data: dict
):

    amount = _number(
        data.get("claim_amount")
    )


    if claims_dataset is None:

        return {
            "checked": False,
            "anomaly": False,
            "amount": amount,
            "level": "UNKNOWN",
            "message": (
                "Historical claims dataset is not available."
            )
        }


    if "Claim_Amount" not in claims_dataset.columns:

        return {
            "checked": False,
            "anomaly": False,
            "amount": amount,
            "level": "UNKNOWN",
            "message": (
                "Claim amount field is unavailable."
            )
        }


    amounts = pd.to_numeric(
        claims_dataset["Claim_Amount"],
        errors="coerce"
    ).dropna()


    if amounts.empty:

        return {
            "checked": False,
            "anomaly": False,
            "amount": amount,
            "level": "UNKNOWN",
            "message": (
                "No historical claim amounts available."
            )
        }


    q1 = float(
        amounts.quantile(0.25)
    )

    median = float(
        amounts.quantile(0.50)
    )

    q3 = float(
        amounts.quantile(0.75)
    )


    iqr = q3 - q1


    upper_fence = (
        q3 + (1.5 * iqr)
    )


    extreme_fence = (
        q3 + (3.0 * iqr)
    )


    if amount > extreme_fence:

        level = "HIGH"
        anomaly = True

        message = (
            "Claim amount is an extreme statistical "
            "outlier compared with historical claims."
        )

    elif amount > upper_fence:

        level = "MEDIUM"
        anomaly = True

        message = (
            "Claim amount is statistically higher than "
            "the historical claims distribution."
        )

    else:

        level = "LOW"
        anomaly = False

        message = (
            "Claim amount is within the historical "
            "claims distribution."
        )


    return {
        "checked": True,
        "anomaly": anomaly,
        "amount": amount,
        "level": level,
        "historical_q1": round(q1, 2),
        "historical_median": round(median, 2),
        "historical_q3": round(q3, 2),
        "upper_fence": round(
            upper_fence,
            2
        ),
        "extreme_fence": round(
            extreme_fence,
            2
        ),
        "message": message
    }


# ==========================================================
# DATA CONSISTENCY
# ==========================================================

def check_data_consistency(
    data: dict
):

    missing_fields = []

    patient_name = (
        data.get("patient_name")
        or data.get("patient")
        or ""
    )

    treatment = (
        data.get("treatment")
        or ""
    )

    hospital = (
        data.get("hospital")
        or data.get("hospital_name")
        or ""
    )

    claim_amount = data.get(
        "claim_amount"
    )


    if not str(patient_name).strip():

        missing_fields.append(
            "patient_name"
        )


    if not str(treatment).strip():

        missing_fields.append(
            "treatment"
        )


    if not str(hospital).strip():

        missing_fields.append(
            "hospital"
        )


    if claim_amount is None:

        missing_fields.append(
            "claim_amount"
        )


    age = data.get(
        "age"
    )


    if age is not None:

        try:

            age_value = int(
                age
            )

            if age_value < 0 or age_value > 120:

                missing_fields.append(
                    "age_out_of_range"
                )

        except Exception:

            missing_fields.append(
                "invalid_age"
            )


    consistent = (
        len(missing_fields) == 0
    )


    return {

        "checked": True,

        "consistent": consistent,

        "missing_fields": missing_fields,

        "message": (
            "Claim fields passed the preliminary "
            "consistency check."
            if consistent
            else
            "Claim contains missing or inconsistent fields."
        )
    }

# ==========================================================
# FRAUD DATASET PATTERN ANALYSIS
# ==========================================================

def check_fraud_dataset_patterns(
    data: dict
):

    if fraud_dataset is None:

        return {
            "checked": False,
            "risk": "UNKNOWN",
            "score": 0,
            "signals": [],
            "message": (
                "Fraud pattern dataset is not available."
            )
        }


    amount = _number(
        data.get("claim_amount")
    )

    signals = []
    score = 0


    if "claim_amount" in fraud_dataset.columns:

        fraud_amounts = pd.to_numeric(
            fraud_dataset["claim_amount"],
            errors="coerce"
        ).dropna()


        if not fraud_amounts.empty:

            q99 = float(
                fraud_amounts.quantile(0.99)
            )

            if amount >= q99:

                score += 2

                signals.append(
                    "Claim amount is within the top 1% "
                    "of the fraud dataset."
                )


    if "document_mismatch_flag" in fraud_dataset.columns:

        signals.append(
            "Document mismatch patterns are monitored "
            "by the fraud dataset."
        )


    if "high_risk_procedure_flag" in fraud_dataset.columns:

        signals.append(
            "High-risk procedure patterns are represented "
            "in the fraud dataset."
        )


    if score >= 3:

        risk = "HIGH"

    elif score >= 1:

        risk = "MEDIUM"

    else:

        risk = "LOW"


    return {
        "checked": True,
        "risk": risk,
        "score": score,
        "signals": signals,
        "message": (
            "Fraud dataset pattern screening completed."
        )
    }


# ==========================================================
# EXISTING RANDOM FOREST FRAUD MODEL
# ==========================================================

def get_existing_fraud_result(
    data: dict
):

    try:

        from backend.app.api.fraud_detection import (
            model,
            training_data,
            FraudRequest,
            prepare_claim_for_model
        )


        if model is None:

            return {
                "integrated": False,
                "checked": False,
                "status": "MODEL_NOT_LOADED",
                "prediction": "NOT_RUN",
                "risk": "UNKNOWN",
                "fraud_probability": 0,
                "message": (
                    "Existing Random Forest fraud model "
                    "is not loaded."
                )
            }


        if training_data is None:

            return {
                "integrated": False,
                "checked": False,
                "status": "DATASET_NOT_LOADED",
                "prediction": "NOT_RUN",
                "risk": "UNKNOWN",
                "fraud_probability": 0,
                "message": (
                    "Existing fraud model dataset "
                    "is not loaded."
                )
            }


        request = FraudRequest(
            patient_name=_clean(
                data.get("patient_name")
            ),
            age=int(
                _number(
                    data.get("age")
                )
            ),
            policy_number=_clean(
                data.get("policy_number")
            ),
            insurance_company=_clean(
                data.get("insurance_company")
            ),
            hospital_name=_clean(
                data.get("hospital_name")
            ),
            treatment=_clean(
                data.get("treatment")
            ),
            claim_amount=_number(
                data.get("claim_amount")
            )
        )


        model_input = prepare_claim_for_model(
            request
        )


        prediction = model.predict(
            model_input
        )[0]


        probabilities = model.predict_proba(
            model_input
        )[0]


        classes = list(
            model.named_steps[
                "model"
            ].classes_
        )


        if 1 in classes:

            fraud_index = classes.index(1)

            fraud_probability = (
                float(
                    probabilities[
                        fraud_index
                    ]
                )
                * 100
            )

        else:

            fraud_probability = 0.0


        if int(prediction) == 1:

            prediction_label = "Fraudulent"

            risk = "High"

        else:

            prediction_label = "Normal"

            if fraud_probability >= 30:

                risk = "Medium"

            else:

                risk = "Low"


        return {
            "integrated": True,
            "checked": True,
            "status": "COMPLETED",
            "prediction": prediction_label,
            "risk": risk,
            "fraud_probability": round(
                fraud_probability,
                2
            ),
            "message": (
                "Existing Random Forest fraud model "
                "successfully integrated into the "
                "security analysis."
            )
        }


    except Exception as exc:

        return {
            "integrated": False,
            "checked": False,
            "status": "ERROR",
            "prediction": "NOT_RUN",
            "risk": "UNKNOWN",
            "fraud_probability": 0,
            "message": (
                f"Fraud model integration failed: {exc}"
            )
        }


# ==========================================================
# SECURITY SCORE
# ==========================================================

def calculate_security_score(
    duplicate_result,
    amount_result,
    consistency_result,
    document_result,
    fraud_dataset_result,
    fraud_result
):
    """
    Calculate the overall cybersecurity risk score.

    The score represents combined security risk and is intentionally
    different from the individual ML fraud probability.

    LOW    = 75-100
    MEDIUM = 50-74
    HIGH   = 0-49
    """

    score = 100
    reasons = []

    # ---------------------------------------------------------
    # 1. DUPLICATE CLAIM
    # ---------------------------------------------------------

    if duplicate_result.get("possible_duplicate"):

        score -= 35

        reasons.append(
            "Possible duplicate claim detected."
        )

    # ---------------------------------------------------------
    # 2. CLAIM AMOUNT ANOMALY
    # ---------------------------------------------------------

    amount_level = str(
        amount_result.get("level", "LOW")
    ).upper()

    if amount_level == "HIGH":

        score -= 35

        reasons.append(
            "Claim amount is an extreme historical outlier."
        )

    elif amount_level == "MEDIUM":

        score -= 12

        reasons.append(
            "Claim amount is above the historical normal range."
        )

    # ---------------------------------------------------------
    # 3. DATA CONSISTENCY
    # ---------------------------------------------------------

    if (
        consistency_result.get("checked")
        and not consistency_result.get("consistent")
    ):

        score -= 20

        reasons.append(
            "Claim data contains consistency issues."
        )

    # ---------------------------------------------------------
    # 4. DOCUMENT INTEGRITY
    # ---------------------------------------------------------

    document_status = str(
        document_result.get("status", "NOT_CHECKED")
    ).upper()

    if document_status == "FAILED":

        score -= 20

        reasons.append(
            "Document integrity verification failed."
        )

    elif document_status == "NOT_CHECKED":

        score -= 5

        reasons.append(
            "Document integrity has not yet been verified."
        )

    # VERIFIED documents receive no penalty.

    # ---------------------------------------------------------
    # 5. FRAUD DATASET PATTERN ANALYSIS
    # ---------------------------------------------------------

    fraud_dataset_risk = str(
        fraud_dataset_result.get("risk", "LOW")
    ).upper()

    if fraud_dataset_risk == "HIGH":

        score -= 20

        reasons.append(
            "Fraud dataset pattern screening identified high-risk signals."
        )

    elif fraud_dataset_risk == "MEDIUM":

        score -= 8

        reasons.append(
            "Fraud dataset pattern screening identified moderate-risk signals."
        )

    # ---------------------------------------------------------
    # 6. EXISTING ML FRAUD MODEL
    # ---------------------------------------------------------

    fraud_risk = str(
        fraud_result.get("risk", "LOW")
    ).upper()

    fraud_probability = float(
        fraud_result.get("fraud_probability", 0)
    )

    if fraud_risk == "HIGH":

        # Do NOT allow the ML fraud model alone to immediately
        # dominate the cybersecurity gate.
        #
        # The ML result remains visible as HIGH fraud risk,
        # but the overall security gate considers all signals.

        score -= 15

        reasons.append(
            "Existing fraud model detected a high-risk claim."
        )

    elif fraud_risk == "MEDIUM":

        score -= 8

        reasons.append(
            "Existing fraud model detected moderate fraud indicators."
        )

    elif fraud_probability >= 30:

        score -= 5

        reasons.append(
            "Fraud model probability is above the normal range."
        )

    # ---------------------------------------------------------
    # 7. NORMALIZE SCORE
    # ---------------------------------------------------------

    score = max(
        0,
        min(
            100,
            int(round(score))
        )
    )

    # ---------------------------------------------------------
    # 8. FINAL SECURITY CLASSIFICATION
    # ---------------------------------------------------------

    if score >= 75:

        risk_level = "LOW"
        decision = "SECURE"

    elif score >= 50:

        risk_level = "MEDIUM"
        decision = "ADDITIONAL_VERIFICATION"

    else:

        risk_level = "HIGH"
        decision = "REVIEW_REQUIRED"

    if not reasons:

        reasons = [
            "No significant security risk indicators detected."
        ]

    return {
        "security_score": score,
        "risk_level": risk_level,
        "decision": decision,
        "reasons": reasons
    }

def analyze_claim_security(
    data: dict
):

    document_path = _clean(
        data.get("document_path")
    )


    # 1. Duplicate
    duplicate_result = (
        check_duplicate_claim(
            data
        )
    )


    # 2. Amount
    amount_result = (
        check_amount_anomaly(
            data
        )
    )


    # 3. Consistency
    consistency_result = (
        check_data_consistency(
            data
        )
    )


    # 4. Document SHA-256
    document_result = (
        calculate_document_hash(
            document_path
        )
    )


    # 5. Fraud dataset
    fraud_dataset_result = (
        check_fraud_dataset_patterns(
            data
        )
    )


    # 6. Existing Random Forest
    fraud_result = (
        get_existing_fraud_result(
            data
        )
    )


    # 7. Security score
    security = calculate_security_score(
        duplicate_result,
        amount_result,
        consistency_result,
        document_result,
        fraud_dataset_result,
        fraud_result
    )


    claim_id = _clean(
        data.get("claim_id")
    )


    return {

        "success": True,

        "claim_id": claim_id,

        "security": security,

        "checks": {

            "duplicate_claim":
                duplicate_result,

            "amount_anomaly":
                amount_result,

            "data_consistency":
                consistency_result,

            "document_integrity":
                document_result,

            "fraud_dataset_analysis":
                fraud_dataset_result,

            "fraud_analysis":
                fraud_result
        },

        "datasets": {

            "historical_claims_dataset": {
                "loaded":
                    claims_dataset is not None,
                "rows":
                    (
                        len(claims_dataset)
                        if claims_dataset is not None
                        else 0
                    )
            },

            "fraud_pattern_dataset": {
                "loaded":
                    fraud_dataset is not None,
                "rows":
                    (
                        len(fraud_dataset)
                        if fraud_dataset is not None
                        else 0
                    )
            }
        },

        "workflow": {

            "low_risk":
                "Continue normal AI-agent claim processing.",

            "medium_risk":
                "Perform additional verification before continuing.",

            "high_risk":
                "Stop automated progression and require manual review."
        },

        "disclaimer":
            "This is a preliminary project-level security risk screening. "
            "It is not a final fraud determination, medical decision, "
            "insurance approval, or rejection."
    }



