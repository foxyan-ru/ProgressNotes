"""Canonical internal schema for weekly practice data.

Every ed-tech vendor's raw export gets mapped, via an adapter
(see app/adapters/), into these models before anything else in the system
touches it. Nothing downstream of this module should ever need to know
what a vendor's raw payload looked like.
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class PracticeItem(BaseModel):
    """A single practice question/prompt attempt within a session."""

    item: str
    correct: bool
    latency_ms: int = Field(ge=0, description="Time to respond, in milliseconds.")
    attempts: int = Field(default=1, ge=1)


class PracticeSession(BaseModel):
    """One practice session, scoped to a single skill area."""

    date: date
    duration_minutes: int = Field(ge=0)
    skill_area: str = Field(
        description='Dotted skill taxonomy path, e.g. "phonics.blends".'
    )
    items: list[PracticeItem] = Field(default_factory=list)


class WeeklyReportRequest(BaseModel):
    """The request body for POST /v1/reports/weekly.

    This is the canonical shape every vendor's raw data is normalized into
    via an app.adapters.SessionAdapter before it ever reaches this API.
    """

    student_id: str
    period_start: date
    period_end: date
    sessions: list[PracticeSession] = Field(default_factory=list)
    mastery_snapshot: dict[str, float] = Field(
        default_factory=dict,
        description="skill_area -> rolling accuracy (0.0-1.0) as of period_end.",
    )
