from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.community import store

router = APIRouter()


class GroundTruthReport(BaseModel):
    plume_id: str
    name: str = Field(max_length=80)
    zip_code: str = Field(max_length=10)
    smell: bool = False
    visible_flare: bool = False
    notes: str = Field(default="", max_length=500)
    # Optional[...] (not `float | None`) so the model builds on Python 3.9 too
    lat: Optional[float] = None
    lon: Optional[float] = None


class CosignRequest(BaseModel):
    plume_id: str
    name: str = Field(max_length=80)
    zip_code: str = Field(max_length=10)


@router.post("/community/reports")
def submit_report(req: GroundTruthReport):
    return store.add_report(req.plume_id, req.model_dump(exclude={"plume_id"}))


@router.get("/community/reports")
def list_reports(plume_id: str):
    return store.get_reports(plume_id)


@router.post("/community/cosign")
def cosign(req: CosignRequest):
    return store.add_cosign(req.plume_id, req.name, req.zip_code)


@router.get("/community/cosign")
def get_cosigns(plume_id: str):
    return store.get_cosigns(plume_id)
