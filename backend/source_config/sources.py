"""
Multi-Source Configuration Module

Manages configuration for all procurement data sources in the BidIQ system.
Provides environment-based configuration loading, enable/disable toggles,
timeout settings, and secure API key management.

Sources:
    - PNCP: Portal Nacional de Contratacoes Publicas (primary)
    - Portal: Portal de Compras Publicas
    - Licitar: Licitar Digital
    - BLL: BLL Compras (disabled - syncs to PNCP)
    - BNC: Bolsa Nacional de Compras (disabled - syncs to PNCP)
    - Querido Diário: Diários Oficiais Municipais (experimental, opt-in)

Security:
    - API keys are loaded from environment variables only
    - Keys are never logged or exposed in error messages
    - Missing required keys raise startup errors

Usage:
    >>> from source_config.sources import SourceConfig, get_source_config
    >>> config = get_source_config()
    >>> config.pncp.enabled
    True
    >>> config.get_enabled_sources()
    ['PNCP', 'Portal', 'Licitar']
"""

import os
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class SourceCode(str, Enum):
    """Enumeration of available procurement data sources."""

    PNCP = "PNCP"
    PORTAL = "Portal"
    LICITAR = "Licitar"
    COMPRAS_GOV = "ComprasGov"
    PORTAL_TRANSPARENCIA = "PortalTransparencia"
    BLL = "BLL"
    BNC = "BNC"
    QUERIDO_DIARIO = "QueridoDiario"


@dataclass
class SourceHealthStatus:
    """Health status entry for a single source."""

    status: Literal["healthy", "degraded", "down"] = "healthy"
    updated_at: float = field(default_factory=time.time)
    consecutive_failures: int = 0
    ttl_seconds: int = 300  # 5 minutes


class SourceHealthRegistry:
    """
    In-memory health registry tracking source availability.

    Maintains status (healthy/degraded/down) for each source with a
    configurable TTL. Status persists between requests within the
    same process. Thread-safe for async (single-process, no locks needed).

    Usage:
        registry = source_health_registry  # module-level singleton
        registry.record_success("PNCP")
        registry.record_failure("PNCP")
        status = registry.get_status("PNCP")  # "healthy" | "degraded" | "down"
        available = registry.is_available("PNCP")  # True if healthy or degraded
    """

    def __init__(self) -> None:
        self._statuses: Dict[str, SourceHealthStatus] = {}

    def get_status(self, source_name: str) -> str:
        """
        Get current health status for a source.

        Returns "healthy" if no status recorded or TTL has expired.

        Args:
            source_name: Source identifier (e.g., "PNCP", "Portal")

        Returns:
            One of "healthy", "degraded", "down"
        """
        entry = self._statuses.get(source_name)
        if entry is None:
            return "healthy"
        # Check TTL expiration
        if time.time() - entry.updated_at > entry.ttl_seconds:
            # TTL expired — reset to healthy
            del self._statuses[source_name]
            return "healthy"
        return entry.status

    def record_success(self, source_name: str) -> None:
        """
        Record a successful interaction with a source.

        Resets status to healthy and clears consecutive failure count.

        Args:
            source_name: Source identifier
        """
        self._statuses[source_name] = SourceHealthStatus(
            status="healthy",
            updated_at=time.time(),
            consecutive_failures=0,
        )

    def record_failure(self, source_name: str) -> None:
        """
        Record a failed interaction with a source.

        Increments consecutive failure counter and updates status:
        - 1-2 failures: remains "healthy"
        - 3-4 failures: transitions to "degraded"
        - 5+ failures: transitions to "down"

        Args:
            source_name: Source identifier
        """
        entry = self._statuses.get(source_name)
        if entry is None:
            entry = SourceHealthStatus()

        previous_status = entry.status
        entry.consecutive_failures += 1
        entry.updated_at = time.time()

        if entry.consecutive_failures >= 5:
            entry.status = "down"
        elif entry.consecutive_failures >= 3:
            entry.status = "degraded"
        # else stays at current status (healthy for 1-2 failures)

        self._statuses[source_name] = entry

        # AC28: Log WARNING when transitioning to degraded or down
        if entry.status != previous_status and entry.status in ("degraded", "down"):
            logger.warning(
                f"Source '{source_name}' transitioned to {entry.status.upper()} status "
                f"after {entry.consecutive_failures} consecutive failures"
            )

    def is_available(self, source_name: str) -> bool:
        """
        Check if a source is available for requests.

        A source is available if its status is "healthy" or "degraded".
        A "down" source is not available.

        Args:
            source_name: Source identifier

        Returns:
            True if healthy or degraded, False if down
        """
        status = self.get_status(source_name)
        return status in ("healthy", "degraded")

    def reset(self) -> None:
        """Clear all health statuses. Useful for testing."""
        self._statuses.clear()


