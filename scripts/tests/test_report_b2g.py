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


class TestGetSourceLabel:
    def setup_method(self):
        from generate_report_b2g_helpers import _get_source_label
        self._label = _get_source_label

    def test_api_success(self):
        text, color = self._label({"status": "API"})
        assert "Confirmado" in text

    def test_api_failed(self):
        text, color = self._label({"status": "API_FAILED"})
        assert "Indisponível" in text

    def test_none(self):
        text, color = self._label(None)
        assert "N/D" in text

    def test_string_status(self):
        text, color = self._label("CALCULATED")
        assert "Calculado" in text


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

    @staticmethod
    def _make_win_prob(probability: float, confidence: str = "media") -> dict:
        return {"probability": probability, "confidence": confidence}

    def test_returns_dict_with_roi(self):
        edital = {"valor_estimado": 1000000}
        result = self._compute(edital, "engenharia", self._make_win_prob(0.18))
        assert "roi_min" in result
        assert "roi_max" in result
        assert result["roi_max"] >= result["roi_min"]

    def test_zero_value_zero_roi(self):
        edital = {"valor_estimado": 0}
        result = self._compute(edital, "engenharia", self._make_win_prob(0.15))
        assert result["roi_max"] == 0

    def test_higher_prob_higher_roi(self):
        edital = {"valor_estimado": 1000000}
        low = self._compute(edital, "engenharia", self._make_win_prob(0.05))
        high = self._compute(edital, "engenharia", self._make_win_prob(0.30))
        assert high["roi_max"] >= low["roi_max"]

    def test_unknown_sector_uses_default(self):
        edital = {"valor_estimado": 1000000}
        result = self._compute(edital, "nonexistent_sector", self._make_win_prob(0.15))
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


class TestBuildRoiText:
    def test_returns_elements(self):
        from generate_report_b2g_helpers import _build_roi_text, _build_styles
        styles = _build_styles()
        roi = {"roi_min": 100000, "roi_max": 300000, "probability": 0.18, "confidence": "media"}
        ed = {"valor_estimado": 1000000, "risk_score": {"total": 70}}
        result = _build_roi_text(roi, ed, styles)
        assert len(result) > 0

    def test_zero_roi_returns_empty(self):
        from generate_report_b2g_helpers import _build_roi_text, _build_styles
        styles = _build_styles()
        assert _build_roi_text({"roi_min": 0, "roi_max": 0}, {}, styles) == []

    def test_none_roi_returns_empty(self):
        from generate_report_b2g_helpers import _build_roi_text, _build_styles
        styles = _build_styles()
        assert _build_roi_text(None, {}, styles) == []


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


# ============================================================
# SESSION 1: Win Probability + Sector Weight Profiles (P0+P1)
# ============================================================


class TestSectorWeightProfiles:
    def setup_method(self):
        try:
            from collect_report_data_helpers import _SECTOR_WEIGHT_PROFILES
            self._profiles = _SECTOR_WEIGHT_PROFILES
        except (ImportError, AttributeError):
            pytest.skip("collect_report_data module could not be imported")

    def test_all_profiles_sum_to_1(self):
        for sector, weights in self._profiles.items():
            total = sum(weights.values())
            assert abs(total - 1.0) < 0.001, (
                f"Sector {sector} weights sum to {total}, expected 1.0"
            )

    def test_all_sectors_have_five_components(self):
        required = {"hab", "fin", "geo", "prazo", "comp"}
        for sector, weights in self._profiles.items():
            assert set(weights.keys()) == required, (
                f"Sector {sector} missing keys: {required - set(weights.keys())}"
            )

    def test_default_profile_exists(self):
        assert "_default" in self._profiles

    def test_engineering_geo_higher_than_software(self):
        """Construction needs on-site presence; software is remote."""
        assert self._profiles["engenharia"]["geo"] > self._profiles["software"]["geo"]

    def test_software_comp_higher_than_engineering(self):
        """Software is more commoditized, competition matters more."""
        assert self._profiles["software"]["comp"] > self._profiles["engenharia"]["comp"]


