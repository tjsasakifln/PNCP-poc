"""DEBT-118 AC10: Shared utility helpers for the filter pipeline.

Contains value parsing and sector config lookup functions used
across filter_llm.py, filter_recovery.py, and filter.py.
"""

import logging

logger = logging.getLogger(__name__)


def parse_valor(val) -> float:
    """Parse a valor field (str, int, float, None) to float.

    Handles Brazilian-format strings (e.g. "1.000.000,50") and
    returns 0.0 for None / unparseable values.

    Args:
        val: Raw value from a licitacao dict (valorTotalEstimado, valorEstimado, etc.)

    Returns:
        Parsed float value, or 0.0 if unparseable/missing.
    """
    if val is None:
        return 0.0
    if isinstance(val, str):
        try:
            return float(val.replace(".", "").replace(",", "."))
        except ValueError:
            return 0.0
    if isinstance(val, (int, float)):
        return float(val) if val else 0.0
    return 0.0


def get_valor_from_lic(lic: dict) -> float:
    """Extract and parse valor from a licitacao dict, trying multiple field names.

    Args:
        lic: Licitacao dictionary from PNCP/PCP/ComprasGov.

    Returns:
        Parsed float value.
    """
    val = lic.get("valorTotalEstimado") or lic.get("valorEstimado") or 0
    return parse_valor(val)


def get_setor_config(setor: str):
    """Look up sector config by ID, returning None on failure.

    Args:
        setor: Sector ID (e.g. "vestuario", "informatica").

    Returns:
        Sector config object, or None if not found.
    """
    try:
        from sectors import get_sector
        return get_sector(setor)
    except (KeyError, Exception):
        logger.warning(f"Setor '{setor}' não encontrado")
        return None
