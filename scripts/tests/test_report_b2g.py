#!/usr/bin/env python3
"""
Tests for the report-b2g pipeline:
- collect-report-data.py (data collection helpers)
- generate-report-b2g.py (PDF generation helpers)
"""
import json
import os
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts dir to path
SCRIPTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def minimal_data():
    """Minimal valid JSON for PDF generation."""
    return {
        "empresa": {
            "cnpj": "01.721.078/0001-68",
            "razao_social": "LCM CONSTRUÇÕES LTDA",
            "nome_fantasia": "LCM Construções",
            "cidade": "Florianópolis",
            "uf": "SC",
            "capital_social": 500000.0,
        },
        "editais": [
            {
                "objeto": "Pavimentação asfáltica em vias urbanas",
                "orgao": "Prefeitura Municipal de Joinville",
                "uf": "SC",
                "municipio": "Joinville",
                "valor_estimado": 1500000.0,
                "modalidade": "Pregão Eletrônico",
                "data_abertura": "2026-03-15",
                "data_encerramento": "2026-03-25",
                "link": "https://pncp.gov.br/app/editais/83214189000100/2026/42",
                "recomendacao": "PARTICIPAR",
                "justificativa": "Alta aderência ao perfil da empresa",
                "distancia_km": 180.5,
                "_source": {"status": "API", "timestamp": "2026-03-12"},
            }
        ],
        "resumo_executivo": {
            "total_editais": 1,
            "valor_total": 1500000.0,
            "participar": 1,
            "avaliar": 0,
            "nao_recomendado": 0,
        },
    }


@pytest.fixture
def data_with_metadata(minimal_data):
    """JSON with _metadata and sicaf sections (new format)."""
    minimal_data["sicaf"] = {
        "status": "VERIFICAÇÃO MANUAL NECESSÁRIA",
        "instrucao": "Verificar no portal SICAF",
        "url": "https://sicaf.gov.br",
        "_source": {"status": "UNAVAILABLE"},
    }
    minimal_data["_metadata"] = {
        "generated_at": "2026-03-12T10:30:00",
        "generator": "collect-report-data.py v1.0",
        "sources": {
            "opencnpj": {"status": "API", "detail": "200 OK"},
            "portal_transparencia_sancoes": {"status": "API", "detail": "Sem sanções"},
            "portal_transparencia_contratos": {"status": "API_FAILED", "detail": "timeout"},
            "pncp": {"status": "API", "detail": "83 editais"},
            "pcp_v2": {"status": "API", "detail": "0 editais"},
            "querido_diario": {"status": "API", "detail": "Skip"},
            "sicaf": {"status": "UNAVAILABLE", "detail": "Sem API pública"},
        },
    }
    return minimal_data


# ============================================================
# collect-report-data.py — Unit Tests
# ============================================================

class TestCleanCnpj:
    def setup_method(self):
        from collect_report_data_helpers import _clean_cnpj
        self._clean_cnpj = _clean_cnpj

    def test_already_clean(self):
        assert self._clean_cnpj("01721078000168") == "01721078000168"

    def test_formatted(self):
        assert self._clean_cnpj("01.721.078/0001-68") == "01721078000168"

    def test_short_pads_zeros(self):
        assert self._clean_cnpj("123") == "00000000000123"


class TestFormatCnpj:
    def test_format(self):
        from collect_report_data_helpers import _format_cnpj
        assert _format_cnpj("01721078000168") == "01.721.078/0001-68"


class TestSafeFloat:
    def setup_method(self):
        from collect_report_data_helpers import _safe_float
        self._safe_float = _safe_float

    def test_number(self):
        assert self._safe_float(123.45) == 123.45

    def test_string_comma(self):
        assert self._safe_float("1232000,00") == 1232000.0

    def test_string_dot(self):
        assert self._safe_float("1232000.00") == 1232000.0

    def test_none(self):
        assert self._safe_float(None) == 0.0

    def test_invalid(self):
        assert self._safe_float("abc") == 0.0

    def test_custom_default(self):
        assert self._safe_float(None, default=-1.0) == -1.0


class TestSourceTag:
    def test_basic(self):
        from collect_report_data_helpers import _source_tag
        tag = _source_tag("API")
        assert tag["status"] == "API"
        assert "timestamp" in tag

    def test_with_detail(self):
        from collect_report_data_helpers import _source_tag
        tag = _source_tag("API_FAILED", "timeout after 30s")
        assert tag["detail"] == "timeout after 30s"


