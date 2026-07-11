# Vakathon

Methane detection → attribution → community action. Satellite-detected methane plumes
(Carbon Mapper / Tanager-1, Permian basin) are attributed to a facility/operator, routed
to the correct state regulator and rule, and turned into a resident-filed complaint that
neighbors can corroborate with ground-truth reports and co-sign.

## Run it

```bash
# backend (from repo root)
pip3 install -r backend/requirements.txt
python3 -m uvicorn backend.main:app --port 8000

# frontend (second terminal)
cd frontend && npm install && npm run dev   # http://localhost:5173
```

Optional: `export ANTHROPIC_API_KEY=...` before starting the backend to get
Claude-drafted complaint letters; without it a deterministic template letter is used
(demo never dead-ends on Wi-Fi).

## Demo script (Sunday)

1. Map loads 32 plumes over the Permian basin (teal = NM, orange = TX).
2. Header "demo pair" buttons jump straight to the cross-border pair (same
   Tanager-1 overpass, 2026-06-07, ~5 km apart).
3. **NM plume** → Marathon Oil Permian LLC at ~1.1 km, confidence score, OCD +
   19.15.27.9 NMAC (98% capture rule).
4. Submit a ground-truth report + co-sign → confidence gets community-corroborated
   bump, co-sign count persists.
5. Generate complaint letter → submit → mocked status tracker.
6. **TX plume** → operator not identified, RRC/TCEQ, 16 TAC §3.32, no capture mandate.
7. "⚖ Compare TX vs NM" → side-by-side regulatory-gap view.

## Team handoff notes

- **Person A**: `data/plumes.csv` + `data/facilities.csv` are schema-exact
  **placeholders** (only the demo pair + regulators.csv are real) — see
  `data/SOURCES.md`. Replace with the real pulls; no code changes needed.
  Community store is `backend/community/store.py` (JSON file; swap to SQLite if needed).
- **Person B**: `backend/attribution/spatial_join.py` is a pure-python
  nearest-neighbor stub — replace internals with geopandas `sjoin_nearest`, keep the
  returned dict shape. Plug the trained model in via
  `backend/attribution/confidence_score.py:score_pair` (expects a
  `backend/attribution/model.py` exposing `predict(plume, facility, distance_m)`);
  the hand-tuned scorer stays as the load-failure fallback.
- **Person C** (done): map, resolve panel, complaint generation + fallback, status
  tracker, comparison view, report/co-sign UI, `/complaint/generate` route.

Full plan: `docs/implementation_plan.md` (plan v2).
