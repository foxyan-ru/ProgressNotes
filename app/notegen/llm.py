"""LLM-backed note generator.

Real, wireable interface code: it defines the LLMClient protocol and
builds a tightly-scoped prompt from ONLY the StructuredSummary fields
(never raw PracticeSession / PracticeItem data). This module never calls
an actual API in this scaffold -- see docs/adr/0001-... for why raw
session logs are never allowed anywhere near this prompt. It is never
wired into app/api/v1/router.py in this scaffold; TemplateNoteGenerator is
the only generator guaranteed to run without external calls.
"""
from __future__ import annotations

import json
from typing import Protocol

from app.features.summarize import StructuredSummary
from app.notegen.base import GeneratedNote, NoteGenerator

SYSTEM_PROMPT = """You are writing a short weekly note for a parent, on \
behalf of the parent's child's tutoring platform. You will be given a \
structured JSON summary of the child's practice this week -- this JSON is \
the ONLY information you have access to. You have NOT seen any raw \
practice logs.

Rules:
- Use ONLY facts present in the JSON. Do not invent skill names, numbers, \
  or session counts that are not present in the JSON.
- Every skill area you name must appear in the JSON's \
  skill_areas_practiced, newly_mastered_skills, stuck_skills, or \
  fluency_trends fields.
- Every number you cite must appear in the JSON.
- Write 2-4 warm, plain-English sentences a non-technical parent can act on.
- End with exactly one recommended focus for the next session.
"""


class LLMClient(Protocol):
    """Minimal interface an LLM provider client must satisfy.

    Concrete implementations (e.g. wrapping a hosted model provider's SDK)
    live outside this scaffold; LLMNoteGenerator is written against this
    protocol so a real client can be swapped in without touching any
    prompt-construction logic.
    """

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return the model's raw text completion for the given prompts."""
        ...


class LLMNoteGenerator(NoteGenerator):
    """Builds a scoped prompt from StructuredSummary and delegates to an
    injected LLMClient.

    Never invoked in this scaffold -- TemplateNoteGenerator is the only
    generator guaranteed to run without external calls -- but this is
    real, complete prompt-construction logic, not a stub.
    """

    def __init__(self, client: LLMClient) -> None:
        self._client = client

    def generate(self, summary: StructuredSummary) -> GeneratedNote:
        user_prompt = self._build_user_prompt(summary)
        raw_text = self._client.complete(
            system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt
        )
        parent_note, next_focus = self._parse_completion(raw_text, summary)
        return GeneratedNote(
            parent_note=parent_note, next_focus=next_focus, confidence=0.8
        )

    @staticmethod
    def _build_user_prompt(summary: StructuredSummary) -> str:
        # model_dump(mode="json") serializes only StructuredSummary's own
        # fields -- there is no path from here back to raw
        # PracticeSession/PracticeItem data.
        payload = summary.model_dump(mode="json")
        return (
            "Structured weekly summary (the only data you may use):\n\n"
            f"{json.dumps(payload, indent=2)}\n\n"
            "Write the parent note now, followed by a line starting with "
            "'NEXT FOCUS:' naming exactly one skill area from the JSON above."
        )

    @staticmethod
    def _parse_completion(
        raw_text: str, summary: StructuredSummary
    ) -> tuple[str, str]:
        marker = "NEXT FOCUS:"
        if marker in raw_text:
            note_part, focus_part = raw_text.split(marker, 1)
            return note_part.strip(), focus_part.strip()

        # Fallback if the model didn't follow the format: use the first
        # practiced skill area as a conservative default.
        default_focus = (
            summary.skill_areas_practiced[0]
            if summary.skill_areas_practiced
            else "general review"
        )
        return raw_text.strip(), default_focus