# Module-level singleton — persists between requests within the same process
source_health_registry = SourceHealthRegistry()


@dataclass
class SourceCredentials:
    """
    Secure credentials container for source authentication.

    Credentials are loaded from environment variables and never logged.
    """

    api_key: Optional[str] = None
    api_secret: Optional[str] = None

    @classmethod
    def from_env(cls, source_code: str) -> "SourceCredentials":
        """
        Load credentials from environment variables.

        Args:
            source_code: Source identifier (e.g., 'PORTAL', 'LICITAR')

        Returns:
            SourceCredentials with loaded values (or None if not set)
        """
        prefix = f"{source_code.upper()}_"
        return cls(
            api_key=os.getenv(f"{prefix}API_KEY"),
            api_secret=os.getenv(f"{prefix}API_SECRET"),
        )

    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return self.api_key is not None and len(self.api_key) > 0

    def __repr__(self) -> str:
        """Safe representation that doesn't expose credentials."""
        has_key = "****" if self.has_api_key() else "None"
        has_secret = "****" if self.api_secret else "None"
        return f"SourceCredentials(api_key={has_key}, api_secret={has_secret})"


@dataclass
class SingleSourceConfig:
    """Configuration for a single procurement data source."""

    code: SourceCode
    name: str
    base_url: str
    enabled: bool = True
    timeout: int = 30
    rate_limit_rps: float = 10.0
    priority: int = 1
    credentials: SourceCredentials = field(default_factory=SourceCredentials)

    def is_available(self) -> bool:
        """Check if source is enabled and has required credentials.

        STORY-257A AC13: Sources without required credentials return False
        to prevent phantom timeout attempts.
        """
        if not self.enabled:
            return False
        # PNCP, ComprasGov, and Querido Diário don't require credentials (open data)
        if self.code in (SourceCode.PNCP, SourceCode.COMPRAS_GOV, SourceCode.QUERIDO_DIARIO):
            return True
        # All other sources require an API key to function
        if not self.credentials.has_api_key():
            logger.debug(
                f"Source {self.code.value} enabled but unavailable: missing API key"
            )
            return False
        return True

    def get_timeout(self) -> int:
        """Get effective timeout for this source."""
        return self.timeout


@dataclass
class ConsolidationConfig:
    """Configuration for multi-source consolidation service."""

    timeout_global: int = 120
    timeout_per_source: int = 50
    fail_on_all_errors: bool = True
    dedup_strategy: str = "first_seen"
    max_concurrent_sources: int = 5

    @classmethod
    def from_env(cls) -> "ConsolidationConfig":
        """Load consolidation config from environment."""
        return cls(
            timeout_global=int(os.getenv("CONSOLIDATION_TIMEOUT_GLOBAL", "120")),
            timeout_per_source=int(os.getenv("CONSOLIDATION_TIMEOUT_PER_SOURCE", "50")),
            fail_on_all_errors=os.getenv("CONSOLIDATION_FAIL_ON_ALL", "true").lower()
            == "true",
            dedup_strategy=os.getenv("CONSOLIDATION_DEDUP_STRATEGY", "first_seen"),
            max_concurrent_sources=int(
                os.getenv("CONSOLIDATION_MAX_CONCURRENT", "5")
            ),
        )