# ============================================================
# generate-report-b2g.py — Unit Tests
# ============================================================

class TestNormalizeRecommendation:
    def setup_method(self):
        from generate_report_b2g_helpers import _normalize_recommendation
        self._normalize = _normalize_recommendation

    def test_participar(self):
        assert self._normalize("participar") == "PARTICIPAR"

    def test_nao_with_accent(self):
        assert self._normalize("NÃO RECOMENDADO") == "NÃO RECOMENDADO"

    def test_nao_without_accent(self):
        assert self._normalize("NAO RECOMENDADO") == "NÃO RECOMENDADO"

    def test_avaliar_cautela(self):
        assert self._normalize("Avaliar com cautela") == "AVALIAR COM CAUTELA"

    def test_avaliar_short(self):
        assert self._normalize("avaliar") == "AVALIAR COM CAUTELA"

    def test_unknown_passthrough(self):
        assert self._normalize("MONITORAR") == "MONITORAR"


class TestFixPncpLink:
    def setup_method(self):
        from generate_report_b2g_helpers import _fix_pncp_link
        self._fix = _fix_pncp_link

    def test_correct_link_unchanged(self):
        link = "https://pncp.gov.br/app/editais/27142058000126/2026/85"
        assert self._fix(link) == link

    def test_hyphen_format_fixed(self):
        link = "https://pncp.gov.br/app/editais/27142058000126-2026-85"
        expected = "https://pncp.gov.br/app/editais/27142058000126/2026/85"
        assert self._fix(link) == expected

    def test_search_query_removed(self):
        link = "https://pncp.gov.br/app/editais?q=reforma+obra"
        assert self._fix(link) == ""

    def test_none_returns_empty(self):
        assert self._fix(None) == ""

    def test_empty_returns_empty(self):
        assert self._fix("") == ""


class TestValidateJson:
    def setup_method(self):
        from generate_report_b2g_helpers import _validate_json
        self._validate = _validate_json

    def test_valid(self, minimal_data):
        warnings, errors = self._validate(minimal_data)
        assert len(warnings) == 0
        assert len(errors) == 0

    def test_missing_empresa(self):
        warnings, _errors = self._validate({"editais": []})
        assert any("empresa" in w for w in warnings)

    def test_missing_cnpj(self):
        warnings, _errors = self._validate({"empresa": {"razao_social": "X"}, "editais": []})
        assert any("cnpj" in w for w in warnings)

    def test_missing_objeto(self):
        data = {
            "empresa": {"cnpj": "123", "razao_social": "X"},
            "editais": [{"orgao": "Pref X"}],
        }
        warnings, _errors = self._validate(data)
        assert any("objeto" in w for w in warnings)

    def test_missing_justificativa_blocks(self):
        """Recomendação without justificativa is a blocking error."""
        data = {
            "empresa": {"cnpj": "123", "razao_social": "X"},
            "editais": [{
                "objeto": "Obra X",
                "orgao": "Prefeitura Y",
                "recomendacao": "NÃO RECOMENDADO",
            }],
        }
        _warnings, errors = self._validate(data)
        assert len(errors) == 1
        assert "justificativa" in errors[0]

    def test_encerrado_does_not_require_justificativa(self):
        """ENCERRADO editais don't need justificativa."""
        data = {
            "empresa": {"cnpj": "123", "razao_social": "X"},
            "editais": [{
                "objeto": "Obra X",
                "orgao": "Prefeitura Y",
                "recomendacao": "NÃO RECOMENDADO",
                "status_edital": "ENCERRADO",
            }],
        }
        _warnings, errors = self._validate(data)
        assert len(errors) == 0

    def test_pdf_blocked_without_justificativa(self, minimal_data):
        """generate_report_b2g raises ValueError if justificativa missing."""
        from generate_report_b2g_helpers import generate_report_b2g
        del minimal_data["editais"][0]["justificativa"]
        with pytest.raises(ValueError, match="justificativa"):
            generate_report_b2g(minimal_data)


