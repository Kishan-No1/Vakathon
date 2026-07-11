from fastapi import APIRouter

from backend.data_pipeline.load_data import load_plumes

router = APIRouter()


@router.get("/events")
def list_events():
    return {"events": load_plumes()}
