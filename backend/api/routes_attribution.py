"""GET /attribution/{plume_id} and GET /attribution/by-location — Person B's routes.

Returns the full attribution result for one plume (or an arbitrary point):
facility match (or an explicit no-match), confidence + method, regulator
routing, and display text.

LEGAL FRAMING (core feature): the response NEVER asserts a company is leaking
or violating any rule. Matched results are phrased as "consistent with ...,
pending verification"; unmatched results say no facility could be confidently
matched. Frontend must render `display_statement` verbatim.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.attribution.confidence_score import hand_tuned_score, score
from backend.attribution.features import location_features, pair_features, wind_consistency
from backend.attribution.regulator_lookup import lookup as regulator_lookup
from backend.attribution.spatial_join import (
    MAX_MATCH_DISTANCE_M,
    load_facilities,
    load_plumes,
    nearest_facility,
    nearest_facility_for_point,
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


def _display_statement_location(att: dict, state_known: bool) -> str:
    if att["matched"]:
        return (
            f"This location is consistent with {att['facility_name']} "
            f"(operator: {att['operator']}), located {att['distance_m']:.0f} m away. "
            f"This is a possible association pending verification, not a confirmed "
            f"source and not an allegation of wrongdoing."
        )
    base = (
        f"No facility could be confidently matched to this location within "
        f"{MAX_MATCH_DISTANCE_M / 1000:.0f} km (nearest known facility: "
        f"{att['nearest_distance_m']:.0f} m). The source operator is not identified."
    )
    if not state_known:
        base += (
            " Jurisdiction could not be determined for this location; "
            "provide a state to look up the applicable regulator."
        )
    return base


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


def attribute_location(lat: float, lon: float, state: str | None = None) -> dict:
    """Pure-Python by-location attribution result (arbitrary coordinates, not
    a known plume_id — e.g. a resident-pinned location with no satellite
    leak-rate/wind data). Always returns a dict; never 404s.

    Confidence always comes from the hand-tuned scorer, never the trained
    model: the model was fit on satellite-plume feature distributions
    (leak_rate_kg_hr in particular) that a bare coordinate doesn't have, and
    hand_tuned_score() conveniently needs only distance/wind/state_match —
    all computable here.

    State resolution: an explicit `state` argument always wins. If omitted
    and matched, defaults to the matched facility's own state (real data, not
    a guess). If omitted and unmatched, state is None and no regulator is
    returned — jurisdiction is never guessed.
    """
    att = nearest_facility_for_point(lat, lon)
    resolved_state = state if state is not None else att["state"]

    confidence, method = None, None
    if att["matched"]:
        wc = wind_consistency(lat, lon, att["facility_lat"], att["facility_lon"], None)
        state_match = resolved_state is None or resolved_state == att["state"]
        confidence = hand_tuned_score(
            location_features(att["distance_m"], wc, state_match))
        method = "hand_tuned_fallback"

    return {
        **att,
        "state": resolved_state,
        "confidence": confidence,
        "confidence_method": method,
        "regulator": regulator_lookup(resolved_state) if resolved_state else None,
        "display_statement": _display_statement_location(att, resolved_state is not None),
    }


# Registered BEFORE /attribution/{plume_id}: that route's {plume_id} is an
# unconstrained string and would otherwise swallow /attribution/by-location
# as plume_id="by-location" (FastAPI/Starlette matches in registration
# order), returning a spurious 404 instead of this route.
@router.get("/attribution/by-location")
def get_attribution_by_location(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    # Optional[str] (not `str | None`) so this builds on Python 3.9 too
    state: Optional[str] = Query(
        None, description="Optional state override for regulator lookup, e.g. 'New Mexico'"),
) -> dict:
    return attribute_location(lat, lon, state)


@router.get("/attribution/{plume_id}")
def get_attribution(plume_id: str) -> dict:
    result = attribute(plume_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"unknown plume_id: {plume_id}")
    return result
