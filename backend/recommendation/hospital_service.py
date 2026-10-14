from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd


# ============================================================
# ClaimCare
# HOSPITAL RECOMMENDATION SERVICE
#
# Source:
#   backend/recommendation/data/hospitals.xlsx
#
# Important:
#   Hospital records are NEVER hardcoded here.
#   All recommendations come from the Excel dataset.
# ============================================================


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "hospitals.xlsx"


# ============================================================
# NORMALIZATION
# ============================================================

def _normalize(value: Any) -> str:
    """
    Convert a dataset value or user input into a normalized
    lowercase string suitable for comparison.
    """

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    text = str(value)

    # Normalize common separators
    text = text.replace("\r", " ")
    text = text.replace("\n", " ")
    text = text.replace("|", ";")
    text = text.replace(",", ";")

    # Normalize multiple spaces
    text = " ".join(text.split())

    return text.strip().lower()


def _clean_display(value: Any) -> str:
    """
    Preserve readable dataset text for API output.
    """

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value).strip()


def _contains(value: Any, search: str) -> bool:
    """
    Case-insensitive partial match.
    """

    value_text = _normalize(value)
    search_text = _normalize(search)

    if not search_text:
        return False

    return search_text in value_text


def _token_match(value: Any, search: str) -> bool:
    """
    More flexible comparison for values that may contain
    multiple semicolon-separated entries.
    """

    value_text = _normalize(value)
    search_text = _normalize(search)

    if not value_text or not search_text:
        return False

    if search_text in value_text:
        return True

    # Split common dataset separators
    parts = [
        part.strip()
        for part in value_text.replace(",", ";").split(";")
        if part.strip()
    ]

    for part in parts:
        if search_text == part:
            return True

        if search_text in part:
            return True

        if part in search_text:
            return True

    return False


# ============================================================
# DATASET LOADING
# ============================================================

def load_hospitals() -> pd.DataFrame:
    """
    Load and validate the hospital Excel dataset.
    """

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Hospital dataset not found: {DATA_FILE}"
        )

    df = pd.read_excel(DATA_FILE)

    # Clean column names
    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    required_columns = [
        "City",
        "Area",
        "Hospital",
        "Specialty",
        "Treatments",
        "Insurance Companies",
        "Cashless",
        "Emergency",
        "Distance Zone",
        "Recommendation",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing hospital dataset columns: {missing}"
        )

    # Replace NaN values
    df = df.fillna("")

    return df


# ============================================================
# MATCH HELPERS
# ============================================================

def _treatment_match(row: pd.Series, treatment: str) -> bool:
    """
    Treatment is the primary hospital filter.

    A hospital is returned only when the requested treatment
    exists in the Treatments field of the dataset.
    """

    if not treatment:
        return True

    return _token_match(
        row.get("Treatments", ""),
        treatment,
    )


def _city_match(row: pd.Series, city: str) -> bool:
    """
    City is a hard filter when supplied.
    """

    if not city:
        return True

    requested = _normalize(city)
    actual = _normalize(row.get("City", ""))

    if not requested:
        return True

    return requested == actual or requested in actual


def _area_match(row: pd.Series, area: str) -> bool:
    """
    Area is a ranking/filtering preference.

    It is NOT a hard filter because a nearby hospital may be
    in another area of the same city.
    """

    if not area:
        return False

    return _token_match(
        row.get("Area", ""),
        area,
    )


def _insurance_match(
    row: pd.Series,
    insurance_company: str,
) -> bool:
    """
    Insurance is a ranking preference.

    It is not a hard filter because the project should still
    show hospitals for the requested treatment/location when
    network information needs to be verified.
    """

    if not insurance_company:
        return False

    return _token_match(
        row.get("Insurance Companies", ""),
        insurance_company,
    )


# ============================================================
# SCORE CALCULATION
# ============================================================

def _calculate_score(
    row: pd.Series,
    treatment: str = "",
    city: str = "",
    area: str = "",
    insurance_company: str = "",
) -> Tuple[int, List[str]]:

    score = 0
    reasons: List[str] = []

    # --------------------------------------------------------
    # Treatment = 40
    # --------------------------------------------------------

    if treatment and _treatment_match(row, treatment):
        score += 40
        reasons.append("Treatment match")

    # --------------------------------------------------------
    # City = 15
    # --------------------------------------------------------

    if city and _city_match(row, city):
        score += 15
        reasons.append("City match")

    # --------------------------------------------------------
    # Area = 20
    # --------------------------------------------------------

    if area and _area_match(row, area):
        score += 20
        reasons.append("Area match")

    # --------------------------------------------------------
    # Insurance = 10
    # --------------------------------------------------------

    if insurance_company and _insurance_match(
        row,
        insurance_company,
    ):
        score += 10
        reasons.append("Insurance company listed")

    # --------------------------------------------------------
    # Cashless = 5
    # --------------------------------------------------------

    cashless = _normalize(
        row.get("Cashless", "")
    )

    if cashless in {
        "yes",
        "true",
        "available",
        "cashless",
        "verify",
    }:
        score += 5

        if cashless == "verify":
            reasons.append(
                "Cashless status should be verified"
            )
        else:
            reasons.append("Cashless available")

    # --------------------------------------------------------
    # Recommendation = 5
    # --------------------------------------------------------

    recommendation = _normalize(
        row.get("Recommendation", "")
    )

    recommendation_keywords = [
        "high match",
        "highly recommended",
        "recommended",
        "best",
        "strong match",
    ]

    if any(
        keyword in recommendation
        for keyword in recommendation_keywords
    ):
        score += 5
        reasons.append("Recommended in dataset")

    # --------------------------------------------------------
    # Emergency = 5
    # --------------------------------------------------------

    emergency = _normalize(
        row.get("Emergency", "")
    )

    if emergency in {
        "yes",
        "true",
        "available",
        "emergency",
    }:
        score += 5
        reasons.append("Emergency facility")

    return score, reasons


