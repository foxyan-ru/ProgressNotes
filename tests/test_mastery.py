from app.features.mastery import detect_newly_mastered


def test_skill_crossing_threshold_is_newly_mastered():
    previous = {"phonics.blends": 0.62}
    current = {"phonics.blends": 0.91}

    result = detect_newly_mastered(current, previous, threshold=0.85)

    assert result == ["phonics.blends"]


def test_skill_already_mastered_last_period_is_not_newly_mastered():
    previous = {"phonics.blends": 0.88}
    current = {"phonics.blends": 0.91}

    result = detect_newly_mastered(current, previous, threshold=0.85)

    assert result == []


def test_skill_below_threshold_is_not_reported():
    previous = {"math.subtraction": 0.60}
    current = {"math.subtraction": 0.72}

    result = detect_newly_mastered(current, previous, threshold=0.85)

    assert result == []


def test_skill_with_no_previous_snapshot_counts_as_not_previously_mastered():
    previous: dict[str, float] = {}
    current = {"reading.fluency_cvc": 0.90}

    result = detect_newly_mastered(current, previous, threshold=0.85)

    assert result == ["reading.fluency_cvc"]


def test_multiple_skills_sorted_alphabetically():
    previous = {"b.skill": 0.5, "a.skill": 0.5}
    current = {"b.skill": 0.9, "a.skill": 0.9}

    result = detect_newly_mastered(current, previous, threshold=0.85)

    assert result == ["a.skill", "b.skill"]
