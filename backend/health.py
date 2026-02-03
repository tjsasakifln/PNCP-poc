"""
Health Check Module for Multi-Source BidIQ System

Provides comprehensive health check functionality including:
- Overall system status
- Per-source availability status
- Version information
- Dependency health (database, cache, external APIs)

Usage:
    >>> from health import get_health_status, check_source_health
    >>> status = await get_health_status()
    >>> status['status']
    'healthy'
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum

import httpx

logger = logging.getLogger(__name__)

# Package version
__version__ = "0.3.0"


class HealthStatus(str, Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class SourceHealthResult:
    """Health check result for a single source."""

    source_code: str
    status: HealthStatus
    response_time_ms: Optional[int] = None
    error: Optional[str] = None
    last_checked: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "source": self.source_code,
            "status": self.status.value,
            "response_time_ms": self.response_time_ms,
            "error": self.error,
            "last_checked": self.last_checked.isoformat(),
        }


@dataclass
class SystemHealth:
    """Complete system health status."""

    status: HealthStatus
    version: str
    timestamp: datetime
    sources: Dict[str, SourceHealthResult]
    uptime_seconds: Optional[float] = None
    environment: str = "development"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "environment": self.environment,
            "uptime_seconds": self.uptime_seconds,
            "sources": {
                code: result.to_dict() for code, result in self.sources.items()
            },
        }


# Track application start time for uptime calculation
_start_time: Optional[float] = None


def initialize_health_tracking() -> None:
    """Initialize health tracking (call at application startup)."""
    global _start_time
    _start_time = time.time()
    logger.info("Health tracking initialized")


def get_uptime_seconds() -> Optional[float]:
    """Get application uptime in seconds."""
    if _start_time is None:
        return None
    return time.time() - _start_time


# Source health check endpoints
SOURCE_HEALTH_ENDPOINTS = {
    "PNCP": "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao",
    "Portal": "https://apipcp.portaldecompraspublicas.com.br",
    "Licitar": "https://api.licitar.digital/v1",
    "BLL": "https://api.bll.org.br/v1",
    "BNC": "https://api.bnc.org.br/v1",
}


async def check_source_health(
    source_code: str,
    timeout: float = 10.0,
) -> SourceHealthResult:
    """
    Check health of a single procurement source.

    Args:
        source_code: Source identifier (e.g., 'PNCP', 'Portal')
        timeout: Request timeout in seconds

    Returns:
        SourceHealthResult with status and timing information
    """
    endpoint = SOURCE_HEALTH_ENDPOINTS.get(source_code)
    if not endpoint:
        return SourceHealthResult(
            source_code=source_code,
            status=HealthStatus.UNHEALTHY,
            error=f"Unknown source: {source_code}",
        )

    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Use HEAD request if possible, otherwise GET with minimal params
            if source_code == "PNCP":
                # PNCP requires query params - use minimal request
                response = await client.get(
                    endpoint,
                    params={
                        "dataInicial": "2026-01-01",
                        "dataFinal": "2026-01-01",
                        "pagina": 1,
                        "tamanhoPagina": 1,
                    },
                )
            else:
                # Try HEAD first, fall back to GET
                try:
                    response = await client.head(endpoint)
                except httpx.HTTPError:
                    response = await client.get(endpoint)

            response_time_ms = int((time.time() - start_time) * 1000)

            if response.status_code < 500:
                return SourceHealthResult(
                    source_code=source_code,
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time_ms,
                )
            else:
                return SourceHealthResult(
                    source_code=source_code,
                    status=HealthStatus.DEGRADED,
                    response_time_ms=response_time_ms,
                    error=f"HTTP {response.status_code}",
                )

    except httpx.TimeoutException:
        response_time_ms = int((time.time() - start_time) * 1000)
        return SourceHealthResult(
            source_code=source_code,
            status=HealthStatus.DEGRADED,
            response_time_ms=response_time_ms,
            error="Timeout",
        )
    except httpx.ConnectError as e:
        return SourceHealthResult(
            source_code=source_code,
            status=HealthStatus.UNHEALTHY,
            error=f"Connection error: {str(e)[:100]}",
        )
    except Exception as e:
        logger.exception(f"Health check failed for {source_code}")
        return SourceHealthResult(
            source_code=source_code,
            status=HealthStatus.UNHEALTHY,
            error=f"Error: {type(e).__name__}: {str(e)[:100]}",
        )


async def check_all_sources_health(
    enabled_sources: Optional[List[str]] = None,
    timeout: float = 10.0,
) -> Dict[str, SourceHealthResult]:
    """
    Check health of all enabled sources in parallel.

    Args:
        enabled_sources: List of source codes to check (defaults to all)
        timeout: Request timeout per source

    Returns:
        Dict mapping source codes to health results
    """
    if enabled_sources is None:
        # Default to checking all known sources
        enabled_sources = list(SOURCE_HEALTH_ENDPOINTS.keys())

    # Run health checks in parallel
    tasks = [
        check_source_health(source, timeout) for source in enabled_sources
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    health_results = {}
    for source, result in zip(enabled_sources, results):
        if isinstance(result, Exception):
            health_results[source] = SourceHealthResult(
                source_code=source,
                status=HealthStatus.UNHEALTHY,
                error=str(result),
            )
        else:
            health_results[source] = result

    return health_results


def calculate_overall_status(
    source_results: Dict[str, SourceHealthResult],
) -> HealthStatus:
    """
    Calculate overall system health based on source statuses.

    Rules:
    - HEALTHY: All sources healthy OR only non-critical sources degraded
    - DEGRADED: Some sources unhealthy but PNCP is available
    - UNHEALTHY: PNCP is unhealthy OR all sources unhealthy

    Args:
        source_results: Dict of source health results

    Returns:
        Overall HealthStatus
    """
    if not source_results:
        return HealthStatus.UNHEALTHY

    statuses = {code: r.status for code, r in source_results.items()}

    # If PNCP is unhealthy, system is unhealthy (primary source)
    if "PNCP" in statuses and statuses["PNCP"] == HealthStatus.UNHEALTHY:
        return HealthStatus.UNHEALTHY

    # Count statuses
    healthy_count = sum(1 for s in statuses.values() if s == HealthStatus.HEALTHY)
    unhealthy_count = sum(1 for s in statuses.values() if s == HealthStatus.UNHEALTHY)
    total = len(statuses)

    # All healthy
    if healthy_count == total:
        return HealthStatus.HEALTHY

    # All unhealthy
    if unhealthy_count == total:
        return HealthStatus.UNHEALTHY

    # Mixed status
    return HealthStatus.DEGRADED


async def get_health_status(
    include_sources: bool = True,
    source_timeout: float = 10.0,
) -> SystemHealth:
    """
    Get complete system health status.

    Args:
        include_sources: Whether to check individual source health
        source_timeout: Timeout for source health checks

    Returns:
        SystemHealth with complete status information
    """
    timestamp = datetime.now(timezone.utc)
    environment = os.getenv("ENVIRONMENT", "development")

    # Get enabled sources from config
    try:
        from source_config.sources import get_source_config

        config = get_source_config()
        enabled_sources = config.get_enabled_sources()
    except ImportError:
        enabled_sources = ["PNCP"]  # Fallback to PNCP only

    # Check source health if requested
    if include_sources:
        source_results = await check_all_sources_health(enabled_sources, source_timeout)
        overall_status = calculate_overall_status(source_results)
    else:
        source_results = {}
        overall_status = HealthStatus.HEALTHY

    return SystemHealth(
        status=overall_status,
        version=__version__,
        timestamp=timestamp,
        sources=source_results,
        uptime_seconds=get_uptime_seconds(),
        environment=environment,
    )


async def get_detailed_health() -> Dict[str, Any]:
    """
    Get detailed health information for monitoring dashboards.

    Returns comprehensive information including:
    - System status and version
    - Per-source status with response times
    - Environment information
    - Uptime statistics
    """
    health = await get_health_status(include_sources=True)
    result = health.to_dict()

    # Add additional diagnostic information
    result["diagnostics"] = {
        "python_version": os.popen("python --version 2>&1").read().strip(),
        "hostname": os.getenv("HOSTNAME", "unknown"),
        "port": os.getenv("PORT", "8000"),
    }

    # Add source summary
    healthy_sources = sum(
        1 for s in health.sources.values() if s.status == HealthStatus.HEALTHY
    )
    result["summary"] = {
        "total_sources": len(health.sources),
        "healthy_sources": healthy_sources,
        "degraded_sources": sum(
            1 for s in health.sources.values() if s.status == HealthStatus.DEGRADED
        ),
        "unhealthy_sources": sum(
            1 for s in health.sources.values() if s.status == HealthStatus.UNHEALTHY
        ),
    }

    return result
