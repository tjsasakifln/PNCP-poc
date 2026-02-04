"""Configuration models for PNCP client."""

from dataclasses import dataclass, field
from typing import Tuple, Type, List
import logging
import sys


# PNCP Modality Codes (codigoModalidadeContratacao)
# Source: https://pncp.gov.br/api/pncp/v1/modalidades
MODALIDADES_PNCP = {
    1: "Leilão - Eletrônico",
    2: "Diálogo Competitivo",
    3: "Concurso",
    4: "Concorrência - Eletrônica",
    5: "Concorrência - Presencial",
    6: "Pregão - Eletrônico",
    7: "Pregão - Presencial",
    8: "Dispensa",
    9: "Inexigibilidade",
    10: "Manifestação de Interesse",
    11: "Pré-qualificação",
    12: "Credenciamento",
    13: "Leilão - Presencial",
    14: "Inaplicabilidade da Licitação",
    15: "Chamada pública",
}

# Default modalities for BidIQ Uniformes search
# Focus on Pregão Eletrônico (6) - most common for uniforms
# NOTE: Modalidade 8 (Dispensa) has 2000+ records and causes timeouts
DEFAULT_MODALIDADES: List[int] = [
    6,  # Pregão - Eletrônico (most common for uniforms, fast response)
]


@dataclass
class RetryConfig:
    """Configuration for HTTP retry logic."""

    max_retries: int = 5
    base_delay: float = 2.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: int = 2
    jitter: bool = True
    timeout: int = 30  # seconds

    # HTTP status codes that should trigger retry
    retryable_status_codes: Tuple[int, ...] = field(
        default_factory=lambda: (408, 429, 500, 502, 503, 504)
    )

    # Exception types that should trigger retry
    retryable_exceptions: Tuple[Type[Exception], ...] = field(
        default_factory=lambda: (
            ConnectionError,
            TimeoutError,
        )
    )


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging for the application.

    Sets up a consistent logging format across all modules with proper
    level filtering and suppression of verbose third-party libraries.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to INFO.

    Example:
        >>> setup_logging("DEBUG")
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started")
        2026-01-25 23:00:00 | INFO     | __main__ | Application started
    """
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(handler)

    # Silence verbose logs from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


# ============================================
# Feature Flags
# ============================================

import os

def str_to_bool(value: str | None) -> bool:
    """
    Convert string environment variable to boolean.
    
    Accepts: 'true', '1', 'yes', 'on' (case-insensitive) as True
    Everything else (including None) is False
    
    Args:
        value: String value from environment variable
        
    Returns:
        Boolean interpretation of the value
        
    Examples:
        >>> str_to_bool("true")
        True
        >>> str_to_bool("1")
        True
        >>> str_to_bool("false")
        False
        >>> str_to_bool(None)
        False
    """
    if value is None:
        return False
    return value.lower() in ("true", "1", "yes", "on")


# Feature Flag: New Pricing Model (STORY-165)
# Controls plan-based capabilities, quota enforcement, and Excel gating
# Default: False (disabled for safety, rollout via gradual deployment)
ENABLE_NEW_PRICING: bool = str_to_bool(os.getenv("ENABLE_NEW_PRICING", "false"))

# Log feature flag state on import
logger = logging.getLogger(__name__)
logger.info(f"Feature Flag - ENABLE_NEW_PRICING: {ENABLE_NEW_PRICING}")
