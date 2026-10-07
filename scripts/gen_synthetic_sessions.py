"""Synthetic data generator for demoing the ProgressNote pipeline without
any real ed-tech partner data.

Not executed as part of scaffolding this project -- intended to be run
later with:
    python scripts/gen_synthetic_sessions.py > sample_request.json

Bakes in three specific, realistic patterns so the whole pipeline
(feature layer -> structured summary -> note generator -> factuality
guard) has something meaningful to demonstrate end-to-end:

  * "phonics.blends"      -- crosses the mastery threshold this period.
  * "math.subtraction"    -- plateaued below threshold for 3+ sessions.
  * "reading.fluency_cvc" -- accuracy holds steady but latency regresses
                             (a fatigue/guessing signal accuracy alone
                             would hide).
"""
from __future__ import annotations

import json
import random
from datetime import date, timedelta

STUDENT_ID = "stu_synthetic_001"
PERIOD_START = date(2026, 9, 15)
PERIOD_END = date(2026, 9, 21)

_rng = random.Random(42)


def _make_items(
    count: int, correct_rate: float, latency_range: tuple[int, int]
) -> list[dict]:
    items = []
    for i in range(count):
        correct = _rng.random() < correct_rate
        latency = _rng.randint(*latency_range)
        items.append(
            {
                "item": f"item_{i}",
                "correct": correct,
                "latency_ms": latency,
                "attempts": 1 if correct else _rng.choice([1, 1, 2]),
            }
        )
    return items


def _session(
    day_offset: int, skill_area: str, duration: int, items: list[dict]
) -> dict:
    return {
        "date": (PERIOD_START + timedelta(days=day_offset)).isoformat(),
        "duration_minutes": duration,
        "skill_area": skill_area,
        "items": items,
    }


def build_sessions() -> list[dict]:
    sessions: list[dict] = []

    # phonics.blends: was ~65% accurate historically, now consistently
    # ~90%+ -- crosses the mastery threshold this period.
    sessions.append(
        _session(0, "phonics.blends", 10, _make_items(12, 0.92, (900, 1600)))
    )
    sessions.append(
        _session(3, "phonics.blends", 8, _make_items(10, 0.90, (850, 1500)))
    )

    # math.subtraction: stuck at ~65-72% for three consecutive sessions.
    sessions.append(
        _session(0, "math.subtraction", 9, _make_items(10, 0.70, (1200, 2200)))
    )
    sessions.append(
        _session(2, "math.subtraction", 9, _make_items(10, 0.65, (1200, 2200)))
    )
    sessions.append(
        _session(5, "math.subtraction", 9, _make_items(10, 0.72, (1200, 2200)))
    )

    # reading.fluency_cvc: accuracy steady (~85%) but latency on correct
    # answers climbs steadily across the period.
    sessions.append(
        _session(0, "reading.fluency_cvc", 10, _make_items(12, 0.85, (900, 1300)))
    )
    sessions.append(
        _session(3, "reading.fluency_cvc", 10, _make_items(12, 0.85, (1400, 1900)))
    )
    sessions.append(
        _session(6, "reading.fluency_cvc", 10, _make_items(12, 0.84, (2000, 2600)))
    )

    return sorted(sessions, key=lambda s: s["date"])


def build_request() -> dict:
    return {
        "student_id": STUDENT_ID,
        "period_start": PERIOD_START.isoformat(),
        "period_end": PERIOD_END.isoformat(),
        "sessions": build_sessions(),
        "mastery_snapshot": {
            "phonics.blends": 0.91,
            "math.subtraction": 0.69,
            "reading.fluency_cvc": 0.85,
        },
    }


if __name__ == "__main__":
    print(json.dumps(build_request(), indent=2))
