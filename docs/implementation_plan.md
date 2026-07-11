# Vakathon — Methane Detection & Attribution App: Implementation Plan (v2, data-integrated)

3-person team, Friday kickoff → Sunday demo. **This version replaces the data-collection
phase with the real datasets already pulled into `/data`, and locks four build decisions.**

## Locked decisions (2026-07-11)
1. **Stack:** React (deck.gl/Mapbox) frontend + FastAPI backend + scikit-learn + Claude API. **No Google Earth Engine / TROPOMI license.**
2. **Map layer:** Carbon Mapper point plumes **only**. TROPOMI regional heatmap is **dropped** (no dual-layer, no GEE signup, no raster cold-start check).
3. **TX/NM comparison view:** **regulatory contrast only.** NM plumes attribute to a named operator + OCD rule; TX plumes show RRC jurisdiction + "no state capture mandate" with operator **"not identified (TX facility data not integrated)."**
4. **Confidence model:** **synthetically augment** the real 32 plumes / 30 facilities into a labeled training set, train a scikit-learn classifier on available features, keep the hand-tuned scorer as a code-level fallback.

---

## 0. Data — ALREADY COLLECTED (this replaces the entire "Day 1 ingestion" phase)

All real, sourced, and committed under `/data`. Provenance + caveats in [`data/SOURCES.md`](../data/SOURCES.md).
**No live ingestion, no GEE, no Copernicus, no HIFLD/RRC/OCD downloads remain on the critical path.**

| File | Rows | What it is | Schema |
|---|---|---|---|
| `data/plumes.csv` | 32 (17 TX, 15 NM) | Real Carbon Mapper / Tanager-1 CH4 plumes, Permian | `plume_id, lat, lon, leak_rate_kg_hr, detected_date, state, place, source` |
| `data/facilities.csv` | 30 (NM only) | Real NM OCD active wells w/ operators | `facility_id, operator, facility_name, lat, lon, state` |
| `data/regulators.csv` | 2 | TX vs NM regulator + rule lookup | `state, regulator_name, complaint_mechanism, applicable_rule, rule_summary` |
| `data/SOURCES.md` | — | Full provenance, URLs, caveats | — |

**Cross-border demo pair (same satellite overpass, 2026-06-07, ~5 km apart across the 32°N line):**
- **NM** `tan20260607t190346c80s4001-F` — 32.0310, −103.4326 (Jal) → nearest facility **Marathon Oil Permian LLC**, 1,143 m → OCD → **19.15.27.9 NMAC (98% capture)**.
- **TX** `tan20260607t190346c80s4001-K` — 31.9824, −103.4257 (Mentone) → no facility within 2 km → RRC/TCEQ → **16 TAC §3.32 (no capture mandate)**, operator not identified.

### Required data augmentation (small, do Friday night)
- **Add wind columns to `plumes.csv`** (`wind_speed_kmh`, `wind_dir_deg`) by re-pulling from the Carbon Mapper CSV endpoint (`wind_speed_avg_auto`, `wind_direction_avg_auto` are already in the source). Needed for the ML `wind_consistency` feature. ~15 min.
- Everything else is build-ready as-is.

### Known data limits (say them plainly in the demo, they are features not bugs)
- **TX has no facility rows** → TX plumes correctly return "no confident match." This is the safe, non-defamatory default.
- **Carbon Mapper licensing** for app embedding is unconfirmed — fine for the hackathon, verify before real deployment.
- **"Texas has no capture mandate"** rests on absence-of-rule + MethaneSAT emission-intensity data, not one affirmative citation.

---

## 1. Ownership (revised — Person A's ingestion work is largely done)

- **Person A — Backend data + community store**: load `/data` CSVs into the API; build the **synthetic training-set generator**; stand up the community store (SQLite/JSON) + `/community` endpoints. (Ingestion/CRS/caching work is **done**.)
- **Person B — Attribution + routing + ML**: spatial nearest-facility join (2 km threshold), feature extraction, train the scikit-learn confidence model on synthetic data, operator→regulator→rule lookup from `regulators.csv`, hand-tuned fallback scorer.
- **Person C — Frontend + complaint gen + community UI**: deck.gl map (single Carbon Mapper layer), click-to-resolve panel, Claude complaint letters, mocked status tracker, **TX/NM regulatory comparison view**, ground-truth report UI + co-sign UI.