# ============================================================
# HOSPITAL RECOMMENDATION
# ============================================================

def recommend_hospitals(
    treatment: str = "",
    city: str = "",
    area: str = "",
    insurance_company: str = "",
    limit: int = 5,
) -> List[Dict[str, Any]]:

    df = load_hospitals()

    treatment = str(treatment or "").strip()
    city = str(city or "").strip()
    area = str(area or "").strip()
    insurance_company = str(insurance_company or "").strip()

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 5

    limit = max(1, min(limit, 50))

    # --------------------------------------------------------
    # STEP 1 — Treatment hard filter
    # --------------------------------------------------------

    if treatment:
        treatment_mask = df["Treatments"].apply(
            lambda value: _treatment_match(
                pd.Series({"Treatments": value}),
                treatment,
            )
        )

        df = df[treatment_mask]

        if df.empty:
            return []

    # --------------------------------------------------------
    # STEP 2 — City hard filter
    # --------------------------------------------------------

    if city:
        normalized_city = _normalize(city)

        city_mask = df["City"].apply(
            lambda value: (
                _normalize(value) == normalized_city
                or normalized_city in _normalize(value)
            )
        )

        df = df[city_mask]

        if df.empty:
            return []

    # --------------------------------------------------------
    # STEP 3 — AREA HARD FILTER
    #
    # If user selects Porur, ONLY Porur hospitals are returned.
    # No Anna Nagar / Adyar / Tambaram fallback.
    # --------------------------------------------------------

    if area:
        normalized_area = _normalize(area)

        area_mask = df["Area"].apply(
            lambda value: (
                _normalize(value) == normalized_area
                or normalized_area in _normalize(value)
                or _normalize(value) in normalized_area
            )
        )

        df = df[area_mask]

        if df.empty:
            return []

    # --------------------------------------------------------
    # STEP 4 — Build ranked results
    # --------------------------------------------------------

    results: List[Dict[str, Any]] = []

    for _, row in df.iterrows():

        score, reasons = _calculate_score(
            row=row,
            treatment=treatment,
            city=city,
            area=area,
            insurance_company=insurance_company,
        )

        result = {
            "hospital": _clean_display(
                row.get("Hospital", "")
            ),

            "city": _clean_display(
                row.get("City", "")
            ),

            "area": _clean_display(
                row.get("Area", "")
            ),

            "specialty": _clean_display(
                row.get("Specialty", "")
            ),

            "treatments": _clean_display(
                row.get("Treatments", "")
            ),

            "insurance_companies": [
                item.strip()
                for item in str(
                    row.get("Insurance Companies", "")
                ).split(";")
                if item.strip()
            ],

            "cashless": _clean_display(
                row.get("Cashless", "")
            ),

            "emergency": _clean_display(
                row.get("Emergency", "")
            ),

            "distance_zone": _clean_display(
                row.get("Distance Zone", "")
            ),

            "recommendation": _clean_display(
                row.get("Recommendation", "")
            ),

            "score": score,

            "match_reasons": reasons,
        }

        results.append(result)

    # --------------------------------------------------------
    # STEP 5 — Insurance preference ranking
    #
    # Insurance does NOT remove hospitals.
    # It only changes their ranking.
    # --------------------------------------------------------

    results.sort(
        key=lambda item: item.get("score", 0),
        reverse=True,
    )

    return results[:limit]

def hospital_dataset_health() -> Dict[str, Any]:
    """
    Return hospital dataset health information.
    """

    df = load_hospitals()

    return {
        "status": "healthy",
        "dataset": str(DATA_FILE),
        "source_type": "Excel",
        "records": len(df),
        "columns": list(df.columns),
        "cities": sorted(
            {
                _clean_display(value)
                for value in df["City"]
                if _clean_display(value)
            }
        ),
        "areas": sorted(
            {
                _clean_display(value)
                for value in df["Area"]
                if _clean_display(value)
            }
        ),
        "treatments": sorted(
            {
                treatment.strip()
                for value in df["Treatments"]
                for treatment in str(value).split(";")
                if treatment.strip()
            }
        ),
    }

