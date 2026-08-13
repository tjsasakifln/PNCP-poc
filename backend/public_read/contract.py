"""Consumer fixture for extra-cli public_read_v1 v1.0.0.

Mirrors docs/contracts/public-read-v1.md from extra-cli PR #358.
A breaking change in producer fingerprint must fail these types/tests.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CONTRACT_VERSION = "v1.0.0"
CONTRACT_FAMILIES = (
    "current_snapshot",
    "tenders",
    "contracts",
    "entities",
    "suppliers",
    "organs",
    "municipalities",
    "surface_health",
)

Freshness = Literal["FRESH", "STALE", "FAILED", "BLOCKED", "UNKNOWN"]
Completeness = Literal["COMPLETE", "INCOMPLETE", "UNKNOWN", "BLOCKED"]
ReasonCode = str


class ProvenanceBlock(BaseModel):
    model_config = ConfigDict(extra="allow")

    source: str
    as_of: datetime | None = None
    source_updated_at: datetime | None = None
    completeness: Completeness = "UNKNOWN"
    freshness: Freshness = "UNKNOWN"
    reason_codes: list[ReasonCode] = Field(default_factory=list)
    document_sha256: str | None = None
    snapshot_id: str | None = None


class PublicEntity(BaseModel):
    model_config = ConfigDict(extra="allow")

    canonical_id: str
    family: str
    display_name: str | None = None
    as_of: datetime | None = None
    source_updated_at: datetime | None = None
    completeness: Completeness = "UNKNOWN"
    freshness: Freshness = "UNKNOWN"
    reason_codes: list[ReasonCode] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)


class SnapshotMeta(BaseModel):
    snapshot_id: str | None = None
    as_of: datetime | None = None
    completeness: Completeness = "UNKNOWN"
    state: str | None = None
    content_hash: str | None = None
    contract_version: str = CONTRACT_VERSION


class SurfaceHealth(BaseModel):
    view_name: str
    enabled: bool = True
    refreshed_at: datetime | None = None
    query_p95_ms: float | None = None
    last_refresh_status: str = "NEVER"
    last_error: str | None = None
    snapshot_id: str | None = None
    as_of: datetime | None = None
    completeness: Completeness = "UNKNOWN"


class FamilyRead(BaseModel):
    family: str
    contract_version: str = CONTRACT_VERSION
    mode: str
    served_from: Literal["public_read_v1", "legacy", "last_known_good", "blocked"]
    snapshot: SnapshotMeta | None = None
    entity: PublicEntity | None = None
    items: list[PublicEntity] = Field(default_factory=list)
    row_count: int | None = None
    health: SurfaceHealth | None = None
    divergence: list[str] = Field(default_factory=list)


REQUIRED_ENTITY_FIELDS = (
    "canonical_id",
    "as_of",
    "source_updated_at",
    "completeness",
    "reason_codes",
)
