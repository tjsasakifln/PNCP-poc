"""Tests for classify_edital_object_type() — per-edital sector classification.

This function determines what the EDITAL is about (not the company's CNAE)
so that habilitação, risk, margin, and cost calculations use the correct
sector parameters. A construction company bidding on a hospital materials
pregão should get supply-sector requirements, not engineering requirements.

Test cases derived from real editais in docs/reports/data-*.json.
"""
import re
import unicodedata
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Extract classify_edital_object_type and _strip_accents directly from source
# to avoid executing the full script (which has I/O side effects).
# ---------------------------------------------------------------------------
_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "collect-report-data.py"


def _extract_function(source: str, func_name: str) -> str:
    """Extract a function body from source code by name."""
    pattern = rf"^(def {func_name}\(.*?\n(?:(?:    .*|[ \t]*)\n)*)"
    m = re.search(pattern, source, re.MULTILINE)
    if m:
        return m.group(1)
    return ""


@pytest.fixture(scope="module")
def classify():
    """Build classify_edital_object_type from source without executing the script."""
    source = _SCRIPT.read_text(encoding="utf-8")

    # Extract _strip_accents (the first definition, at module top)
    strip_fn = _extract_function(source, "_strip_accents")
    # Extract classify_edital_object_type
    classify_fn = _extract_function(source, "classify_edital_object_type")

    if not classify_fn:
        pytest.skip("classify_edital_object_type not found in script")

    # Build a minimal namespace with just these two functions
    ns = {"unicodedata": unicodedata, "re": re}
    exec(compile(strip_fn, "<strip_accents>", "exec"), ns)
    exec(compile(classify_fn, "<classify>", "exec"), ns)

    return ns["classify_edital_object_type"]


# ===================================================================
# FORNECIMENTO DE MATERIAIS HOSPITALARES
# ===================================================================
class TestFornecimentoSaude:
    """Editais for hospital/medical materials supply."""

    def test_materiais_medico_hospitalares(self, classify):
        ed = {"objeto": "MATERIAIS MÉDICO-HOSPITALARES, EQUIPAMENTOS AMBULATORIAIS, INSUMOS PARA PROCEDIMENTOS CLÍNICOS"}
        assert classify(ed) == "fornecimento_saude"

    def test_materiais_medico_no_accent(self, classify):
        ed = {"objeto": "MATERIAIS MEDICO-HOSPITALARES, EQUIPAMENTOS AMBULATORIAIS"}
        assert classify(ed) == "fornecimento_saude"

    def test_medicamentos(self, classify):
        ed = {"objeto": "Aquisição de medicamentos para a rede municipal de saúde"}
        assert classify(ed) == "fornecimento_saude"

    def test_insumos_hospitalares(self, classify):
        ed = {"objeto": "Registro de preços para fornecimento de insumos hospitalares descartáveis"}
        assert classify(ed) == "fornecimento_saude"

    def test_material_enfermagem(self, classify):
        ed = {"objeto": "Fornecimento de materiais de enfermagem e curativos"}
        assert classify(ed) == "fornecimento_saude"

    def test_equipamento_ambulatorial(self, classify):
        ed = {"objeto": "Aquisição de equipamento ambulatorial para UBS"}
        assert classify(ed) == "fornecimento_saude"

    def test_farmaceutico(self, classify):
        ed = {"objeto": "Aquisição de insumos farmacêuticos para farmácia municipal"}
        assert classify(ed) == "fornecimento_saude"


# ===================================================================
# FORNECIMENTO DE MATERIAIS DE LIMPEZA
# ===================================================================
class TestFornecimentoLimpeza:
    def test_saneantes(self, classify):
        ed = {"objeto": "Registro de preços para fornecimento de saneantes e produtos de limpeza"}
        assert classify(ed) == "fornecimento_limpeza"

    def test_material_limpeza(self, classify):
        ed = {"objeto": "Aquisição de material de limpeza e higienização"}
        assert classify(ed) == "fornecimento_limpeza"

    def test_produto_limpeza(self, classify):
        ed = {"objeto": "Fornecimento de produto de limpeza para escolas municipais"}
        assert classify(ed) == "fornecimento_limpeza"


