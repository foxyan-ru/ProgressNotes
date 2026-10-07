"""Plateau/stuck-skill detection.

Flags a skill area whose per-session accuracy has stayed at or below a
threshold for at least `min_sessions` consecutive most-recent sessions --
the "this isn't clicking, a tutor should intervene" signal.
"""
from __future__ import annotations

from statistics import mean

from pydantic import BaseModel

from app.schemas.practice import PracticeSession


class StuckSkill(BaseModel):
    skill_area: str
    stuck_session_count: int
    average_accuracy: float


def _session_accuracy(session: PracticeSession) -> float | None:
    if not session.items:
        return None
    correct = sum(1 for item in session.items if item.correct)
    return correct / len(session.items)


def detect_stuck_skills(
    session_history: list[PracticeSession],
    threshold: float = 0.80,
    min_sessions: int = 3,
) -> list[StuckSkill]:
    """Flag skill areas whose per-session accuracy has stayed at or below
    `threshold` for at least `min_sessions` consecutive most-recent sessions.

    `session_history` should be the full history available for the student
    (not just the current reporting period) so that streaks spanning period
    boundaries are detected correctly. Sessions are grouped by skill_area
    and ordered chronologically by date; a streak is measured from the most
    recent session backwards, and breaks the moment a session rises above
    threshold.
    """
    by_skill: dict[str, list[PracticeSession]] = {}
    for session in session_history:
        by_skill.setdefault(session.skill_area, []).append(session)

    stuck: list[StuckSkill] = []
    for skill_area, sessions in by_skill.items():
        ordered = sorted(sessions, key=lambda s: s.date)
        accuracies = [_session_accuracy(s) for s in ordered]

        streak = 0
        streak_accuracies: list[float] = []
        for accuracy in reversed(accuracies):
            if accuracy is None:
                break
            if accuracy <= threshold:
                streak += 1
                streak_accuracies.append(accuracy)
            else:
                break

        if streak >= min_sessions:
            stuck.append(
                StuckSkill(
                    skill_area=skill_area,
                    stuck_session_count=streak,
                    average_accuracy=round(mean(streak_accuracies), 4),
                )
            )

    return sorted(stuck, key=lambda s: s.skill_area)
