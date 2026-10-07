"""Example adapter for a hypothetical ed-tech vendor ("ExampleVendor") whose
raw export uses different field names and nesting than our canonical
schema. This is the one concrete adapter in the scaffold -- it exists to
demonstrate the adapter pattern (the same shape as vendor-normalization
adapters used elsewhere in this developer's portfolio, applied here to
ed-tech data instead of e.g. KYC vendor data), not to be a template
marketplace.

ExampleVendor's raw shape (illustrative):

    {
        "learner_id": "stu_123",
        "week_start": "2026-09-01",
        "week_end": "2026-09-07",
        "mastery": {"phonics.blends": 0.91, "math.addition_facts": 0.62},
        "practice_blocks": [
            {
                "logged_on": "2026-09-02",
                "minutes_spent": 12,
                "topic_code": "phonics.blends",
                "attempts_log": [
                    {"prompt": "bl-01", "was_correct": true,
                     "response_time_ms": 2200, "tries": 1},
                    ...
                ],
            },
            ...
        ],
    }
"""
from __future__ import annotations

from datetime import date

from app.adapters.base import SessionAdapter
from app.schemas.practice import PracticeItem, PracticeSession, WeeklyReportRequest


class ExampleVendorAdapter(SessionAdapter):
    """Maps ExampleVendor's raw weekly export into WeeklyReportRequest."""

    def to_canonical(self, raw: dict) -> WeeklyReportRequest:
        sessions = [
            self._to_practice_session(block)
            for block in raw.get("practice_blocks", [])
        ]

        return WeeklyReportRequest(
            student_id=raw["learner_id"],
            period_start=date.fromisoformat(raw["week_start"]),
            period_end=date.fromisoformat(raw["week_end"]),
            sessions=sessions,
            mastery_snapshot=dict(raw.get("mastery", {})),
        )

    @staticmethod
    def _to_practice_session(block: dict) -> PracticeSession:
        items = [
            PracticeItem(
                item=attempt["prompt"],
                correct=bool(attempt["was_correct"]),
                latency_ms=int(attempt["response_time_ms"]),
                attempts=int(attempt.get("tries", 1)),
            )
            for attempt in block.get("attempts_log", [])
        ]
        return PracticeSession(
            date=date.fromisoformat(block["logged_on"]),
            duration_minutes=int(block["minutes_spent"]),
            skill_area=block["topic_code"],
            items=items,
        )