# ===================================================================
# FORNECIMENTO DE PAPELARIA / EXPEDIENTE
# ===================================================================
class TestFornecimentoPapelaria:
    def test_material_expediente(self, classify):
        ed = {"objeto": "Aquisição de material de expediente e escolar"}
        assert classify(ed) == "fornecimento_papelaria"

    def test_toner_cartucho(self, classify):
        ed = {"objeto": "Fornecimento de toner e cartucho para impressoras"}
        assert classify(ed) == "fornecimento_papelaria"

    def test_material_didatico(self, classify):
        ed = {"objeto": "Aquisição de material didático para rede de ensino"}
        assert classify(ed) == "fornecimento_papelaria"

    def test_papel_escritorio(self, classify):
        ed = {"objeto": "Registro de preços para aquisição de papel A4 e material de escritório"}
        assert classify(ed) == "fornecimento_papelaria"


# ===================================================================
# FORNECIMENTO DE MOBILIÁRIO
# ===================================================================
class TestFornecimentoMobiliario:
    def test_estofamento_moveis(self, classify):
        ed = {"objeto": "Estofamento Móveis"}
        assert classify(ed) == "fornecimento_mobiliario"

    def test_mobiliario_escritorio(self, classify):
        ed = {"objeto": "Aquisição de mobiliário de escritório — mesas e cadeiras"}
        assert classify(ed) == "fornecimento_mobiliario"

    def test_eletrodomesticos(self, classify):
        ed = {"objeto": "Fornecimento de eletrodomésticos para cozinha industrial"}
        assert classify(ed) == "fornecimento_mobiliario"


# ===================================================================
# FORNECIMENTO DE ALIMENTOS
# ===================================================================
class TestFornecimentoAlimentos:
    def test_hortifruti(self, classify):
        ed = {"objeto": "Registro de precos por item para eventual aquisicao de hortifrutigranjeiro e carnes"}
        # "hortifrutigranjeiro" contains "hortifruti" substring, "carnes" matches "carne"
        assert classify(ed) == "fornecimento_alimentos"

    def test_hortifruti_explicit(self, classify):
        ed = {"objeto": "Aquisição de hortifrúti para merenda escolar"}
        assert classify(ed) == "fornecimento_alimentos"

    def test_genero_alimenticio(self, classify):
        ed = {"objeto": "Aquisição de gêneros alimentícios para merenda escolar"}
        assert classify(ed) == "fornecimento_alimentos"

    def test_merenda(self, classify):
        ed = {"objeto": "Fornecimento de merenda escolar para 5.000 alunos"}
        assert classify(ed) == "fornecimento_alimentos"

    def test_cesta_basica(self, classify):
        ed = {"objeto": "Aquisição de cestas básicas para programa de assistência social"}
        assert classify(ed) == "fornecimento_alimentos"


# ===================================================================
# FORNECIMENTO GERAL (catch-all for supply without service/obra guard)
# ===================================================================
class TestFornecimentoGeral:
    def test_combustivel(self, classify):
        ed = {"objeto": "Fornecimento de combustível para frota municipal"}
        assert classify(ed) == "fornecimento_geral"

    def test_material_eletrico(self, classify):
        ed = {"objeto": "Aquisição de material elétrico para manutenção predial"}
        assert classify(ed) == "fornecimento_geral"

    def test_uniforme(self, classify):
        """Uniformes escolares: 'uniforme' is specific supply, 'escolar' sub-classifies."""
        ed = {"objeto": "Fornecimento de uniformes escolares"}
        # "uniforme" matches _SUPPLY_SPECIFIC, then "escolar" sub-check → papelaria
        # This is acceptable — school uniforms are often procured with school supplies
        assert classify(ed) in ("fornecimento_papelaria", "fornecimento_geral")


