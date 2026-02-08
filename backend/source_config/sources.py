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
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class SourceCode(str, Enum):
    """Enumeration of available procurement data sources."""

    PNCP = "PNCP"
    PORTAL = "Portal"
    LICITAR = "Licitar"
    BLL = "BLL"
    BNC = "BNC"


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
        """Check if source is enabled and has required credentials."""
        if not self.enabled:
            return False
        # PNCP doesn't require credentials
        if self.code == SourceCode.PNCP:
            return True
        # Other sources may require API keys
        return True  # For now, allow even without credentials

    def get_timeout(self) -> int:
        """Get effective timeout for this source."""
        return self.timeout


@dataclass
class ConsolidationConfig:
    """Configuration for multi-source consolidation service."""

    timeout_global: int = 60
    timeout_per_source: int = 25
    fail_on_all_errors: bool = True
    dedup_strategy: str = "first_seen"
    max_concurrent_sources: int = 5

    @classmethod
    def from_env(cls) -> "ConsolidationConfig":
        """Load consolidation config from environment."""
        return cls(
            timeout_global=int(os.getenv("CONSOLIDATION_TIMEOUT_GLOBAL", "60")),
            timeout_per_source=int(os.getenv("CONSOLIDATION_TIMEOUT_PER_SOURCE", "25")),
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
        config.bll.enabled = os.getenv("ENABLE_SOURCE_BLL", "false").lower() == "true"
        config.bnc.enabled = os.getenv("ENABLE_SOURCE_BNC", "false").lower() == "true"

        # Load credentials
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
        for source in [self.pncp, self.portal, self.licitar, self.bll, self.bnc]:
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
            "BLL": self.bll,
            "BNC": self.bnc,
        }
        return source_map.get(code)

    def get_enabled_source_configs(self) -> List[SingleSourceConfig]:
        """
        Get list of enabled source configurations, sorted by priority.

        Returns:
            List of SingleSourceConfig objects for enabled sources
        """
        configs = []
        for source in [self.pncp, self.portal, self.licitar, self.bll, self.bnc]:
            if source.enabled:
                configs.append(source)
        return sorted(configs, key=lambda s: s.priority)

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
