from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "backend" / "recommendation" / "data"

DOCTORS_CSV = DATA_DIR / "doctors.csv"
DOCTORS_PDF = DATA_DIR / "doctors.pdf"
HOSPITALS_XLSX = DATA_DIR / "hospitals.xlsx"


# ============================================================
# TEXT HELPERS
# ============================================================

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    text = str(value).strip()

    if text.lower() in {
        "nan",
        "none",
        "null",
        "na",
        "n/a",
        "not available",
    }:
        return ""

    return re.sub(r"\s+", " ", text)


def normalize(value: Any) -> str:
    text = clean_text(value).lower()

    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def contains_phrase(text: str, query: str) -> bool:
    text = normalize(text)
    query = normalize(query)

    if not query:
        return False

    return query in text


def words(value: str) -> list[str]:
    return [
        w
        for w in normalize(value).split()
        if len(w) >= 2
    ]


# ============================================================
# COLUMN FINDER
# ============================================================

def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    normalized_columns = {
        normalize(column).replace(" ", "_"): column
        for column in df.columns
    }

    for candidate in candidates:
        key = normalize(candidate).replace(" ", "_")

        if key in normalized_columns:
            return normalized_columns[key]

    # fuzzy fallback
    for normalized_name, original_name in normalized_columns.items():
        for candidate in candidates:
            candidate_key = normalize(candidate).replace(" ", "_")

            if (
                candidate_key in normalized_name
                or normalized_name in candidate_key
            ):
                return original_name

    return None


def value_from_row(
    row: pd.Series,
    df: pd.DataFrame,
    candidates: list[str],
) -> str:
    column = find_column(df, candidates)

    if not column:
        return ""

    return clean_text(row.get(column, ""))


# ============================================================
# DATASET LOADING
# ============================================================

_doctors_cache: pd.DataFrame | None = None
_hospitals_cache: pd.DataFrame | None = None


def load_doctors() -> pd.DataFrame:
    global _doctors_cache

    if _doctors_cache is not None:
        return _doctors_cache.copy()

    frames: list[pd.DataFrame] = []

    # --------------------------------------------------------
    # DOCTORS CSV
    # --------------------------------------------------------

    if DOCTORS_CSV.exists():
        try:
            csv_df = pd.read_csv(
                DOCTORS_CSV,
                encoding="utf-8-sig",
            )

            csv_df["__source"] = "doctors.csv"

            frames.append(csv_df)

            print(
                f"[RECOMMENDATION] doctors.csv loaded: "
                f"{len(csv_df)} rows"
            )

        except Exception as exc:
            print(
                f"[RECOMMENDATION] doctors.csv failed: {exc}"
            )

    # --------------------------------------------------------
    # DOCTORS PDF
    # --------------------------------------------------------
    #
    # PDF is used only when readable structured information
    # can be extracted. CSV remains the primary doctor source.
    # --------------------------------------------------------

    if DOCTORS_PDF.exists():

        try:
            from pypdf import PdfReader

            reader = PdfReader(str(DOCTORS_PDF))

            pdf_rows = []

            for page in reader.pages:
                text = page.extract_text() or ""

                if text.strip():
                    pdf_rows.append(
                        {
                            "raw_text": text,
                            "__source": "doctors.pdf",
                        }
                    )

            if pdf_rows:
                pdf_df = pd.DataFrame(pdf_rows)

                frames.append(pdf_df)

                print(
                    f"[RECOMMENDATION] doctors.pdf loaded: "
                    f"{len(pdf_df)} pages"
                )

        except Exception as exc:
            print(
                f"[RECOMMENDATION] doctors.pdf skipped: {exc}"
            )

    if not frames:
        _doctors_cache = pd.DataFrame()

        return _doctors_cache.copy()

    # Use CSV as structured source.
    # PDF pages are retained but will only be used as fallback.
    structured = [
        frame
        for frame in frames
        if "raw_text" not in frame.columns
    ]

    if structured:
        df = pd.concat(
            structured,
            ignore_index=True,
            sort=False,
        )
    else:
        df = pd.concat(
            frames,
            ignore_index=True,
            sort=False,
        )

    df = df.fillna("")

    _doctors_cache = df

    return df.copy()


