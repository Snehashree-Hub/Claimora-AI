import pandas as pd
import numpy as np
import os
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


# ============================================================
# 1. LOAD DATASET
# ============================================================

DATASET_PATH = r".\datasets\health_insurance_claims.csv.csv"
MODEL_PATH = r".\ml_models\fraud_detection_model.pkl"

print("=" * 70)
print("AI AGENT FOR HEALTH INSURANCE CLAIM ASSISTANCE")
print("FRAUD DETECTION MODEL TRAINING")
print("=" * 70)

df = pd.read_csv(DATASET_PATH)

print("\nDataset loaded successfully")
print("Rows:", len(df))
print("Columns:", len(df.columns))


# ============================================================
# 2. TARGET
# ============================================================

TARGET = "Is_Fraudulent"

if TARGET not in df.columns:
    raise ValueError(f"Target column '{TARGET}' not found.")

print("\nTarget column:", TARGET)
print("\nFraud distribution:")
print(df[TARGET].value_counts())


# ============================================================
# 3. REMOVE IDENTIFIER / DATE COLUMNS
# ============================================================

drop_columns = [
    "Patient_ID",
    "Policy_Number",
    "Claim_ID",
    "Claim_Date",
    "Service_Date",
    "Policy_Expiration_Date"
]

drop_columns = [
    column for column in drop_columns
    if column in df.columns
]

X = df.drop(columns=[TARGET] + drop_columns)
y = df[TARGET].astype(int)


# ============================================================
# 4. DETERMINE COLUMN TYPES
# ============================================================

categorical_columns = X.select_dtypes(
    include=["object", "bool"]
).columns.tolist()

numeric_columns = X.select_dtypes(
    include=["int64", "float64", "int32", "float32"]
).columns.tolist()

print("\nNumeric features:")
print(numeric_columns)

print("\nCategorical features:")
print(categorical_columns)


# ============================================================
# 5. PREPROCESSING
# ============================================================

preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            "passthrough",
            numeric_columns
        ),
        (
            "categorical",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False
            ),
            categorical_columns
        )
    ]
)


# ============================================================
# 6. RANDOM FOREST
# ============================================================

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)


# ============================================================
# 7. PIPELINE
# ============================================================

pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ]
)


# ============================================================
# 8. TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# ============================================================
# 9. TRAIN MODEL
# ============================================================

print("\nTraining Random Forest...")
print("Please wait...")

pipeline.fit(X_train, y_train)

print("Training completed.")


# ============================================================
# 10. EVALUATION
# ============================================================

y_pred = pipeline.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print("\n" + "=" * 70)
print("MODEL RESULTS")
print("=" * 70)

print(f"\nAccuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        target_names=["Normal", "Fraud"]
    )
)

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))


# ============================================================
# 11. SAVE MODEL
# ============================================================

os.makedirs(
    os.path.dirname(MODEL_PATH),
    exist_ok=True
)

joblib.dump(
    pipeline,
    MODEL_PATH
)

print("\n" + "=" * 70)
print("MODEL SAVED")
print("=" * 70)

print("\nModel file:")
print(MODEL_PATH)

print("\nFraud Detection Agent model is ready.")
