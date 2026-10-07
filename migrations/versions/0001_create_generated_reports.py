"""create generated_reports table

Revision ID: 0001
Revises:
Create Date: 2026-09-27

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "generated_reports",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("student_id", sa.String(length=128), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column("next_focus", sa.String(length=256), nullable=False),
        sa.Column("factuality_passed", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_generated_reports_student_id",
        "generated_reports",
        ["student_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_generated_reports_student_id", table_name="generated_reports")
    op.drop_table("generated_reports")
