"""SQLAlchemy 2.0 async-style models."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, String, Text, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class GeneratedReport(Base):
    """A generated weekly note, persisted so a partner can retrieve report
    history for a student via the API.
    """

    __tablename__ = "generated_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    student_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    next_focus: Mapped[str] = mapped_column(String(256), nullable=False)
    factuality_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
