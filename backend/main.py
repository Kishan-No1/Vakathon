from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import (
    routes_attribution,
    routes_community,
    routes_complaint,
    routes_events,
)

app = FastAPI(title="Vakathon API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_events.router)
app.include_router(routes_attribution.router)
app.include_router(routes_complaint.router)
app.include_router(routes_community.router)


@app.get("/health")
def health():
    return {"status": "ok"}