def load_hospitals() -> pd.DataFrame:
    global _hospitals_cache

    if _hospitals_cache is not None:
        return _hospitals_cache.copy()

    if not HOSPITALS_XLSX.exists():
        print(
            f"[RECOMMENDATION] Hospital dataset missing: "
            f"{HOSPITALS_XLSX}"
        )

        _hospitals_cache = pd.DataFrame()

        return _hospitals_cache.copy()

    try:
        sheets = pd.read_excel(
            HOSPITALS_XLSX,
            sheet_name=None,
        )

        frames = []

        for sheet_name, frame in sheets.items():

            if frame is None or frame.empty:
                continue

            frame = frame.copy()

            frame["__sheet"] = sheet_name
            frame["__source"] = "hospitals.xlsx"

            frames.append(frame)

        if frames:
            df = pd.concat(
                frames,
                ignore_index=True,
                sort=False,
            )
        else:
            df = pd.DataFrame()

        df = df.fillna("")

        _hospitals_cache = df

        print(
            f"[RECOMMENDATION] hospitals.xlsx loaded: "
            f"{len(df)} rows"
        )

        return df.copy()

    except Exception as exc:
        print(
            f"[RECOMMENDATION] hospitals.xlsx failed: {exc}"
        )

        _hospitals_cache = pd.DataFrame()

        return _hospitals_cache.copy()


# ============================================================
# DATASET INFORMATION
# ============================================================

def recommendation_health() -> dict[str, Any]:
    doctors = load_doctors()
    hospitals = load_hospitals()

    return {
        "success": True,
        "doctor_dataset": {
            "path": str(DOCTORS_CSV),
            "exists": DOCTORS_CSV.exists(),
            "rows": len(doctors),
            "columns": list(doctors.columns),
        },
        "doctor_pdf": {
            "path": str(DOCTORS_PDF),
            "exists": DOCTORS_PDF.exists(),
        },
        "hospital_dataset": {
            "path": str(HOSPITALS_XLSX),
            "exists": HOSPITALS_XLSX.exists(),
            "rows": len(hospitals),
            "columns": list(hospitals.columns),
        },
    }


# ============================================================
# GENERIC DATASET VALUE EXTRACTION
# ============================================================

DOCTOR_FIELDS = {
    "name": [
        "doctor_name",
        "doctor",
        "name",
        "physician",
        "consultant",
    ],
    "specialty": [
        "specialty",
        "speciality",
        "department",
        "specialization",
    ],
    "hospital": [
        "hospital",
        "hospital_name",
        "provider",
        "medical_center",
        "medical_centre",
    ],
    "area": [
        "branch_area",
        "area",
        "branch",
        "locality",
        "location",
        "search_location",
    ],
    "city": [
        "city",
        "district",
    ],
    "address": [
        "hospital_address",
        "address",
        "hospital_location",
    ],
    "treatment": [
        "disease_treatment",
        "treatment",
        "disease",
        "condition",
        "diagnosis",
    ],
    "procedure": [
        "relevant_procedure",
        "procedure",
        "treatment_procedure",
        "procedures",
    ],
    "history": [
        "procedure_clinical_history",
        "clinical_history",
        "treatment_history",
        "success_history",
        "successful_treatments",
    ],
    "logic": [
        "recommendation_logic",
        "logic",
        "recommendation_reason",
    ],
    "insurance": [
        "insurance_company",
        "insurance",
        "insurer",
        "insurance_provider",
        "network",
        "accepted_insurance",
    ],
}


HOSPITAL_FIELDS = {
    "hospital": [
        "hospital",
        "hospital_name",
        "name",
        "provider",
        "provider_name",
    ],
    "specialty": [
        "specialty",
        "speciality",
        "department",
        "specialization",
    ],
    "area": [
        "area",
        "branch_area",
        "branch",
        "locality",
        "location",
    ],
    "city": [
        "city",
        "district",
    ],
    "address": [
        "hospital_address",
        "address",
        "location_address",
    ],
    "treatment": [
        "treatment",
        "disease_treatment",
        "disease",
        "condition",
        "procedure",
    ],
    "facilities": [
        "facilities",
        "facility",
        "services",
        "amenities",
    ],
    "insurance": [
        "insurance_company",
        "insurance",
        "insurer",
        "insurance_provider",
        "network",
        "accepted_insurance",
    ],
}


def get_doctor_value(
    row: pd.Series,
    df: pd.DataFrame,
    key: str,
) -> str:
    return value_from_row(
        row,
        df,
        DOCTOR_FIELDS[key],
    )


def get_hospital_value(
    row: pd.Series,
    df: pd.DataFrame,
    key: str,
) -> str:
    return value_from_row(
        row,
        df,
        HOSPITAL_FIELDS[key],
    )


