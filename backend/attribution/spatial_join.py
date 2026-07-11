"""Nearest-facility spatial join with a hard confidence threshold.

Core safety rule (a feature, not an afterthought): if the nearest facility is
farther than MAX_MATCH_DISTANCE_M, the plume gets NO match — the app must say
"no facility could be confidently matched" rather than guess. All matched
output is an association pending verification, never an accusation.

Uses geopandas sjoin_nearest in a projected CRS (UTM 13N covers the Permian);
falls back to a plain haversine scan if geopandas is unavailable at runtime.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import pandas as pd

# repo_root/backend/attribution/spatial_join.py -> repo_root/data
DATA_DIR = Path(__file__).resolve().parents[2] / "data"

MAX_MATCH_DISTANCE_M = 2000.0
_UTM_PERMIAN = "EPSG:32613"  # UTM zone 13N; fine for lon -108..-102


@lru_cache(maxsize=1)
def load_plumes() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "plumes.csv")


@lru_cache(maxsize=1)
def load_facilities() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "facilities.csv")


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters."""
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _join_geopandas(plumes: pd.DataFrame, facilities: pd.DataFrame) -> pd.DataFrame:
    import geopandas as gpd

    gp = gpd.GeoDataFrame(
        plumes, geometry=gpd.points_from_xy(plumes.lon, plumes.lat), crs="EPSG:4326"
    ).to_crs(_UTM_PERMIAN)
    gf = gpd.GeoDataFrame(
        facilities, geometry=gpd.points_from_xy(facilities.lon, facilities.lat),
        crs="EPSG:4326",
    ).to_crs(_UTM_PERMIAN)

    joined = gpd.sjoin_nearest(
        gp, gf.rename(columns={"lat": "facility_lat", "lon": "facility_lon"}),
        how="left", distance_col="distance_m",
    )
    # sjoin_nearest can return ties; keep the first (identical distance)
    joined = joined[~joined.index.duplicated(keep="first")]
    # both inputs carry 'state'; keep the plume's as 'state'
    joined = joined.rename(columns={"state_left": "state"})
    return pd.DataFrame(joined.drop(columns=["geometry", "index_right"]))


def _join_haversine(plumes: pd.DataFrame, facilities: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, p in plumes.iterrows():
        d = facilities.apply(
            lambda f: haversine_m(p.lat, p.lon, f.lat, f.lon), axis=1
        )
        i = d.idxmin()
        f = facilities.loc[i]
        rows.append({**p.to_dict(),
                     "facility_id": f.facility_id, "operator": f.operator,
                     "facility_name": f.facility_name,
                     "facility_lat": f.lat, "facility_lon": f.lon,
                     "state_right": f.state, "distance_m": float(d.loc[i])})
    return pd.DataFrame(rows)


def join_all() -> pd.DataFrame:
    """Every plume with its single nearest facility and distance_m.
    Rows beyond MAX_MATCH_DISTANCE_M are still present — callers decide via
    `matched` — so the UI can honestly show 'nearest was N km away'."""
    plumes, facilities = load_plumes(), load_facilities()
    try:
        out = _join_geopandas(plumes, facilities)
    except ImportError:  # geopandas missing on a teammate's machine
        out = _join_haversine(plumes, facilities)
    out["matched"] = out["distance_m"] <= MAX_MATCH_DISTANCE_M
    return out


def nearest_facility(plume_id: str) -> dict | None:
    """Attribution result for one plume, or None if the plume_id is unknown.

    Returns dict with `matched` False (facility fields set to None) when the
    nearest facility is beyond the confidence threshold.
    """
    df = join_all()
    row = df[df["plume_id"] == plume_id]
    if row.empty:
        return None
    r = row.iloc[0]
    base = {
        "plume_id": r["plume_id"],
        "plume_lat": float(r["lat"]),
        "plume_lon": float(r["lon"]),
        "leak_rate_kg_hr": float(r["leak_rate_kg_hr"]),
        "detected_date": r["detected_date"],
        "state": r["state"],
        "source": r["source"],
        "matched": bool(r["matched"]),
        "nearest_distance_m": round(float(r["distance_m"]), 1),
    }
    if r["matched"]:
        base.update({
            "facility_id": r["facility_id"],
            "operator": r["operator"],
            "facility_name": r["facility_name"],
            "facility_lat": float(r["facility_lat"]),
            "facility_lon": float(r["facility_lon"]),
            "distance_m": round(float(r["distance_m"]), 1),
        })
    else:
        base.update({
            "facility_id": None, "operator": None, "facility_name": None,
            "facility_lat": None, "facility_lon": None, "distance_m": None,
        })
    return base


if __name__ == "__main__":
    df = join_all()
    n_match = int(df["matched"].sum())
    print(f"{len(df)} plumes | {n_match} matched within {MAX_MATCH_DISTANCE_M:.0f} m")
    print(df.groupby("state")["matched"].sum().to_string())
    print("\n--- demo pair ---")
    for pid in ("tan20260607t190346c80s4001-F", "tan20260607t190346c80s4001-K"):
        r = nearest_facility(pid)
        print(f"{pid} [{r['state']}]: matched={r['matched']} "
              f"operator={r['operator']} dist={r['nearest_distance_m']} m")
