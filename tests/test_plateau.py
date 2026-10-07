from datetime import date, timedelta

from app.features.plateau import detect_stuck_skills
from app.schemas.practice import PracticeItem, PracticeSession

BASE_DATE = date(2026, 9, 1)


def _session(
    day_offset: int, skill_area: str, correct_count: int, total: int
) -> PracticeSession:
    items = [
        PracticeItem(item=f"i{i}", correct=(i < correct_count), latency_ms=1000)
        for i in range(total)
    ]
    return PracticeSession(
        date=BASE_DATE + timedelta(days=day_offset),
        duration_minutes=10,
        skill_area=skill_area,
        items=items,
    )


def test_skill_stuck_for_three_consecutive_sessions_is_flagged():
    sessions = [
        _session(0, "math.subtraction", correct_count=7, total=10),  # 70%
        _session(2, "math.subtraction", correct_count=7, total=10),  # 70%
        _session(4, "math.subtraction", correct_count=7, total=10),  # 70%
    ]

    result = detect_stuck_skills(sessions, threshold=0.80, min_sessions=3)

    assert len(result) == 1
    assert result[0].skill_area == "math.subtraction"
    assert result[0].stuck_session_count == 3


def test_skill_stuck_for_only_two_sessions_is_not_flagged():
    sessions = [
        _session(0, "math.subtraction", correct_count=7, total=10),
        _session(2, "math.subtraction", correct_count=7, total=10),
    ]

    result = detect_stuck_skills(sessions, threshold=0.80, min_sessions=3)

    assert result == []


def test_recent_improvement_breaks_the_streak():
    sessions = [
        _session(0, "math.subtraction", correct_count=7, total=10),  # 70%
        _session(2, "math.subtraction", correct_count=7, total=10),  # 70%
        _session(4, "math.subtraction", correct_count=9, total=10),  # 90%
    ]

    result = detect_stuck_skills(sessions, threshold=0.80, min_sessions=3)

    assert result == []


def test_skills_above_threshold_are_never_flagged():
    sessions = [
        _session(0, "phonics.blends", correct_count=9, total=10),
        _session(2, "phonics.blends", correct_count=9, total=10),
        _session(4, "phonics.blends", correct_count=9, total=10),
    ]

    result = detect_stuck_skills(sessions, threshold=0.80, min_sessions=3)

    assert result == []


def test_different_skill_areas_tracked_independently():
    sessions = [
        _session(0, "math.subtraction", correct_count=7, total=10),
        _session(2, "math.subtraction", correct_count=7, total=10),
        _session(4, "math.subtraction", correct_count=7, total=10),
        _session(0, "phonics.blends", correct_count=9, total=10),
        _session(2, "phonics.blends", correct_count=9, total=10),
        _session(4, "phonics.blends", correct_count=9, total=10),
    ]

    result = detect_stuck_skills(sessions, threshold=0.80, min_sessions=3)

    assert [s.skill_area for s in result] == ["math.subtraction"]
