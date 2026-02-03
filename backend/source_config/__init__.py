"""
Configuration module for BidIQ backend.

Provides centralized configuration management for:
- Multi-source procurement data sources
- API credentials and timeouts
- Consolidation service settings
"""

from source_config.sources import (
    SourceCode,
    SourceConfig,
    SourceCredentials,
    SingleSourceConfig,
    ConsolidationConfig,
    get_source_config,
    validate_environment_on_startup,
)

__all__ = [
    "SourceCode",
    "SourceConfig",
    "SourceCredentials",
    "SingleSourceConfig",
    "ConsolidationConfig",
    "get_source_config",
    "validate_environment_on_startup",
]
