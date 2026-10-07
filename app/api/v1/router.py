"""v1 API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_api_key
from app.db.models import GeneratedReport
from app.db.session import get_db_session
from app.features.summarize import build_structured_summary
from app.notegen.factuality import check_factuality
from app.notegen.template import TemplateNoteGenerator
from app.schemas.practice import WeeklyReportRequest

router = APIRouter(prefix="/v1", tags=["reports"])

# TemplateNoteGenerator has zero external dependencies and is the only
# generator guaranteed to run without any LLM configured -- it is the
# default (and, in this scaffold, only wired-up) generator. An
# LLMNoteGenerator (app/notegen/llm.py) can be swapped in behind the same
# NoteGenerator interface once a real LLMClient is available.
_note_generator = TemplateNoteGenerator()


class WeeklyReportResponse(BaseModel):
    parent_note: str
    next_focus: str
    confidence: float
    factuality_passed: bool


@router.post("/reports/weekly", response_model=WeeklyReportResponse)
async def create_weekly_report(
    request: WeeklyReportRequest,
    db: AsyncSession = Depends(get_db_session),
    _api_key: str = Depends(require_api_key),
) -> WeeklyReportResponse:
    # A production deployment would load the student's previous mastery
    # snapshot and prior-period session/engagement stats from persistent
    # history here. This scaffold has no such history store yet (see
    # app/db/models.py -- only generated reports are persisted so far), so
    # it conservatively treats "no prior data" as the baseline, which is
    # also the correct behavior for a brand-new student.
    previous_snapshot: dict[str, float] = {}
    prior_period_stats: dict = {
        "session_count": 0,
        "total_minutes": 0,
        "prior_sessions": [],
    }

    summary = build_structured_summary(
        request=request,
        previous_snapshot=previous_snapshot,
        prior_period_stats=prior_period_stats,
    )

    note = _note_generator.generate(summary)
    factuality_result = check_factuality(note.parent_note, summary)

    report = GeneratedReport(
        student_id=request.student_id,
        period_start=request.period_start,
        period_end=request.period_end,
        note_text=note.parent_note,
        next_focus=note.next_focus,
        factuality_passed=factuality_result.passed,
    )
    db.add(report)
    await db.commit()

    return WeeklyReportResponse(
        parent_note=note.parent_note,
        next_focus=note.next_focus,
        confidence=note.confidence,
        factuality_passed=factuality_result.passed,
    )
