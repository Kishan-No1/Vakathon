"""Hand-authored regulator metadata not present in data/regulators.csv
(Person A's file — do not add columns there). Keyed by the same state
strings regulators.csv uses ("New Mexico", "Texas"). Merged into
regulator_rules.json by regulator_lookup.regenerate().

Citations verified against data/regulators.csv's actual `applicable_rule`
text so `rule_citation` never contradicts it: New Mexico's rule reads
"19.15.27.9 NMAC — Statewide Natural Gas Capture Requirements..."; Texas's
reads "16 TAC 3.32 — Statewide Rule 32..."; Oklahoma's reads
"OAC 165:10-3-15 — Venting and Flaring".

New states added here only take effect once matched by a state string also
present in data/regulators.csv — regenerate() doesn't invent
regulator_name/complaint_mechanism/applicable_rule for states Person A
hasn't added yet; it falls back to a generic auto-derived enrichment for any
state missing from this table (see regulator_lookup.regenerate()).
"""
from __future__ import annotations

ENRICHMENT: dict[str, dict] = {
    "New Mexico": {
        "salutation": "To the New Mexico Oil Conservation Division:",
        "tone": "formal",
        "rule_citation": "19.15.27.9 NMAC",
    },
    "Texas": {
        "salutation": "To the Railroad Commission of Texas:",
        "tone": "formal",
        "rule_citation": "16 TAC 3.32",
    },
    "Oklahoma": {
        "salutation": "To the Oklahoma Corporation Commission:",
        "tone": "formal",
        "rule_citation": "OAC 165:10-3-15",
    },
}
