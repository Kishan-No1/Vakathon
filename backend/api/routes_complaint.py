"""POST /complaint/generate — Claude-drafted regulator complaint letter.

Uses ANTHROPIC_API_KEY from the environment. If the key is missing or the call
fails, returns a deterministic template letter so the demo never dead-ends
(checklist §5.5: "cached fallback letter ready if API is down").
"""
import os
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.api.routes_attribution import attribute
from backend.data_pipeline.load_data import get_plume

router = APIRouter()

PROMPT_TEMPLATE = """You are helping a resident draft a formal methane-emission \
complaint to a state regulator. Write a professional, factual complaint letter \
(no more than 350 words) using ONLY the facts below. Do not invent facts, \
measurements, or legal claims beyond the cited rule. If no operator is identified, \
request that the regulator investigate and identify the responsible party.

Facts:
- Detection: methane plume {plume_id}, detected {detected_date} by {source}
- Location: {lat:.4f}, {lon:.4f} near {place}, {state}
- Estimated leak rate: {leak_rate_kg_hr} kg/hr
- Attributed operator: {operator}
- Attribution confidence: {confidence}
- Regulator: {regulator_name}
- Applicable rule: {applicable_rule} — {rule_summary}
- Community co-signers: {cosign_count} residents have co-signed this complaint
- Date of letter: {today}

Output only the letter text, starting with "To: {regulator_name}"."""

CITIZEN_PROMPT_TEMPLATE = """You are helping a resident draft a formal citizen \
report to a state regulator about suspected methane emissions they personally \
observed. Write a professional, factual complaint letter (no more than 350 words) \
using ONLY the facts below. This is a FIRST-PERSON citizen report: lead with the \
resident's own observations, and cite the satellite detection as supporting \
context. Do not invent facts, measurements, or legal claims beyond the cited \
rule. Never assert the operator is violating the law — the attribution is a \
possible association pending verification. If no operator is identified, request \
that the regulator investigate and identify the responsible party.

Facts:
- Reporting resident: {reporter_name} (ZIP {reporter_zip})
- Resident's observations: {observations}
- Resident's notes: {notes}
- Nearby satellite detection: methane plume {plume_id}, detected {detected_date} by {source}
- Location: {lat:.4f}, {lon:.4f} near {place}, {state}
- Estimated leak rate: {leak_rate_kg_hr} kg/hr
- Possibly associated operator (pending verification): {operator}
- Regulator: {regulator_name}
- Applicable rule: {applicable_rule} — {rule_summary}
- Date of letter: {today}

Output only the letter text, starting with "To: {regulator_name}"."""


class CitizenReport(BaseModel):
    """Resident-entered observations that ground a citizen-report letter."""
    name: str = Field(default="A concerned resident", max_length=80)
    zip_code: str = Field(default="", max_length=10)
    smell: bool = False
    visible_flare: bool = False
    notes: str = Field(default="", max_length=500)


class ComplaintRequest(BaseModel):
    plume_id: str
    cosign_count: int = 0
    # Optional[...] (not `| None`) so the model builds on Python 3.9 too
    citizen_report: Optional[CitizenReport] = None


def _fallback_letter(ctx: dict) -> str:
    operator_line = (
        f"our records attribute this emission to {ctx['operator']} "
        f"(confidence {ctx['confidence']})"
        if ctx["operator"] != "Not identified"
        else "the responsible operator has not been identified; we request that "
             "your office investigate and identify the responsible party"
    )
    return (
        f"To: {ctx['regulator_name']}\n"
        f"Date: {ctx['today']}\n\n"
        f"Re: Methane emission event {ctx['plume_id']} near {ctx['place']}, {ctx['state']}\n\n"
        f"Dear Sir or Madam,\n\n"
        f"On {ctx['detected_date']}, satellite instrument {ctx['source']} detected a "
        f"methane plume at coordinates {ctx['lat']:.4f}, {ctx['lon']:.4f} with an "
        f"estimated release rate of {ctx['leak_rate_kg_hr']} kg/hr. Based on available "
        f"facility data, {operator_line}.\n\n"
        f"We believe this event falls under {ctx['applicable_rule']}: "
        f"{ctx['rule_summary']}\n\n"
        f"{ctx['cosign_count']} residents of the affected area have co-signed this "
        f"complaint. We respectfully request an investigation and a written response.\n\n"
        f"Sincerely,\nConcerned residents of {ctx['place']}, {ctx['state']}"
    )