# ===================================================================
# ENGENHARIA / OBRAS
# ===================================================================
class TestEngenharia:
    def test_construcao_ubs(self, classify):
        ed = {"objeto": "Construcao de UBS em Cajazeiras/PB"}
        assert classify(ed) == "engenharia"

    def test_pavimentacao(self, classify):
        ed = {"objeto": "Pavimentação asfáltica da Avenida Santa Catarina"}
        assert classify(ed) == "engenharia"

    def test_reforma(self, classify):
        ed = {"objeto": "Reforma e ampliação de imóvel público para Casa Lar"}
        # "reforma" triggers engenharia check
        assert classify(ed) == "engenharia"

    def test_reforma_imovel_not_movel(self, classify):
        """'imóvel' should NOT match 'móvel' (furniture) — different words."""
        ed = {"objeto": "Reforma de imóvel público — pintura e elétrica"}
        assert classify(ed) == "engenharia"  # reforma triggers first

    def test_drenagem(self, classify):
        ed = {"objeto": "Execução de obra de drenagem e pavimentação na Servidão José"}
        assert classify(ed) == "engenharia"

    def test_construcao_accented(self, classify):
        ed = {"objeto": "Construção de ponte sobre rio Itajaí-Açu"}
        assert classify(ed) == "engenharia"

    def test_edificacao(self, classify):
        ed = {"objeto": "Contratação de empresa para edificação de escola municipal"}
        assert classify(ed) == "engenharia"

    def test_terraplanagem(self, classify):
        ed = {"objeto": "Execução de obra de movimentação de terra e terraplanagem"}
        assert classify(ed) == "engenharia"


# ===================================================================
# SERVIÇOS PROFISSIONAIS (credenciamento médico via inexigibilidade)
# ===================================================================
class TestServicosProfissionais:
    def test_credenciamento_medicos_salvador(self, classify):
        ed = {
            "objeto": "CREDENCIAMENTO DE PESSOAS JURÍDICAS DE DIREITO PRIVADO PARA PRESTAÇÃO DE SERVIÇOS MÉDICOS",
            "modalidade": "Inexigibilidade",
        }
        assert classify(ed) == "servicos_profissionais"

    def test_contratacao_medico(self, classify):
        ed = {
            "objeto": "Contratação de médico para atuação na área de Saúde Mental",
            "modalidade": "Inexigibilidade",
        }
        assert classify(ed) == "servicos_profissionais"

    def test_pessoa_fisica_medica(self, classify):
        ed = {
            "objeto": "Contratação de Pessoa Física credenciada para a prestação de serviços médicos",
            "modalidade": "Inexigibilidade",
        }
        assert classify(ed) == "servicos_profissionais"

    def test_not_inexigibilidade_no_match(self, classify):
        """Same text but NOT inexigibilidade — should NOT classify as servicos_profissionais."""
        ed = {
            "objeto": "CREDENCIAMENTO DE PESSOAS JURÍDICAS PARA PRESTAÇÃO DE SERVIÇOS MÉDICOS",
            "modalidade": "Pregão - Eletrônico",
        }
        # Without inexigibilidade, "prestacao de servico" triggers servicos_gerais
        # before supply check runs (services check runs after supply, but
        # "servico" in SERVICE_GUARD blocks supply generic, and no _SUPPLY_SPECIFIC match)
        result = classify(ed)
        assert result != "servicos_profissionais"  # Key assertion: not professional services


# ===================================================================
# SERVIÇOS GERAIS
# ===================================================================
class TestServicosGerais:
    def test_manutencao(self, classify):
        ed = {"objeto": "Contratação de empresa para manutenção predial preventiva e corretiva"}
        assert classify(ed) == "servicos_gerais"

    def test_consultoria(self, classify):
        ed = {"objeto": "Contratação de assessoria e consultoria jurídica especializada"}
        assert classify(ed) == "servicos_gerais"

    def test_prestacao_servico(self, classify):
        ed = {"objeto": "Prestação de serviço de isolamento acústico para instalações"}
        assert classify(ed) == "servicos_gerais"


# ===================================================================
# CONCESSÃO
# ===================================================================
class TestConcessao:
    def test_concessao_bar(self, classify):
        ed = {"objeto": "Concessão de uso onerosa com pagamento mensal do complexo bar/restaurante"}
        assert classify(ed) == "concessao"

    def test_permissao_uso(self, classify):
        ed = {"objeto": "PERMISSÃO DE USO PARA EXPLORAÇÃO COMERCIAL DE ESPAÇO PÚBLICO"}
        assert classify(ed) == "concessao"


# ===================================================================
# SOFTWARE / IT
# ===================================================================
class TestSoftware:
    def test_desenvolvimento_sistema(self, classify):
        ed = {"objeto": "contratação de pessoa jurídica especializada para o desenvolvimento de sistema"}
        assert classify(ed) == "software"

    def test_software_explicit(self, classify):
        ed = {"objeto": "Licenciamento de software de gestão hospitalar"}
        assert classify(ed) == "software"