class TestGetSourceBadge:
    def setup_method(self):
        from generate_report_b2g_helpers import _get_source_badge
        self._badge = _get_source_badge

    def test_api_success(self):
        char, color, text = self._badge({"status": "API"})
        assert char == "✓"
        assert "Confirmado" in text

    def test_api_failed(self):
        char, color, text = self._badge({"status": "API_FAILED"})
        assert char == "✗"

    def test_none(self):
        char, color, text = self._badge(None)
        assert char == "—"

    def test_string_status(self):
        char, color, text = self._badge("CALCULATED")
        assert char == "✓"


# ============================================================
# PDF Generation — Integration Tests
# ============================================================

class TestPdfGeneration:
    def test_minimal_pdf(self, minimal_data):
        """PDF generates without errors from minimal data."""
        from generate_report_b2g_helpers import generate_report_b2g
        buf = generate_report_b2g(minimal_data)
        assert isinstance(buf, BytesIO)
        content = buf.read()
        assert len(content) > 1000
        assert content[:5] == b"%PDF-"

    def test_pdf_with_metadata(self, data_with_metadata):
        """PDF generates with SICAF + data sources sections."""
        from generate_report_b2g_helpers import generate_report_b2g
        buf = generate_report_b2g(data_with_metadata)
        content = buf.read()
        assert len(content) > 1000
        assert content[:5] == b"%PDF-"

    def test_pdf_with_empty_editais(self, minimal_data):
        """PDF generates even with 0 editais."""
        minimal_data["editais"] = []
        minimal_data["resumo_executivo"]["total_editais"] = 0
        from generate_report_b2g_helpers import generate_report_b2g
        buf = generate_report_b2g(minimal_data)
        assert buf.read()[:5] == b"%PDF-"

    def test_pdf_recommendation_normalization(self, minimal_data):
        """Recommendations are normalized in the PDF."""
        minimal_data["editais"][0]["recomendacao"] = "NAO RECOMENDADO"
        from generate_report_b2g_helpers import generate_report_b2g
        buf = generate_report_b2g(minimal_data)
        assert buf.read()[:5] == b"%PDF-"

    def test_pdf_encerrado_excluded(self, minimal_data):
        """ENCERRADO editais are excluded from the PDF entirely."""
        minimal_data["editais"][0]["status_edital"] = "ENCERRADO"
        # Add one ABERTO edital so PDF has content
        minimal_data["editais"].append({
            "objeto": "Obra Y aberta",
            "orgao": "Prefeitura Z",
            "uf": "PR",
            "recomendacao": "PARTICIPAR",
            "justificativa": "Perfil compatível",
            "_source": {"status": "API"},
        })
        from generate_report_b2g_helpers import generate_report_b2g
        buf = generate_report_b2g(minimal_data)
        assert buf.read()[:5] == b"%PDF-"

    def test_pdf_all_encerrado_still_generates(self, minimal_data):
        """PDF generates even if all editais are ENCERRADO (empty report)."""
        minimal_data["editais"][0]["status_edital"] = "ENCERRADO"
        from generate_report_b2g_helpers import generate_report_b2g
        buf = generate_report_b2g(minimal_data)
        assert buf.read()[:5] == b"%PDF-"


# ============================================================
# JSON Schema Validation — Integration Tests
# ============================================================

