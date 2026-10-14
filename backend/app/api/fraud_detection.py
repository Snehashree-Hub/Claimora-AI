from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib
import os

router = APIRouter(
    prefix="/api/fraud",
    tags=["Fraud Detection Agent"]
)

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "ml_models",
    "fraud_detection_model.pkl"
)

DATASET_PATH = os.path.join(
    BASE_DIR,
    "datasets",
    "health_insurance_claims.csv.csv"
)

model = None
training_data = None


# =========================================================
# LOAD ML MODEL
# =========================================================

if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)

        print(">>> FRAUD ML MODEL LOADED")
        print(f">>> MODEL: {MODEL_PATH}")

    except Exception as e:
        print(">>> FRAUD MODEL LOAD ERROR:", e)

else:
    print(">>> FRAUD MODEL NOT FOUND")
    print(f">>> EXPECTED: {MODEL_PATH}")


# =========================================================
# LOAD DATASET
# =========================================================

if os.path.exists(DATASET_PATH):
    try:
        training_data = pd.read_csv(DATASET_PATH)

        print(">>> FRAUD DATASET LOADED")
        print(f">>> DATASET: {DATASET_PATH}")
        print(f">>> ROWS: {len(training_data)}")
        print(f">>> COLUMNS: {len(training_data.columns)}")

    except Exception as e:
        print(">>> DATASET LOAD ERROR:", e)

else:
    print(">>> FRAUD DATASET NOT FOUND")
    print(f">>> EXPECTED: {DATASET_PATH}")


# =========================================================
# REQUEST MODEL
# =========================================================

class FraudRequest(BaseModel):
    patient_name: str
    age: int
    policy_number: str
    insurance_company: str
    hospital_name: str
    treatment: str
    claim_amount: float


# =========================================================
# TEST ENDPOINT
# =========================================================

@router.get("/test")
def fraud_test():

    return {
        "success": True,
        "agent": "Fraud Detection Agent",
        "model": "Random Forest",
        "model_loaded": model is not None,
        "dataset_loaded": training_data is not None,
        "status": "working"
    }


# =========================================================
# PREPARE MODEL INPUT
# =========================================================

def prepare_claim_for_model(data: FraudRequest):

    if training_data is None:
        raise Exception(
            "Training dataset is not loaded."
        )

    # -----------------------------------------------------
    # Take one real row from the training dataset.
    #
    # This ensures that every feature has the same
    # datatype expected by the trained ML pipeline.
    # -----------------------------------------------------

    claim = training_data.iloc[0].copy()

    # -----------------------------------------------------
    # USER PROVIDED VALUES
    # -----------------------------------------------------

    claim["Claim_Amount"] = float(
        data.claim_amount
    )

    claim["Patient_Age"] = int(
        data.age
    )

    # -----------------------------------------------------
    # Policy number is NOT used by the ML model.
    # Patient name is NOT used by the ML model.
    # Insurance company is NOT used by the ML model.
    # Hospital name is NOT used directly by the model.
    # -----------------------------------------------------

    # Treatment can be mapped to provider specialty.
    if "Provider_Specialty" in claim.index:
        claim["Provider_Specialty"] = str(
            data.treatment
        )

    # -----------------------------------------------------
    # IMPORTANT:
    #
    # Procedure_Code is NUMERIC in your model.
    # Never put "UNKNOWN" here.
    # Keep the numeric value from the dataset row.
    # -----------------------------------------------------

    if "Procedure_Code" in claim.index:
        claim["Procedure_Code"] = pd.to_numeric(
            claim["Procedure_Code"],
            errors="coerce"
        )

        if pd.isna(claim["Procedure_Code"]):
            claim["Procedure_Code"] = 0.0

    # -----------------------------------------------------
    # Hospital ID is numeric.
    # Keep the original numeric value.
    # -----------------------------------------------------

    if "Hospital_ID" in claim.index:
        claim["Hospital_ID"] = pd.to_numeric(
            claim["Hospital_ID"],
            errors="coerce"
        )

        if pd.isna(claim["Hospital_ID"]):
            claim["Hospital_ID"] = 0.0

    # -----------------------------------------------------
    # Ensure ALL numeric columns are numeric.
    # -----------------------------------------------------

    numeric_columns = [
        "Claim_Amount",
        "Patient_Age",
        "Hospital_ID",
        "Procedure_Code",
        "Number_of_Procedures",
        "Length_of_Stay_Days",
        "Deductible_Amount",
        "CoPay_Amount",
        "Number_of_Previous_Claims_Patient",
        "Number_of_Previous_Claims_Provider",
        "Provider_Patient_Distance_Miles"
    ]

    for column in numeric_columns:

        if column in claim.index:

            claim[column] = pd.to_numeric(
                claim[column],
                errors="coerce"
            )

            if pd.isna(claim[column]):
                claim[column] = 0.0

    # -----------------------------------------------------
    # Make sure categorical values are strings.
    # -----------------------------------------------------

    categorical_columns = [
        "Patient_Gender",
        "Patient_City",
        "Patient_State",
        "Provider_Type",
        "Provider_Specialty",
        "Provider_City",
        "Provider_State",
        "Diagnosis_Code",
        "Admission_Type",
        "Discharge_Type",
        "Service_Type"
    ]

    for column in categorical_columns:

        if column in claim.index:
            claim[column] = str(
                claim[column]
            )

    # Claim_Submitted_Late is categorical according
    # to the trained pipeline.
    if "Claim_Submitted_Late" in claim.index:

        value = claim["Claim_Submitted_Late"]

        if isinstance(value, str):

            value_lower = value.strip().lower()

            if value_lower in [
                "true",
                "yes",
                "1"
            ]:
                claim["Claim_Submitted_Late"] = "True"

            else:
                claim["Claim_Submitted_Late"] = "False"

    # -----------------------------------------------------
    # Remove target column if present.
    # -----------------------------------------------------

    if "Is_Fraudulent" in claim.index:
        claim = claim.drop(
            labels=["Is_Fraudulent"]
        )

    # -----------------------------------------------------
    # EXACT MODEL FEATURES
    # -----------------------------------------------------

    model_features = [
        "Claim_Amount",
        "Patient_Age",
        "Patient_Gender",
        "Patient_City",
        "Patient_State",
        "Hospital_ID",
        "Provider_Type",
        "Provider_Specialty",
        "Provider_City",
        "Provider_State",
        "Diagnosis_Code",
        "Procedure_Code",
        "Number_of_Procedures",
        "Admission_Type",
        "Discharge_Type",
        "Length_of_Stay_Days",
        "Service_Type",
        "Deductible_Amount",
        "CoPay_Amount",
        "Number_of_Previous_Claims_Patient",
        "Number_of_Previous_Claims_Provider",
        "Provider_Patient_Distance_Miles",
        "Claim_Submitted_Late"
    ]

    # Make sure every required feature exists.
    for column in model_features:

        if column not in claim.index:

            raise Exception(
                f"Required model feature missing: {column}"
            )

    model_input = pd.DataFrame(
        [[claim[column] for column in model_features]],
        columns=model_features
    )

    return model_input