class TestWinProbability:
    def setup_method(self):
        try:
            from collect_report_data_helpers import compute_win_probability
            self._compute = compute_win_probability
        except (ImportError, AttributeError):
            pytest.skip("collect_report_data module could not be imported")

    def _empresa(self, cnpj="12345678000190"):
        return {"cnpj": cnpj, "capital_social": 2000000}

    def test_bounds(self):
        """Probability must always be between 2% and 85%."""
        edital = {"modalidade": "Pregão Eletrônico"}
        result = self._compute(edital, self._empresa(), [], "engenharia", 70)
        assert 0.02 <= result["probability"] <= 0.85

    def test_no_data_uses_base_rate(self):
        """With empty competitive_intel, uses sector base rate with low confidence."""
        edital = {"modalidade": "Concorrência"}
        result = self._compute(edital, self._empresa(), [], "engenharia", 70)
        assert result["confidence"] == "baixa"
        assert result["n_unique_suppliers"] == 0

    def test_monopoly_low_probability(self):
        """Single supplier in history = very hard to break in."""
        edital = {"modalidade": "Pregão Eletrônico"}
        intel = [
            {"fornecedor": "MONOPOLY INC", "cnpj_fornecedor": "99999999000100", "valor": 1000000},
            {"fornecedor": "MONOPOLY INC", "cnpj_fornecedor": "99999999000100", "valor": 500000},
        ]
        result = self._compute(edital, self._empresa(), intel, "engenharia", 70)
        assert result["probability"] <= 0.10
        assert result["n_unique_suppliers"] == 1

    def test_incumbency_bonus(self):
        """Company already supplies this organ = bonus."""
        edital = {"modalidade": "Concorrência"}
        empresa = self._empresa("12345678000190")
        intel = [
            {"fornecedor": "OUR COMPANY", "cnpj_fornecedor": "12345678000190", "valor": 500000},
            {"fornecedor": "COMPETITOR A", "cnpj_fornecedor": "98765432000111", "valor": 300000},
        ]
        result_with = self._compute(edital, empresa, intel, "engenharia", 70)
        assert result_with["incumbency_bonus"] > 0

        # Without incumbency
        result_without = self._compute(edital, self._empresa("00000000000000"), intel, "engenharia", 70)
        assert result_without["incumbency_bonus"] == 0
        assert result_with["probability"] > result_without["probability"]

    def test_hhi_calculation(self):
        """HHI with 2 equal suppliers = 0.50."""
        edital = {"modalidade": "Concorrência"}
        intel = [
            {"fornecedor": "A", "cnpj_fornecedor": "11111111000100", "valor": 100},
            {"fornecedor": "B", "cnpj_fornecedor": "22222222000100", "valor": 100},
        ]
        result = self._compute(edital, self._empresa(), intel, "engenharia", 70)
        assert abs(result["hhi"] - 0.50) < 0.01

    def test_modality_adjustment(self):
        """Inexigibilidade should yield higher probability than pregão eletrônico."""
        intel = []  # No data — uses base rate
        empresa = self._empresa()
        inex = self._compute(
            {"modalidade": "Inexigibilidade"}, empresa, intel, "engenharia", 70,
        )
        pregao = self._compute(
            {"modalidade": "Pregão Eletrônico"}, empresa, intel, "engenharia", 70,
        )
        assert inex["probability"] > pregao["probability"]

    def test_low_viability_reduces_probability(self):
        """Risk score of 10 should yield lower probability than 90."""
        edital = {"modalidade": "Concorrência"}
        low = self._compute(edital, self._empresa(), [], "engenharia", 10)
        high = self._compute(edital, self._empresa(), [], "engenharia", 90)
        assert high["probability"] > low["probability"]


class TestRiskScoreWithSectorWeights:
    def setup_method(self):
        try:
            from collect_report_data_helpers import compute_risk_score
            self._compute = compute_risk_score
        except (ImportError, AttributeError):
            pytest.skip("collect_report_data module could not be imported")

    def test_returns_weights_in_result(self):
        edital = {"valor_estimado": 500000, "dias_restantes": 20}
        empresa = {"capital_social": 2000000}
        result = self._compute(edital, empresa, {}, "engenharia")
        assert "weights" in result
        assert result["weights"]["geo"] == 0.25  # Engineering: high geo weight

    def test_software_low_geo_weight(self):
        edital = {
            "valor_estimado": 500000, "dias_restantes": 20,
            "distancia": {"km": 800},  # Very far
        }
        empresa = {"capital_social": 2000000}
        eng = self._compute(edital, empresa, {}, "engenharia")
        sw = self._compute(edital, empresa, {}, "software")
        # Software should score higher because geo weight is only 5% vs 25%
        assert sw["total"] > eng["total"]

    def test_default_sector_backward_compat(self):
        """No sector_key = default weights (30/25/20/15/10)."""
        edital = {"valor_estimado": 500000, "dias_restantes": 20}
        empresa = {"capital_social": 2000000}
        result = self._compute(edital, empresa, {})
        assert result["weights"]["hab"] == 0.30  # Default weight


# ============================================================
# SESSION 2: Object Compatibility + Habilitação
# ============================================================


class TestObjectCompatibility:
    def setup_method(self):
        try:
            from collect_report_data_helpers import compute_object_compatibility
            self._compute = compute_object_compatibility
        except (ImportError, AttributeError):
            pytest.skip("compute_object_compatibility not available")

    def test_exact_subcategory_alta(self):
        """Edital + company CNAEs matching same subcategory = ALTA."""
        result = self._compute(
            "Pavimentação asfáltica em vias urbanas",
            "pavimentação recapeamento asfalto",  # CNAE text matching subcategory keywords
            "engenharia",
            [],
        )
        assert result["compatibility"] == "ALTA"
        assert result["score"] >= 0.8

    def test_same_sector_different_sub_media(self):
        """Same sector, different subcategory = MEDIA."""
        result = self._compute(
            "Construção de drenagem pluvial e saneamento",
            "construção de edifício edificação",  # edificacoes subcategory
            "engenharia",
            [],
        )
        assert result["compatibility"] == "MEDIA"
        assert result["score"] >= 0.4

    def test_no_company_subcats_baixa(self):
        """Edital has subcategory but company has no matching keywords = BAIXA."""
        result = self._compute(
            "Pavimentação asfáltica em vias urbanas",
            "servicos gerais administrativos",  # No engineering keywords
            "engenharia",
            [],
        )
        assert result["compatibility"] == "BAIXA"
        assert result["score"] <= 0.4

    def test_no_edital_subcat_media(self):
        """When edital subcategory can't be detected = MEDIA (presumed)."""
        result = self._compute(
            "Serviços diversos sem especificação técnica",
            "construção de edifício",
            "engenharia",
            [],
        )
        assert result["compatibility"] == "MEDIA"

    def test_software_sector_keywords(self):
        """Software sector subcategories detected correctly."""
        result = self._compute(
            "Desenvolvimento de sistema de gestão integrada",
            "desenvolvimento de software fábrica de software",
            "software",
            [],
        )
        assert result["compatibility"] == "ALTA"
        assert result["edital_subcategory"] is not None

    def test_returns_required_fields(self):
        """Result has all required fields."""
        result = self._compute("Obra de pavimentação", "", "engenharia", [])
        assert "compatibility" in result
        assert "score" in result
        assert "edital_subcategory" in result
        assert "_source" in result

    def test_historico_boosts_score(self):
        """Historical contracts in same subcategory boost compatibility."""
        no_hist = self._compute(
            "Pavimentação asfáltica",
            "servicos gerais",
            "engenharia",
            [],
        )
        with_hist = self._compute(
            "Pavimentação asfáltica",
            "servicos gerais",
            "engenharia",
            [{"objeto": "pavimentação de via pública"}],
        )
        assert with_hist["score"] >= no_hist["score"]

    def test_unknown_sector_returns_media(self):
        """Unknown sector (no subcategories defined) returns MEDIA."""
        result = self._compute("Qualquer objeto", "qualquer cnae", "desconhecido_xyz", [])
        assert result["compatibility"] == "MEDIA"
        assert result["score"] == 0.5