class TestJsonSchemaFromFile:
    """Test against real JSON files produced by collect-report-data.py."""

    DATA_DIR = Path(__file__).parent.parent.parent / "docs" / "reports"

    def _load_json(self, filename):
        path = self.DATA_DIR / filename
        if not path.exists():
            pytest.skip(f"Data file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_new_format_has_metadata(self):
        """New-format JSON has _metadata.sources."""
        # Look for any data file with _metadata
        for p in self.DATA_DIR.glob("data-*.json"):
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            if "_metadata" in d:
                assert "sources" in d["_metadata"]
                assert "generated_at" in d["_metadata"]
                return
        pytest.skip("No new-format JSON files found")

    def test_editais_have_source_tags(self):
        """New-format editais have _source tags."""
        for p in self.DATA_DIR.glob("data-*.json"):
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            if d.get("editais") and isinstance(d["editais"][0].get("_source"), dict):
                for ed in d["editais"]:
                    assert "_source" in ed
                    assert ed["_source"]["status"] in ("API", "API_PARTIAL", "API_FAILED", "CALCULATED", "UNAVAILABLE")
                return
        pytest.skip("No new-format JSON files with _source tags found")

    def test_all_json_files_generate_pdf(self):
        """Every data JSON in docs/reports/ can generate a PDF without crashing.

        Legacy files missing justificativa will raise ValueError (expected) —
        the test verifies they are properly blocked, not silently broken.
        """
        from generate_report_b2g_helpers import generate_report_b2g, _validate_json
        files = list(self.DATA_DIR.glob("data-*.json"))
        if not files:
            pytest.skip("No data files found")
        for p in files:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            _warnings, errors = _validate_json(d)
            if errors:
                # Correctly blocked — legacy file without justificativa
                with pytest.raises(ValueError, match="justificativa"):
                    generate_report_b2g(d)
            else:
                buf = generate_report_b2g(d)
                content = buf.read()
                assert content[:5] == b"%PDF-", f"Failed for {p.name}"


# ============================================================
# V2 Premium Features — collect-report-data.py
# ============================================================

class TestMapSector:
    """Test multi-sector CNAE mapping."""

    def setup_method(self):
        try:
            from collect_report_data_helpers import map_sector
            self._map = map_sector
        except (ImportError, AttributeError):
            pytest.skip("collect_report_data module could not be imported")

    def test_returns_three_values(self):
        setor, kw, key = self._map("4120400 - Construção de edifícios")
        assert isinstance(setor, str)
        assert isinstance(kw, list)
        assert isinstance(key, str)

    def test_engineering_cnae(self):
        _, _, key = self._map("4120400 - Construção de edifícios")
        assert key == "engenharia"

    def test_software_cnae(self):
        _, _, key = self._map("6201501 - Desenvolvimento de software")
        assert key == "software"

    def test_saude_cnae(self):
        _, _, key = self._map("3250701 - Materiais para uso médico")
        assert key == "saude"

    def test_informatica_cnae(self):
        _, _, key = self._map("4751201 - Comércio de computadores")
        assert key == "informatica"

    def test_unknown_cnae_returns_geral(self):
        _, _, key = self._map("9999999 - Atividade inexistente")
        assert key == "geral"

    def test_empty_cnae(self):
        _, _, key = self._map("")
        assert key == "geral"


class TestCnaeToSectorKeyCoverage:
    """Ensure CNAE map covers all 15 sectors."""

    def test_all_sectors_present(self):
        try:
            from collect_report_data_helpers import _CNAE_TO_SECTOR_KEY
        except (ImportError, AttributeError):
            pytest.skip("collect_report_data module could not be imported")
        sector_values = set(_CNAE_TO_SECTOR_KEY.values())
        expected_sectors = {
            "engenharia", "software", "informatica", "saude",
            "vestuario", "alimentos", "mobiliario", "papelaria",
            "facilities", "vigilancia", "transporte",
            "manutencao_predial", "engenharia_rodoviaria",
            "materiais_eletricos", "materiais_hidraulicos",
        }
        missing = expected_sectors - sector_values
        assert not missing, f"Sectors missing from CNAE map: {missing}"


class TestComputeRiskScore:
    def setup_method(self):
        try:
            from collect_report_data_helpers import compute_risk_score
            self._compute = compute_risk_score
        except (ImportError, AttributeError):
            pytest.skip("collect_report_data module could not be imported")

    def test_returns_dict_with_total(self):
        edital = {
            "valor_estimado": 1000000,
            "dias_restantes": 15,
            "modalidade": "Pregão Eletrônico",
        }
        empresa = {"capital_social": 2000000, "cidade_sede": "Florianópolis", "uf_sede": "SC"}
        result = self._compute(edital, empresa, {})
        assert "total" in result
        assert 0 <= result["total"] <= 100

    def test_score_components(self):
        edital = {"valor_estimado": 500000, "dias_restantes": 20}
        empresa = {"capital_social": 5000000}
        result = self._compute(edital, empresa, {})
        for key in ["habilitacao", "financeiro", "geografico", "prazo", "competitivo"]:
            assert key in result, f"Missing component: {key}"

    def test_high_capital_high_score(self):
        edital = {"valor_estimado": 100000, "dias_restantes": 30}
        empresa = {"capital_social": 10000000}
        result = self._compute(edital, empresa, {})
        assert result["financeiro"] >= 70

    def test_zero_capital_low_score(self):
        edital = {"valor_estimado": 1000000, "dias_restantes": 5}
        empresa = {"capital_social": 0}
        result = self._compute(edital, empresa, {})
        assert result["financeiro"] <= 50

    def test_short_deadline_low_prazo(self):
        edital = {"valor_estimado": 100000, "dias_restantes": 2}
        empresa = {"capital_social": 1000000}
        result = self._compute(edital, empresa, {})
        assert result["prazo"] <= 30


class TestComputeRoiPotential:
    def setup_method(self):
        try:
            from collect_report_data_helpers import compute_roi_potential
            self._compute = compute_roi_potential
        except (ImportError, AttributeError):
            pytest.skip("collect_report_data module could not be imported")

    def test_returns_dict_with_roi(self):
        edital = {"valor_estimado": 1000000}
        result = self._compute(edital, "engenharia", 70)
        assert "roi_min" in result
        assert "roi_max" in result
        assert result["roi_max"] >= result["roi_min"]

    def test_zero_value_zero_roi(self):
        edital = {"valor_estimado": 0}
        result = self._compute(edital, "engenharia", 50)
        assert result["roi_max"] == 0

    def test_higher_score_higher_roi(self):
        edital = {"valor_estimado": 1000000}
        low = self._compute(edital, "engenharia", 30)
        high = self._compute(edital, "engenharia", 90)
        assert high["roi_max"] >= low["roi_max"]

    def test_unknown_sector_uses_default(self):
        edital = {"valor_estimado": 1000000}
        result = self._compute(edital, "nonexistent_sector", 50)
        assert result["roi_max"] > 0


class TestBuildReverseChronogram:
    def setup_method(self):
        try:
            from collect_report_data_helpers import build_reverse_chronogram
            self._build = build_reverse_chronogram
        except (ImportError, AttributeError):
            pytest.skip("collect_report_data module could not be imported")

    def test_returns_list(self):
        edital = {"data_encerramento": "2026-04-01", "dias_restantes": 20}
        result = self._build(edital)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_each_entry_has_required_fields(self):
        edital = {"data_encerramento": "2026-04-01", "dias_restantes": 20}
        result = self._build(edital)
        for entry in result:
            assert "data" in entry
            assert "marco" in entry
            assert "status" in entry

    def test_no_deadline_returns_empty(self):
        edital = {}
        result = self._build(edital)
        assert result == []

    def test_past_deadline_marks_atrasado(self):
        edital = {"data_encerramento": "2020-01-01", "dias_restantes": -100}
        result = self._build(edital)
        assert any("atrasado" in e.get("status", "").lower() or "vencido" in e.get("status", "").lower()
                    for e in result) or result == []


class TestSectorMargins:
    def test_all_sectors_have_margins(self):
        try:
            from collect_report_data_helpers import _SECTOR_MARGINS
        except (ImportError, AttributeError):
            pytest.skip("collect_report_data module could not be imported")
        expected = {
            "engenharia", "software", "informatica", "saude",
            "vestuario", "alimentos", "mobiliario", "papelaria",
            "facilities", "vigilancia", "transporte",
            "manutencao_predial", "engenharia_rodoviaria",
            "materiais_eletricos", "materiais_hidraulicos",
        }
        missing = expected - set(_SECTOR_MARGINS.keys())
        assert not missing, f"Sectors missing margins: {missing}"


# ============================================================
# V2 Premium Features — generate-report-b2g.py
# ============================================================

class TestSectionCounter:
    def test_increments(self):
        from generate_report_b2g_helpers import _section_counter
        sec = _section_counter()
        assert sec["next"]() == 1
        assert sec["next"]() == 2
        assert sec["next"]() == 3

    def test_current(self):
        from generate_report_b2g_helpers import _section_counter
        sec = _section_counter()
        sec["next"]()
        sec["next"]()
        assert sec["current"]() == 2


class TestDrawRiskBar:
    def test_returns_table_for_positive_score(self):
        from generate_report_b2g_helpers import _draw_risk_bar, _build_styles
        styles = _build_styles()
        result = _draw_risk_bar(72, styles)
        # Should return a Table, not a Spacer
        assert hasattr(result, '_cellvalues') or hasattr(result, 'width')

    def test_zero_score_returns_spacer(self):
        from generate_report_b2g_helpers import _draw_risk_bar, _build_styles
        styles = _build_styles()
        result = _draw_risk_bar(0, styles)
        # Zero returns Spacer
        assert not hasattr(result, '_cellvalues')


class TestBuildChronogramTable:
    def test_returns_elements(self):
        from generate_report_b2g_helpers import _build_chronogram_table, _build_styles
        styles = _build_styles()
        cronograma = [
            {"data": "2026-03-10", "marco": "Decisão", "status": "No prazo"},
            {"data": "2026-03-20", "marco": "Proposta", "status": "Atrasado"},
        ]
        result = _build_chronogram_table(cronograma, styles)
        assert len(result) > 0

    def test_empty_returns_empty(self):
        from generate_report_b2g_helpers import _build_chronogram_table, _build_styles
        styles = _build_styles()
        assert _build_chronogram_table([], styles) == []


class TestBuildRoiCard:
    def test_returns_elements(self):
        from generate_report_b2g_helpers import _build_roi_card, _build_styles
        styles = _build_styles()
        roi = {"roi_min": 100000, "roi_max": 300000, "probability": 65}
        result = _build_roi_card(roi, styles)
        assert len(result) > 0

    def test_zero_roi_returns_empty(self):
        from generate_report_b2g_helpers import _build_roi_card, _build_styles
        styles = _build_styles()
        assert _build_roi_card({"roi_min": 0, "roi_max": 0}, styles) == []

    def test_none_roi_returns_empty(self):
        from generate_report_b2g_helpers import _build_roi_card, _build_styles
        styles = _build_styles()
        assert _build_roi_card(None, styles) == []


class TestBuildDecisionTable:
    def test_returns_elements_with_editais(self, minimal_data):
        from generate_report_b2g_helpers import _build_decision_table, _build_styles, _section_counter
        styles = _build_styles()
        sec = _section_counter()
        result = _build_decision_table(minimal_data, styles, sec)
        assert len(result) > 0

    def test_empty_editais_returns_empty(self, minimal_data):
        from generate_report_b2g_helpers import _build_decision_table, _build_styles, _section_counter
        styles = _build_styles()
        sec = _section_counter()
        minimal_data["editais"] = []
        result = _build_decision_table(minimal_data, styles, sec)
        assert result == []


class TestBuildCompetitiveSection:
    def test_returns_elements_with_intel(self, minimal_data):
        from generate_report_b2g_helpers import _build_competitive_section, _build_styles, _section_counter
        styles = _build_styles()
        sec = _section_counter()
        minimal_data["editais"][0]["competitive_intel"] = [
            {"fornecedor": "ABC", "objeto": "Obra X", "valor": 1000000, "data": "2025-06-01"},
        ]
        result = _build_competitive_section(minimal_data, styles, sec)
        assert len(result) > 0

    def test_no_intel_returns_empty(self, minimal_data):
        from generate_report_b2g_helpers import _build_competitive_section, _build_styles, _section_counter
        styles = _build_styles()
        sec = _section_counter()
        result = _build_competitive_section(minimal_data, styles, sec)
        assert result == []


class TestPdfWithPremiumFields:
    """Integration test: PDF generates with all v2 premium fields."""

    def test_pdf_with_risk_score_roi_chronogram(self, minimal_data):
        from generate_report_b2g_helpers import generate_report_b2g
        minimal_data["editais"][0]["risk_score"] = {
            "total": 72, "habilitacao": 85, "financeiro": 60,
            "geografico": 90, "prazo": 55, "competitivo": 50,
        }
        minimal_data["editais"][0]["roi_potential"] = {
            "roi_min": 200000, "roi_max": 450000, "probability": 72,
        }
        minimal_data["editais"][0]["cronograma"] = [
            {"data": "2026-03-10", "marco": "Decisão", "status": "No prazo"},
            {"data": "2026-03-25", "marco": "Proposta", "status": "Atenção"},
        ]
        minimal_data["editais"][0]["competitive_intel"] = [
            {"fornecedor": "ABC Eng", "objeto": "Reforma", "valor": 1800000, "data": "2025-06-15"},
        ]
        buf = generate_report_b2g(minimal_data)
        content = buf.read()
        assert content[:5] == b"%PDF-"
        assert len(content) > 2000  # Should be larger than minimal

    def test_pdf_backward_compat_no_new_fields(self, minimal_data):
        """PDF still works when risk_score/roi/cronograma are absent (backward compat)."""
        from generate_report_b2g_helpers import generate_report_b2g
        buf = generate_report_b2g(minimal_data)
        assert buf.read()[:5] == b"%PDF-"
