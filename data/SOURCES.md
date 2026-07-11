# Data Sources — Methane Plume Attribution & Complaint Tool

All coordinates and values trace to real, public sources. The ONE exception is
Texas facility **operator names**, which are clearly-labeled fictional placeholders
(see Dataset 2) — Texas's public well GIS layer has no operator field, and we will
not risk falsely naming a real company at an unverified well location. Everything
else — every coordinate, every leak rate, every Oklahoma operator name, every rule
citation — is real.
Initial pull 2026-07-11 for the Permian Basin (West Texas + SE New Mexico).
Expanded 2026-07-11/12 with Texas facilities and a third state, Oklahoma
(Anadarko Basin), as part of Person A's post-skeleton Theme 1 work.

---

## Dataset 1 — `plumes.csv` (47 rows: 17 Texas, 15 New Mexico, 15 Oklahoma)

**Source:** Carbon Mapper public Data API — `GET /api/v1/catalog/plume-csv`
(no API token required for reads).

- Base: https://api.carbonmapper.org/api/v1/docs
- Query used: `bbox=-104.9,31.0,-101.8,33.6` (Delaware + Midland sub-basins),
  `plume_gas=CH4`, `limit=300`, then filtered to Texas/New Mexico rows with a real
  `emission_auto`, and selected the strongest emitters per state plus the demo pair.
- Instrument: Tanager-1 (Planet Labs / Carbon Mapper coalition).
- Fields mapped: `plume_id`, `plume_latitude`→lat, `plume_longitude`→lon,
  `emission_auto` (kg/hr)→leak_rate_kg_hr, `datetime`→detected_date, `region`→state,
  `place`, instrument→source.

**Cross-border demo pair** (same satellite overpass `...c80s4001`, 2026-06-07, ~5 km apart across the 32°N state line):
- TX: `tan20260607t190346c80s4001-K` — 31.982391, -103.425745 (Mentone, Texas)
- NM: `tan20260607t190346c80s4001-F` — 32.030955, -103.432583 (Jal, New Mexico)

**Supplementary (not loaded, citable):** MethaneSAT peer-reviewed release — 14 Midland
sub-basin plumes, 0.5–15 t/hr, 28 Sep 2024. ACP vol 26 p2941 (2026):
https://acp.copernicus.org/articles/26/2941/2026/

**Oklahoma addition (15 rows):** same Carbon Mapper endpoint, new bbox
`-100.0,34.5,-97.0,36.5` (Anadarko Basin / western-central Oklahoma), filtered to
`region == "Oklahoma"` and `ipcc_sector` containing "Oil" (98 of 112 raw records were
real Oil & Gas detections; the rest were Solid Waste sources and were excluded), then
the 15 strongest emitters selected. Pull script: `backend/data_pipeline/pull_ok_plumes.py`.
Leak rates observed: 1,588–12,379 kg/hr. Appended, not merged — the original 32 rows
are untouched.

**Caveats:**
- Carbon Mapper data is continuously updated (L2C/L4A products release ~30 days after
  acquisition); re-pull for fresh detections. Coordinates are "estimate of plume origin."
- Carbon Mapper's exact licensing terms for embedding plume detections in a third-party
  app were NOT confirmed (a "free for non-commercial use" claim was refuted in research).
  **Verify licensing with Carbon Mapper before any public/production deployment.**

---

## Dataset 2 — `facilities.csv` (94 rows: 30 New Mexico, 34 Texas, 30 Oklahoma)

**Texas operator names are fictional placeholders — flagged prominently, not buried.**
Texas well *coordinates* are real (RRC); the RRC layer has no operator field, so real
company names were never available for Texas, and none were guessed. New Mexico and
Oklahoma operator names are both fully real, sourced independently from each state's
own regulator.

### New Mexico — New Mexico OCD (authoritative, real operators — 30 rows)
- Service: https://mapservice.nmstatelands.org/arcgis/rest/services/Public/NMOCD_Wells_V3/MapServer/5 (NMOCD_Active)
- ArcGIS Hub page: https://ocd-hub-nm-emnrd.hub.arcgis.com/datasets/dd971b8e25c54d1a8ab7c549244cf3cc_0/explore
- Fields used: `API`, `wellname`, `ogrid_name` (operator), `county`, `latitude`, `longitude`.
- Verified: returns real operators near NM plumes (e.g., Mewbourne Oil Co, XTO Energy,
  Tap Rock Operating) with WGS84 coordinates. ("Pre-Ongard Well Operator" placeholder
  rows filtered out — not a real company.)
- 12 distinct real operators: Marathon Oil Permian, XTO Energy, Devon Energy, EOG
  Resources, Apache, Mewbourne Oil, Oxy, COG Operating, WPX, Novo, Mack Energy, Tap
  Rock, Armstrong.

### Texas — Railroad Commission of Texas (RRC) — real coordinates, FICTIONAL operators (34 rows)
- Service: https://gis.rrc.texas.gov/server/rest/services/rrc_public/RRC_Public_Viewer_Srvs/MapServer/1 (Well Locations)
- Fields available: `API`, `GIS_WELL_NUMBER`, `GIS_LAT83`/`GIS_LONG83` (WGS84 — good coords).
- **LIMITATION (confirmed, unchanged since initial research):** the RRC GIS well layer
  does NOT carry the operator company name. RRC's pipeline layer (TPMS) does carry
  `OPER_NM`, but those are pipeline systems (lines), not point facilities, so it can't
  substitute. HIFLD's national wells layer was also investigated and rejected earlier
  (its download-format/API claim was refuted in research).
