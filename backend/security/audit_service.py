import os
import json
from datetime import datetime
from typing import Optional


PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

AUDIT_DIR = os.path.join(
    PROJECT_ROOT,
    "backend",
    "security",
    "logs"
)

AUDIT_FILE = os.path.join(
    AUDIT_DIR,
    "security_audit.json"
)


def _ensure_storage():
    os.makedirs(AUDIT_DIR, exist_ok=True)

    if not os.path.exists(AUDIT_FILE):
        with open(
            AUDIT_FILE,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump([], file, indent=2)


def log_security_event(
    claim_id: str,
    action: str,
    status: str,
    risk_level: Optional[str] = None,
    security_score: Optional[int] = None,
    decision: Optional[str] = None,
    user: Optional[str] = None,
    details: Optional[dict] = None
):
    _ensure_storage()

    try:
        with open(
            AUDIT_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            events = json.load(file)

        if not isinstance(events, list):
            events = []

    except Exception:
        events = []

    event = {
        "event_id": f"SEC-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "timestamp": datetime.now().isoformat(),
        "claim_id": claim_id or "",
        "user": user or "system",
        "action": action,
        "status": status,
        "risk_level": risk_level,
        "security_score": security_score,
        "decision": decision,
        "details": details or {}
    }

    events.append(event)

    with open(
        AUDIT_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            events,
            file,
            indent=2
        )

    return event


def get_security_events(
    claim_id: Optional[str] = None
):
    _ensure_storage()

    try:
        with open(
            AUDIT_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            events = json.load(file)

        if not isinstance(events, list):
            return []

    except Exception:
        return []

    if claim_id:
        return [
            event
            for event in events
            if event.get("claim_id") == claim_id
        ]

    return events


def clear_security_events():
    _ensure_storage()

    with open(
        AUDIT_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump([], file, indent=2)

    return True