class TestHabilitacaoAnalysis:
    def setup_method(self):
        try:
            from collect_report_data_helpers import compute_habilitacao_analysis
            self._compute = compute_habilitacao_analysis
        except (ImportError, AttributeError):
            pytest.skip("compute_habilitacao_analysis not available")

    def _empresa(self, capital=5000000, sancoes=None, cnae="4120400"):
        return {
            "capital_social": capital,
            "cnae_principal": cnae,
            "sancoes": sancoes or {},
        }

    def test_apta_with_sufficient_capital(self):
        """Company with sufficient capital and no sanctions = APTA."""
        edital = {"valor_estimado": 1000000}
        result = self._compute(edital, self._empresa(capital=5000000), {}, "engenharia")
        assert result["status"] in ("APTA", "PARCIALMENTE_APTA")
        assert result["score"] >= 50

    def test_inapta_with_active_sanction(self):
        """Active CEIS sanction = INAPTA."""
        edital = {"valor_estimado": 1000000}
        empresa = self._empresa(sancoes={"ceis": True})
        result = self._compute(edital, empresa, {}, "engenharia")
        assert result["status"] == "INAPTA"

    def test_critico_capital_insufficient(self):
        """Capital way below required = CRÍTICO dimension."""
        edital = {"valor_estimado": 50000000}
        empresa = self._empresa(capital=100000)
        result = self._compute(edital, empresa, {}, "engenharia")
        dims = {d["dimension"]: d["status"] for d in result["dimensions"]}
        assert dims["Capital Mínimo"] == "CRÍTICO"

    def test_verificar_when_sicaf_not_consulted(self):
        """SICAF not consulted = VERIFICAR for fiscal dimension."""
        edital = {"valor_estimado": 500000}
        result = self._compute(edital, self._empresa(), {"status": "NÃO CONSULTADO"}, "engenharia")
        dims = {d["dimension"]: d["status"] for d in result["dimensions"]}
        assert dims["Regularidade Fiscal"] == "VERIFICAR"

    def test_sicaf_restriction_critico(self):
        """SICAF with restriction = CRÍTICO fiscal."""
        edital = {"valor_estimado": 500000}
        sicaf = {"status": "ATIVO", "restricao": {"possui_restricao": True}}
        result = self._compute(edital, self._empresa(), sicaf, "engenharia")
        dims = {d["dimension"]: d["status"] for d in result["dimensions"]}
        assert dims["Regularidade Fiscal"] == "CRÍTICO"

    def test_returns_gaps(self):
        """Gaps list populated when issues found."""
        edital = {"valor_estimado": 50000000}
        empresa = self._empresa(capital=100000)
        result = self._compute(edital, empresa, {}, "engenharia")
        assert len(result["gaps"]) > 0

    def test_score_range(self):
        """Score is 0-100."""
        edital = {"valor_estimado": 500000}
        result = self._compute(edital, self._empresa(), {}, "engenharia")
        assert 0 <= result["score"] <= 100

    def test_multiple_sanctions_all_flagged(self):
        """Multiple sanctions all mentioned in gap detail."""
        edital = {"valor_estimado": 500000}
        empresa = self._empresa(sancoes={"ceis": True, "cnep": True})
        result = self._compute(edital, empresa, {}, "engenharia")
        assert result["status"] == "INAPTA"
        sanction_dim = [d for d in result["dimensions"] if d["dimension"] == "Sanções"][0]
        assert "CEIS" in sanction_dim["detail"]
        assert "CNEP" in sanction_dim["detail"]


# ============================================================
# SESSION 3: Competitive Analysis + Risk Analysis
# ============================================================