@dataclass
class SourceConfig:
    """
    Complete multi-source configuration.

    Central configuration object that manages all source configs,
    credentials, and consolidation settings.
    """

    pncp: SingleSourceConfig = field(default_factory=lambda: SingleSourceConfig(
        code=SourceCode.PNCP,
        name="Portal Nacional de Contratacoes Publicas",
        base_url="https://pncp.gov.br/api/consulta/v1",
        enabled=True,
        timeout=30,
        rate_limit_rps=10.0,
        priority=1,
    ))

    portal: SingleSourceConfig = field(default_factory=lambda: SingleSourceConfig(
        code=SourceCode.PORTAL,
        name="Portal de Compras Publicas",
        base_url="https://apipcp.portaldecompraspublicas.com.br",
        enabled=True,
        timeout=30,
        rate_limit_rps=10.0,
        priority=2,
    ))

    licitar: SingleSourceConfig = field(default_factory=lambda: SingleSourceConfig(
        code=SourceCode.LICITAR,
        name="Licitar Digital",
        base_url="https://api.licitar.digital/v1",
        enabled=True,
        timeout=20,
        rate_limit_rps=5.0,
        priority=3,
    ))

    compras_gov: SingleSourceConfig = field(default_factory=lambda: SingleSourceConfig(
        code=SourceCode.COMPRAS_GOV,
        name="ComprasGov - Dados Abertos Federal",
        base_url="https://compras.dados.gov.br",
        enabled=True,  # No auth required (open government data)
        timeout=30,
        rate_limit_rps=2.0,
        priority=4,
    ))

    portal_transparencia: SingleSourceConfig = field(default_factory=lambda: SingleSourceConfig(
        code=SourceCode.PORTAL_TRANSPARENCIA,
        name="Portal da Transparência - CGU",
        base_url="https://api.portaldatransparencia.gov.br/api-de-dados",
        enabled=False,  # Requires API key from Gov.br
        timeout=30,
        rate_limit_rps=1.5,  # 90 req/min
        priority=3,
    ))

    bll: SingleSourceConfig = field(default_factory=lambda: SingleSourceConfig(
        code=SourceCode.BLL,
        name="BLL Compras",
        base_url="https://api.bll.org.br/v1",
        enabled=False,  # Disabled by default - syncs to PNCP
        timeout=25,
        rate_limit_rps=5.0,
        priority=4,
    ))

    bnc: SingleSourceConfig = field(default_factory=lambda: SingleSourceConfig(
        code=SourceCode.BNC,
        name="Bolsa Nacional de Compras",
        base_url="https://api.bnc.org.br/v1",
        enabled=False,  # Disabled by default - syncs to PNCP
        timeout=20,
        rate_limit_rps=5.0,
        priority=5,
    ))

    querido_diario: SingleSourceConfig = field(default_factory=lambda: SingleSourceConfig(
        code=SourceCode.QUERIDO_DIARIO,
        name="Querido Diário - Diários Oficiais Municipais",
        base_url="https://api.queridodiario.ok.org.br",
        enabled=False,  # Experimental — opt-in (AC14)
        timeout=30,
        rate_limit_rps=1.0,  # Conservative: 1 req/s
        priority=5,  # Lowest priority (complement to PNCP)
    ))

    consolidation: ConsolidationConfig = field(
        default_factory=ConsolidationConfig.from_env
    )

    @classmethod
    def from_env(cls) -> "SourceConfig":
        """
        Load complete source configuration from environment variables.

        Environment Variables:
            ENABLE_SOURCE_PNCP: Enable/disable PNCP source (default: true)
            ENABLE_SOURCE_PORTAL: Enable/disable Portal source (default: true)
            ENABLE_SOURCE_LICITAR: Enable/disable Licitar source (default: true)
            ENABLE_SOURCE_BLL: Enable/disable BLL source (default: false)
            ENABLE_SOURCE_BNC: Enable/disable BNC source (default: false)
            ENABLE_SOURCE_QUERIDO_DIARIO: Enable/disable Querido Diário source (default: false)
            PORTAL_COMPRAS_API_KEY: API key for Portal de Compras Publicas
            LICITAR_API_KEY: API key for Licitar Digital
            LICITAR_API_URL: Custom API URL for Licitar Digital
            CONSOLIDATION_TIMEOUT_GLOBAL: Global timeout in seconds (default: 60)
            CONSOLIDATION_TIMEOUT_PER_SOURCE: Per-source timeout (default: 25)

        Returns:
            SourceConfig with all settings loaded from environment
        """
        config = cls()

        # Load enabled states from environment
        config.pncp.enabled = os.getenv("ENABLE_SOURCE_PNCP", "true").lower() == "true"
        config.portal.enabled = (
            os.getenv("ENABLE_SOURCE_PORTAL", "true").lower() == "true"
        )
        config.licitar.enabled = (
            os.getenv("ENABLE_SOURCE_LICITAR", "true").lower() == "true"
        )
        config.compras_gov.enabled = (
            os.getenv("ENABLE_SOURCE_COMPRAS_GOV", "true").lower() == "true"
        )
        config.portal_transparencia.enabled = (
            os.getenv("ENABLE_SOURCE_PORTAL_TRANSPARENCIA", "false").lower() == "true"
        )
        config.bll.enabled = os.getenv("ENABLE_SOURCE_BLL", "false").lower() == "true"
        config.bnc.enabled = os.getenv("ENABLE_SOURCE_BNC", "false").lower() == "true"
        config.querido_diario.enabled = (
            os.getenv("ENABLE_SOURCE_QUERIDO_DIARIO", "false").lower() == "true"
        )

        # Load credentials
        config.portal_transparencia.credentials = SourceCredentials(
            api_key=os.getenv("PORTAL_TRANSPARENCIA_API_KEY")
        )
        config.portal.credentials = SourceCredentials(
            api_key=os.getenv("PORTAL_COMPRAS_API_KEY")
        )
        config.licitar.credentials = SourceCredentials(
            api_key=os.getenv("LICITAR_API_KEY")
        )
        config.bll.credentials = SourceCredentials.from_env("BLL")
        config.bnc.credentials = SourceCredentials.from_env("BNC")

        # Load custom URLs
        licitar_url = os.getenv("LICITAR_API_URL")
        if licitar_url:
            config.licitar.base_url = licitar_url

        # Load consolidation config
        config.consolidation = ConsolidationConfig.from_env()

        return config

    def get_enabled_sources(self) -> List[str]:
        """
        Get list of enabled source codes.

        Returns:
            List of enabled source code strings
        """
        sources = []
        for source in [self.pncp, self.portal, self.licitar, self.compras_gov, self.portal_transparencia, self.bll, self.bnc, self.querido_diario]:
            if source.enabled:
                sources.append(source.code.value)
        return sources

    def get_source(self, code: str) -> Optional[SingleSourceConfig]:
        """
        Get configuration for a specific source.

        Args:
            code: Source code string (e.g., 'PNCP', 'Portal')

        Returns:
            SingleSourceConfig if found, None otherwise
        """
        source_map = {
            "PNCP": self.pncp,
            "Portal": self.portal,
            "Licitar": self.licitar,
            "ComprasGov": self.compras_gov,
            "PortalTransparencia": self.portal_transparencia,
            "BLL": self.bll,
            "BNC": self.bnc,
            "QueridoDiario": self.querido_diario,
        }
        return source_map.get(code)

    def get_enabled_source_configs(self) -> List[SingleSourceConfig]:
        """
        Get list of enabled source configurations, sorted by priority.

        Returns:
            List of SingleSourceConfig objects for enabled sources
        """
        configs = []
        for source in [self.pncp, self.portal, self.licitar, self.compras_gov, self.portal_transparencia, self.bll, self.bnc, self.querido_diario]:
            if source.enabled:
                configs.append(source)
        return sorted(configs, key=lambda s: s.priority)

    def get_pending_credentials(self) -> List[str]:
        """Get list of enabled sources that are missing required credentials.

        STORY-257A AC13: For health endpoint reporting.
        """
        pending = []
        for source in [self.portal, self.licitar, self.portal_transparencia, self.bll, self.bnc]:
            if source.enabled and not source.is_available():
                pending.append(source.code.value)
        return pending

    def validate(self) -> List[str]:
        """
        Validate configuration and return list of warnings/errors.

        Returns:
            List of validation messages (empty if all valid)
        """
        messages = []

        # Check at least one source is enabled
        enabled = self.get_enabled_sources()
        if not enabled:
            messages.append("ERROR: No sources enabled. At least one source required.")

        # Check credentials for enabled sources that require them
        if self.portal.enabled and not self.portal.credentials.has_api_key():
            messages.append(
                "WARNING: Portal de Compras enabled but PORTAL_COMPRAS_API_KEY not set"
            )

        if self.licitar.enabled and not self.licitar.credentials.has_api_key():
            messages.append(
                "WARNING: Licitar Digital enabled but LICITAR_API_KEY not set"
            )

        if self.portal_transparencia.enabled and not self.portal_transparencia.credentials.has_api_key():
            messages.append(
                "WARNING: Portal da Transparência enabled but PORTAL_TRANSPARENCIA_API_KEY not set"
            )

        # Check timeout configuration
        if self.consolidation.timeout_per_source >= self.consolidation.timeout_global:
            messages.append(
                "WARNING: Per-source timeout >= global timeout may cause issues"
            )

        return messages

    def log_configuration(self) -> None:
        """Log current configuration (without exposing credentials)."""
        logger.info("Multi-Source Configuration:")
        logger.info(f"  Enabled sources: {self.get_enabled_sources()}")
        logger.info(f"  Global timeout: {self.consolidation.timeout_global}s")
        logger.info(f"  Per-source timeout: {self.consolidation.timeout_per_source}s")
        logger.info(f"  Dedup strategy: {self.consolidation.dedup_strategy}")

        for source in self.get_enabled_source_configs():
            has_creds = (
                "yes" if source.credentials.has_api_key() else "no"
            )
            logger.info(
                f"  {source.code.value}: url={source.base_url}, "
                f"timeout={source.timeout}s, credentials={has_creds}"
            )

        # Log validation warnings
        warnings = self.validate()
        for msg in warnings:
            if msg.startswith("ERROR"):
                logger.error(msg)
            else:
                logger.warning(msg)


# Global cached config instance
_source_config: Optional[SourceConfig] = None


def get_source_config(reload: bool = False) -> SourceConfig:
    """
    Get the global source configuration instance.

    Uses lazy initialization and caching for performance.

    Args:
        reload: Force reload from environment (default: False)

    Returns:
        SourceConfig instance
    """
    global _source_config

    if _source_config is None or reload:
        _source_config = SourceConfig.from_env()
        _source_config.log_configuration()

    return _source_config


def validate_environment_on_startup() -> None:
    """
    Validate environment configuration at application startup.

    Raises:
        ValueError: If critical configuration is missing
    """
    config = get_source_config(reload=True)
    errors = [msg for msg in config.validate() if msg.startswith("ERROR")]

    if errors:
        for error in errors:
            logger.error(error)
        raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

    logger.info("Environment configuration validated successfully")
