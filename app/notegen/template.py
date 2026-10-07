"""Deterministic, non-LLM note generator.

This is the safe fallback: it has zero external dependencies and zero
factuality risk by construction, because it only ever emits sentences
built directly from StructuredSummary fields -- there is no free-text
generation step for the factuality guard to check. It is also what powers
the pipeline end-to-end without any LLM configured, which is the default
(and, in this scaffold, only wired-up) generator behind POST
/v1/reports/weekly.
"""
from __future__ import annotations

from app.features.fluency import FluencyDirection
from app.features.engagement import EngagementDirection
from app.features.summarize import StructuredSummary
from app.notegen.base import GeneratedNote, NoteGenerator


class TemplateNoteGenerator(NoteGenerator):
    def generate(self, summary: StructuredSummary) -> GeneratedNote:
        sentences: list[str] = []

        if summary.newly_mastered_skills:
            skills = _join_and(summary.newly_mastered_skills)
            verb = "is" if len(summary.newly_mastered_skills) == 1 else "are"
            sentences.append(f"Great news this week -- {skills} {verb} now mastered!")

        improving = [
            t.skill_area
            for t in summary.fluency_trends
            if t.direction == FluencyDirection.IMPROVING
        ]
        if improving:
            sentences.append(
                f"Response times are getting faster on {_join_and(improving)}, "
                "a sign fluency is building, not just accuracy."
            )

        regressing = [
            t.skill_area
            for t in summary.fluency_trends
            if t.direction == FluencyDirection.REGRESSING
        ]
        if regressing:
            sentences.append(
                f"Worth noting: answers on {_join_and(regressing)} are taking "
                "longer than usual even though accuracy looks steady -- this can "
                "be a sign of fatigue or guessing rather than confident recall."
            )

        if summary.stuck_skills:
            stuck_names = _join_and([s.skill_area for s in summary.stuck_skills])
            verb = "has" if len(summary.stuck_skills) == 1 else "have"
            sentences.append(
                f"{stuck_names} {verb} stayed below target accuracy for "
                f"{summary.stuck_skills[0].stuck_session_count} sessions in a row "
                "and would benefit from focused attention."
            )

        if summary.engagement.direction == EngagementDirection.DOWN:
            sentences.append(
                "Practice frequency dipped compared to last period -- a few "
                "extra short sessions this week would help."
            )
        elif summary.engagement.direction == EngagementDirection.UP:
            sentences.append(
                "Practice frequency was up compared to last period -- great "
                "consistency."
            )

        if not sentences:
            sentences.append(
                f"{summary.student_id} completed {summary.total_sessions} "
                f"session(s) totaling {summary.total_practice_minutes} minutes "
                "this period, with steady performance across all skill areas "
                "practiced."
            )

        parent_note = " ".join(sentences)
        next_focus = _pick_next_focus(summary)

        return GeneratedNote(
            parent_note=parent_note, next_focus=next_focus, confidence=1.0
        )


def _pick_next_focus(summary: StructuredSummary) -> str:
    """Pick a single recommended focus skill for next session.

    Priority: a stuck skill (most sessions stuck first) beats a fluency
    regression, which beats simply continuing the most recently practiced
    skill area. This ordering mirrors what a tutor would triage first.
    """
    if summary.stuck_skills:
        worst = max(summary.stuck_skills, key=lambda s: s.stuck_session_count)
        return worst.skill_area

    regressing = [
        t for t in summary.fluency_trends if t.direction == FluencyDirection.REGRESSING
    ]
    if regressing:
        return regressing[0].skill_area

    if summary.skill_areas_practiced:
        return summary.skill_areas_practiced[0]

    return "general review"


def _join_and(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"