- **Deliberate design decision (2026-07-12):** rather than guess which real company
  operates a specific, unverified Texas well — a defamation risk this entire project
  is built to avoid — each well was assigned a clearly-fictional placeholder operator
  name (`"Permian Basin Operator #1"`, `#2`, ... 7 clusters total, one per plume-area
  cluster so wells that are geographically near each other share a placeholder,
  mirroring how real operators actually cluster). These names can never be mistaken
  for a real company. Pull script: `backend/data_pipeline/pull_tx_facilities.py`
  (nearest 2 real RRC wells per TX plume, deduplicated).

### RRC / TX facility datasets (download, for reference)
- https://www.rrc.texas.gov/resource-center/research/data-sets-available-for-download/
  (county GIS shapefiles; note coordinates in NAD 27 — reproject to WGS84 for web mapping).

### Oklahoma — Oklahoma Corporation Commission (OCC), real operators (30 rows)
- Service: https://gis.occ.ok.gov/server/rest/services/Hosted/RBDMS_WELLS/FeatureServer/2
  (RBDMS_WELLS — Risk Based Data Management System, found via OCC's ArcGIS Hub
  https://gisdata-occokc.opendata.arcgis.com/).
- Fields used: `api`, `well_name`, `operator`, `sh_lat`, `sh_lon`, `county`. Unlike Texas,
  **this layer DOES carry a real operator field**, confirmed via a live query.
- Verified: returns real, named operators (e.g., Shell Oil Company, Devon Energy
  Production Company, Apache Corporation, Burlington Resources Oil & Gas). Rows where
  `operator` was `"OTC/OCC NOT ASSIGNED"` (an OCC internal placeholder, not a real
  company) were filtered out — same treatment as NM's "Pre-Ongard" rows.
- 26 distinct real operators. Pull script:
  `backend/data_pipeline/pull_ok_facilities.py` (nearest 2 real wells per OK plume).

---

## Dataset 3 — `regulators.csv` (3 rows, verified)

### New Mexico — 98% gas-capture mandate
- Rule: **19.15.27.9 NMAC** "Statewide Natural Gas Capture Requirements" (part of 19.15.27
  NMAC, "Venting and Flaring of Natural Gas"). Capture ≥98% of produced gas by Dec 31, 2026.
  - https://www.law.cornell.edu/regulations/new-mexico/19-15-27-9-NMAC
  - https://www.srca.nm.gov/parts/title19/19.015.0027.html
  - Administered by OCD/EMNRD: https://www.emnrd.nm.gov/ocd/
- Separate air rule: **20.2.50 NMAC** (NMED "Oil and Gas Sector — Ozone Precursor Pollutants",
  VOC/NOx) — distinct from the capture rule; its 98% figures are combustion-efficiency /
  pneumatic-controller phase-ins, NOT produced-gas capture.
  - https://www.env.nm.gov/wp-content/uploads/sites/2/2022/07/Oil-and-Gas-Sector-Ozone-Precursor-Polutants-Final-rule-20.2.50-NMAC-06Jul22.pdf
- Complaint: NMED incident form https://ents.web.env.nm.gov/public/INCIDENT_HDR_add.php ;
  OCD contact https://www.emnrd.nm.gov/ocd/contact-us/

### Texas — no equivalent capture mandate
- Rule: **16 TAC §3.32** (RRC Statewide Rule 32) governs gas disposition and venting/flaring
  but permits flaring by exception; no 98%-capture equivalent.
- Complaint: TCEQ https://www.tceq.texas.gov/compliance/complaints (1-888-777-3186) for air;
  RRC oil & gas https://www.rrc.texas.gov/oil-and-gas/o-g-complaints/
- **Caveat:** the "Texas has no state capture mandate" statement rests on absence of such a
  rule plus emission-intensity data, not a single affirmative citation. MethaneSAT: "New
  Mexico operators emitted less than half the methane relative to production compared to
  their counterparts in Texas."
  - https://www.methanesat.org/project-updates/methanesat-data-enables-novel-comparison-methane-mitigation-efforts-permian-basin

### Oklahoma — no capture mandate, permit-based flaring thresholds
- Rule: **OAC 165:10-3-15** (Venting and Flaring), Oklahoma Corporation Commission (OCC)
  Oil and Gas Conservation Division.
  - https://okrules.elaws.us/oac/165:10-3-15
- Summary (confirmed via direct rule text): operators may vent/flare up to 50 mcf/d
  without a permit when marketing the gas is not economically feasible; larger volumes
  require an administrative permit (Form 1022), with temporary exemptions during
  flowback. **The rule regulates venting/flaring permits only and sets no affirmative
  gas-capture requirement** — structurally similar to Texas in that respect, though
  Oklahoma's permit-threshold system is more codified than Texas's exception-based one.
- Complaint: OCC Crude Oil & Natural Gas complaint form
  https://oklahoma.gov/occ/complaints/crude-oil-natural-gas.html (submission portal
  https://public.occ.ok.gov/Forms/OGComplaints); Oil and Gas Conservation Division
  24/7 line 405-521-2331.

---

## Regulatory-contrast thesis (verified, now three states)
New Mexico enforces a 98% gas-capture rule (19.15.27.9 NMAC); Texas and Oklahoma both
lack any capture mandate, regulating venting/flaring only through permits/exceptions
(Texas Statewide Rule 32; Oklahoma OAC 165:10-3-15's 50 mcf/d permit threshold).
Satellite data (MethaneSAT) shows NM operators emitting roughly half the methane per
unit of production versus Texas. The NM-vs-Texas cross-border pair remains the demo's
emotional core; Oklahoma adds a second, independently-sourced state showing the same
"no capture mandate" pattern recurs outside the Permian Basin.
