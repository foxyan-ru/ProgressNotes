"""Latency/fluency trend detection.

Accuracy alone hides fatigue and guessing: a student who keeps the same
accuracy but takes much longer per correct answer (or, suspiciously, much
less time) is showing a signal a bare accuracy percentage would miss
entirely. This module compares average latency-on-correct-answers between
the earlier and more recent halves of a skill area's session history.
"""
from __future__ import annotations

from enum import Enum
from statistics import mean

from pydantic import BaseModel

from app.schemas.practice import PracticeSession


class FluencyDirection(str, Enum):
    IMPROVING = "improving"
    REGRESSING = "regressing"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


class FluencyTrend(BaseModel):
    skill_area: str
    direction: FluencyDirection
    baseline_avg_latency_ms: float | None
    current_avg_latency_ms: float | None
    percent_change: float | None


def _avg_correct_latency(sessions: list[PracticeSession]) -> float | None:
    latencies = [
        item.latency_ms
        for session in sessions
        for item in session.items
        if item.correct
    ]
    if not latencies:
        return None
    return mean(latencies)


def compute_latency_trend(
    sessions: list[PracticeSession],
    skill_area: str,
    stable_band_pct: float = 0.10,
) -> FluencyTrend:
    """Compare average latency-on-correct-answers for the most recent half
    of a skill area's sessions ("current") against the earlier half
    ("baseline").

    `stable_band_pct` is the fractional change (default +/-10%) within
    which the trend is considered STABLE rather than improving/regressing.
    Fewer than two sessions with recorded correct-answer latencies for the
    skill area results in INSUFFICIENT_DATA rather than a guess.
    """
    relevant = sorted(
        (s for s in sessions if s.skill_area == skill_area), key=lambda s: s.date
    )

    if len(relevant) < 2:
        baseline_only = _avg_correct_latency(relevant)
        return FluencyTrend(
            skill_area=skill_area,
            direction=FluencyDirection.INSUFFICIENT_DATA,
            baseline_avg_latency_ms=baseline_only,
            current_avg_latency_ms=None,
            percent_change=None,
        )

    midpoint = len(relevant) // 2
    baseline_sessions = relevant[:midpoint]
    current_sessions = relevant[midpoint:]

    baseline_avg = _avg_correct_latency(baseline_sessions)
    current_avg = _avg_correct_latency(current_sessions)

    if baseline_avg is None or current_avg is None:
        return FluencyTrend(
            skill_area=skill_area,
            direction=FluencyDirection.INSUFFICIENT_DATA,
            baseline_avg_latency_ms=baseline_avg,
            current_avg_latency_ms=current_avg,
            percent_change=None,
        )

    percent_change = (current_avg - baseline_avg) / baseline_avg

    if percent_change > stable_band_pct:
        direction = FluencyDirection.REGRESSING  # slower -> possible fatigue/guessing
    elif percent_change < -stable_band_pct:
        direction = FluencyDirection.IMPROVING  # faster -> growing fluency
    else:
        direction = FluencyDirection.STABLE

    return FluencyTrend(
        skill_area=skill_area,
        direction=direction,
        baseline_avg_latency_ms=round(baseline_avg, 2),
        current_avg_latency_ms=round(current_avg, 2),
        percent_change=round(percent_change, 4),
    )
