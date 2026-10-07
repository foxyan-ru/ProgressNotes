"""Factuality guard for generated notes.

Extracts skill-area mentions and numeric claims from a generated note's
text and verifies each one traces back to a field on the StructuredSummary
that produced it. This is what makes it safe to let an LLM phrase the
note in natural language: no matter what the model says, this check can
catch (and let a caller reject/retry on) any claim that is not actually
backed by the input data.

This is deliberately conservative and regex/keyword based rather than
another LLM call -- a factuality checker that itself depends on an LLM's
judgment would not buy much additional trust.
"""
from __future__ import annotations

import re

from pydantic import BaseModel

from app.features.summarize import StructuredSummary

_SKILL_TOKEN_RE = re.compile(r"\b[a-zA-Z][a-zA-Z_]*(?:\.[a-zA-Z_]+)+\b")
_NUMBER_TOKEN_RE = re.compile(r"\d+(?:\.\d+)?")


class FactualityCheckResult(BaseModel):
    passed: bool
    unverifiable_skill_mentions: list[str]
    unverifiable_numbers: list[str]
    checked_skill_mentions: list[str]
    checked_numbers: list[str]


def _known_skill_areas(summary: StructuredSummary) -> set[str]:
    known = set(summary.skill_areas_practiced)
    known.update(summary.newly_mastered_skills)
    known.update(summary.current_mastery_snapshot.keys())
    known.update(s.skill_area for s in summary.stuck_skills)
    known.update(t.skill_area for t in summary.fluency_trends)
    return known


def _known_numbers(summary: StructuredSummary) -> set[str]:
    """Collect every numeric value present anywhere on the summary, in a
    handful of plausible textual forms (int, whole-percent, one/two
    decimal), so that reasonable phrasings ("85%", "85.0%", "85") all
    verify against the same underlying field.
    """
    raw_numbers: list[float] = [
        summary.total_sessions,
        summary.total_practice_minutes,
        summary.engagement.current_session_count,
        summary.engagement.current_total_minutes,
        summary.engagement.prior_session_count,
        summary.engagement.prior_total_minutes,
    ]
    raw_numbers.extend(summary.current_mastery_snapshot.values())
    for stuck in summary.stuck_skills:
        raw_numbers.append(stuck.stuck_session_count)
        raw_numbers.append(stuck.average_accuracy)
    for trend in summary.fluency_trends:
        if trend.baseline_avg_latency_ms is not None:
            raw_numbers.append(trend.baseline_avg_latency_ms)
        if trend.current_avg_latency_ms is not None:
            raw_numbers.append(trend.current_avg_latency_ms)
        if trend.percent_change is not None:
            raw_numbers.append(trend.percent_change)
    if summary.engagement.session_count_change_pct is not None:
        raw_numbers.append(summary.engagement.session_count_change_pct)
    if summary.engagement.total_minutes_change_pct is not None:
        raw_numbers.append(summary.engagement.total_minutes_change_pct)

    known: set[str] = set()
    for value in raw_numbers:
        fvalue = float(value)
        known.add(str(int(fvalue)) if fvalue.is_integer() else str(value))
        known.add(f"{fvalue:.1f}")
        known.add(f"{fvalue:.2f}")
        # Accuracy / percent-change values (roughly -1..1) expressed as
        # whole or one-decimal percentages, e.g. 0.85 -> "85" / "85.0".
        if -1.0 <= fvalue <= 1.0:
            pct = fvalue * 100
            known.add(str(int(round(pct))))
            known.add(f"{pct:.1f}")
    return known


def check_factuality(
    note_text: str, summary: StructuredSummary
) -> FactualityCheckResult:
    """Verify that every skill-area mention and number in `note_text`
    traces back to a field on `summary`.

    Returns a FactualityCheckResult; `passed` is True only if every
    extracted claim was verifiable. Callers should treat `passed=False` as
    grounds to reject the note and either retry generation or fall back to
    TemplateNoteGenerator.
    """
    known_skills = _known_skill_areas(summary)
    known_numbers = _known_numbers(summary)

    mentioned_skills = sorted(set(_SKILL_TOKEN_RE.findall(note_text)))
    mentioned_numbers = sorted(set(_NUMBER_TOKEN_RE.findall(note_text)))

    unverifiable_skills = [s for s in mentioned_skills if s not in known_skills]
    unverifiable_numbers = [n for n in mentioned_numbers if n not in known_numbers]

    passed = not unverifiable_skills and not unverifiable_numbers

    return FactualityCheckResult(
        passed=passed,
        unverifiable_skill_mentions=unverifiable_skills,
        unverifiable_numbers=unverifiable_numbers,
        checked_skill_mentions=mentioned_skills,
        checked_numbers=mentioned_numbers,
    )