---

## 2. Timeline

### Friday night (kickoff, ~3–4 hrs)
- **All:** scaffold repo (structure below). The unified schema is **already fixed** by `data/plumes.csv` — no schema debate needed.
- **A:** re-pull plumes with wind columns; write `load_data.py` that serves the 3 CSVs; skeleton `synthetic_data.py`.
- **B:** get geopandas doing `sjoin_nearest` between `plumes.csv` and `facilities.csv` with the 2 km cutoff; confirm the NM demo plume resolves to Marathon Oil at ~1.1 km and TX plumes resolve to no-match.
- **C:** blank React app + deck.gl map with TX/NM outlines + the 32 plumes plotted from `/events`; FastAPI health-check.

### Saturday AM
- **A:** finish `synthetic_data.py` (see §3); commit `training_data.csv`.
- **B:** hand-tuned confidence scorer (distance + wind consistency) as the always-works baseline; wire `/attribution/{plume_id}`.
- **C:** click-to-resolve panel on a mocked response; start Claude complaint letter from a hardcoded attributed event.

### Saturday PM
- **B:** train scikit-learn classifier on synthetic data → `model.pkl`; `confidence_score.py` switch (model, fallback to hand-tuned on load failure); finalize `regulator_rules.json` from `regulators.csv`.
- **A:** community store + `/community/reports` + `/community/cosign`.
- **C:** real Claude letters from live attributions; mocked status tracker; ground-truth report form + co-sign button.

### Sunday AM
- Integration pass (§5 checklist), fix breakage, wire community endpoints into the panel, build the **TX/NM comparison view**.

### Sunday midday → demo
- Apply cuts (§6) if behind; polish; rehearse: load map → click NM plume → confidence + Marathon Oil + OCD 98% rule + complaint + community reports + co-sign → click paired TX plume → RRC, no mandate, operator not identified → "same basin, 5 km apart, different rules." Generate a complaint live.

---

## 3. Synthetic training data (`backend/attribution/synthetic_data.py`)

Goal: turn 32 real plumes + 30 real facilities into a labeled `(plume, facility)` pair set the classifier can learn on. **Only NM plumes can form positives** (TX has no facilities) — that is expected and honest.

- **Positive pairs:** each NM plume × its true nearest facility within 2 km (real match).
- **Hard negatives:** each NM plume × the 2nd–5th nearest facilities, and × random farther facilities.
- **Augmentation to grow the set:** jitter each real plume's lat/lon by small Gaussian noise (±few hundred m) and its leak rate by ±10–20%, regenerate pairs. Produces a few hundred to ~1–2k labeled rows from the real 45-point seed. Log the jitter parameters — disclose augmentation in the demo.
- **Features per pair (only ones we actually have):**
  - `distance_m` (haversine, plume→facility)
  - `wind_consistency` (alignment of facility→plume bearing with plume wind direction; from the new wind columns)
  - `leak_rate_kg_hr` (plume magnitude)
  - `operator_well_density` (count of same-operator wells within ~2 km — a weak proxy for facility scale, since we lack true capacity)
  - `state_match` (facility state == plume state)
- **Label:** 1 if the pair is the true nearest real facility, else 0.
- Write `training_data.csv`; `model_train.py` fits `LogisticRegression` or `GradientBoostingClassifier`, reports CV accuracy/AUC, saves `model.pkl`.

---

## 4. Monorepo structure (TROPOMI + raster paths removed)