# ============================================================
# INSURANCE MATCH
# ============================================================

def insurance_matches(
    row_text: str,
    requested_insurance: str,
) -> bool:
    requested = normalize(requested_insurance)

    if not requested:
        return True

    text = normalize(row_text)

    aliases = {
        "care": [
            "care",
            "care health",
            "care health insurance",
        ],
        "niva bupa": [
            "niva bupa",
        ],
        "star health": [
            "star health",
            "star health insurance",
        ],
        "manipalcigna": [
            "manipalcigna",
            "manipal cigna",
        ],
        "aditya birla": [
            "aditya birla",
            "aditya birla health",
        ],
        "hdfc ergo": [
            "hdfc ergo",
        ],
        "icici lombard": [
            "icici lombard",
        ],
        "tata aig": [
            "tata aig",
        ],
        "bajaj allianz": [
            "bajaj allianz",
        ],
        "ClaimCare": [
            "ClaimCare",
        ],
    }

    for key, values in aliases.items():

        if key in requested:

            return any(
                normalize(alias) in text
                for alias in values
            )

    return requested in text


# ============================================================
# DOCTOR SCORING
# ============================================================

def score_doctor(
    row: pd.Series,
    df: pd.DataFrame,
    treatment: str,
    city: str,
    area: str,
    insurance_company: str,
    specialty: str,
    hospital: str,
) -> tuple[int, list[str], bool]:
    doctor_name = get_doctor_value(row, df, "name")
    doctor_specialty = get_doctor_value(row, df, "specialty")
    doctor_hospital = get_doctor_value(row, df, "hospital")
    doctor_area = get_doctor_value(row, df, "area")
    doctor_city = get_doctor_value(row, df, "city")
    doctor_treatment = get_doctor_value(row, df, "treatment")
    doctor_procedure = get_doctor_value(row, df, "procedure")
    doctor_history = get_doctor_value(row, df, "history")
    doctor_logic = get_doctor_value(row, df, "logic")
    doctor_insurance = get_doctor_value(row, df, "insurance")

    combined = " ".join(
        [
            doctor_treatment,
            doctor_procedure,
            doctor_history,
            doctor_logic,
        ]
    )

    score = 0
    reasons = []

    # --------------------------------------------------------
    # EXACT TREATMENT
    # --------------------------------------------------------

    if treatment:

        q = normalize(treatment)
        dt = normalize(doctor_treatment)

        if q == dt:
            score += 50
            reasons.append("Exact treatment match")

        elif q in dt or dt in q:
            score += 35
            reasons.append("Treatment match")

        else:
            treatment_words = words(treatment)

            matched = sum(
                1
                for word in treatment_words
                if word in dt or word in normalize(combined)
            )

            if treatment_words and matched == len(treatment_words):
                score += 25
                reasons.append("Treatment keyword match")

            elif matched > 0:
                score += 10
                reasons.append("Related treatment keyword")

    # --------------------------------------------------------
    # CITY
    # --------------------------------------------------------

    if city:
        q = normalize(city)
        c = normalize(doctor_city)

        if q == c:
            score += 15
            reasons.append("City match")

        elif q in c or c in q:
            score += 10
            reasons.append("City partial match")

    # --------------------------------------------------------
    # AREA
    # --------------------------------------------------------

    if area:
        q = normalize(area)
        a = normalize(doctor_area)

        if q == a:
            score += 20
            reasons.append("Exact area match")

        elif q in a or a in q:
            score += 15
            reasons.append("Area match")

        else:
            address_text = normalize(
                get_doctor_value(row, df, "address")
            )

            if q in address_text:
                score += 10
                reasons.append("Area found in address")

    # --------------------------------------------------------
    # SPECIALTY
    # --------------------------------------------------------

    if specialty:

        q = normalize(specialty)
        s = normalize(doctor_specialty)

        if q in s or s in q:
            score += 15
            reasons.append("Specialty match")

    # --------------------------------------------------------
    # HOSPITAL
    # --------------------------------------------------------

    if hospital:

        q = normalize(hospital)
        h = normalize(doctor_hospital)

        if q in h or h in q:
            score += 15
            reasons.append("Hospital match")

    # --------------------------------------------------------
    # PROCEDURE
    # --------------------------------------------------------

    if treatment and normalize(treatment) in normalize(doctor_procedure):
        score += 10
        reasons.append("Relevant procedure")

    # --------------------------------------------------------
    # CLINICAL HISTORY
    # --------------------------------------------------------

    if doctor_history:
        score += 3
        reasons.append("Clinical history available")

    # --------------------------------------------------------
    # RECOMMENDATION LOGIC
    # --------------------------------------------------------

    if doctor_logic:
        score += 3
        reasons.append("Recommendation logic available")

    # --------------------------------------------------------
    # INSURANCE
    # --------------------------------------------------------

    if insurance_company:

        if doctor_insurance:

            if insurance_matches(
                doctor_insurance,
                insurance_company,
            ):
                score += 10
                reasons.append("Insurance match")

            else:
                # If the dataset explicitly contains insurance
                # and requested insurer does not match, reject.
                return 0, [], False

        else:
            # Dataset has no insurer information for this row.
            # Don't reject the doctor.
            reasons.append(
                "Insurance not specified in dataset"
            )

    # --------------------------------------------------------
    # EXACT TREATMENT GATE
    # --------------------------------------------------------
    #
    # If treatment is provided and an exact treatment is present,
    # weak generic records should not enter the first result set.
    #

    exact_treatment_exists = (
        normalize(treatment)
        and normalize(treatment) == normalize(doctor_treatment)
    )

    return score, reasons, bool(exact_treatment_exists)


