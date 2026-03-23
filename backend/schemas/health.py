"""Health check, sources, and system response schemas."""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class RootResponse(BaseModel):
    """Response for GET / root endpoint."""
    name: str
    version: str
    api_version: str
    description: str
    endpoints: Dict[str, str]
    versioning: Dict[str, Any]
    status: str


class RedisMetrics(BaseModel):
    """Redis health metrics (B-04 AC8)."""
    connected: bool = False
    latency_ms: Optional[float] = None
    memory_used_mb: Optional[float] = None


class HealthDependencies(BaseModel):
    """Health check dependency statuses."""
    supabase: str
    openai: str
    redis: str
    redis_metrics: Optional[RedisMetrics] = None
    queue: Optional[str] = Field(
        default=None,
        description="GTM-RESILIENCE-F01 AC4: ARQ job queue status — 'healthy' or 'unavailable'"
    )


class HealthResponse(BaseModel):
    """Response for GET /health endpoint."""
    status: str
    ready: bool = True  # CRIT-010 AC5: False until lifespan startup completes
    uptime_seconds: float = 0.0  # CRIT-010 AC5: Seconds since application became ready
    timestamp: str
    version: str
    dependencies: HealthDependencies
    sources: Optional[Dict[str, Any]] = None  # AC27 + B-06: Per-source health status (str or dict)


class SourceInfo(BaseModel):
    """Individual data source health info."""
    code: str
    name: str
    enabled: bool
    priority: int
    status: Optional[str] = None
    response_ms: Optional[int] = None


class SourcesHealthResponse(BaseModel):
    """Response for GET /sources/health endpoint."""
    sources: List[SourceInfo]
    multi_source_enabled: bool
    total_enabled: int
    total_available: int
    checked_at: str


class SetoresResponse(BaseModel):
    """Response for GET /setores endpoint."""
    setores: List[Dict[str, Any]]


class DebugPNCPResponse(BaseModel):
    """Response for GET /debug/pncp-test endpoint."""
    success: bool
    total_registros: Optional[int] = None
    items_returned: Optional[int] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    elapsed_ms: int
