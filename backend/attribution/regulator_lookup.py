"""State -> regulator/rule routing.

regulator_rules.json is generated from data/regulators.csv (read-only; that
file is Person A's territory) so the attribution package carries its own copy
and the API never depends on CSV parsing at request time. Regenerate with:
    python -m backend.attribution.regulator_lookup
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .regulator_enrichment import ENRICHMENT

HERE = Path(__file__).resolve().parent
RULES_PATH = HERE / "regulator_rules.json"
_REGULATORS_CSV = HERE.parents[1] / "data" / "regulators.csv"  # read-only


def regenerate() -> dict:
    """Rebuild regulator_rules.json from data/regulators.csv, merging in the
    hand-authored ENRICHMENT (salutation/tone/rule_citation) per state. A
    state missing from ENRICHMENT gets a generic auto-derived fallback so the
    schema always has all 7 keys and this never crashes on an unmapped
    state."""
    import pandas as pd

    df = pd.read_csv(_REGULATORS_CSV)
    rules = {}
    for _, row in df.iterrows():
        regulator_name = row["regulator_name"].strip()
        fallback = {
            "salutation": f"To the {regulator_name}:",
            "tone": "formal",
            "rule_citation": row["applicable_rule"].strip(),
        }
        rules[row["state"]] = {
            "regulator_name": regulator_name,
            "complaint_mechanism": row["complaint_mechanism"].strip(),
            "applicable_rule": row["applicable_rule"].strip(),
            "rule_summary": row["rule_summary"].strip(),
            **ENRICHMENT.get(row["state"], fallback),
        }
    RULES_PATH.write_text(json.dumps(rules, indent=2))
    print(f"wrote {RULES_PATH.name} with states: {list(rules)}")
    return rules


@lru_cache(maxsize=1)
def _rules() -> dict:
    return json.loads(RULES_PATH.read_text())


def lookup(state: str) -> dict | None:
    """Regulator/rule record for a plume's state, or None if out of scope."""
    return _rules().get(state)


if __name__ == "__main__":
    regenerate()
