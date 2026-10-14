import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from groq import Groq
import os


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# EXISTING DATA SERVICES
# ============================================================

from backend.recommendation.hospital_service import (
    recommend_hospitals,
    hospital_dataset_health,
)

from backend.recommendation.doctor_service import (
    recommend_doctors,
    doctor_dataset_health,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/recommendations",
    tags=["Hospital & Doctor Recommendations"],
)


# ============================================================
# GROQ CONFIGURATION
# ============================================================

GROQ_MODEL = "openai/gpt-oss-120b"


def get_groq_client():
    """
    Create Groq client using GROQ_API_KEY from .env.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("GROQ ERROR: GROQ_API_KEY is not configured.")

        return None

    try:
        return Groq(
            api_key=api_key.strip()
        )

    except Exception as exc:

        print(
            "GROQ CLIENT ERROR:",
            repr(exc)
        )

        return None


# ============================================================
# GROQ FALLBACK
#
# This function is called ONLY when doctors.pdf does not
# contain a matching doctor record.
# ============================================================

def clean_groq_guidance(value):
    """Normalize common mojibake in Groq-generated guidance."""
    import re

    if not isinstance(value, str):
        return ""

    # Repair known phrases before normalizing malformed separators.
    fixes = [
        (r"board(?:â|\\?)certified", "board-certified"),
        (r"surgeon(?:â|\\?)s", "surgeon's"),
        (r"health(?:â|\\?)insurance", "health insurance"),
        (r"out(?:â|\\?)of(?:â|\\?)pocket", "out-of-pocket"),
        (r"pre(?:â|\\?)operative", "pre-operative"),
        (r"post(?:â|\\?)operative", "post-operative"),
        (r"follow(?:â|\\?)up", "follow-up"),
        (r"care(?:â|\\?)these", "care - these"),
        (r"medical(?:â|\\?)emergency", "medical emergency"),
    ]

    for pattern, replacement in fixes:
        value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)

    # Remove any remaining visible mojibake marker without splitting
    # ordinary words or deleting normal apostrophes and hyphens.
    value = value.replace(chr(0x00E2), " ")
    value = value.replace("â", " ")

    return re.sub(r"[ \t]+", " ", value).strip()


def generate_groq_doctor_guidance(
    treatment: str,
    city: str,
    area: str,
):
    """
    Generate general healthcare guidance using Groq.

    IMPORTANT:
    Groq is NOT allowed to invent doctors or hospitals.
    """

    client = get_groq_client()

    if client is None:

        return {
            "success": False,
            "source": "groq",
            "message": (
                "No matching doctor was found in the verified "
                "doctor dataset, and Groq is not configured."
            ),
            "guidance": "",
            "error": "GROQ_API_KEY is missing or Groq client could not be created.",
        }

    search_area = area.strip() if area else "Any Area"

    prompt = f"""
You are a healthcare information assistant inside an
AI-powered health insurance claim assistance application.

The application searched its verified doctor dataset first.

No matching doctor record was found for this search.

USER SEARCH:
Treatment / Disease: {treatment}
City: {city}
Area: {search_area}

YOUR TASK:

Provide concise GENERAL healthcare information.

IMPORTANT SAFETY RULES:

1. Do NOT invent doctor names.
2. Do NOT invent hospital names.
3. Do NOT invent hospital addresses.
4. Do NOT claim that a specific doctor is available.
5. Do NOT claim that a hospital accepts a specific insurance company.
6. Do NOT provide a diagnosis.
7. Do NOT prescribe medicines or dosages.
8. Explain which medical specialty generally handles the condition.
9. Explain what type of doctor the user can look for.
10. Mention what the user should verify before booking.
11. If the condition can sometimes require urgent medical attention,
    mention appropriate warning signs briefly.
12. Clearly say that no matching doctor was found in the project's
    verified doctor dataset.
