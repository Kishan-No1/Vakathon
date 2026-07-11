"""Bridge from Person A's community store into real training-set labels.

Reads backend.community.store (Person A's module) and spatial_join.py's own
nearest_facility() — both read-only — to find plumes where residents have
independently corroborated an ALREADY geometrically-matched detection. This
never manufactures a positive for an unmatched plume: doing so would violate
the 2 km safety rule (no confident match => no named operator), so
confirmation can only strengthen an existing match, never create one.
"""
from __future__ import annotations

MIN_REPORTS = 2  # local constant; not imported from Person A's store to
                  # avoid coupling to a module we don't own


def confirmed_plume_ids(min_reports: int = MIN_REPORTS) -> list[str]:
    """Plume ids with >=min_reports community reports AND an existing
    matched nearest facility. Returns [] if the community store is empty or
    unavailable (safe no-op — training data is unaffected until real reports
    exist)."""
    try:
        from backend.community.store import get_reports
    except Exception:
        return []

    from .spatial_join import join_all

    df = join_all()
    matched_ids = df.loc[df["matched"], "plume_id"].tolist()

    confirmed = []
    for plume_id in matched_ids:
        try:
            summary = get_reports(plume_id)
        except Exception:
            continue
        if summary.get("count", 0) >= min_reports:
            confirmed.append(plume_id)
    return confirmed


if __name__ == "__main__":
    ids = confirmed_plume_ids()
    print(f"{len(ids)} community-confirmed plume(s): {ids}")
