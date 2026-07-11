"""Load the three committed CSVs under /data. Replaces all live fetchers (plan §0)."""
import csv
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _read_csv(name: str) -> list[dict]:
    with open(DATA_DIR / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@lru_cache(maxsize=1)
def load_plumes() -> list[dict]:
    rows = _read_csv("plumes.csv")
    for r in rows:
        r["lat"] = float(r["lat"])
        r["lon"] = float(r["lon"])
        r["leak_rate_kg_hr"] = float(r["leak_rate_kg_hr"])
        r["wind_speed_kmh"] = float(r.get("wind_speed_kmh") or 0)
        r["wind_dir_deg"] = float(r.get("wind_dir_deg") or 0)
    return rows


@lru_cache(maxsize=1)
def load_facilities() -> list[dict]:
    rows = _read_csv("facilities.csv")
    for r in rows:
        r["lat"] = float(r["lat"])
        r["lon"] = float(r["lon"])
    return rows


@lru_cache(maxsize=1)
def load_regulators() -> dict[str, dict]:
    return {r["state"]: r for r in _read_csv("regulators.csv")}


def get_plume(plume_id: str) -> dict | None:
    return next((p for p in load_plumes() if p["plume_id"] == plume_id), None)
