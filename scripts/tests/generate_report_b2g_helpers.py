"""
Testable helpers from generate-report-b2g.py.

Safe to import — no Windows encoding wrapper in the PDF generator.
"""
import sys
from pathlib import Path
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "generate_report_b2g",
    str(Path(__file__).parent.parent / "generate-report-b2g.py"),
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

# Re-export functions for tests
_normalize_recommendation = _mod._normalize_recommendation
_validate_json = _mod._validate_json
_get_source_badge = _mod._get_source_badge
_fix_pncp_link = _mod._fix_pncp_link
_section_counter = _mod._section_counter
_draw_risk_bar = _mod._draw_risk_bar
_build_chronogram_table = _mod._build_chronogram_table
_build_roi_card = _mod._build_roi_card
_build_decision_table = _mod._build_decision_table
_build_competitive_section = _mod._build_competitive_section
_build_styles = _mod._build_styles
generate_report_b2g = _mod.generate_report_b2g
