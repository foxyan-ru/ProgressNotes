"""Mastery detection: pure functions comparing rolling mastery snapshots.

A "mastery snapshot" is a mapping of skill_area -> rolling accuracy
(0.0-1.0), as tracked by the calling system across all of a student's
practice history. This module never looks at raw practice items -- only
at the aggregated snapshot values already computed upstream.
"""
from __future__ import annotations


def detect_newly_mastered(
    current_snapshot: dict[str, float],
    previous_snapshot: dict[str, float],
    threshold: float = 0.85,
) -> list[str]:
    """Return skill areas that crossed `threshold` this period but had not
    crossed it as of the previous snapshot.

    A skill area that is present in `current_snapshot` but absent from
    `previous_snapshot` is treated as having a previous accuracy of 0.0
    (i.e. "not previously tracked" counts as "not previously mastered").
    """
    newly_mastered: list[str] = []
    for skill_area, current_accuracy in current_snapshot.items():
        if current_accuracy < threshold:
            continue
        previous_accuracy = previous_snapshot.get(skill_area, 0.0)
        if previous_accuracy < threshold:
            newly_mastered.append(skill_area)
    return sorted(newly_mastered)