def _observations_text(cr: CitizenReport) -> str:
    obs = []
    if cr.smell:
        obs.append("a strong gas / rotten-egg odor")
    if cr.visible_flare:
        obs.append("a visible flare, venting, or haze")
    return " and ".join(obs) if obs else "conditions described in their notes"


def _citizen_fallback_letter(ctx: dict, cr: CitizenReport) -> str:
    operator_line = (
        f"available facility data indicates this detection is consistent with "
        f"{ctx['operator']} (a possible association pending verification, not a "
        f"confirmed source)"
        if ctx["operator"] != "Not identified"
        else "the responsible operator has not been identified; we request that "
             "your office investigate and identify the responsible party"
    )
    notes_line = f"\n\nAdditional notes from the resident: {cr.notes}" if cr.notes else ""
    return (
        f"To: {ctx['regulator_name']}\n"
        f"Date: {ctx['today']}\n\n"
        f"Re: Citizen report of suspected methane emissions near {ctx['place']}, {ctx['state']}\n\n"
        f"Dear Sir or Madam,\n\n"
        f"I am {cr.name}" + (f" (ZIP {cr.zip_code})" if cr.zip_code else "") + ", a "
        f"resident reporting first-hand observations of {_observations_text(cr)} "
        f"near {ctx['place']}, {ctx['state']}.{notes_line}\n\n"
        f"My report is supported by an independent satellite detection: on "
        f"{ctx['detected_date']}, instrument {ctx['source']} detected methane plume "
        f"{ctx['plume_id']} at coordinates {ctx['lat']:.4f}, {ctx['lon']:.4f} with an "
        f"estimated release rate of {ctx['leak_rate_kg_hr']} kg/hr. Based on that "
        f"detection, {operator_line}.\n\n"
        f"I believe this event falls under {ctx['applicable_rule']}: "
        f"{ctx['rule_summary']}\n\n"
        f"I respectfully request an investigation and a written response.\n\n"
        f"Sincerely,\n{cr.name}"
    )


@router.post("/complaint/generate")
def generate_complaint(req: ComplaintRequest):
    plume = get_plume(req.plume_id)
    if plume is None:
        raise HTTPException(404, f"Unknown plume_id {req.plume_id}")
    attr = attribute(req.plume_id)
    reg = attr["regulator"] or {}

    ctx = {
        **{k: plume[k] for k in ("plume_id", "detected_date", "source", "lat", "lon",
                                 "place", "state", "leak_rate_kg_hr")},
        "operator": attr["operator"] or "Not identified",
        "confidence": attr["confidence"] if attr["matched"] else "n/a",
        "regulator_name": reg.get("regulator_name", "State environmental regulator"),
        "applicable_rule": reg.get("applicable_rule", ""),
        "rule_summary": reg.get("rule_summary", ""),
        "cosign_count": req.cosign_count,
        "today": date.today().isoformat(),
    }

    cr = req.citizen_report
    if cr is not None:
        prompt = CITIZEN_PROMPT_TEMPLATE.format(
            **ctx,
            reporter_name=cr.name,
            reporter_zip=cr.zip_code or "not provided",
            observations=_observations_text(cr),
            notes=cr.notes or "none",
        )
    else:
        prompt = PROMPT_TEMPLATE.format(**ctx)

    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic

            client = anthropic.Anthropic()
            msg = client.messages.create(
                model="claude-sonnet-5",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return {"letter": msg.content[0].text, "generator": "claude"}
        except Exception:
            pass  # fall through to template

    fallback = _citizen_fallback_letter(ctx, cr) if cr is not None else _fallback_letter(ctx)
    return {"letter": fallback, "generator": "template_fallback"}
