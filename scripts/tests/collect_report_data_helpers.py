"""
Testable helpers extracted from collect-report-data.py.

We can't directly import the script because its top-level Windows encoding
wrapper (sys.stdout replacement) breaks pytest's capture mechanism.
Instead, we duplicate the pure functions here for testing.
"""
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _clean_cnpj(cnpj: str) -> str:
    """Remove formatting from CNPJ, return 14 digits."""
    return re.sub(r"[^0-9]", "", cnpj).zfill(14)


def _format_cnpj(cnpj14: str) -> str:
    """Format 14-digit CNPJ as XX.XXX.XXX/XXXX-XX."""
    c = cnpj14
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:14]}"


def _safe_float(v: Any, default: float = 0.0) -> float:
    if v is None:
        return default
    try:
        if isinstance(v, str):
            v = v.replace(",", ".")
        return float(v)
    except (ValueError, TypeError):
        return default


def _source_tag(status: str, detail: str = "") -> dict:
    """Create a _source metadata tag."""
    tag = {"status": status, "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    if detail:
        tag["detail"] = detail
    return tag


# Import deterministic functions from collect-report-data.py
# The script has a Windows stdout encoding wrapper that breaks pytest,
# so we use a careful import approach.
import importlib.util as _iu
import os as _os
import sys as _sys

_script_path = str(Path(__file__).parent.parent / "collect-report-data.py")
_mod = None

try:
    _spec = _iu.spec_from_file_location("collect_report_data", _script_path)
    _temp_mod = _iu.module_from_spec(_spec)
    # Redirect stdout/stderr to devnull during import to avoid encoding crash
    _saved_stdout = _sys.stdout
    _saved_stderr = _sys.stderr
    _sys.stdout = open(_os.devnull, "w", encoding="utf-8")
    _sys.stderr = open(_os.devnull, "w", encoding="utf-8")
    try:
        _spec.loader.exec_module(_temp_mod)
        _mod = _temp_mod
    finally:
        _sys.stdout.close()
        _sys.stderr.close()
        _sys.stdout = _saved_stdout
        _sys.stderr = _saved_stderr
except Exception:
    _mod = None

if _mod is not None:
    map_sector = _mod.map_sector
    compute_risk_score = _mod.compute_risk_score
    compute_win_probability = _mod.compute_win_probability
    compute_roi_potential = _mod.compute_roi_potential
    build_reverse_chronogram = _mod.build_reverse_chronogram
    compute_all_deterministic = _mod.compute_all_deterministic
    compute_object_compatibility = _mod.compute_object_compatibility
    compute_habilitacao_analysis = _mod.compute_habilitacao_analysis
    compute_competitive_analysis = _mod.compute_competitive_analysis
    compute_risk_analysis = _mod.compute_risk_analysis
    compute_portfolio_analysis = _mod.compute_portfolio_analysis
    _CNAE_TO_SECTOR_KEY = _mod._CNAE_TO_SECTOR_KEY
    _SECTOR_MARGINS = _mod._SECTOR_MARGINS
    _SECTOR_WEIGHT_PROFILES = _mod._SECTOR_WEIGHT_PROFILES
    _SECTOR_BASE_WIN_RATES = _mod._SECTOR_BASE_WIN_RATES
    _SECTOR_SUBCATEGORIES = _mod._SECTOR_SUBCATEGORIES
    _HABILITACAO_REQUIREMENTS = _mod._HABILITACAO_REQUIREMENTS
    _SECTOR_RISK_FLAGS = _mod._SECTOR_RISK_FLAGS
    _PARTICIPATION_COST = _mod._PARTICIPATION_COST
    # E1-E8 new functions
    detect_maturity_profile = _mod.detect_maturity_profile
    compute_qualification_gap_analysis = _mod.compute_qualification_gap_analysis
    compute_regional_clusters = _mod.compute_regional_clusters
    _SECTOR_REQUIREMENTS_DETAILED = _mod._SECTOR_REQUIREMENTS_DETAILED
