"""Application configuration.

Deliberately simple (plain env-var reads, no extra settings-management
dependency) so the dependency list matches pyproject.toml exactly -- this
project never adds a dependency it doesn't declare.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(v.strip() for v in value.split(",") if v.strip())


@dataclass(frozen=True)
class Settings:
    database_url: str = field(
        default_factory=lambda: os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://progressnote:progressnote@localhost:5432/progressnote",
        )
    )
    api_keys: tuple[str, ...] = field(
        default_factory=lambda: _split_csv(
            os.environ.get("PROGRESSNOTE_API_KEYS", "dev-local-key")
        )
    )
    mastery_threshold: float = field(
        default_factory=lambda: float(os.environ.get("MASTERY_THRESHOLD", "0.85"))
    )
    plateau_threshold: float = field(
        default_factory=lambda: float(os.environ.get("PLATEAU_THRESHOLD", "0.80"))
    )
    plateau_min_sessions: int = field(
        default_factory=lambda: int(os.environ.get("PLATEAU_MIN_SESSIONS", "3"))
    )


settings = Settings()
