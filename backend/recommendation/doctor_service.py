
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Dict, List


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "doctors.csv"
PDF_PATH = BASE_DIR / "data" / "doctors.pdf"


def _normalise(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _normalise_search(value: Any) -> str:
    return _normalise(value).lower()


def _load_records() -> List[Dict[str, str]]:
    """
    Use the CSV only as structured field data.
    A doctor and hospital must both be present in the source PDF.
    If the PDF is unavailable or unreadable, return no records.
    """
    if not PDF_PATH.exists():
        print(f"[DOCTORS] Source PDF missing: {PDF_PATH}")
        return []

    try:
        from pypdf import PdfReader
        reader = PdfReader(str(PDF_PATH))
        pdf_text = " ".join(
            page.extract_text() or "" for page in reader.pages
        )
    except Exception as exc:
        print(f"[DOCTORS] Cannot read source PDF: {exc}")
        return []

    def key(value: Any) -> str:
        value = _normalise(value).lower()
        return re.sub(r"[^a-z0-9]+", " ", value).strip()

    pdf_key = key(pdf_text)
    if not pdf_key:
        print("[DOCTORS] PDF has no extractable text; returning no records.")
        return []

    if not CSV_PATH.exists():
        print(f"[DOCTORS] Structured CSV missing: {CSV_PATH}")
        return []

    try:
        with CSV_PATH.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            rows = [
                {
                    _normalise(k): _normalise(v)
                    for k, v in row.items()
                    if k is not None
                }
                for row in csv.DictReader(file)
            ]
    except Exception as exc:
        print(f"[DOCTORS] Cannot read structured records: {exc}")
        return []

    verified = []
    for row in rows:
        name = key(row.get("Doctor Name", ""))
        hospital = key(row.get("Hospital", ""))

        if not name or not hospital:
            continue

        # Both identifying fields must be present in the PDF text.
        if name in pdf_key and hospital in pdf_key:
            verified.append(row)

    print(
        f"[DOCTORS] PDF-verified doctor records: "
        f"{len(verified)} / {len(rows)}"
    )
    return verified

def _treatment_match(
    query: str,
    disease_treatment: str,
    procedure: str,
    history: str,
) -> tuple[int, str]:
    """Match only terms supported by the stored treatment/procedure fields."""
    query_norm = _normalise_search(query)

    if not query_norm:
        return 0, ""

    disease_norm = _normalise_search(disease_treatment)
    procedure_norm = _normalise_search(procedure)
    history_norm = _normalise_search(history)

    if query_norm == disease_norm:
        return 50, "Exact treatment match"

    if query_norm in disease_norm:
        return 45, "Treatment match"

    if disease_norm and disease_norm in query_norm:
        return 35, "Related treatment match"

    if query_norm in procedure_norm:
        return 30, "Procedure relevance"

    if query_norm in history_norm:
        return 25, "Clinical history relevance"

    # Carefully handle common equivalent terms.
    aliases = {
        "kidney stone": (
            "kidney stone", "kidney stones", "renal stone",
            "renal stones", "nephrolithiasis",
        ),
        "appendectomy": (
            "appendectomy", "appendicitis", "appendix surgery",
        ),
        "hernia repair": (
            "hernia", "hernia repair", "hernia surgery",
        ),
        "gallbladder surgery": (
            "gallbladder", "cholecystectomy",
        ),
        "thyroid surgery": (
            "thyroid", "thyroidectomy",
        ),
    }

    terms = aliases.get(query_norm, ())

    for term in terms:
        term_norm = _normalise_search(term)
        if (
            term_norm
            and (
                term_norm in disease_norm
                or term_norm in procedure_norm
                or term_norm in history_norm
            )
        ):
            return 35, "Related treatment/procedure match"

    return 0, ""


def recommend_doctors(
    treatment: str = "",
    city: str = "",
    area: str = "",
    hospital: str = "",
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Search CSV doctor records using treatment and location filters."""

    limit = max(1, min(int(limit), 50))

    treatment = _normalise(treatment)
    city = _normalise(city)
    area = _normalise(area)
    hospital = _normalise(hospital)

    records = _load_records()
    results: List[Dict[str, Any]] = []

    for record in records:
        doctor_name = record.get("Doctor Name", "")
        specialty = record.get("Specialty", "")
        hospital_name = record.get("Hospital", "")
        branch_area = record.get("Branch / Area", "")
        record_city = record.get("City", "")
        disease_treatment = record.get("Disease / Treatment", "")
        search_location = record.get("Search Location", "")
        hospital_address = record.get("Hospital Address", "")
        procedure = record.get("Relevant Procedure", "")
        history = record.get("Procedure / Clinical History", "")
        recommendation_logic = record.get("Recommendation Logic", "")
        verification_source = record.get("Verification Source", "")

        if city and _normalise_search(city) != _normalise_search(record_city):
            continue

        # STRICT AREA FILTER: use the real branch or actual address.
        # "Vadapalani" and "Vadapalani Branch" are equivalent labels.
        area_filter = _normalise_search(area)

        if area_filter and area_filter in ("any area", "all areas"):
            area_filter = ""

        if area_filter:
            def area_key(value):
                value = _normalise_search(value)
                value = re.sub(r"\\bbranch\\b", " ", value)
                return re.sub(r"\\s+", " ", value).strip()

            requested_area = area_key(area_filter)
            actual_branch = area_key(branch_area)
            actual_search_location = area_key(search_location)
            actual_address = area_key(hospital_address)

            area_matches = (
                requested_area == actual_branch
                or requested_area == actual_search_location
                or bool(
                    requested_area
                    and requested_area in actual_address
                )
            )

            if not area_matches:
                continue

        if hospital and _normalise_search(hospital) not in _normalise_search(hospital_name):
            continue

        treatment_score, treatment_reason = _treatment_match(
            treatment,
            disease_treatment,
            procedure,
            history,
        )

        # Never return unrelated doctors for a treatment-specific search.
        if treatment and treatment_score == 0:
            continue

        score = treatment_score
        reasons: List[str] = []

        if treatment_reason:
            reasons.append(treatment_reason)

        if area and _normalise_search(area) not in ("any area", "all areas"):
            score += 20
            reasons.append("Area match")

        if city:
            score += 15
            reasons.append("City match")

        results.append({
            "record": record.get("Record", ""),
            "doctor_name": doctor_name,
            "specialty": specialty,
            "hospital": hospital_name,
            "branch_area": branch_area,
            "city": record_city,
            "hospital_address": hospital_address,
            "disease_treatment": disease_treatment,
            "search_location": search_location,
            "relevant_procedure": procedure,
            "procedure_clinical_history": history,
            "recommendation_logic": recommendation_logic,
            "verification_source": verification_source,
            "score": score,
            "match_reasons": reasons,
        })

    results.sort(
        key=lambda item: (
            item.get("score", 0),
            item.get("doctor_name", ""),
        ),
        reverse=True,
    )

    unique: Dict[tuple[str, str, str], Dict[str, Any]] = {}

    for result in results:
        key = (
            _normalise_search(result.get("doctor_name")),
            _normalise_search(result.get("hospital")),
            _normalise_search(result.get("branch_area")),
        )
        if key not in unique or result["score"] > unique[key]["score"]:
            unique[key] = result

    final_results = list(unique.values())
    final_results.sort(
        key=lambda item: (
            item.get("score", 0),
            item.get("doctor_name", ""),
        ),
        reverse=True,
    )

    return final_results[:limit]


def doctor_dataset_health() -> Dict[str, Any]:
    """Return health information for the doctor CSV dataset."""
    records = _load_records()

    return {
        "source": str(CSV_PATH),
        "source_type": "CSV",
        "records": len(records),
        "hospitals": len({
            row.get("Hospital", "").strip()
            for row in records if row.get("Hospital", "").strip()
        }),
        "cities": len({
            row.get("City", "").strip()
            for row in records if row.get("City", "").strip()
        }),
        "treatments": len({
            row.get("Disease / Treatment", "").strip()
            for row in records
            if row.get("Disease / Treatment", "").strip()
        }),
        "status": "healthy",
    }