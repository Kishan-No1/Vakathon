"""GET /attribution/{plume_id} — Person B's route.

Returns the full attribution result for one plume: facility match (or an
explicit no-match), confidence + method, regulator routing, and display text.

LEGAL FRAMING (core feature): the response NEVER asserts a company is leaking
or violating any rule. Matched results are phrased as "consistent with ...,
pending verification"; unmatched results say no facility could be confidently
matched. Frontend must render `display_statement` verbatim.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.attribution.confidence_score import score
from backend.attribution.features import pair_features
from backend.attribution.regulator_lookup import lookup as regulator_lookup
from backend.attribution.spatial_join import (
    MAX_MATCH_DISTANCE_M,
    load_facilities,
    load_plumes,
    nearest_facility,
)

router = APIRouter(tags=["attribution"])


def _display_statement(att: dict) -> str:
    if att["matched"]:
        return (
            f"This detection is consistent with {att['facility_name']} "
            f"(operator: {att['operator']}), located {att['distance_m']:.0f} m away. "
            f"This is a possible association pending verification, not a confirmed "
            f"source and not an allegation of wrongdoing."
        )
    return (
        f"No facility could be confidently matched to this detection within "
        f"{MAX_MATCH_DISTANCE_M / 1000:.0f} km (nearest known facility: "
        f"{att['nearest_distance_m']:.0f} m). The source operator is not identified."
    )


def attribute(plume_id: str) -> dict:
    """Pure-Python attribution result (also callable without FastAPI)."""
    att = nearest_facility(plume_id)
    if att is None:
        return {}

    confidence, method = None, None
    if att["matched"]:
        plumes, facilities = load_plumes(), load_facilities()
        plume = plumes[plumes["plume_id"] == plume_id].iloc[0]
        facility = facilities[facilities["facility_id"] == att["facility_id"]].iloc[0]
        confidence, method = score(pair_features(plume, facility, facilities))

    return {
        **att,
        "confidence": confidence,
        "confidence_method": method,
        "regulator": regulator_lookup(att["state"]),
        "display_statement": _display_statement(att),
    }


@router.get("/attribution/{plume_id}")
def get_attribution(plume_id: str) -> dict:
    result = attribute(plume_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"unknown plume_id: {plume_id}")
    return result
