"""Engagement trend detection.

Compares this period's session frequency and total practice time against
the prior period's. Falling engagement is often the earliest warning sign
available -- well before accuracy or mastery numbers move.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from app.schemas.practice import PracticeSession


class EngagementDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class EngagementTrend(BaseModel):
    current_session_count: int
    current_total_minutes: int
    prior_session_count: int
    prior_total_minutes: int
    session_count_change_pct: float | None
    total_minutes_change_pct: float | None
    direction: EngagementDirection


def _pct_change(current: float, prior: float) -> float | None:
    if prior == 0:
        return None if current == 0 else 1.0
    return (current - prior) / prior


def compute_engagement_trend(
    sessions: list[PracticeSession],
    prior_period_session_count: int,
    prior_period_total_minutes: int,
    stable_band_pct: float = 0.10,
) -> EngagementTrend:
    """Compare this period's session count/total minutes against the prior
    period's. Direction is driven primarily by session count (frequency
    matters more than raw minutes for habit formation), falling back to
    minutes if the session-count comparison is undefined (prior count 0).
    """
    current_session_count = len(sessions)
    current_total_minutes = sum(s.duration_minutes for s in sessions)

    session_change = _pct_change(current_session_count, prior_period_session_count)
    minutes_change = _pct_change(current_total_minutes, prior_period_total_minutes)

    primary_change = session_change if session_change is not None else minutes_change

    if primary_change is None:
        direction = EngagementDirection.STABLE
    elif primary_change > stable_band_pct:
        direction = EngagementDirection.UP
    elif primary_change < -stable_band_pct:
        direction = EngagementDirection.DOWN
    else:
        direction = EngagementDirection.STABLE

    return EngagementTrend(
        current_session_count=current_session_count,
        current_total_minutes=current_total_minutes,
        prior_session_count=prior_period_session_count,
        prior_total_minutes=prior_period_total_minutes,
        session_count_change_pct=(
            round(session_change, 4) if session_change is not None else None
        ),
        total_minutes_change_pct=(
            round(minutes_change, 4) if minutes_change is not None else None
        ),
        direction=direction,
    )
