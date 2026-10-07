"""Assembles the StructuredSummary -- the single, closed, fully-typed
object that is the ONLY thing any note generator (LLM or template) is
allowed to see.

Every field on StructuredSummary is either a raw echo of an input
(student_id, period dates) or the output of a deterministic feature
function in this package. There is no "raw session dump" field. If a fact
is not derivable from one of these fields, no generator is permitted to
say it -- the factuality guard (see app/notegen/factuality.py) enforces
this at runtime. This function and StructuredSummary are the real "IP" of
this project, not any particular note-generation prompt.
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.features.engagement import EngagementTrend, compute_engagement_trend
from app.features.fluency import FluencyTrend, compute_latency_trend
from app.features.mastery import detect_newly_mastered
from app.features.plateau import StuckSkill, detect_stuck_skills
from app.schemas.practice import PracticeSession, WeeklyReportRequest


class StructuredSummary(BaseModel):
    student_id: str
    period_start: date
    period_end: date

    total_sessions: int
    total_practice_minutes: int
    skill_areas_practiced: list[str]

    current_mastery_snapshot: dict[str, float]
    newly_mastered_skills: list[str]
    stuck_skills: list[StuckSkill]
    fluency_trends: list[FluencyTrend]
    engagement: EngagementTrend


def build_structured_summary(
    request: WeeklyReportRequest,
    previous_snapshot: dict[str, float],
    prior_period_stats: dict,
) -> StructuredSummary:
    """Assemble the single structured summary object for a reporting period.

    `prior_period_stats` is expected to contain:
      - "session_count": int -- number of sessions in the prior period.
      - "total_minutes": int -- total practice minutes in the prior period.
      - "prior_sessions": list[PracticeSession] -- historical sessions
        preceding this period's `request.sessions`, used so that plateau
        streaks and fluency baselines spanning the period boundary are
        computed correctly. May be an empty list if no history is
        available (e.g. a brand-new student).

    This function performs no LLM calls and has no side effects -- it is
    pure aggregation over already-validated, already-computed inputs. Its
    output is the full and only surface area the note generator sees.
    """
    sessions = request.sessions
    skill_areas_practiced = sorted({s.skill_area for s in sessions})

    newly_mastered = detect_newly_mastered(
        current_snapshot=request.mastery_snapshot,
        previous_snapshot=previous_snapshot,
    )

    prior_sessions: list[PracticeSession] = prior_period_stats.get(
        "prior_sessions", []
    )
    full_history = [*prior_sessions, *sessions]

    stuck_skills = detect_stuck_skills(session_history=full_history)

    fluency_trends = [
        compute_latency_trend(sessions=full_history, skill_area=skill_area)
        for skill_area in skill_areas_practiced
    ]

    engagement = compute_engagement_trend(
        sessions=sessions,
        prior_period_session_count=prior_period_stats.get("session_count", 0),
        prior_period_total_minutes=prior_period_stats.get("total_minutes", 0),
    )

    return StructuredSummary(
        student_id=request.student_id,
        period_start=request.period_start,
        period_end=request.period_end,
        total_sessions=len(sessions),
        total_practice_minutes=sum(s.duration_minutes for s in sessions),
        skill_areas_practiced=skill_areas_practiced,
        current_mastery_snapshot=request.mastery_snapshot,
        newly_mastered_skills=newly_mastered,
        stuck_skills=stuck_skills,
        fluency_trends=fluency_trends,
        engagement=engagement,
    )
