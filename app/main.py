"""FastAPI application entrypoint.

Not executed as part of scaffolding this project. Would later be run with:
    uvicorn app.main:app --reload
"""
from __future__ import annotations

from fastapi import FastAPI

from app.api.v1.router import router as v1_router

app = FastAPI(
    title="ProgressNote API",
    description=(
        "B2B API that turns structured weekly practice data into a "
        "factuality-checked, plain-English parent note and next-session "
        "focus recommendation."
    ),
    version="0.1.0",
)

app.include_router(v1_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
