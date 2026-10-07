from datetime import date

from app.features.engagement import EngagementDirection, EngagementTrend
from app.features.fluency import FluencyDirection, FluencyTrend
from app.features.plateau import StuckSkill
from app.features.summarize import StructuredSummary
from app.notegen.factuality import check_factuality


def _sample_summary() -> StructuredSummary:
    return StructuredSummary(
        student_id="stu_1",
        period_start=date(2026, 9, 15),
        period_end=date(2026, 9, 21),
        total_sessions=5,
        total_practice_minutes=50,
        skill_areas_practiced=["phonics.blends", "math.subtraction"],
        current_mastery_snapshot={
            "phonics.blends": 0.91,
            "math.subtraction": 0.69,
        },
        newly_mastered_skills=["phonics.blends"],
        stuck_skills=[
            StuckSkill(
                skill_area="math.subtraction",
                stuck_session_count=3,
                average_accuracy=0.69,
            )
        ],
        fluency_trends=[
            FluencyTrend(
                skill_area="phonics.blends",
                direction=FluencyDirection.STABLE,
                baseline_avg_latency_ms=1000.0,
                current_avg_latency_ms=1020.0,
                percent_change=0.02,
            )
        ],
        engagement=EngagementTrend(
            current_session_count=5,
            current_total_minutes=50,
            prior_session_count=4,
            prior_total_minutes=40,
            session_count_change_pct=0.25,
            total_minutes_change_pct=0.25,
            direction=EngagementDirection.UP,
        ),
    )


def test_note_referencing_only_known_facts_passes():
    summary = _sample_summary()
    note = (
        "phonics.blends is now mastered after 5 sessions this week! "
        "math.subtraction has been stuck for 3 sessions in a row."
    )

    result = check_factuality(note, summary)

    assert result.passed is True
    assert result.unverifiable_skill_mentions == []
    assert result.unverifiable_numbers == []


def test_note_mentioning_unknown_skill_fails():
    summary = _sample_summary()
    note = "reading.comprehension is now mastered!"

    result = check_factuality(note, summary)

    assert result.passed is False
    assert "reading.comprehension" in result.unverifiable_skill_mentions


def test_note_mentioning_fabricated_number_fails():
    summary = _sample_summary()
    note = "math.subtraction has been stuck for 17 sessions in a row."

    result = check_factuality(note, summary)

    assert result.passed is False
    assert "17" in result.unverifiable_numbers


def test_note_with_no_claims_passes_trivially():
    summary = _sample_summary()
    note = "Nice work this week, keep it up!"

    result = check_factuality(note, summary)

    assert result.passed is True