13. Keep the response easy to understand.
14. Do not make unsupported claims about local doctor availability.
15. Use plain ASCII punctuation only. Use a normal hyphen (-) in
    board-certified, pre-operative, post-operative, and follow-up.
    Use a normal apostrophe (') in possessives such as surgeon's.
    Avoid smart quotes, en dashes, em dashes, and unusual Unicode symbols.
    Do not insert punctuation inside ordinary words.

Return a short helpful response with these sections:

Why no result:
Recommended specialty:
What to look for:
Before booking:
Safety note:
"""

    try:

        print(
            "GROQ FALLBACK STARTED:",
            treatment,
            city,
            search_area,
        )

        response = client.chat.completions.create(
            model=GROQ_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a safe healthcare information "
                        "assistant. Never fabricate doctors, "
                        "hospitals, addresses, insurance coverage, "
                        "or medical records."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],

            temperature=0.2,

            max_tokens=700,
        )

        # ----------------------------------------------------
        # SAFELY READ RESPONSE
        # ----------------------------------------------------

        guidance = ""

        if (
            response
            and getattr(response, "choices", None)
            and len(response.choices) > 0
        ):

            message = response.choices[0].message

            if message:

                guidance = clean_groq_guidance(
                getattr(message, "content", "") or ""
            )

        # ----------------------------------------------------
        # EMPTY RESPONSE CHECK
        # ----------------------------------------------------

        if not guidance:

            print(
                "GROQ ERROR: Empty response received."
            )

            return {
                "success": False,
                "source": "groq",
                "message": (
                    "Groq returned an empty response."
                ),
                "guidance": "",
                "error": "Empty Groq response.",
            }

        print(
            "GROQ FALLBACK SUCCESS"
        )

        return {
            "success": True,
            "source": "groq",
            "message": (
                "No matching doctor was found in the verified "
                "doctor dataset. Groq AI provided general "
                "healthcare guidance."
            ),
            "guidance": guidance,
            "error": "",
        }

    except Exception as exc:

        # ----------------------------------------------------
        # PRINT COMPLETE ERROR IN BACKEND TERMINAL
        # ----------------------------------------------------

        print(
            "=================================================="
        )

        print(
            "GROQ FALLBACK ERROR:"
        )

        print(
            repr(exc)
        )

        print(
            "=================================================="
        )

        return {
            "success": False,
            "source": "groq",
            "message": (
                "No matching doctor was found and the AI "
                "fallback could not be completed."
            ),
            "guidance": "",
            "error": str(exc),
        }


# ============================================================
# EXISTING HOSPITAL + DOCTOR REQUEST
# ============================================================

class RecommendationRequest(BaseModel):

    treatment: str = Field(
        default="",
        max_length=200,
    )

    city: str = Field(
        default="",
        max_length=100,
    )

    area: str = Field(
        default="",
        max_length=100,
    )

    insurance_company: str = Field(
        default="",
        max_length=150,
    )

    hospital: str = Field(
        default="",
        max_length=200,
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=10,
    )


# ============================================================
# DOCTOR-ONLY SEARCH REQUEST
#
# Find Doctor UI:
#
# Treatment
# City
# Area
#
# Hospital is NOT a search input.
# ============================================================

class DoctorSearchRequest(BaseModel):

    treatment: str = Field(
        default="",
        max_length=200,
    )

    city: str = Field(
        default="",
        max_length=100,
    )

    area: str = Field(
        default="",
        max_length=100,
    )

    limit: int = Field(
        default=20,
        ge=1,
        le=50,
    )


# ============================================================
# EXISTING HOSPITAL + DOCTOR SEARCH
#
# POST /api/recommendations/search
# ============================================================

@router.post("/search")
def search_recommendations(
    request: RecommendationRequest,
):

    try:

        # ----------------------------------------------------
        # HOSPITAL RECOMMENDATIONS
        # ----------------------------------------------------

        hospitals = recommend_hospitals(
            treatment=request.treatment,
            city=request.city,
            area=request.area,
            insurance_company=request.insurance_company,
            limit=request.limit,
        )

        # ----------------------------------------------------
        # DOCTOR RECOMMENDATIONS
        # ----------------------------------------------------

        doctors = recommend_doctors(
            treatment=request.treatment,
            city=request.city,
            area=request.area,
            hospital=request.hospital,
            limit=request.limit,
        )

        # ----------------------------------------------------
        # REMOVE DUPLICATE DOCTORS
        # ----------------------------------------------------

        unique_doctors = {}

        for doctor in doctors:

            key = (
                str(
                    doctor.get(
                        "doctor_name",
                        "",
                    )
                ).strip().lower(),

                str(
                    doctor.get(
                        "hospital",
                        "",
                    )
                ).strip().lower(),

                str(
                    doctor.get(
                        "branch_area",
                        "",
                    )
                ).strip().lower(),
            )

            existing = unique_doctors.get(key)

            if (
                existing is None
                or doctor.get("score", 0)
                > existing.get("score", 0)
            ):

                unique_doctors[key] = doctor

        doctors = list(
            unique_doctors.values()
        )

        doctors.sort(
            key=lambda item: item.get(
                "score",
                0,
            ),
            reverse=True,
        )

        doctors = doctors[:request.limit]

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return {

            "success": True,

            "query": {
                "treatment": request.treatment,
                "city": request.city,
                "area": request.area,
                "insurance_company": request.insurance_company,
                "hospital": request.hospital,
            },

            "hospitals": hospitals,

            "doctors": doctors,

            "hospital_count": len(
                hospitals
            ),

            "doctor_count": len(
                doctors
            ),

            "message": (
                "Hospital and doctor recommendations "
                "generated from the project datasets."
            ),

            "disclaimer": (
                "Recommendations are based on the available "
                "project datasets. Insurance coverage, network "
                "status, cashless availability, doctor "
                "availability and final claim approval must be "
                "verified with the applicable hospital and "
                "insurance provider."
            ),
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# DOCTOR-ONLY SEARCH
#
# POST /api/recommendations/doctors/search
#
# FLOW:
#
# USER SEARCH
#      â†“
# doctors.pdf
#      â†“
# Match?
#   YES     NO
#    â†“       â†“
# PDF      GROQ
# Result   AI Guidance
# ============================================================

@router.post("/doctors/search")
def search_doctors(
    request: DoctorSearchRequest,
):

    try:

        # ====================================================
        # STEP 1
        # SEARCH VERIFIED DOCTOR PDF
        # ====================================================

        doctors = recommend_doctors(
            treatment=request.treatment,
            city=request.city,
            area=request.area,
            hospital="",
            limit=request.limit,
        )

        # ====================================================
        # STEP 2
        # REMOVE DUPLICATES
        # ====================================================

        unique_doctors = {}

        for doctor in doctors:

            key = (
                str(
                    doctor.get(
                        "doctor_name",
                        "",
                    )
                ).strip().lower(),

                str(
                    doctor.get(
                        "hospital",
                        "",
                    )
                ).strip().lower(),

                str(
                    doctor.get(
                        "branch_area",
                        "",
                    )
                ).strip().lower(),
            )

            existing = unique_doctors.get(key)

            if (
                existing is None
                or doctor.get("score", 0)
                > existing.get("score", 0)
            ):

                unique_doctors[key] = doctor

        doctors = list(
            unique_doctors.values()
        )

        # ====================================================
        # STEP 3
        # SORT BY MATCH SCORE
        # ====================================================

        # Rank doctors by actual branch match before overall score.
        def doctor_api_sort(item):
            requested_area = str(request.area or "").strip().casefold()
            requested_treatment = str(request.treatment or "").strip().casefold()
            requested_city = str(request.city or "").strip().casefold()

            branch_area = str(item.get("branch_area") or "").strip().casefold()
            address = str(item.get("hospital_address") or "").strip().casefold()
            treatment = str(item.get("disease_treatment") or "").strip().casefold()
            city = str(item.get("city") or "").strip().casefold()

            exact_area = bool(requested_area and branch_area == requested_area)
            area_match = bool(
                requested_area and (
                    exact_area
                    or requested_area in branch_area
                    or branch_area in requested_area
                    or requested_area in address
                )
            )
            exact_treatment = bool(
                requested_treatment and treatment == requested_treatment
            )
            exact_city = bool(requested_city and city == requested_city)

            return (
                1 if exact_area else 0,
                1 if area_match else 0,
                1 if exact_treatment else 0,
                1 if exact_city else 0,
                item.get("score", 0),
            )

        doctors.sort(key=doctor_api_sort, reverse=True)

        doctors = doctors[:request.limit]

        # ====================================================
        # STEP 4
        # PDF RESULT FOUND
        # ====================================================

        if doctors:

            return {

                "success": True,

                "query": {
                    "treatment": request.treatment,
                    "city": request.city,
                    "area": request.area,
                },

                "source": "doctors.pdf",

                "doctor_count": len(
                    doctors
                ),

                "doctors": doctors,

                "ai_fallback_used": False,

                "ai_guidance": "",

                "message": (
                    "Matching doctor records were retrieved "
                    "from the verified doctor PDF dataset."
                ),

                "disclaimer": (
                    "Doctor information is based on the available "
                    "project dataset. Doctor availability, hospital "
                    "services and treatment suitability must be "
                    "verified with the hospital."
                ),
            }

        # ====================================================
        # STEP 5
        # NO PDF RESULT
        #
        # CALL GROQ
        # ====================================================

        print(
            "NO PDF DOCTOR MATCH."
        )

        print(
            "Starting Groq fallback..."
        )

        ai_result = generate_groq_doctor_guidance(
            treatment=request.treatment,
            city=request.city,
            area=request.area,
        )

        # ====================================================
        # STEP 6
        # GROQ SUCCESS
        # ====================================================

        if ai_result.get(
            "success",
            False,
        ):

            return {

                "success": True,

                "query": {
                    "treatment": request.treatment,
                    "city": request.city,
                    "area": request.area,
                },

                "source": "groq",

                "doctor_count": 0,

                "doctors": [],

                "ai_fallback_used": True,

                "ai_guidance": clean_groq_guidance(
                    ai_result.get("guidance", "")
                ),

                "message": ai_result.get(
                    "message",
                    "Groq AI guidance generated.",
                ),

                "disclaimer": (
                    "No matching doctor was found in the "
                    "project's verified doctor dataset. "
                    "AI guidance is general healthcare "
                    "information and must not be treated "
                    "as a diagnosis or substitute for "
                    "professional medical advice."
                ),
            }

        # ====================================================
        # STEP 7
        # GROQ FAILED
        # ====================================================

        return {

            "success": False,

            "query": {
                "treatment": request.treatment,
                "city": request.city,
                "area": request.area,
            },

            "source": "groq",

            "doctor_count": 0,

            "doctors": [],

            "ai_fallback_used": True,

            "ai_guidance": "",

            "message": ai_result.get(
                "message",
                "AI fallback failed.",
            ),

            "error": ai_result.get(
                "error",
                "",
            ),

            "disclaimer": (
                "No matching doctor was found in the "
                "project's verified doctor dataset."
            ),
        }

    except Exception as exc:

        print(
            "DOCTOR SEARCH ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# DATASET HEALTH
#
# GET /api/recommendations/health
# ============================================================

@router.get("/health")
def recommendation_health():

    try:

        hospital_health = (
            hospital_dataset_health()
        )

        doctor_health = (
            doctor_dataset_health()
        )

        groq_configured = bool(
            os.getenv(
                "GROQ_API_KEY"
            )
        )

        return {

            "status": "healthy",

            "hospital_recommendation": (
                hospital_health
            ),

            "doctor_recommendation": (
                doctor_health
            ),

            "groq_fallback": {

                "configured": (
                    groq_configured
                ),

                "model": GROQ_MODEL,

                "enabled": True,
            },
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

# ============================================================
# DATASET-DRIVEN DROPDOWN OPTIONS
#
# GET /api/recommendations/options
# Reads existing hospital Excel and doctor CSV datasets.
# Existing search endpoints remain unchanged.
# ============================================================

@router.get("/options")
def recommendation_options():
    try:
        import re
        import pandas as pd
        from pathlib import Path

        data_dir = (
            Path(__file__).resolve().parents[2]
            / "recommendation"
            / "data"
        )

        hospital_file = data_dir / "hospitals.xlsx"
        doctor_file = data_dir / "doctors.csv"

        if not hospital_file.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Hospital dataset not found: {hospital_file}",
            )

        if not doctor_file.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Doctor dataset not found: {doctor_file}",
            )

        hospital_df = pd.read_excel(hospital_file)
        doctor_df = pd.read_csv(
            doctor_file,
            encoding="utf-8-sig",
        )

        def column_values(frame, column):
            if column not in frame.columns:
                return []

            values = set()

            for value in frame[column].dropna():
                text = str(value).strip()

                if text and text.lower() not in {
                    "nan", "none", "null", "n/a"
                }:
                    values.add(text)

            return sorted(values, key=str.casefold)

        def treatment_values(frame, column, split_values=False):
            if column not in frame.columns:
                return []

            values = set()
            for value in frame[column].dropna():
                text = str(value).strip()
                if not text or text.lower() in {"nan", "none", "null", "n/a"}:
                    continue

                parts = re.split(r"[,;|\r\n]+", text) if split_values else [text]

                for part in parts:
                    item = part.strip()
                    if item and item.lower() not in {"nan", "none", "null", "n/a"}:
                        values.add(item)

            return sorted(values, key=str.casefold)

        return {
            "success": True,
            "city_options": ["Chennai"],
            "hospital_options": {
                "treatments": [
    "Appendectomy",
    "Emergency Care",
    "Gallbladder Surgery",
    "General Surgery",
    "Hernia Repair"
],
                "areas": column_values(
                    hospital_df,
                    "Area",
                ),
            },
            "doctor_options": {
                "treatments": treatment_values(
                    doctor_df,
                    "Disease / Treatment",
                ),
                "areas": column_values(
                    doctor_df,
                    "Branch / Area",
                ),
            },
            "insurance_options": [
                "All Insurance",
                "Star Health",
                "Care",
                "Niva Bupa",
                "ManipalCigna",
                "Aditya Birla",
                "HDFC ERGO",
                "ICICI Lombard",
                "Tata AIG",
                "Bajaj Allianz",
            ],
            "source": {
                "hospitals": "hospitals.xlsx",
                "doctors": "doctors.csv",
            },
        }

    except HTTPException:
        raise

    except Exception as exc:
        print("RECOMMENDATION OPTIONS ERROR:", repr(exc))

        raise HTTPException(
            status_code=500,
            detail="Could not load dropdown options from the datasets.",
        )





