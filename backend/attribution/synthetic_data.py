"""Synthetic training-set generation from the real 32 plumes / 30 facilities.

Honest-augmentation recipe (disclose in the demo):
  * Positives: each NM plume whose true nearest facility is within 2 km, paired
    with that facility (8 real anchor pairs).
  * Hard negatives: the same plume paired with its 2nd-5th nearest facilities.
  * Easy negatives: the same plume paired with random facilities > 5 km away.
  * Augmentation: each anchor plume is jittered N_JITTER times — Gaussian
    position noise (sigma JITTER_POS_M meters) and multiplicative leak-rate
    noise (sigma JITTER_RATE_FRAC) — and all its pairs are regenerated. Wind is
    kept from the real observation.
  * Only NM plumes can anchor positives (no TX facilities yet) — expected.

All parameters are logged into the output so augmentation is auditable.
Output: backend/attribution/training_data.csv (label 1 = true source pair).
Deterministic: seeded RNG.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .features import pair_features
from .spatial_join import MAX_MATCH_DISTANCE_M, haversine_m, load_facilities, load_plumes

OUT_PATH = Path(__file__).resolve().parent / "training_data.csv"
PARAMS_PATH = Path(__file__).resolve().parent / "training_data_params.json"

PARAMS = {
    "seed": 42,
    "n_jitter": 30,             # jittered copies per anchor plume
    "jitter_pos_m": 250.0,      # sigma of Gaussian position noise, meters
    "jitter_rate_frac": 0.15,   # sigma of multiplicative leak-rate noise
    "hard_negative_ranks": [2, 3, 4, 5],  # 2nd..5th nearest facilities
    "easy_negatives_per_plume": 2,
    "easy_negative_min_m": 5000.0,
    "positive_max_m": MAX_MATCH_DISTANCE_M,
}

_M_PER_DEG_LAT = 111_320.0


def _jitter(plume: pd.Series, rng: np.random.Generator) -> pd.Series:
    p = plume.copy()
    dlat = rng.normal(0, PARAMS["jitter_pos_m"]) / _M_PER_DEG_LAT
    dlon = rng.normal(0, PARAMS["jitter_pos_m"]) / (
        _M_PER_DEG_LAT * np.cos(np.radians(plume["lat"])))
    p["lat"] = plume["lat"] + dlat
    p["lon"] = plume["lon"] + dlon
    p["leak_rate_kg_hr"] = max(
        1.0, plume["leak_rate_kg_hr"] * (1 + rng.normal(0, PARAMS["jitter_rate_frac"])))
    return p


def _ranked_facilities(plume: pd.Series, facilities: pd.DataFrame) -> pd.DataFrame:
    d = facilities.apply(
        lambda f: haversine_m(plume["lat"], plume["lon"], f["lat"], f["lon"]), axis=1)
    out = facilities.assign(distance_m=d).sort_values("distance_m")
    return out.reset_index(drop=True)


def _pairs_for_plume(plume: pd.Series, facilities: pd.DataFrame,
                     true_facility_id: str, rng: np.random.Generator) -> list[dict]:
    """Feature rows for one (possibly jittered) plume against its candidates."""
    ranked = _ranked_facilities(plume, facilities)
    rows = []

    def add(facility: pd.Series, label: int, kind: str):
        feats = pair_features(plume, facility, facilities)
        rows.append({"plume_id": plume["plume_id"], "facility_id": facility["facility_id"],
                     "pair_kind": kind, **feats, "label": label})

    # positive: the true facility (skip if jitter pushed it past the threshold —
    # keeps positives clean)
    true_row = ranked[ranked["facility_id"] == true_facility_id].iloc[0]
    if true_row["distance_m"] <= PARAMS["positive_max_m"]:
        add(true_row, 1, "positive")

    # hard negatives: next-nearest non-true facilities
    others = ranked[ranked["facility_id"] != true_facility_id]
    for i, rank in enumerate(PARAMS["hard_negative_ranks"]):
        if i < len(others):
            add(others.iloc[i], 0, "hard_negative")

    # easy negatives: random far facilities
    far = others[others["distance_m"] >= PARAMS["easy_negative_min_m"]]
    if not far.empty:
        take = min(PARAMS["easy_negatives_per_plume"], len(far))
        for idx in rng.choice(far.index, size=take, replace=False):
            add(far.loc[idx], 0, "easy_negative")
    return rows


def generate() -> pd.DataFrame:
    rng = np.random.default_rng(PARAMS["seed"])
    plumes, facilities = load_plumes(), load_facilities()

    # anchors: plumes with a true nearest facility within the threshold
    anchors = []
    for _, p in plumes.iterrows():
        ranked = _ranked_facilities(p, facilities)
        if ranked.iloc[0]["distance_m"] <= PARAMS["positive_max_m"]:
            anchors.append((p, ranked.iloc[0]["facility_id"]))
    print(f"{len(anchors)} anchor plumes with a true match within "
          f"{PARAMS['positive_max_m']:.0f} m (NM only is expected)")

    rows: list[dict] = []
    for p, true_id in anchors:
        rows += _pairs_for_plume(p, facilities, true_id, rng)          # real anchor
        for _ in range(PARAMS["n_jitter"]):                            # augmented copies
            rows += _pairs_for_plume(_jitter(p, rng), facilities, true_id, rng)

    df = pd.DataFrame(rows)
    df.to_csv(OUT_PATH, index=False)
    PARAMS_PATH.write_text(json.dumps(PARAMS, indent=2))
    print(f"Wrote {len(df)} pairs -> {OUT_PATH.name} "
          f"(positives={int(df['label'].sum())}, negatives={int((1 - df['label']).sum())})")
    print(df["pair_kind"].value_counts().to_string())
    return df


if __name__ == "__main__":
    generate()
