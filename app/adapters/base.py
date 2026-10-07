"""Abstract base for vendor session adapters.

ed-tech partners each have their own raw export shape. An adapter's only
job is to map that raw shape into the canonical `WeeklyReportRequest`
schema (app/schemas/practice.py) -- it must never perform feature
extraction, note generation, or any business logic beyond field mapping
and light validation. Keeping that boundary strict is what lets the
feature layer and note generator stay vendor-agnostic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.practice import WeeklyReportRequest


class SessionAdapter(ABC):
    """Base class for a single vendor's raw-data-to-canonical-schema mapping."""

    @abstractmethod
    def to_canonical(self, raw: dict) -> WeeklyReportRequest:
        """Map one vendor's raw payload into a WeeklyReportRequest.

        Implementations should raise a clear exception (e.g. KeyError,
        ValueError, or a pydantic ValidationError from constructing the
        WeeklyReportRequest itself) if the raw payload is missing required
        fields, rather than silently guessing at defaults.
        """
        raise NotImplementedError
