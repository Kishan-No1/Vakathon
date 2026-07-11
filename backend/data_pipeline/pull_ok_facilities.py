"""One-off script: append real Oklahoma well coordinates + real operator names
to data/facilities.csv, sourced from the Oklahoma Corporation Commission (OCC)
RBDMS_WELLS feature service (unlike Texas RRC, this layer DOES carry a real
operator field, confirmed via a live query — see data/SOURCES.md).

Run: python -m backend.data_pipeline.pull_ok_facilities
Appends only — never rewrites existing NM/TX rows in facilities.csv.
"""
import math
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
OCC_URL = "https://gis.occ.ok.gov/server/rest/services/Hosted/RBDMS_WELLS/FeatureServer/2/query"
WELLS_PER_PLUME = 2
SEARCH_DEG = 0.03  # ~3 km half-box
UNASSIGNED_MARKERS = ("NOT ASSIGNED", "OTC/OCC", "UNKNOWN")


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def query_wells_near(lat: float, lon: float) -> list[dict]:
    params = {
        "where": "1=1",
        "geometry": f"{lon-SEARCH_DEG},{lat-SEARCH_DEG},{lon+SEARCH_DEG},{lat+SEARCH_DEG}",
        "geometryType": "esriGeometryEnvelope", "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "api,well_name,operator,sh_lat,sh_lon,county",
        "returnGeometry": "false", "resultRecordCount": 20, "f": "json",
    }
    r = requests.get(OCC_URL, params=params, timeout=60)
    r.raise_for_status()
    feats = r.json().get("features", [])
    out = []
    for f in feats:
        a = f["attributes"]
        if not a.get("sh_lat") or not a.get("sh_lon") or not a.get("operator"):
            continue
        if any(m in str(a["operator"]).upper() for m in UNASSIGNED_MARKERS):
            continue  # OCC placeholder rows, not real companies
        out.append(a)
    return out


def main() -> None:
    plumes = pd.read_csv(DATA_DIR / "plumes.csv")
    ok_plumes = plumes[plumes["state"] == "Oklahoma"]
    print(f"{len(ok_plumes)} OK plumes to source facilities for")

    rows, seen_api = [], set()
    for _, p in ok_plumes.iterrows():
        try:
            wells = query_wells_near(p.lat, p.lon)
        except Exception as e:
            print(f"  query failed for {p.plume_id}: {e}")
            continue

        wells = sorted(wells, key=lambda w: haversine_m(
            p.lat, p.lon, w["sh_lat"], w["sh_lon"]))

        added = 0
        for w in wells:
            if added >= WELLS_PER_PLUME:
                break
            api = str(w["api"])
            if api in seen_api:
                continue
            seen_api.add(api)
            rows.append({
                "facility_id": f"OK-{api}",
                "operator": str(w["operator"]).strip().title(),
                "facility_name": str(w["well_name"]).strip().title(),
                "lat": round(float(w["sh_lat"]), 6),
                "lon": round(float(w["sh_lon"]), 6),
                "state": "Oklahoma",
            })
            added += 1
        if added == 0:
            print(f"  no real-operator well found near {p.plume_id} ({p.place})")

    new_rows = pd.DataFrame(rows, columns=[
        "facility_id", "operator", "facility_name", "lat", "lon", "state"])
    new_rows.to_csv(DATA_DIR / "facilities.csv", mode="a", header=False, index=False)

    print(f"Appended {len(new_rows)} OK facility rows "
          f"({new_rows['operator'].nunique()} distinct real operators)")
    print(new_rows.to_string())


if __name__ == "__main__":
    main()