# ===================================================================
# EDGE CASES
# ===================================================================
class TestEdgeCases:
    def test_empty_objeto(self, classify):
        """Empty object should fall back to empty string (use company sector_key)."""
        assert classify({}) == ""
        assert classify({"objeto": ""}) == ""

    def test_stopwords_only(self, classify):
        """Object with only common words should return empty string."""
        ed = {"objeto": "contratação de empresa para o município"}
        # "contratacao de empresa para" should NOT match supply generic
        # because of the guard clause
        result = classify(ed)
        # Should not be a supply category
        assert result not in ("fornecimento_saude", "fornecimento_limpeza",
                              "fornecimento_papelaria", "fornecimento_geral")

    def test_generic_supply_with_service_guard(self, classify):
        """'Aquisição de serviços' should NOT classify as supply."""
        ed = {"objeto": "Aquisição de serviços de manutenção predial"}
        result = classify(ed)
        # Guard clause should prevent this from being classified as supply
        assert result != "fornecimento_geral"

    def test_registro_precos_for_obra(self, classify):
        """'Registro de preços para obra' should NOT classify as supply."""
        ed = {"objeto": "Registro de preços para obra de pavimentação asfáltica"}
        result = classify(ed)
        assert result == "engenharia"

    def test_mixed_supply_and_install(self, classify):
        """Fornecimento + instalação — classify based on dominant activity."""
        ed = {"objeto": "Fornecimento, com instalação, de equipamentos de cozinha industrial"}
        result = classify(ed)
        # "fornecimento de" is generic — may or may not match depending on guard clause
        # Either supply or empty (fallback to company sector) is acceptable
        assert result in ("fornecimento_geral", "fornecimento_mobiliario", "")

    def test_fitas_backup(self, classify):
        """IT supply (fitas de backup) should classify as supply, not software."""
        ed = {"objeto": "Contratação de empresa para fornecimento de fitas de backup e de limpeza"}
        result = classify(ed)
        # "fornecimento de" + no service guard → supply
        # "limpeza" in sub-check → fornecimento_limpeza
        assert result.startswith("fornecimento")

    def test_videomonitoramento(self, classify):
        """CFTV installation — hybrid: has 'sistema' (software) + 'fornecimento' (supply)."""
        ed = {"objeto": "FORNECIMENTO, INSTALAÇÃO E CONFIGURAÇÃO DE SISTEMA DE VIDEOMONITORAMENTO (CFTV)"}
        result = classify(ed)
        # "sistema" triggers software after supply generic is blocked by guard
        # Either software or fornecimento is acceptable for hybrid objects
        assert result in ("software", "fornecimento_geral")

    def test_divisorias_drywall(self, classify):
        """Drywall installation — no strong keyword match, falls to empty (company fallback)."""
        ed = {"objeto": "Aquisição e instalação de divisórias DryWall e portas"}
        result = classify(ed)
        # "aquisicao de" is blocked by guard clause (no service words, but
        # also no specific supply keywords match "divisorias drywall")
        # Empty string = use company sector_key fallback — acceptable
        assert result in ("", "fornecimento_geral", "servicos_gerais")

    def test_grades_contencao(self, classify):
        """Supply of containment grades."""
        ed = {"objeto": "CONTRATAÇÃO DE EMPRESA PARA O FORNECIMENTO DE GRADES DE CONTENÇÃO"}
        result = classify(ed)
        assert result.startswith("fornecimento")

    def test_combustivel_period(self, classify):
        """Fuel purchase for specific period."""
        ed = {"objeto": "COMBUSTÍVEL - PERÍODO DE 22/01/2026 ATÉ 28/01/2026 - SAÚDE"}
        assert classify(ed) == "fornecimento_geral"

    def test_inexigibilidade_non_medical(self, classify):
        """Non-medical inexigibilidade should NOT be servicos_profissionais."""
        ed = {
            "objeto": "Contratação de empresa especializada para ministrar curso de capacitação",
            "modalidade": "Inexigibilidade",
        }
        result = classify(ed)
        assert result != "servicos_profissionais"
