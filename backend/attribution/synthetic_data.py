"""Synthetic training-set generation from the real 32 plumes / 30 facilities.

Honest-augmentation recipe (disclose in the demo):
  * Positives: each plume whose true nearest facility is within 2 km, paired
    with that facility (anchor pairs; count grows as states land in
    facilities.csv — NM-only at first, now NM+TX+OK).
  * Hard negatives: the same plume paired with its 2nd-5th nearest facilities.
  * Easy negatives: the same plume paired with random facilities > 5 km away.
  * Augmentation: each anchor plume is jittered N_JITTER times — Gaussian
    position noise (sigma JITTER_POS_M meters) and multiplicative leak-rate
    noise (sigma JITTER_RATE_FRAC) — and all its pairs are regenerated. Wind is
    kept from the real observation.
  * A state's plumes can only anchor positives once that state has facility
    rows (originally NM-only; TX and OK facilities have since landed).
  * Community-confirmed anchors: when residents independently corroborate an
    already-matched plume (>=2 reports, see community_labels.py), its real
    pair-set is jittered-and-repeated COMMUNITY_REPLICATION extra times,
    tagged pair_kind="community_confirmed". Every anchor already gets ~31x
    representation (1 real + 30 jitter); +10 lifts a confirmed anchor to
    ~41x — a clear, defensible signal boost without letting one confirmed
    plume dominate the set. Never applied to unmatched plumes: community
    corroboration can only strengthen an existing geometric match, never
    manufacture one (that would violate the 2 km no-confident-match rule).

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
    "community_replication": 10,  # extra jittered repeats for community-confirmed anchors
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


def _community_confirmed_rows(anchors: list[tuple[pd.Series, str]], facilities: pd.DataFrame,
                              rng: np.random.Generator) -> tuple[list[dict], list[str]]:
    """Extra jittered-and-repeated pair-sets for anchors the community has
    corroborated. Relabels each repeat's positive row to
    pair_kind='community_confirmed'. Returns (rows, confirmed_plume_ids)."""
    from .community_labels import confirmed_plume_ids

    confirmed = set(confirmed_plume_ids())
    if not confirmed:
        return [], []

    rows: list[dict] = []
    hit_ids: list[str] = []
    for p, true_id in anchors:
        if p["plume_id"] not in confirmed:
            continue
        hit_ids.append(p["plume_id"])
        for _ in range(PARAMS["community_replication"]):
            pair_rows = _pairs_for_plume(_jitter(p, rng), facilities, true_id, rng)
            for r in pair_rows:
                if r["label"] == 1:
                    r["pair_kind"] = "community_confirmed"
            rows += pair_rows
    return rows, hit_ids


def generate() -> pd.DataFrame:
    rng = np.random.default_rng(PARAMS["seed"])
    plumes, facilities = load_plumes(), load_facilities()

    # anchors: plumes with a true nearest facility within the threshold
    anchors = []
    for _, p in plumes.iterrows():
        ranked = _ranked_facilities(p, facilities)
        if ranked.iloc[0]["distance_m"] <= PARAMS["positive_max_m"]:
            anchors.append((p, ranked.iloc[0]["facility_id"]))
    by_state = pd.Series([p["state"] for p, _ in anchors]).value_counts().to_dict()
    print(f"{len(anchors)} anchor plumes with a true match within "
          f"{PARAMS['positive_max_m']:.0f} m (by state: {by_state})")

    rows: list[dict] = []
    for p, true_id in anchors:
        rows += _pairs_for_plume(p, facilities, true_id, rng)          # real anchor
        for _ in range(PARAMS["n_jitter"]):                            # augmented copies
            rows += _pairs_for_plume(_jitter(p, rng), facilities, true_id, rng)

    community_rows, confirmed_ids = _community_confirmed_rows(anchors, facilities, rng)
    if confirmed_ids:
        print(f"community-confirmed anchors: {len(confirmed_ids)} -> "
              f"+{len(community_rows)} rows ({confirmed_ids})")
    rows += community_rows

    df = pd.DataFrame(rows)
    df.to_csv(OUT_PATH, index=False)
    params_out = {**PARAMS, "community_confirmed_plume_ids": confirmed_ids}
    PARAMS_PATH.write_text(json.dumps(params_out, indent=2))
    print(f"Wrote {len(df)} pairs -> {OUT_PATH.name} "
          f"(positives={int(df['label'].sum())}, negatives={int((1 - df['label']).sum())})")
    print(df["pair_kind"].value_counts().to_string())
    return df


if __name__ == "__main__":
    generate()