# =========================================================
# FRAUD DETECTION
# =========================================================

@router.post("/check")
def detect_fraud(data: FraudRequest):

    if model is None:

        raise HTTPException(
            status_code=503,
            detail=(
                "Fraud Detection ML model is not loaded. "
                "Train the model first."
            )
        )

    if training_data is None:

        raise HTTPException(
            status_code=503,
            detail=(
                "Fraud Detection training dataset "
                "is not loaded."
            )
        )

    try:

        # -------------------------------------------------
        # PREPARE CLAIM
        # -------------------------------------------------

        df = prepare_claim_for_model(data)

        print()
        print("=" * 60)
        print(">>> FRAUD PREDICTION")
        print("=" * 60)

        print("Patient      :", data.patient_name)
        print("Age          :", data.age)
        print("Policy       :", data.policy_number)
        print("Treatment    :", data.treatment)
        print("Claim Amount :", data.claim_amount)

        print()
        print("MODEL INPUT:")
        print(df.to_string(index=False))

        print("=" * 60)

        # -------------------------------------------------
        # PREDICTION
        # -------------------------------------------------

        prediction = model.predict(df)[0]

        probabilities = model.predict_proba(df)[0]

        # -------------------------------------------------
        # FRAUD PROBABILITY
        # -------------------------------------------------

        classes = list(
            model.named_steps["model"].classes_
        )

        if 1 in classes:

            fraud_index = classes.index(1)

            fraud_probability = (
                float(
                    probabilities[fraud_index]
                ) * 100
            )

        else:

            fraud_probability = 0.0

        # -------------------------------------------------
        # RISK
        # -------------------------------------------------

        if int(prediction) == 1:

            prediction_label = "Fraudulent"

            risk_level = "High"

            recommendation = (
                "ML model detected a potential "
                "fraudulent claim. Manual investigation "
                "is recommended."
            )

        else:

            prediction_label = "Normal"

            if fraud_probability >= 30:

                risk_level = "Medium"

                recommendation = (
                    "Claim is classified as non-fraudulent "
                    "by the ML model, but additional "
                    "verification is recommended."
                )

            else:

                risk_level = "Low"

                recommendation = (
                    "ML model did not detect significant "
                    "fraud indicators. Claim can proceed "
                    "to normal processing."
                )

        # -------------------------------------------------
        # TERMINAL RESULT
        # -------------------------------------------------

        print("Prediction   :", prediction_label)
        print(
            "Fraud %      :",
            round(fraud_probability, 2)
        )
        print("Risk Level   :", risk_level)

        print("=" * 60)
        print()

        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        return {
            "success": True,
            "agent": "Fraud Detection Agent",
            "model": "Random Forest",

            "prediction": prediction_label,

            "risk_level": risk_level,

            "fraud_probability": round(
                fraud_probability,
                2
            ),

            "recommendation": recommendation,

            "claim": {
                "patient_name": data.patient_name,
                "age": data.age,
                "policy_number": data.policy_number,
                "insurance_company": data.insurance_company,
                "hospital_name": data.hospital_name,
                "treatment": data.treatment,
                "claim_amount": data.claim_amount
            }
        }

    except Exception as e:

        print()
        print("=" * 60)
        print(">>> FRAUD PREDICTION ERROR")
        print("=" * 60)
        print(str(e))
        print("=" * 60)
        print()

        raise HTTPException(
            status_code=500,
            detail=f"Fraud prediction failed: {str(e)}"
        )