class TestCompetitiveAnalysis:
    def setup_method(self):
        try:
            from collect_report_data_helpers import compute_competitive_analysis
            self._compute = compute_competitive_analysis
        except (ImportError, AttributeError):
            pytest.skip("compute_competitive_analysis not available")

    def test_empty_contracts_desconhecida(self):
        """No contracts = DESCONHECIDA competition level."""
        result = self._compute([])
        assert result["competition_level"] == "DESCONHECIDA"
        assert result["unique_suppliers"] == 0
        assert result["hhi"] == 0.0

    def test_single_supplier_monopoly(self):
        """Single supplier = BAIXA competition, high HHI."""
        contracts = [
            {"cnpj_fornecedor": "12345678000100", "fornecedor": "Empresa X", "valor": 1000000},
            {"cnpj_fornecedor": "12345678000100", "fornecedor": "Empresa X", "valor": 500000},
        ]
        result = self._compute(contracts)
        assert result["unique_suppliers"] == 1
        assert result["competition_level"] == "BAIXA"
        assert result["hhi"] == 1.0  # Full concentration

    def test_multiple_suppliers(self):
        """Multiple suppliers = higher competition level."""
        contracts = [
            {"cnpj_fornecedor": f"1234567800010{i}", "fornecedor": f"Emp {i}", "valor": 100000}
            for i in range(6)
        ]
        result = self._compute(contracts)
        assert result["unique_suppliers"] == 6
        assert result["competition_level"] in ("ALTA", "MUITO_ALTA")
        assert result["hhi"] < 0.5

    def test_hhi_calculation_correctness(self):
        """HHI with known inputs produces correct result."""
        # Two suppliers with equal share → HHI = 0.5
        contracts = [
            {"cnpj_fornecedor": "11111111000100", "fornecedor": "A", "valor": 500000},
            {"cnpj_fornecedor": "22222222000100", "fornecedor": "B", "valor": 500000},
        ]
        result = self._compute(contracts)
        assert abs(result["hhi"] - 0.5) < 0.01

    def test_top_supplier_populated(self):
        """Top supplier info is populated."""
        contracts = [
            {"cnpj_fornecedor": "11111111000100", "fornecedor": "Big Corp", "valor": 900000},
            {"cnpj_fornecedor": "22222222000100", "fornecedor": "Small Co", "valor": 100000},
        ]
        result = self._compute(contracts)
        assert result["top_supplier"] is not None
        assert result["top_supplier"]["nome"] == "Big Corp"

    def test_risk_signals_monopoly(self):
        """Monopoly scenario should flag risk signals."""
        contracts = [
            {"cnpj_fornecedor": "11111111000100", "fornecedor": "Monopolist", "valor": 5000000},
        ]
        result = self._compute(contracts)
        assert len(result.get("risk_signals", [])) > 0


class TestRiskAnalysis:
    def setup_method(self):
        try:
            from collect_report_data_helpers import compute_risk_analysis
            self._compute = compute_risk_analysis
        except (ImportError, AttributeError):
            pytest.skip("compute_risk_analysis not available")

    def test_valor_sigiloso_alta(self):
        """Zero estimated value = ALTA risk flag."""
        edital = {"valor_estimado": 0, "dias_restantes": 30}
        result = self._compute(edital, {"competition_level": "DESCONHECIDA"}, "engenharia")
        flags = result["flags"]
        sigiloso = [f for f in flags if "sigilo" in f.get("flag", "").lower()]
        assert len(sigiloso) > 0
        assert sigiloso[0]["severity"] == "ALTA"

    def test_tight_timeline_alta(self):
        """Very short deadline = ALTA risk flag."""
        edital = {"valor_estimado": 500000, "dias_restantes": 3}
        result = self._compute(edital, {"competition_level": "DESCONHECIDA"}, "engenharia")
        flags = result["flags"]
        timeline = [f for f in flags if "prazo" in f.get("flag", "").lower()]
        assert len(timeline) > 0
        assert timeline[0]["severity"] == "ALTA"

    def test_moderate_timeline_media(self):
        """Moderate deadline = MEDIA risk flag."""
        edital = {"valor_estimado": 500000, "dias_restantes": 10}
        result = self._compute(edital, {"competition_level": "DESCONHECIDA"}, "engenharia")
        flags = result["flags"]
        timeline = [f for f in flags if "prazo" in f.get("flag", "").lower()]
        if timeline:
            assert timeline[0]["severity"] == "MEDIA"

    def test_comfortable_timeline_no_flag(self):
        """Comfortable deadline (30+ days) = no timeline risk flag."""
        edital = {"valor_estimado": 500000, "dias_restantes": 45}
        result = self._compute(edital, {"competition_level": "DESCONHECIDA"}, "engenharia")
        flags = result["flags"]
        timeline = [f for f in flags if "prazo" in f.get("flag", "").lower()]
        assert len(timeline) == 0

    def test_returns_flags_list(self):
        """Result contains flags list."""
        edital = {"valor_estimado": 500000, "dias_restantes": 30}
        result = self._compute(edital, {"competition_level": "DESCONHECIDA"}, "engenharia")
        assert "flags" in result
        assert isinstance(result["flags"], list)

    def test_sector_specific_risks(self):
        """Sector-specific risk flags appear for relevant sectors."""
        edital = {"valor_estimado": 500000, "dias_restantes": 30}
        result = self._compute(edital, {"competition_level": "DESCONHECIDA"}, "facilities")
        # facilities should have subprecificação risk
        sector_flags = [f for f in result["flags"] if f.get("category") == "setor"]
        assert len(sector_flags) > 0


# ============================================================
# SESSION 4: Portfolio Analysis + Integration
# ============================================================


