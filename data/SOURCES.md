# Data Sources — Methane Plume Attribution & Complaint Tool

All coordinates and values trace to real, public sources. Nothing is fabricated.
Pulled 2026-07-11 for the Permian Basin (West Texas + SE New Mexico).

---

## Dataset 1 — `plumes.csv` (32 rows: 17 Texas, 15 New Mexico)

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

**Caveats:**
- Carbon Mapper data is continuously updated (L2C/L4A products release ~30 days after
  acquisition); re-pull for fresh detections. Coordinates are "estimate of plume origin."
- Carbon Mapper's exact licensing terms for embedding plume detections in a third-party
  app were NOT confirmed (a "free for non-commercial use" claim was refuted in research).
  **Verify licensing with Carbon Mapper before any public/production deployment.**

---

## Dataset 2 — `facilities.csv` (CURRENTLY NEW MEXICO ONLY — 30 rows, 12 named operators)

**Status:** Texas facilities intentionally deferred (per build decision, 2026-07-11). The file
currently holds real NM wells only. Consequence: Texas plumes will correctly return "no
confident match within 2 km" until TX facility data is added — the intended safe behavior.
NM operators include Marathon Oil Permian, XTO Energy, Devon Energy, EOG Resources, Apache,
Mewbourne Oil, Oxy, COG Operating, WPX, Novo, Mack Energy, Tap Rock, Armstrong. (OCD's
"Pre-Ongard Well Operator" placeholder rows were filtered out — not real companies.)


### New Mexico — New Mexico OCD (authoritative, includes operator names)
- Service: https://mapservice.nmstatelands.org/arcgis/rest/services/Public/NMOCD_Wells_V3/MapServer/5 (NMOCD_Active)
- ArcGIS Hub page: https://ocd-hub-nm-emnrd.hub.arcgis.com/datasets/dd971b8e25c54d1a8ab7c549244cf3cc_0/explore
- Fields used: `API`, `wellname`, `ogrid_name` (operator), `county`, `latitude`, `longitude`.
- Verified: returns real operators near NM plumes (e.g., Mewbourne Oil Co, XTO Energy,
  Tap Rock Operating) with WGS84 coordinates.

### Texas — Railroad Commission of Texas (RRC)
- Service: https://gis.rrc.texas.gov/server/rest/services/rrc_public/RRC_Public_Viewer_Srvs/MapServer/1 (Well Locations)
- Fields available: `API`, `GIS_WELL_NUMBER`, `GIS_LAT83`/`GIS_LONG83` (WGS84 — good coords).
- **LIMITATION:** the RRC GIS well layer does NOT carry the operator company name. Operator
  requires a separate API-number→operator join not exposed via GIS. RRC's pipeline layer
  (TPMS) does carry `OPER_NM`, but those are pipeline systems (lines), not point facilities.
- HIFLD national wells layer was investigated as a backup; its download-format/API claim was
  refuted in research — prefer the state portals.

### RRC / TX facility datasets (download, for reference)
- https://www.rrc.texas.gov/resource-center/research/data-sets-available-for-download/
  (county GIS shapefiles; note coordinates in NAD 27 — reproject to WGS84 for web mapping).

---

## Dataset 3 — `regulators.csv` (2 rows, verified)

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

---

## Regulatory-contrast thesis (verified)
New Mexico and Texas share the Permian Basin, but NM enforces a 98% gas-capture rule
(19.15.27.9 NMAC) and Texas does not — and satellite data (MethaneSAT) shows NM operators
emitting roughly half the methane per unit of production versus Texas. This is the demo's core.