# ============================================================
# HOSPITAL SCORING
# ============================================================

def score_hospital(
    row: pd.Series,
    df: pd.DataFrame,
    treatment: str,
    city: str,
    area: str,
    insurance_company: str,
    specialty: str,
    hospital: str,
) -> tuple[int, list[str]]:
    hospital_name = get_hospital_value(
        row,
        df,
        "hospital",
    )

    hospital_specialty = get_hospital_value(
        row,
        df,
        "specialty",
    )

    hospital_area = get_hospital_value(
        row,
        df,
        "area",
    )

    hospital_city = get_hospital_value(
        row,
        df,
        "city",
    )

    hospital_address = get_hospital_value(
        row,
        df,
        "address",
    )

    hospital_treatment = get_hospital_value(
        row,
        df,
        "treatment",
    )

    hospital_facilities = get_hospital_value(
        row,
        df,
        "facilities",
    )

    hospital_insurance = get_hospital_value(
        row,
        df,
        "insurance",
    )

    score = 0
    reasons = []

    # Treatment
    if treatment:

        q = normalize(treatment)
        t = normalize(hospital_treatment)

        if q == t:
            score += 50
            reasons.append("Exact treatment match")

        elif q in t or t in q:
            score += 35
            reasons.append("Treatment match")

        else:
            q_words = words(treatment)

            matched = sum(
                1
                for word in q_words
                if word in t
            )

            if q_words and matched == len(q_words):
                score += 25
                reasons.append("Treatment keyword match")

            elif matched:
                score += 10
                reasons.append("Related treatment keyword")

    # City
    if city:

        q = normalize(city)
        c = normalize(hospital_city)

        if q == c:
            score += 15
            reasons.append("City match")

        elif q in c or c in q:
            score += 10
            reasons.append("City partial match")

    # Area
    if area:

        q = normalize(area)
        a = normalize(hospital_area)
        address = normalize(hospital_address)

        if q == a:
            score += 20
            reasons.append("Exact area match")

        elif q in a or a in q:
            score += 15
            reasons.append("Area match")

        elif q in address:
            score += 10
            reasons.append("Area found in address")

    # Specialty
    if specialty:

        q = normalize(specialty)
        s = normalize(hospital_specialty)

        if q in s or s in q:
            score += 15
            reasons.append("Specialty match")

    # Hospital
    if hospital:

        q = normalize(hospital)
        h = normalize(hospital_name)

        if q in h or h in q:
            score += 20
            reasons.append("Hospital match")

    # Insurance
    if insurance_company and hospital_insurance:

        if insurance_matches(
            hospital_insurance,
            insurance_company,
        ):
            score += 10
            reasons.append("Insurance match")
        else:
            return 0, []

    if hospital_facilities:
        reasons.append("Facilities information available")

    return score, reasons


# ============================================================
# DOCTOR RESULT
# ============================================================