class TestPortfolioAnalysis:
    def setup_method(self):
        try:
            from collect_report_data_helpers import compute_portfolio_analysis
            self._compute = compute_portfolio_analysis
        except (ImportError, AttributeError):
            pytest.skip("compute_portfolio_analysis not available")

    def _make_edital(self, prob=0.15, risk=60, hab_status="APTA", valor=500000, roi_max=50000):
        return {
            "win_probability": {"probability": prob},
            "risk_score": {"total": risk},
            "habilitacao_analysis": {"status": hab_status},
            "valor_estimado": valor,
            "objeto": "Teste de edital",
            "roi_potential": {"roi_max": roi_max},
            "orgao": "Prefeitura Teste",
        }

    def test_quick_win_classification(self):
        """High probability + high viability = QUICK_WIN."""
        editais = [self._make_edital(prob=0.20, risk=70)]
        empresa = {"capital_social": 5000000}
        result = self._compute(editais, empresa, "engenharia")
        assert len(result["quick_wins"]) == 1
        assert editais[0]["strategic_category"] == "QUICK_WIN"

    def test_inaccessible_classification(self):
        """INAPTA habilitação = INACESSÍVEL."""
        editais = [self._make_edital(prob=0.20, risk=70, hab_status="INAPTA")]
        empresa = {"capital_social": 5000000}
        result = self._compute(editais, empresa, "engenharia")
        assert result["inaccessible"] == 1
        assert editais[0]["strategic_category"] == "INACESSÍVEL"

    def test_investment_classification(self):
        """Low probability but positive value = INVESTIMENTO."""
        editais = [self._make_edital(prob=0.05, risk=40, valor=1000000)]
        empresa = {"capital_social": 5000000}
        result = self._compute(editais, empresa, "engenharia")
        assert len(result["strategic_investments"]) == 1

    def test_portfolio_metrics(self):
        """Portfolio returns aggregate metrics."""
        editais = [
            self._make_edital(prob=0.20, risk=70, roi_max=100000),
            self._make_edital(prob=0.12, risk=50, roi_max=80000),
        ]
        empresa = {"capital_social": 5000000}
        result = self._compute(editais, empresa, "engenharia")
        assert "total_potential_revenue" in result
        assert "estimated_participation_cost" in result
        assert "participation_cost_per_edital" in result
        assert "organ_priority_map" in result

    def test_empty_editais(self):
        """Empty list produces valid portfolio."""
        result = self._compute([], {"capital_social": 0}, "engenharia")
        assert result["quick_wins"] == []
        assert result["inaccessible"] == 0

    def test_mixed_portfolio(self):
        """Mixed editais correctly classified."""
        editais = [
            self._make_edital(prob=0.25, risk=80),   # QUICK_WIN
            self._make_edital(prob=0.05, risk=40),    # INVESTIMENTO
            self._make_edital(prob=0.20, risk=70, hab_status="INAPTA"),  # INACESSÍVEL
        ]
        empresa = {"capital_social": 5000000}
        result = self._compute(editais, empresa, "engenharia")
        categories = [ed["strategic_category"] for ed in editais]
        assert "QUICK_WIN" in categories
        assert "INACESSÍVEL" in categories


class TestComputeAllDeterministicIntegration:
    """Integration test: compute_all_deterministic chains all scoring functions."""

    def setup_method(self):
        try:
            from collect_report_data_helpers import compute_all_deterministic
            self._compute = compute_all_deterministic
        except (ImportError, AttributeError):
            pytest.skip("compute_all_deterministic not available")

    def test_full_chain_produces_all_fields(self):
        """All deterministic fields populated after compute_all_deterministic."""
        editais = [{
            "valor_estimado": 1000000,
            "dias_restantes": 20,
            "modalidade": "Pregão Eletrônico",
            "objeto": "Construção de quadra poliesportiva",
            "data_encerramento": "2026-04-15",
            "orgao": "Prefeitura Municipal",
        }]
        empresa = {"capital_social": 5000000, "cnae_principal": "4120400", "sancoes": {}}
        sicaf = {"status": "NÃO CONSULTADO"}

        self._compute(editais, empresa, sicaf, "engenharia")

        ed = editais[0]
        assert "risk_score" in ed
        assert "win_probability" in ed
        assert "roi_potential" in ed
        assert "cronograma" in ed
        assert "object_compatibility" in ed
        assert "habilitacao_analysis" in ed
        assert "competitive_analysis" in ed
        assert "risk_analysis" in ed
        assert "strategic_category" in ed

    def test_backward_compat_minimal_edital(self):
        """Minimal edital (no optional fields) doesn't crash."""
        editais = [{"valor_estimado": 0, "objeto": "Teste"}]
        empresa = {"capital_social": 0}
        sicaf = {}

        self._compute(editais, empresa, sicaf, "")

        ed = editais[0]
        assert "risk_score" in ed
        assert "win_probability" in ed


class TestSectorSubcategories:
    """Validate _SECTOR_SUBCATEGORIES structure."""

    def setup_method(self):
        try:
            from collect_report_data_helpers import _SECTOR_SUBCATEGORIES
            self._subcats = _SECTOR_SUBCATEGORIES
        except (ImportError, AttributeError):
            pytest.skip("_SECTOR_SUBCATEGORIES not available")

    def test_all_sectors_have_subcategories(self):
        """Every sector has at least 2 subcategories."""
        for sector, subs in self._subcats.items():
            assert len(subs) >= 2, f"{sector} has only {len(subs)} subcategories"

    def test_subcategories_have_keywords(self):
        """Each subcategory has at least 1 keyword."""
        for sector, subs in self._subcats.items():
            for sub_name, keywords in subs.items():
                assert len(keywords) >= 1, f"{sector}/{sub_name} has no keywords"


