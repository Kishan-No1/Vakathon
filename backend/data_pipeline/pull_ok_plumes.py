"""One-off script: append real Oklahoma (Anadarko Basin) CH4 plumes from Carbon
Mapper to data/plumes.csv. Same source/methodology as the original NM/TX pull
(see data/SOURCES.md) — append only, never touches the existing 32 rows.

Run: python -m backend.data_pipeline.pull_ok_plumes
"""
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
URL = "https://api.carbonmapper.org/api/v1/catalog/plume-csv"

# Anadarko Basin / western-central Oklahoma oil & gas corridor
BBOX = (-100.0, 34.5, -97.0, 36.5)
TARGET_ROWS = 15  # comparable in scale to the existing NM(15)/TX(17) sets


def main() -> None:
    params = [("bbox", BBOX[0]), ("bbox", BBOX[1]), ("bbox", BBOX[2]), ("bbox", BBOX[3]),
              ("plume_gas", "CH4"), ("limit", 500)]
    r = requests.get(URL, params=params, timeout=90)
    r.raise_for_status()
    raw = pd.read_csv(__import__("io").StringIO(r.text))
    print(f"Raw records pulled: {len(raw)}")

    raw = raw.dropna(subset=["plume_latitude", "plume_longitude", "emission_auto"])
    raw = raw[raw["region"] == "Oklahoma"]
    raw = raw[raw["ipcc_sector"].str.contains("Oil", case=False, na=False)]
    print(f"Oil & Gas Oklahoma records with a real emission estimate: {len(raw)}")

    existing_ids = set(pd.read_csv(DATA_DIR / "plumes.csv")["plume_id"])
    raw = raw[~raw["plume_id"].isin(existing_ids)]

    sel = raw.sort_values("emission_auto", ascending=False).head(TARGET_ROWS)

    out = pd.DataFrame({
        "plume_id": sel["plume_id"],
        "lat": sel["plume_latitude"].round(6),
        "lon": sel["plume_longitude"].round(6),
        "leak_rate_kg_hr": sel["emission_auto"].round(1),
        "detected_date": sel["datetime"].str[:10],
        "state": "Oklahoma",
        "place": sel["place"],
        "source": sel["instrument"].map(
            lambda x: "Carbon Mapper / Tanager-1" if str(x).startswith("tan")
            else f"Carbon Mapper / {x}"),
        "wind_speed_m_s": sel["wind_speed_avg_auto"].round(2),
        "wind_dir_deg": sel["wind_direction_avg_auto"].round(1),
    }).reset_index(drop=True)

    out.to_csv(DATA_DIR / "plumes.csv", mode="a", header=False, index=False)
    print(f"Appended {len(out)} Oklahoma plumes -> data/plumes.csv")
    print(out.to_string())


if __name__ == "__main__":
    main()