def make_doctor_result(
    row: pd.Series,
    df: pd.DataFrame,
    score: int,
    reasons: list[str],
) -> dict[str, Any]:

    return {
        "record": get_doctor_value(
            row,
            df,
            "record",
        ) or str(row.name + 1),

        "doctor_name": get_doctor_value(
            row,
            df,
            "name",
        ),

        "specialty": get_doctor_value(
            row,
            df,
            "specialty",
        ),

        "hospital": get_doctor_value(
            row,
            df,
            "hospital",
        ),

        "branch_area": get_doctor_value(
            row,
            df,
            "area",
        ),

        "search_location": get_doctor_value(
            row,
            df,
            "area",
        ),

        "city": get_doctor_value(
            row,
            df,
            "city",
        ),

        "hospital_address": get_doctor_value(
            row,
            df,
            "address",
        ),

        "disease_treatment": get_doctor_value(
            row,
            df,
            "treatment",
        ),

        "relevant_procedure": get_doctor_value(
            row,
            df,
            "procedure",
        ),

        "procedure_clinical_history": get_doctor_value(
            row,
            df,
            "history",
        ),

        "recommendation_logic": get_doctor_value(
            row,
            df,
            "logic",
        ),

        "insurance_company": get_doctor_value(
            row,
            df,
            "insurance",
        ),

        "verification_source": (
            get_doctor_value(row, df, "logic")
            or "ClaimCare project dataset"
        ),

        "score": score,

        "match_reasons": reasons,
    }


# ============================================================
# HOSPITAL RESULT
# ============================================================

def make_hospital_result(
    row: pd.Series,
    df: pd.DataFrame,
    score: int,
    reasons: list[str],
) -> dict[str, Any]:

    return {
        "record": str(row.name + 1),

        "hospital": get_hospital_value(
            row,
            df,
            "hospital",
        ),

        "hospital_name": get_hospital_value(
            row,
            df,
            "hospital",
        ),

        "specialty": get_hospital_value(
            row,
            df,
            "specialty",
        ),

        "branch_area": get_hospital_value(
            row,
            df,
            "area",
        ),

        "area": get_hospital_value(
            row,
            df,
            "area",
        ),

        "city": get_hospital_value(
            row,
            df,
            "city",
        ),

        "address": get_hospital_value(
            row,
            df,
            "address",
        ),

        "hospital_address": get_hospital_value(
            row,
            df,
            "address",
        ),

        "treatment": get_hospital_value(
            row,
            df,
            "treatment",
        ),

        "facilities": get_hospital_value(
            row,
            df,
            "facilities",
        ),

        "insurance_company": get_hospital_value(
            row,
            df,
            "insurance",
        ),

        "score": score,

        "match_reasons": reasons,

        "verification_source": (
            "ClaimCare hospital dataset"
        ),
    }


# ============================================================
# HOSPITAL RECOMMENDATIONS
# ============================================================

def search_hospitals(
    treatment: str = "",
    city: str = "",
    area: str = "",
    insurance_company: str = "",
    specialty: str = "",
    hospital: str = "",
    limit: int = 10,
) -> list[dict[str, Any]]:

    df = load_hospitals()

    if df.empty:
        return []

    results = []

    for index, row in df.iterrows():

        score, reasons = score_hospital(
            row=row,
            df=df,
            treatment=treatment,
            city=city,
            area=area,
            insurance_company=insurance_company,
            specialty=specialty,
            hospital=hospital,
        )

        if score <= 0:
            continue

        item = make_hospital_result(
            row=row,
            df=df,
            score=score,
            reasons=reasons,
        )

        item["_index"] = index

        results.append(item)

    # Exact treatment first
    query_treatment = normalize(treatment)

    def hospital_sort(item):
        exact = (
            query_treatment
            and normalize(item.get("treatment", ""))
            == query_treatment
        )

        exact_area = (
            normalize(area)
            and normalize(item.get("area", ""))
            == normalize(area)
        )

        exact_city = (
            normalize(city)
            and normalize(item.get("city", ""))
            == normalize(city)
        )

        return (
            1 if exact else 0,
            1 if exact_area else 0,
            1 if exact_city else 0,
            item.get("score", 0),
        )

    results.sort(
        key=hospital_sort,
        reverse=True,
    )

    for item in results:
        item.pop("_index", None)

    return results[:limit]


# ============================================================
# DOCTOR RECOMMENDATIONS
# ============================================================