```
vakathon/
├── data/                               # REAL DATA, committed (see §0)
│   ├── plumes.csv
│   ├── facilities.csv
│   ├── regulators.csv
│   └── SOURCES.md
├── backend/
│   ├── main.py                         # FastAPI entrypoint
│   ├── api/
│   │   ├── routes_events.py            # GET /events (plumes.csv)
│   │   ├── routes_attribution.py       # GET /attribution/{plume_id}
│   │   ├── routes_complaint.py         # POST /complaint/generate (Claude API)
│   │   └── routes_community.py         # /community/reports, /community/cosign
│   ├── data_pipeline/
│   │   ├── load_data.py                # read the 3 CSVs (replaces all fetchers)
│   │   └── repull_plumes.py            # one-off: add wind columns from Carbon Mapper
│   ├── attribution/
│   │   ├── spatial_join.py             # sjoin_nearest, 2 km threshold
│   │   ├── features.py
│   │   ├── synthetic_data.py           # §3 — generate training_data.csv
│   │   ├── model_train.py              # scikit-learn (offline, run once)
│   │   ├── model.pkl                   # committed artifact
│   │   ├── confidence_score.py         # model + hand-tuned fallback switch
│   │   ├── regulator_lookup.py         # keyed by plume state
│   │   └── regulator_rules.json        # generated from regulators.csv
│   ├── community/
│   │   ├── store.py                    # SQLite/JSON
│   │   ├── reports.py
│   │   └── cosign.py
│   └── tests/
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── map/
│       │   ├── MapView.tsx
│       │   └── layers/plumeLayer.ts    # single Carbon Mapper layer (no TROPOMI)
│       ├── components/
│       │   ├── ClickResolvePanel.tsx
│       │   ├── ComplaintLetter.tsx
│       │   ├── StatusTracker.tsx
│       │   └── ComparisonView.tsx      # TX vs NM regulatory diff — centerpiece
│       ├── community/
│       │   ├── ReportForm.tsx
│       │   ├── ReportsList.tsx
│       │   └── CosignButton.tsx
│       └── api/client.ts
└── docs/
    └── implementation_plan.md          # this file
```

---

## 5. Verification / demo-readiness checklist (Sunday AM go/no-go)

1. Cold start, network blocked except Claude API — map loads the 32 plumes from `/data` only (no external calls).
2. Plumes render correctly over TX and NM (no CRS offset; coords are WGS84).
3. Click the **NM demo plume** → panel shows Marathon Oil Permian (~1.1 km), model confidence (fallback if model fails to load), OCD + 19.15.27.9 NMAC.
4. Click the **TX demo plume** → "no confident match within 2 km," RRC/TCEQ jurisdiction, 16 TAC §3.32, operator not identified.
5. Generate complaint → live Claude call succeeds; cached fallback letter ready if API is down.
6. Submit a mock ground-truth report near the NM plume → confidence indicator updates; co-sign → count increments and **persists on refresh**.
7. Status tracker shows submitted → (mock) acknowledged.
8. Comparison view → NM plume vs paired TX plume side by side; diff panel states the differing regulatory treatment.

Passing 3–8 on cached data + one live Claude call = demo survives bad venue Wi-Fi.

---

## 6. Fallback / cut list (top-down)

1. **First cut:** `operator_well_density` feature (weakest, proxy-only) — drop to distance + wind + rate.
2. **Second cut:** co-sign live-update polish — keep raw count + button.
3. **Third cut:** status-tracker states beyond "submitted."
4. **Fourth cut:** ground-truth photo upload — keep smell/flare checkbox + geolocation + name/zip.
5. **Fifth cut:** trained ML model — fall back to the hand-tuned scorer and say so plainly.
6. **Never cut:** the 3 CSVs loading, spatial-join attribution + 2 km threshold, regulator lookup, Claude complaint generation, TX/NM regulatory comparison view.

---

## 7. Critical files (build in this order of blocking-ness)

- `backend/data_pipeline/load_data.py` — serves the real CSVs; everything depends on it. (Schema already fixed by the data.)
- `backend/attribution/spatial_join.py` — nearest-facility + 2 km threshold; the app's core truth. Must return Marathon Oil for the NM demo plume and no-match for TX.
- `backend/attribution/synthetic_data.py` + `model_train.py` — the ML deliverable; isolated so a training failure falls back cleanly.
- `backend/attribution/confidence_score.py` — model/fallback switch; central to ML requirement + demo resilience.
- `backend/attribution/regulator_rules.json` — generated from `regulators.csv`; blocks Person C's panel + comparison view.
- `backend/community/store.py` — shared persistence for reports + co-signs.
- `frontend/src/components/ComparisonView.tsx` — TX-vs-NM diff, the differentiator.