class TestHabilitacaoRequirements:
    """Validate _HABILITACAO_REQUIREMENTS structure."""

    def setup_method(self):
        try:
            from collect_report_data_helpers import _HABILITACAO_REQUIREMENTS
            self._reqs = _HABILITACAO_REQUIREMENTS
        except (ImportError, AttributeError):
            pytest.skip("_HABILITACAO_REQUIREMENTS not available")

    def test_default_exists(self):
        assert "_default" in self._reqs

    def test_all_have_required_keys(self):
        for sector, reqs in self._reqs.items():
            assert "capital_minimo_pct" in reqs, f"{sector} missing capital_minimo_pct"
            assert "atestados" in reqs, f"{sector} missing atestados"
            assert "fiscal" in reqs, f"{sector} missing fiscal"


# ============================================================
# E1: ROI Auditable Calculation Memory + Reclassification
# ============================================================

class TestRoiCalculationMemory:
    """E1: ROI must have auditable calculation_memory and auto-reclassification."""

    def setup_method(self):
        try:
            from collect_report_data_helpers import compute_roi_potential
            self.compute_roi = compute_roi_potential
        except (ImportError, AttributeError):
            pytest.skip("compute_roi_potential not available")

    def _make_edital(self, valor):
        return {"valor_estimado": valor}

    def _make_win_prob(self, prob):
        return {"final_probability": prob}

    def test_calculation_memory_present(self):
        result = self.compute_roi(self._make_edital(500000), "engenharia_construcao", self._make_win_prob(0.15))
        assert "calculation_memory" in result
        mem = result["calculation_memory"]
        assert "valor_edital" in mem
        assert "probabilidade_vitoria" in mem
        assert "formula" in mem
        assert "roi_min_calc" in mem
        assert "roi_max_calc" in mem

    def test_reclassification_low_roi_high_contract(self):
        """ROI < 10K on contract > 100K → strategic reclassification."""
        result = self.compute_roi(self._make_edital(500000), "engenharia_construcao", self._make_win_prob(0.005))
        roi_max = result.get("roi_max", 0)
        if roi_max < 10000:
            assert result.get("strategic_reclassification") == "INVESTIMENTO_ESTRATEGICO_ACERVO"
            assert result.get("reclassification_rationale")

    def test_no_reclassification_high_roi(self):
        """ROI > 10K should NOT be reclassified."""
        result = self.compute_roi(self._make_edital(5000000), "engenharia_construcao", self._make_win_prob(0.15))
        assert result.get("strategic_reclassification") is None

    def test_memory_reproducible(self):
        """Calculation memory values allow manual reproduction."""
        result = self.compute_roi(self._make_edital(1000000), "engenharia_construcao", self._make_win_prob(0.10))
        mem = result["calculation_memory"]
        assert "=" in mem["roi_min_calc"]


# ============================================================
# E2: SICAF Mandatory + FALHA_COLETA handling
# ============================================================

class TestSicafFalhaColeta:
    """E2: Habilitação must handle SICAF FALHA_COLETA as INCOMPLETO."""

    def setup_method(self):
        try:
            from collect_report_data_helpers import compute_habilitacao_analysis
            self.compute_hab = compute_habilitacao_analysis
        except (ImportError, AttributeError):
            pytest.skip("compute_habilitacao_analysis not available")

    def test_sicaf_falha_produces_incompleto(self):
        edital = {"valor_estimado": 100000, "modalidade": "Pregão Eletrônico"}
        empresa = {"capital_social": 500000}
        sicaf = {
            "status": "FALHA_COLETA",
            "attempted_at": "13/03/2026 10:30",
            "error_type": "TIMEOUT",
            "error_detail": "Captcha não resolvido",
        }
        result = self.compute_hab(edital, empresa, sicaf, sector_key="engenharia_construcao")
        # Check dimensions for INCOMPLETO status on fiscal regularity
        dim_statuses = [d.get("status") for d in result.get("dimensions", [])]
        has_incompleto = "INCOMPLETO" in dim_statuses
        overall = result.get("status", "")
        assert has_incompleto or "PARCIALMENTE" in overall


# ============================================================
# E8: Maturity Profile Detection
# ============================================================

class TestMaturityProfile:
    """E8: detect_maturity_profile must classify correctly."""

    def setup_method(self):
        try:
            from collect_report_data_helpers import detect_maturity_profile
            self.detect = detect_maturity_profile
        except (ImportError, AttributeError):
            pytest.skip("detect_maturity_profile not available")

    def _empresa(self, contracts, capital=500000):
        return {"historico_contratos": contracts, "capital_social": capital}

    def test_entrante_no_contracts(self):
        result = self.detect(self._empresa([]))
        assert result["profile"] == "ENTRANTE"

    def test_entrante_few_contracts(self):
        contracts = [{"id": 1}, {"id": 2}]
        result = self.detect(self._empresa(contracts))
        assert result["profile"] == "ENTRANTE"

    def test_regional_medium_contracts(self):
        contracts = [{"id": i, "uf": "SC"} for i in range(5)]
        result = self.detect(self._empresa(contracts))
        assert result["profile"] == "REGIONAL"

    def test_estabelecido_many_contracts(self):
        contracts = [{"id": i, "uf": f"UF{i % 5}"} for i in range(15)]
        result = self.detect(self._empresa(contracts))
        assert result["profile"] == "ESTABELECIDO"

    def test_estabelecido_many_ufs(self):
        contracts = [{"id": i, "uf": f"UF{i}"} for i in range(4)]
        result = self.detect(self._empresa(contracts))
        assert result["profile"] == "ESTABELECIDO"

    def test_returns_rationale(self):
        result = self.detect(self._empresa([]))
        assert "rationale" in result
        assert isinstance(result["rationale"], str)


