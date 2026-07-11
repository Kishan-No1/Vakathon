"""Feature extraction for (plume, facility) pairs.

Only features we can actually compute from the real data:
  distance_m             haversine plume -> facility
  wind_consistency       0..1, alignment of the facility->plume bearing with the
                         downwind direction (plume origin should sit downwind of
                         its true source). 0.5 = uninformative.
  leak_rate_kg_hr        plume magnitude
  operator_well_density  same-operator facilities within 2 km of the candidate
                         (weak proxy for site scale; first cut per plan §6)
  state_match            1 if plume and facility are in the same state

Wind convention: Carbon Mapper's wind_dir_deg is meteorological (direction the
wind blows FROM, HRRR model), so downwind = wind_dir + 180.
"""
from __future__ import annotations

import math

import pandas as pd

from .spatial_join import haversine_m, load_facilities

FEATURE_NAMES = [
    "distance_m",
    "wind_consistency",
    "leak_rate_kg_hr",
    "operator_well_density",
    "state_match",
]

# below this separation the bearing is dominated by geolocation noise
_BEARING_NOISE_FLOOR_M = 150.0


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial bearing from point 1 to point 2, degrees clockwise from north."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0


def wind_consistency(plume_lat: float, plume_lon: float,
                     facility_lat: float, facility_lon: float,
                     wind_dir_deg: float | None) -> float:
    """1.0 = plume sits exactly downwind of the facility, 0.0 = exactly upwind,
    0.5 = perpendicular/uninformative. Returns 0.5 when wind is missing or the
    pair is too close for the bearing to mean anything."""
    if wind_dir_deg is None or pd.isna(wind_dir_deg):
        return 0.5
    sep = haversine_m(facility_lat, facility_lon, plume_lat, plume_lon)
    if sep < _BEARING_NOISE_FLOOR_M:
        return 0.5
    downwind = (wind_dir_deg + 180.0) % 360.0
    b = bearing_deg(facility_lat, facility_lon, plume_lat, plume_lon)
    return (math.cos(math.radians(b - downwind)) + 1.0) / 2.0


def operator_well_density(facility_row: pd.Series,
                          facilities: pd.DataFrame | None = None,
                          radius_m: float = 2000.0) -> int:
    """Count of OTHER facilities by the same operator within radius_m."""
    if facilities is None:
        facilities = load_facilities()
    same = facilities[(facilities["operator"] == facility_row["operator"])
                      & (facilities["facility_id"] != facility_row["facility_id"])]
    if same.empty:
        return 0
    return int(sum(
        haversine_m(facility_row["lat"], facility_row["lon"], r.lat, r.lon) <= radius_m
        for r in same.itertuples()
    ))


def pair_features(plume: pd.Series, facility: pd.Series,
                  facilities: pd.DataFrame | None = None) -> dict:
    """Feature dict for one (plume, facility) candidate pair.
    `plume` needs lat, lon, leak_rate_kg_hr, state, wind_dir_deg;
    `facility` needs facility_id, operator, lat, lon, state."""
    return {
        "distance_m": haversine_m(plume["lat"], plume["lon"],
                                  facility["lat"], facility["lon"]),
        "wind_consistency": wind_consistency(
            plume["lat"], plume["lon"], facility["lat"], facility["lon"],
            plume.get("wind_dir_deg")),
        "leak_rate_kg_hr": float(plume["leak_rate_kg_hr"]),
        "operator_well_density": operator_well_density(facility, facilities),
        "state_match": int(plume["state"] == facility["state"]),
    }


def features_frame(pairs: list[tuple[pd.Series, pd.Series]],
                   facilities: pd.DataFrame | None = None) -> pd.DataFrame:
    """Feature matrix (columns = FEATURE_NAMES) for a list of pairs."""
    if facilities is None:
        facilities = load_facilities()
    return pd.DataFrame([pair_features(p, f, facilities) for p, f in pairs],
                        columns=FEATURE_NAMES)


def location_features(distance_m: float, wind_consistency_val: float,
                      state_match: bool) -> dict:
    """Feature dict for a by-location candidate (an arbitrary resident-pinned
    point, not a satellite-detected plume) — omits leak_rate_kg_hr and
    operator_well_density, which don't exist for a bare coordinate. Valid
    input for confidence_score.hand_tuned_score() only: the trained model's
    schema requires the full FEATURE_NAMES columns, and would silently be
    fed a distribution it never saw in training."""
    return {
        "distance_m": distance_m,
        "wind_consistency": wind_consistency_val,
        "state_match": int(state_match),
    }
