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
        warnings = self._validate(minimal_data)
        assert len(warnings) == 0

    def test_missing_empresa(self):
        warnings = self._validate({"editais": []})
        assert any("empresa" in w for w in warnings)

    def test_missing_cnpj(self):
        warnings = self._validate({"empresa": {"razao_social": "X"}, "editais": []})
        assert any("cnpj" in w for w in warnings)

    def test_missing_objeto(self):
        data = {
            "empresa": {"cnpj": "123", "razao_social": "X"},
            "editais": [{"orgao": "Pref X"}],
        }
        warnings = self._validate(data)
        assert any("objeto" in w for w in warnings)


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

    def test_pdf_encerrado_status(self, minimal_data):
        """ENCERRADO editais don't crash PDF generation."""
        minimal_data["editais"][0]["data_encerramento"] = "2026-01-01"
        minimal_data["editais"][0]["dias_restantes"] = -70
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
        """Every data JSON in docs/reports/ can generate a PDF without crashing."""
        from generate_report_b2g_helpers import generate_report_b2g
        files = list(self.DATA_DIR.glob("data-*.json"))
        if not files:
            pytest.skip("No data files found")
        for p in files:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            buf = generate_report_b2g(d)
            content = buf.read()
            assert content[:5] == b"%PDF-", f"Failed for {p.name}"
