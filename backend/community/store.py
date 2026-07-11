"""JSON-file community store (plan: SQLite/JSON — JSON chosen for hackathon simplicity).

Person A: owns this module; swap to SQLite if concurrency becomes an issue.
Persists across restarts so co-sign counts survive a page refresh (checklist §5.6).
"""
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

STORE_PATH = Path(__file__).resolve().parent / "community_store.json"
_LOCK = threading.Lock()

# Reports needed near a plume before the UI shows a confidence bump
CONFIDENCE_BUMP_MIN_REPORTS = 2
CONFIDENCE_BUMP = 0.05


def _load() -> dict:
    if STORE_PATH.exists():
        return json.loads(STORE_PATH.read_text())
    return {"reports": {}, "cosigns": {}}


def _save(data: dict) -> None:
    STORE_PATH.write_text(json.dumps(data, indent=2))


def add_report(plume_id: str, report: dict) -> dict:
    with _LOCK:
        data = _load()
        report["submitted_at"] = datetime.now(timezone.utc).isoformat()
        data["reports"].setdefault(plume_id, []).append(report)
        _save(data)
        return _report_summary(data, plume_id)


def get_reports(plume_id: str) -> dict:
    with _LOCK:
        return _report_summary(_load(), plume_id)


def _report_summary(data: dict, plume_id: str) -> dict:
    reports = data["reports"].get(plume_id, [])
    bumped = len(reports) >= CONFIDENCE_BUMP_MIN_REPORTS
    return {
        "plume_id": plume_id,
        "reports": reports,
        "count": len(reports),
        "confidence_bump": CONFIDENCE_BUMP if bumped else 0.0,
    }


def add_cosign(plume_id: str, name: str, zip_code: str) -> dict:
    with _LOCK:
        data = _load()
        entry = data["cosigns"].setdefault(plume_id, {"signers": []})
        entry["signers"].append(
            {"name": name, "zip": zip_code,
             "signed_at": datetime.now(timezone.utc).isoformat()}
        )
        _save(data)
        return {"plume_id": plume_id, "count": len(entry["signers"]),
                "signers": entry["signers"]}


def get_cosigns(plume_id: str) -> dict:
    with _LOCK:
        entry = _load()["cosigns"].get(plume_id, {"signers": []})
        return {"plume_id": plume_id, "count": len(entry["signers"]),
                "signers": entry["signers"]}
