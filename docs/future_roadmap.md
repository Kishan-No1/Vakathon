# Vakathon — Post-Skeleton Roadmap (v1)

**Read this AFTER the skeleton (implementation_plan.md) is working end-to-end.**
This plan expands the working slice into a fuller product. It keeps the same three
owners and the same rule: **no engineer edits another person's files.** New work is
assigned so each theme splits cleanly across A / B / C.

## Guiding principles (unchanged)
- **Data-driven, not hard-coded** — the attribution engine already generalizes; growth = more data + more UI, not rewrites.
- **Human stays in the loop** — letters are generated and shown, never auto-filed. (See Theme 3.)
- **Non-accusatory framing everywhere** — "consistent with, pending verification," never "Company X is leaking illegally."
- **Ownership boundaries hold** — see the boundary table at the end before writing any file.

---

## THEME 1 — Make the model more accurate (multi-state expansion)

Goal: more real matches so the model leans on more than just distance, and so more
plumes resolve to a real facility. The code does **not** change — this is data + retrain.

### Person A (data — owns `data/`, `backend/data_pipeline/`)
- Add facilities for new states **one at a time**, cheapest first:
  1. **Texas** (highest priority — completes the headline demo pair; plumes + regulator already exist, only facilities missing).
  2. **Oklahoma** (Anadarko basin — Corporation Commission).
  3. **Colorado** (DJ basin — has strong methane rules → a possible *second* regulatory contrast).
- For each state: locate the facility portal, pull operator + lat/lon, append to `facilities.csv` (same schema).
- Add one `regulators.csv` row per new state (short deep-research task each).
- Widen the Carbon Mapper pull bounding box so plumes cover the new states (≈5-min change).

### Person B (model — owns `backend/attribution/`)
- **Integrate community ground-truth as real labels** (biggest accuracy lever): when a resident confirms a plume near a facility, treat it as a real positive in `synthetic_data.py` so the model learns from real human confirmations, not just augmented copies.
- Re-run `synthetic_data.py` → `model_train.py` whenever A lands new data; commit fresh `model.pkl`.
- Add features **only if the data supports them** (e.g., facility type/size if a new source provides it). Keep it simple — with limited data, more features can hurt.
- Track accuracy over time: keep a short log of AUC per data version so you can *show growth* ("8 matches → 0.92; 40 matches → 0.9x").

### Person C (frontend)
- Surface the richer confidence in the panel (e.g., show confidence + "based on N real community confirmations").

---

## THEME 2 — Two-sided UI (the big new feature)

One app, two doors, **one shared complaint-letter engine**. A toggle at the top switches modes.

### Side 1 — "Detection" (environmentalist / researcher)
The existing flow: click a satellite plume → model attributes it → LLM writes the letter.
Already built end-to-end; just needs to live behind the toggle.

### Side 2 — "Report" (person affected by a plume)
A resident who *doesn't* have satellite data enters what they can:
- where they are / where they see/smell the plume (map pin or address),
- any nearby facility they know of (optional),
- simple observations (flare visible? strong smell? how long? optional photo).

The app then runs the **same engine** on the *user-supplied* location (find nearby
facilities + the right regulator) and feeds it into the **same LLM** to produce a
letter — this time grounded in the resident's report instead of a satellite detection.

### Who builds what

**Person B (`backend/attribution/`)**
- Add `attribute_location(lat, lon)` — the same nearest-facility + 2 km threshold +
  regulator lookup, but taking arbitrary coordinates instead of a known `plume_id`.
  (Reuses everything already built; just a second entry point.)
- Expose it on B's own route file (e.g. `GET /attribution/by-location?lat=&lon=`).
- Same safety rule: beyond 2 km → "no confident facility match," no named operator.

**Person C (`frontend/`, complaint generation)**
- Build the **mode toggle** (Detection ↔ Report) at the top of the app.
- Build the **Report form** (`frontend/src/report/ReportForm.tsx`): map pin / address,
  optional facility, observation checkboxes.
- Wire the form → B's `by-location` endpoint → the shared complaint generator.
- Make the **complaint generator accept two input shapes**: (a) a satellite attribution,
  (b) a resident report. Same LLM, two prompt templates; the resident version leans on
  the human's first-hand observations and is explicit that it is a citizen report.

**Person A (`backend/community/`)**
- Store resident reports in the existing community store (they *are* ground-truth) so
  Theme 1's model can learn from them. One shared table, no new territory.

---

## THEME 3 — Dynamic, regulator-aware letter text (demo only, never mailed)

Goal: the letter automatically re-addresses itself to the correct regulator, cites the
correct rule, and adjusts tone/wording depending on which state the complaint is in —
so a Texas complaint reads differently from a New Mexico one. **This is for the demo;
the app generates and displays the letter and mocks "sending." Nothing is emailed to any
real agency** (unverified complaints naming real companies must never be auto-filed).

### Person B (`backend/attribution/`)
- Enrich `regulator_rules.json` with the extra fields the letter needs per state:
  addressee/office line, the exact rule citation + one-line summary, the citizen
  complaint mechanism, and optional tone hints. B owns this file; C consumes it.

### Person C (complaint generation, frontend)
- Make the LLM prompt **template off the regulator block** returned by B: salutation to
  the right office, the state's rule cited in the body, the correct complaint channel.
- Same input → different, correctly-addressed letter depending on state, live in the demo.
- Keep the **"Download / Copy letter"** action + the **mocked status tracker**
  (submitted → acknowledged). No real send button, no email API.

### Person A (backend)
- Ensure the complaint endpoint passes B's regulator block straight through to C intact.

---

## Ownership boundary table (holds for all new work)

| Area | Owner | Files |
|---|---|---|
| New-state facility + regulator data | **A** | `data/*.csv`, `backend/data_pipeline/` |
| Community/ground-truth + resident-report store | **A** | `backend/community/` |
| `main.py` (wires everyone's routers) | **A** | `backend/main.py` |
| Attribution, model, `attribute_location`, `regulator_rules.json` | **B** | `backend/attribution/`, `backend/api/routes_attribution.py` |
| Model retraining / accuracy tracking | **B** | `backend/attribution/` |
| Two-sided UI, Report form, mode toggle | **C** | `frontend/` |
| Complaint generation (both templates), dynamic regulator text | **C** | complaint-gen module + `frontend/` |

Cross-person contract stays the same: talk to each other through **API responses and
data files**, never by editing each other's code.

---

## Suggested order (do not start until the skeleton passes its checklist)
1. **Texas facilities** (A) → retrain (B) → completes the headline demo. Fastest, highest value.
2. **Dynamic regulator letter text** (B enrich JSON → C templating) — small, high polish payoff.
3. **Two-sided UI** (B `attribute_location` → C Report form + toggle) — the big new capability.
4. **Community ground-truth into the model** (A store → B retrain) — turns real usage into accuracy.
5. **More states** (OK, CO) — breadth + a possible second regulatory contrast.
