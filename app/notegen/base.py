"""Abstract base for note generators.

A NoteGenerator's contract is narrow and strict: it receives a
StructuredSummary (never raw sessions, never the WeeklyReportRequest) and
returns a GeneratedNote. This boundary is what makes the factuality guard
(app/notegen/factuality.py) meaningful -- if a generator had access to
raw data, "is every claim traceable to the summary" would be an
unanswerable question.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel

from app.features.summarize import StructuredSummary


class GeneratedNote(BaseModel):
    parent_note: str
    next_focus: str
    confidence: float = 1.0


class NoteGenerator(ABC):
    @abstractmethod
    def generate(self, summary: StructuredSummary) -> GeneratedNote:
        raise NotImplementedError
