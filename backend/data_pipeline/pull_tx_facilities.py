"""One-off script: append real Texas RRC well coordinates to data/facilities.csv,
with clearly-fictional operator placeholders (RRC's public well-location layer has
no operator field; we deliberately never guess a real company name for a specific
unverified well — see data/SOURCES.md and docs/implementation_plan.md).

Operator placeholders are assigned per geographic cluster (by plume `place` name),
not per-row-random, so backend/attribution/features.py's operator_well_density
feature sees realistic same-operator clustering instead of permanent zeros.

Run: python -m backend.data_pipeline.pull_tx_facilities
Appends only — never rewrites the existing NM rows in facilities.csv.
"""
import math
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RRC_URL = ("https://gis.rrc.texas.gov/server/rest/services/rrc_public/"
           "RRC_Public_Viewer_Srvs/MapServer/1/query")
WELLS_PER_PLUME = 2
SEARCH_DEG = 0.03  # ~3 km half-box


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
        "outFields": "API,GIS_WELL_NUMBER,GIS_LAT83,GIS_LONG83",
        "returnGeometry": "false", "resultRecordCount": 20, "f": "json",
    }
    r = requests.get(RRC_URL, params=params, timeout=60)
    r.raise_for_status()
    feats = r.json().get("features", [])
    return [f["attributes"] for f in feats
            if f["attributes"].get("GIS_LAT83") and f["attributes"].get("GIS_LONG83")]


def main() -> None:
    plumes = pd.read_csv(DATA_DIR / "plumes.csv")
    tx_plumes = plumes[plumes["state"] == "Texas"]
    print(f"{len(tx_plumes)} TX plumes to source facilities for")

    # cluster -> sequential fictional operator name, assigned by first-seen order
    cluster_operator: dict[str, str] = {}
    rows, seen_api = [], set()

    for _, p in tx_plumes.iterrows():
        cluster = p["place"]
        if cluster not in cluster_operator:
            cluster_operator[cluster] = f"Permian Basin Operator #{len(cluster_operator) + 1}"
        operator = cluster_operator[cluster]

        try:
            wells = query_wells_near(p.lat, p.lon)
        except Exception as e:
            print(f"  query failed for {p.plume_id}: {e}")
            continue

        wells = sorted(wells, key=lambda w: haversine_m(
            p.lat, p.lon, w["GIS_LAT83"], w["GIS_LONG83"]))

        added = 0
        for w in wells:
            if added >= WELLS_PER_PLUME:
                break
            api = str(w["API"])
            if api in seen_api:
                continue
            seen_api.add(api)
            rows.append({
                "facility_id": f"TX-{api}",
                "operator": operator,
                "facility_name": f"Well #{w['GIS_WELL_NUMBER']}",
                "lat": round(float(w["GIS_LAT83"]), 6),
                "lon": round(float(w["GIS_LONG83"]), 6),
                "state": "Texas",
            })
            added += 1

    new_rows = pd.DataFrame(rows, columns=[
        "facility_id", "operator", "facility_name", "lat", "lon", "state"])
    new_rows.to_csv(DATA_DIR / "facilities.csv", mode="a", header=False, index=False)

    print(f"Appended {len(new_rows)} TX facility rows "
          f"({new_rows['operator'].nunique()} fictional operator clusters)")
    print(new_rows.to_string())


if __name__ == "__main__":
    main()
