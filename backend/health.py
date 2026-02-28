"""
Health Check Module for Multi-Source SmartLic System

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
from datetime import datetime, timezone, timedelta
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
    "Portal": "https://compras.api.portaldecompraspublicas.com.br",
    "ComprasGov": "https://dadosabertos.compras.gov.br",
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
                # STORY-316 AC1: Realistic canary — tamanhoPagina=50 (same as production)
                # Detects the silent HTTP 400 bug when PNCP reduces max page size
                response = await client.get(
                    endpoint,
                    params={
                        "dataInicial": "20260101",
                        "dataFinal": "20260101",
                        "codigoModalidadeContratacao": 6,
                        "pagina": 1,
                        "tamanhoPagina": 50,
                    },
                )
            elif source_code == "Portal":
                # STORY-316 AC1: PCP v2 realistic canary with pagination
                response = await client.get(
                    "https://compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos",
                    params={"pagina": 1},
                )
            elif source_code == "ComprasGov":
                # STORY-316 AC1: ComprasGov dual-endpoint test (legacy)
                response = await client.get(
                    "https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/1_consultarMaterial",
                    params={"pagina": 1, "tamanhoPagina": 1},
                )
            else:
                # Try HEAD first, fall back to GET
                try:
                    response = await client.head(endpoint)
                except httpx.HTTPError:
                    response = await client.get(endpoint)

            response_time_ms = int((time.time() - start_time) * 1000)

            if response.status_code < 400:
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


async def get_system_health() -> Dict[str, Any]:
    """GTM-STAB-008 AC3: Comprehensive system health check.

    Returns component-level statuses for Redis, Supabase, ARQ Worker, and PNCP,
    plus overall health classification (healthy / degraded / unhealthy).
    Designed for monitoring dashboards and uptime checks.
    """
    components: Dict[str, Any] = {}

    # Redis check
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            start = time.monotonic()
            await redis.ping()
            latency = int((time.monotonic() - start) * 1000)
            components["redis"] = {"status": "up", "latency_ms": latency}
        else:
            components["redis"] = {"status": "down", "latency_ms": 0}
    except Exception as e:
        components["redis"] = {"status": "down", "error": str(e)[:100]}

    # Supabase check
    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        start = time.monotonic()
        await sb_execute(sb.table("profiles").select("id").limit(1))
        latency = int((time.monotonic() - start) * 1000)
        components["supabase"] = {"status": "up", "latency_ms": latency}
    except Exception as e:
        components["supabase"] = {"status": "down", "error": str(e)[:100]}

    # ARQ Worker check
    try:
        from job_queue import is_queue_available
        worker_ok = await is_queue_available()
        components["arq_worker"] = {"status": "up" if worker_ok else "down"}
    except Exception:
        components["arq_worker"] = {"status": "unknown"}

    # STORY-305 AC4/AC11: Circuit breaker health for all 3 sources — includes try_recover canary
    try:
        from pncp_client import get_circuit_breaker
        for src_name in ("pncp", "pcp", "comprasgov"):
            cb = get_circuit_breaker(src_name)
            # AC4: Health canary — try_recover on each check to detect cooldown expiry
            await cb.try_recover()
            is_deg = cb.is_degraded
            components[src_name] = {
                "status": "degraded" if is_deg else "up",
                "circuit_breaker": "open" if is_deg else "closed",
            }
    except Exception:
        components["pncp"] = {"status": "unknown"}

    # Overall status
    redis_down = components.get("redis", {}).get("status") == "down"
    supabase_down = components.get("supabase", {}).get("status") == "down"
    any_source_degraded = any(
        components.get(src, {}).get("status") == "degraded"
        for src in ("pncp", "pcp", "comprasgov")
    )

    if redis_down or supabase_down:
        overall = "unhealthy"
    elif any_source_degraded:
        overall = "degraded"
    else:
        overall = "healthy"

    # STORY-299 AC6: SLO compliance status
    slo_compliance = None
    try:
        from slo import get_slo_compliance_summary
        slo_compliance = get_slo_compliance_summary()
    except Exception as e:
        logger.debug("SLO compliance check failed (non-fatal): %s", e)
        slo_compliance = {"compliance": "unavailable", "error": str(e)[:100]}

    return {
        "status": overall,
        "components": components,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": __version__,
        "uptime_seconds": get_uptime_seconds(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "slo": slo_compliance,
    }


# ============================================================================
# STORY-316: Public Status Page data
# ============================================================================

async def get_public_status() -> Dict[str, Any]:
    """STORY-316 AC2/AC3: Public status endpoint data.

    Returns per-source status, component health, uptime percentages,
    and last incident info — all sanitized for public consumption.
    """
    # Get source health with realistic canary (AC1)
    source_checks = await check_all_sources_health(
        enabled_sources=["PNCP", "Portal", "ComprasGov"],
        timeout=10.0,
    )

    sources = {}
    for code, result in source_checks.items():
        entry: Dict[str, Any] = {
            "status": result.status.value,
            "latency_ms": result.response_time_ms,
        }
        if result.error:
            entry["error"] = result.error
        # Use last_checked from result
        entry["last_check"] = result.last_checked.isoformat()
        sources[code.lower()] = entry

    # Component health (Redis, Supabase, ARQ)
    components: Dict[str, str] = {}
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            await redis.ping()
            components["redis"] = "healthy"
        else:
            components["redis"] = "unhealthy"
    except Exception:
        components["redis"] = "unhealthy"

    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        await sb_execute(sb.table("profiles").select("id").limit(1))
        components["supabase"] = "healthy"
    except Exception:
        components["supabase"] = "unhealthy"

    try:
        from job_queue import is_queue_available
        worker_ok = await is_queue_available()
        components["arq_worker"] = "healthy" if worker_ok else "unhealthy"
    except Exception:
        components["arq_worker"] = "unknown"

    # Overall status
    source_statuses = [r.status for r in source_checks.values()]
    comp_unhealthy = any(v == "unhealthy" for v in components.values())

    if comp_unhealthy or all(s == HealthStatus.UNHEALTHY for s in source_statuses):
        overall = "unhealthy"
    elif any(s != HealthStatus.HEALTHY for s in source_statuses):
        overall = "degraded"
    else:
        overall = "healthy"

    # Uptime percentages (AC7)
    uptime = await calculate_uptime_percentages()

    # Last incident
    last_incident = await get_last_incident()

    return {
        "status": overall,
        "sources": sources,
        "components": components,
        "uptime_pct_24h": uptime.get("24h", 0.0),
        "uptime_pct_7d": uptime.get("7d", 0.0),
        "uptime_pct_30d": uptime.get("30d", 0.0),
        "last_incident": last_incident,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def calculate_uptime_percentages() -> Dict[str, float]:
    """STORY-316 AC7: Calculate uptime from health_checks history.

    healthy=100%, degraded=50%, unhealthy=0%.
    Returns percentages for 24h, 7d, 30d windows.
    """
    result = {"24h": 100.0, "7d": 100.0, "30d": 100.0}
    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        now = datetime.now(timezone.utc)

        for label, delta in [("24h", timedelta(hours=24)), ("7d", timedelta(days=7)), ("30d", timedelta(days=30))]:
            cutoff = (now - delta).isoformat()
            resp = await sb_execute(
                sb.table("health_checks")
                .select("overall_status")
                .gte("checked_at", cutoff)
                .order("checked_at", desc=True)
            )
            rows = resp.data or []
            if not rows:
                result[label] = 100.0
                continue

            total_score = 0.0
            for row in rows:
                status = row.get("overall_status", "healthy")
                if status == "healthy":
                    total_score += 100.0
                elif status == "degraded":
                    total_score += 50.0
                # unhealthy = 0

            result[label] = round(total_score / len(rows), 1)
    except Exception as e:
        logger.warning("Failed to calculate uptime percentages: %s", e)

    return result


async def get_last_incident() -> Optional[str]:
    """Get the timestamp of the last incident."""
    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        resp = await sb_execute(
            sb.table("incidents")
            .select("started_at")
            .order("started_at", desc=True)
            .limit(1)
        )
        if resp.data:
            return resp.data[0].get("started_at")
    except Exception as e:
        logger.debug("Failed to get last incident: %s", e)
    return None


async def get_recent_incidents(days: int = 30) -> List[Dict[str, Any]]:
    """STORY-316 AC13: Get incidents from the last N days."""
    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        resp = await sb_execute(
            sb.table("incidents")
            .select("*")
            .gte("started_at", cutoff)
            .order("started_at", desc=True)
        )
        return resp.data or []
    except Exception as e:
        logger.warning("Failed to get recent incidents: %s", e)
        return []


async def save_health_check(overall_status: str, sources: Dict, components: Dict, latency_ms: Optional[int] = None) -> None:
    """STORY-316 AC6: Save a health check result to DB."""
    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        import json
        await sb_execute(
            sb.table("health_checks").insert({
                "overall_status": overall_status,
                "sources_json": json.dumps(sources) if isinstance(sources, dict) else sources,
                "components_json": json.dumps(components) if isinstance(components, dict) else components,
                "latency_ms": latency_ms,
            })
        )
    except Exception as e:
        logger.error("Failed to save health check: %s", e)


async def detect_incident(current_status: str, sources: Dict) -> None:
    """STORY-316 AC8: Detect status transitions and create/resolve incidents.

    - healthy → degraded/unhealthy: create incident + email admin + Sentry alert
    - 3 consecutive healthy after incident: auto-resolve (AC10)
    """
    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()

        # Check for ongoing incidents
        ongoing_resp = await sb_execute(
            sb.table("incidents")
            .select("*")
            .eq("status", "ongoing")
            .order("started_at", desc=True)
            .limit(1)
        )
        ongoing = ongoing_resp.data[0] if ongoing_resp.data else None

        if current_status in ("degraded", "unhealthy") and not ongoing:
            # New incident — determine affected sources
            affected = [
                src for src, data in sources.items()
                if isinstance(data, dict) and data.get("status") in ("degraded", "unhealthy", "Timeout")
                or (isinstance(data, dict) and data.get("error"))
            ]
            severity = "critical" if current_status == "unhealthy" else "warning"
            description = f"System status changed to {current_status}. Affected: {', '.join(affected) or 'unknown'}"

            await sb_execute(
                sb.table("incidents").insert({
                    "status": "ongoing",
                    "affected_sources": affected,
                    "description": description,
                })
            )

            # Fire-and-forget: email admin (AC8)
            try:
                from email_service import send_email
                admin_email = os.getenv("ADMIN_EMAIL", "tiago.sasaki@gmail.com")
                send_email(
                    to=admin_email,
                    subject=f"[SmartLic] Incidente: {current_status}",
                    html=f"<h2>Incidente detectado</h2><p>{description}</p><p>Verifique: <a href='https://smartlic.tech/status'>Status Page</a></p>",
                    tags=[{"name": "category", "value": "incident"}],
                )
            except Exception:
                logger.warning("Failed to send incident email")

            # Sentry alert
            try:
                import sentry_sdk
                sentry_sdk.capture_message(
                    f"Health incident: {description}",
                    level="error" if current_status == "unhealthy" else "warning",
                )
            except Exception:
                pass

            # Metrics
            try:
                from metrics import INCIDENTS_TOTAL
                for src in affected:
                    INCIDENTS_TOTAL.labels(source=src, severity=severity).inc()
            except Exception:
                pass

            logger.warning("Incident created: %s", description)

        elif current_status == "healthy" and ongoing:
            # AC10: Check for 3 consecutive healthy checks
            recent_resp = await sb_execute(
                sb.table("health_checks")
                .select("overall_status")
                .order("checked_at", desc=True)
                .limit(3)
            )
            recent_statuses = [r.get("overall_status") for r in (recent_resp.data or [])]

            if len(recent_statuses) >= 3 and all(s == "healthy" for s in recent_statuses):
                # Auto-resolve incident
                await sb_execute(
                    sb.table("incidents")
                    .update({
                        "status": "resolved",
                        "resolved_at": datetime.now(timezone.utc).isoformat(),
                    })
                    .eq("id", ongoing["id"])
                )

                # Email resolution
                try:
                    from email_service import send_email
                    admin_email = os.getenv("ADMIN_EMAIL", "tiago.sasaki@gmail.com")
                    send_email(
                        to=admin_email,
                        subject="[SmartLic] Incidente resolvido",
                        html=f"<h2>Incidente resolvido</h2><p>O sistema voltou ao status saudável após 3 checks consecutivos.</p><p>Incidente: {ongoing.get('description', '')}</p>",
                        tags=[{"name": "category", "value": "incident_resolved"}],
                    )
                except Exception:
                    logger.warning("Failed to send resolution email")

                logger.info("Incident auto-resolved: %s", ongoing.get("id"))

    except Exception as e:
        logger.error("Incident detection failed: %s", e)


async def cleanup_old_health_checks() -> int:
    """Clean up health checks older than retention period."""
    try:
        from config import HEALTH_CHECKS_RETENTION_DAYS
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=HEALTH_CHECKS_RETENTION_DAYS)).isoformat()
        resp = await sb_execute(
            sb.table("health_checks")
            .delete()
            .lt("checked_at", cutoff)
        )
        deleted = len(resp.data) if resp.data else 0
        if deleted > 0:
            logger.info("Cleaned up %d old health checks", deleted)
        return deleted
    except Exception as e:
        logger.warning("Failed to cleanup old health checks: %s", e)
        return 0


async def get_uptime_history(days: int = 90) -> List[Dict[str, Any]]:
    """STORY-316 AC12: Get daily uptime data for the status page chart."""
    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        resp = await sb_execute(
            sb.table("health_checks")
            .select("checked_at, overall_status")
            .gte("checked_at", cutoff)
            .order("checked_at", desc=False)
        )
        rows = resp.data or []

        # Group by date
        daily: Dict[str, List[str]] = {}
        for row in rows:
            date_str = row["checked_at"][:10]  # YYYY-MM-DD
            daily.setdefault(date_str, []).append(row["overall_status"])

        result = []
        for date_str, statuses in sorted(daily.items()):
            total = len(statuses)
            healthy = sum(1 for s in statuses if s == "healthy")
            degraded = sum(1 for s in statuses if s == "degraded")
            unhealthy = total - healthy - degraded
            pct = round((healthy * 100 + degraded * 50) / total, 1) if total else 100.0
            result.append({
                "date": date_str,
                "uptime_pct": pct,
                "checks": total,
                "healthy": healthy,
                "degraded": degraded,
                "unhealthy": unhealthy,
            })

        return result
    except Exception as e:
        logger.warning("Failed to get uptime history: %s", e)
        return []