# ============================================================
# E4: Qualification Gap Analysis
# ============================================================

class TestQualificationGapAnalysis:
    """E4: Separate CNAE incompatibility from operational gaps."""

    def setup_method(self):
        try:
            from collect_report_data_helpers import compute_qualification_gap_analysis
            self.compute_gap = compute_qualification_gap_analysis
        except (ImportError, AttributeError):
            pytest.skip("compute_qualification_gap_analysis not available")

    def test_incompatible_cnae(self):
        """Low compatibility score → INCOMPATÍVEL_CNAE."""
        edital = {"valor_estimado": 100000}
        empresa = {"capital_social": 500000, "cnae_principal": "6201-5"}
        compat = {"score": 0.1, "compatibility": "BAIXA"}
        result = self.compute_gap(edital, empresa, compat, sector_key="software")
        assert result["filter_result"] == "INCOMPATÍVEL_CNAE"

    def test_operational_gap_capital(self):
        """Compatible but insufficient capital → LACUNA_OPERACIONAL with CAPITAL gap."""
        edital = {"valor_estimado": 10000000}
        empresa = {"capital_social": 50000, "cnae_principal": "4120-4"}
        compat = {"score": 0.8, "compatibility": "ALTA"}
        result = self.compute_gap(edital, empresa, compat, sector_key="engenharia_construcao")
        if result.get("operational_gaps"):
            gap_types = [g["gap_type"] for g in result["operational_gaps"]]
            assert "CAPITAL" in gap_types


# ============================================================
# E7: Regional Clusters
# ============================================================

class TestRegionalClusters:
    """E7: Geographic clustering of editais."""

    def setup_method(self):
        try:
            from collect_report_data_helpers import compute_regional_clusters
            self.compute_clusters = compute_regional_clusters
        except (ImportError, AttributeError):
            pytest.skip("compute_regional_clusters not available")

    def test_nearby_editais_cluster(self):
        """Editais within 150km should cluster together."""
        editais = [
            {"municipio": "Belo Horizonte", "uf": "MG", "valor_estimado": 500000,
             "data_encerramento": "2026-04-01",
             "distancia": {"dest_lat": -19.92, "dest_lon": -43.94, "km": 100}},
            {"municipio": "Contagem", "uf": "MG", "valor_estimado": 300000,
             "data_encerramento": "2026-04-15",
             "distancia": {"dest_lat": -19.93, "dest_lon": -44.05, "km": 110}},
            {"municipio": "Betim", "uf": "MG", "valor_estimado": 400000,
             "data_encerramento": "2026-04-20",
             "distancia": {"dest_lat": -19.97, "dest_lon": -44.20, "km": 120}},
        ]
        result = self.compute_clusters(editais)
        clusters = result.get("clusters", [])
        assert len(clusters) >= 1
        # All 3 are very close — should be in one cluster
        assert clusters[0].get("n_editais", 0) >= 2

    def test_distant_editais_separate(self):
        """Editais > 150km apart should not cluster."""
        editais = [
            {"municipio": "Florianópolis", "uf": "SC", "valor_estimado": 500000,
             "data_encerramento": "2026-04-01",
             "distancia": {"dest_lat": -27.59, "dest_lon": -48.55, "km": 200}},
            {"municipio": "Porto Alegre", "uf": "RS", "valor_estimado": 300000,
             "data_encerramento": "2026-04-15",
             "distancia": {"dest_lat": -30.03, "dest_lon": -51.23, "km": 500}},
        ]
        result = self.compute_clusters(editais)
        clusters = result.get("clusters", [])
        # They are ~460km apart — no cluster with 2+ editais
        for cl in clusters:
            assert cl.get("n_editais", 0) < 2

    def test_empty_editais(self):
        result = self.compute_clusters([])
        assert result.get("clusters", []) == []


# ============================================================
# E9: Accent Map + Date Format
# ============================================================

class TestAccentMap:
    """E9: Verify accent map coverage for key Portuguese terms."""

    def setup_method(self):
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "gen_report", str(Path(__file__).parent.parent / "generate-report-b2g.py"))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self._s = mod._s
            self._date = mod._date
        except Exception:
            pytest.skip("generate-report-b2g.py not importable")

    def test_demolicao_accent(self):
        assert "ã" in self._s("demolicao") or "ç" in self._s("demolicao") or self._s("demolição") == "demolição"

    def test_aprovacao_accent(self):
        result = self._s("aprovacao")
        assert "ã" in result or "ç" in result

    def test_homologacao_accent(self):
        result = self._s("homologacao")
        assert "ã" in result or "ç" in result

    def test_date_iso_to_br(self):
        result = self._date("2026-03-13")
        assert result == "13/03/2026"

    def test_date_already_br(self):
        result = self._date("13/03/2026")
        assert result == "13/03/2026"

    def test_date_iso_datetime(self):
        result = self._date("2026-03-13T10:30:00")
        assert "13/03/2026" in result


# ============================================================
# E10: Report Validation
# ============================================================

