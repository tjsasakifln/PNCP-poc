"""Pydantic model for search_results_cache table — Single Source of Truth.

CRIT-001 AC3: This model defines ALL 18 columns of the search_results_cache table.
Any column added to the table MUST be added here first.
Any query referencing this table MUST validate against expected_columns().
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SearchResultsCacheRow(BaseModel):
    """Single Source of Truth for search_results_cache table schema.

    All 18 columns defined with their types, defaults, and nullability.
    Used for:
    - Startup schema health check (AC4)
    - Runtime validation in queries (AC10-AC12)
    - CI schema validation (AC13)
    """

    # Core fields (migration 026)
    id: UUID
    user_id: UUID
    params_hash: str
    search_params: dict[str, Any]
    results: list[Any]
    total_results: int
    created_at: datetime

    # Source tracking (migration 027-cache / 033)
    sources_json: list[str] = Field(default_factory=lambda: ["pncp"])
    fetched_at: datetime

    # Health metadata (migration 031)
    last_success_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    fail_streak: int = 0
    degraded_until: Optional[datetime] = None
    coverage: Optional[dict[str, Any]] = None
    fetch_duration_ms: Optional[int] = None

    # Priority fields (migration 032)
    priority: str = "cold"
    access_count: int = 0
    last_accessed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def expected_columns(cls) -> set[str]:
        """Return the set of expected column names for schema validation."""
        return set(cls.model_fields.keys())