def search_doctors(
    treatment: str = "",
    city: str = "",
    area: str = "",
    insurance_company: str = "",
    specialty: str = "",
    hospital: str = "",
    limit: int = 10,
) -> list[dict[str, Any]]:

    df = load_doctors()

    if df.empty:
        return []

    # STRICT CITY FILTER - VERIFIED RECORDS ONLY
    if city and str(city).strip():
        requested_city = normalize(city)
        city_mask = df.apply(
            lambda row: normalize(
                get_doctor_value(row, df, "city")
            ) == requested_city,
            axis=1,
        )
        df = df.loc[city_mask].copy()

        if df.empty:
            return []
    candidates = []

    for index, row in df.iterrows():

        score, reasons, exact_treatment = score_doctor(
            row=row,
            df=df,
            treatment=treatment,
            city=city,
            area=area,
            insurance_company=insurance_company,
            specialty=specialty,
            hospital=hospital,
        )

        if score <= 0:
            continue

        item = make_doctor_result(
            row=row,
            df=df,
            score=score,
            reasons=reasons,
        )

        item["_index"] = index
        item["_exact_treatment"] = exact_treatment

        candidates.append(item)

    query_treatment = normalize(treatment)
    requested_area = normalize(area)
    requested_city = normalize(city)

    # STRICT AREA FILTER:
    # If a specific area is requested, do not return doctors from
    # unrelated branches as if they match that area.
    if requested_area:
        area_candidates = []

        for item in candidates:
            branch = normalize(item.get("branch_area", ""))
            address = normalize(item.get("hospital_address", ""))

            area_match = (
                branch == requested_area
                or bool(branch and (
                    requested_area in branch or branch in requested_area
                ))
                or bool(address and requested_area in address)
            )

            if area_match:
                area_candidates.append(item)

        candidates = area_candidates

    # Prefer exact treatment records within the selected candidate set.
    exact_results = [
        item for item in candidates
        if item.get("_exact_treatment")
    ]

    if query_treatment and exact_results:
        candidates = exact_results

    def doctor_sort(item):
        item_treatment = normalize(item.get("disease_treatment", ""))
        item_area = normalize(item.get("branch_area", ""))
        item_city = normalize(item.get("city", ""))

        exact_treatment = bool(
            query_treatment and item_treatment == query_treatment
        )
        exact_area = bool(
            requested_area and item_area == requested_area
        )
        exact_city = bool(
            requested_city and item_city == requested_city
        )

        return (
            1 if exact_area else 0,
            1 if exact_treatment else 0,
            1 if exact_city else 0,
            item.get("score", 0),
        )

    candidates.sort(key=doctor_sort, reverse=True)

    for item in candidates:
        item.pop("_index", None)
        item.pop("_exact_treatment", None)

    return candidates[:limit]


# ============================================================
# MAIN SEARCH
# ============================================================

def search_recommendations(
    treatment: str = "",
    city: str = "",
    area: str = "",
    insurance_company: str = "",
    specialty: str = "",
    hospital: str = "",
    limit: int = 10,
) -> dict[str, Any]:

    limit = max(
        1,
        min(int(limit or 10), 10),
    )

    treatment = clean_text(treatment)
    city = clean_text(city)
    area = clean_text(area)
    insurance_company = clean_text(
        insurance_company
    )
    specialty = clean_text(specialty)
    hospital = clean_text(hospital)

    hospitals = search_hospitals(
        treatment=treatment,
        city=city,
        area=area,
        insurance_company=insurance_company,
        specialty=specialty,
        hospital=hospital,
        limit=limit,
    )

    doctors = search_doctors(
        treatment=treatment,
        city=city,
        area=area,
        insurance_company=insurance_company,
        specialty=specialty,
        hospital=hospital,
        limit=limit,
    )

    return {
        "success": True,

        "query": {
            "treatment": treatment,
            "city": city,
            "area": area,
            "insurance_company": insurance_company,
            "specialty": specialty,
            "hospital": hospital,
        },

        "hospitals": hospitals,

        "doctors": doctors,

        "hospital_count": len(hospitals),

        "doctor_count": len(doctors),

        "message": (
            "Hospital and doctor recommendations generated "
            "directly from the ClaimCare project "
            "datasets."
        ),

        "dataset_sources": {
            "hospitals": str(HOSPITALS_XLSX),
            "doctors_csv": str(DOCTORS_CSV),
            "doctors_pdf": str(DOCTORS_PDF),
        },

        "disclaimer": (
            "Recommendations are based on the available "
            "project datasets. Insurance coverage, network "
            "status, cashless availability, doctor availability "
            "and final claim approval must be verified with the "
            "applicable hospital and insurance provider."
        ),
    }