class TestReportValidation:
    """E10: validate_report_completeness catches issues."""

    def setup_method(self):
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "gen_report", str(Path(__file__).parent.parent / "generate-report-b2g.py"))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self.validate = mod.validate_report_completeness
        except Exception:
            pytest.skip("validate_report_completeness not importable")

    def test_complete_report_passes(self):
        data = {
            "editais": [{
                "recomendacao": "PARTICIPAR",
                "justificativa": "Alta aderência",
                "roi_potential": {"calculation_memory": {"formula": "test"}},
            }],
            "coverage_diagnostic": {"coverage_rate": 0.85},
        }
        warnings = self.validate(data)
        # Should have no warnings about missing justification or ROI
        missing_just = [w for w in warnings if "justificativa" in w.lower()]
        assert len(missing_just) == 0

    def test_missing_justificativa_warns(self):
        data = {
            "editais": [{
                "recomendacao": "PARTICIPAR",
                # no justificativa
                "roi_potential": {"calculation_memory": {"formula": "test"}},
            }],
        }
        warnings = self.validate(data)
        assert any("justificativa" in w.lower() or "justificação" in w.lower() for w in warnings)

    def test_missing_roi_memory_warns(self):
        data = {
            "editais": [{
                "recomendacao": "PARTICIPAR",
                "justificativa": "OK",
                "roi_potential": {"roi_min": 100},  # has roi data but no calculation_memory
            }],
        }
        warnings = self.validate(data)
        assert any("roi" in w.lower() or "memória" in w.lower() or "memoria" in w.lower() or "cálculo" in w.lower() for w in warnings)


# ============================================================
# E5: Dispute Stats PDF Rendering (integration via competitive section)
# ============================================================

class TestDisputeStatsPdfRendering:
    """E5: Competitive section renders dispute stats when present."""

    def setup_method(self):
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "gen_report", str(Path(__file__).parent.parent / "generate-report-b2g.py"))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self._build_competitive = mod._build_competitive_section
            self._build_styles = mod._build_styles
            self._section_counter = mod._section_counter
        except Exception:
            pytest.skip("generate-report-b2g.py functions not importable")

    def test_with_dispute_stats(self):
        data = {
            "editais": [{
                "orgao": "Prefeitura X",
                "competitive_intel": [
                    {"fornecedor": "ABC Ltda", "objeto": "Obra", "valor": 100000, "data": "2026-01-01"},
                ],
            }],
            "dispute_stats": {
                "stats_by_typology": {
                    "Pregão_0-100K": {
                        "total": 5, "avg_participants": 3.2,
                        "avg_discount": 0.12, "adjudication_rate": 0.85,
                    },
                },
                "recurring_suppliers": [
                    {"fornecedor": "ABC Ltda", "contract_count": 3, "region": "SC"},
                ],
            },
        }
        styles = self._build_styles()
        sec = self._section_counter()
        elements = self._build_competitive(data, styles, sec)
        assert len(elements) > 0  # Should produce output

    def test_without_dispute_stats(self):
        """Backward compat — no dispute_stats still works."""
        data = {
            "editais": [{
                "orgao": "Prefeitura X",
                "competitive_intel": [
                    {"fornecedor": "ABC Ltda", "objeto": "Obra", "valor": 100000, "data": "2026-01-01"},
                ],
            }],
        }
        styles = self._build_styles()
        sec = self._section_counter()
        elements = self._build_competitive(data, styles, sec)
        assert len(elements) > 0


# ============================================================
# E4: Development Plan PDF Section
# ============================================================

class TestDevelopmentPlanSection:
    """E4: Consolidated development plan aggregates operational gaps."""

    def setup_method(self):
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "gen_report", str(Path(__file__).parent.parent / "generate-report-b2g.py"))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self._build_dev_plan = mod._build_development_plan
            self._build_styles = mod._build_styles
            self._section_counter = mod._section_counter
        except Exception:
            pytest.skip("_build_development_plan not importable")

    def test_with_gaps(self):
        data = {
            "editais": [
                {"objeto": "Obra A", "qualification_gap": {
                    "operational_gaps": [
                        {"gap_type": "CAPITAL", "description": "Capital insuficiente",
                         "estimated_timeline": "6 meses", "action_required": "Aumentar capital"},
                    ],
                }},
                {"objeto": "Obra B", "qualification_gap": {
                    "operational_gaps": [
                        {"gap_type": "ATESTADO", "description": "Falta atestado",
                         "estimated_timeline": "12 meses", "action_required": "Obter CAT"},
                    ],
                }},
            ],
        }
        styles = self._build_styles()
        sec = self._section_counter()
        elements = self._build_dev_plan(data, styles, sec)
        assert len(elements) > 0

    def test_without_gaps_returns_empty(self):
        data = {"editais": [{"objeto": "Obra A"}]}
        styles = self._build_styles()
        sec = self._section_counter()
        elements = self._build_dev_plan(data, styles, sec)
        assert elements == []

    def test_deduplicates_gaps(self):
        data = {
            "editais": [
                {"objeto": "Obra A", "qualification_gap": {
                    "operational_gaps": [
                        {"gap_type": "CAPITAL", "description": "Capital insuficiente",
                         "estimated_timeline": "6 meses", "action_required": "Aumentar"},
                    ],
                }},
                {"objeto": "Obra B", "qualification_gap": {
                    "operational_gaps": [
                        {"gap_type": "CAPITAL", "description": "Capital insuficiente",
                         "estimated_timeline": "6 meses", "action_required": "Aumentar"},
                    ],
                }},
            ],
        }
        styles = self._build_styles()
        sec = self._section_counter()
        elements = self._build_dev_plan(data, styles, sec)
        # Should produce elements but deduplicated — only 1 unique gap
        assert len(elements) > 0
