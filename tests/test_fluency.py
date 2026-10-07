from datetime import date, timedelta

from app.features.fluency import FluencyDirection, compute_latency_trend
from app.schemas.practice import PracticeItem, PracticeSession

BASE_DATE = date(2026, 9, 1)


def _session(day_offset: int, skill_area: str, latencies: list[int]) -> PracticeSession:
    items = [
        PracticeItem(item=f"i{i}", correct=True, latency_ms=latency)
        for i, latency in enumerate(latencies)
    ]
    return PracticeSession(
        date=BASE_DATE + timedelta(days=day_offset),
        duration_minutes=10,
        skill_area=skill_area,
        items=items,
    )


def test_slower_latency_is_flagged_as_regressing():
    sessions = [
        _session(0, "reading.fluency_cvc", [900, 1000, 1100]),
        _session(2, "reading.fluency_cvc", [900, 1000, 1100]),
        _session(4, "reading.fluency_cvc", [2200, 2300, 2400]),
        _session(6, "reading.fluency_cvc", [2200, 2300, 2400]),
    ]

    trend = compute_latency_trend(sessions, "reading.fluency_cvc")

    assert trend.direction == FluencyDirection.REGRESSING
    assert trend.current_avg_latency_ms > trend.baseline_avg_latency_ms


def test_faster_latency_is_flagged_as_improving():
    sessions = [
        _session(0, "phonics.blends", [2200, 2300]),
        _session(2, "phonics.blends", [2200, 2300]),
        _session(4, "phonics.blends", [900, 1000]),
        _session(6, "phonics.blends", [900, 1000]),
    ]

    trend = compute_latency_trend(sessions, "phonics.blends")

    assert trend.direction == FluencyDirection.IMPROVING


def test_similar_latency_is_stable():
    sessions = [
        _session(0, "math.addition", [1000, 1050]),
        _session(2, "math.addition", [1000, 1050]),
        _session(4, "math.addition", [1020, 1040]),
        _session(6, "math.addition", [1020, 1040]),
    ]

    trend = compute_latency_trend(sessions, "math.addition")

    assert trend.direction == FluencyDirection.STABLE


def test_insufficient_data_with_single_session():
    sessions = [_session(0, "phonics.blends", [1000])]

    trend = compute_latency_trend(sessions, "phonics.blends")

    assert trend.direction == FluencyDirection.INSUFFICIENT_DATA


def test_unrelated_skill_areas_are_ignored():
    sessions = [
        _session(0, "phonics.blends", [1000]),
        _session(2, "math.addition", [5000]),
    ]

    trend = compute_latency_trend(sessions, "phonics.blends")

    # Only one phonics.blends session remains once math.addition is
    # filtered out, so there isn't enough data for a trend.
    assert trend.direction == FluencyDirection.INSUFFICIENT_DATA
