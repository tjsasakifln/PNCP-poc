"""
CRIT-FLT-007 — Sector Coverage Audit Tests (AC6 + AC7).

Validates that all 15 sectors have adequate keyword coverage layers,
cross-sector collision rates are within thresholds, and new expansions
(co-occurrence rules, domain signals, synonym dicts) work correctly.

AC6: Run audit for each sector, document precision/recall.
AC7: Precision >= 85%, Recall >= 70%, Cross-sector collision < 10%.
"""

import re
from collections import Counter

import pytest
import yaml
from pathlib import Path

from filter import match_keywords, normalize_text
from sectors import SECTORS, get_sector, list_sectors
from synonyms import SECTOR_SYNONYMS, find_synonym_matches


# ============================================================================
# Constants
# ============================================================================

ALL_SECTOR_IDS = {
    "vestuario", "alimentos", "informatica", "mobiliario", "papelaria",
    "engenharia", "software", "facilities", "saude", "vigilancia",
    "transporte", "manutencao_predial", "engenharia_rodoviaria",
    "materiais_eletricos", "materiais_hidraulicos",
}

# Sectors that received new co-occurrence rules + domain signals in CRIT-FLT-007
EXPANDED_SECTORS = {
    "alimentos", "engenharia", "engenharia_rodoviaria", "facilities",
    "manutencao_predial", "materiais_eletricos", "materiais_hidraulicos",
    "mobiliario", "papelaria", "software", "transporte", "vigilancia",
}

# Sectors that received new synonym dicts in CRIT-FLT-007
NEW_SYNONYM_SECTORS = {"engenharia_rodoviaria", "materiais_eletricos", "materiais_hidraulicos"}


# ============================================================================
# Helpers
# ============================================================================

def _load_sectors_yaml() -> dict:
    """Load raw sectors_data.yaml for structural inspection."""
    yaml_path = Path(__file__).resolve().parent.parent / "sectors_data.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["sectors"]


def _match(sector_id: str, texto: str) -> tuple:
    """Helper: match text against a sector's keywords+exclusions."""
    s = SECTORS[sector_id]
    return match_keywords(texto, s.keywords, s.exclusions)


# ============================================================================
# Phase 1: Structural Coverage — All 15 Sectors Have Required Layers (AC6)
# ============================================================================


class TestAllSectorsExist:
    """Verify all 15 sectors are loaded and accessible."""

    def test_15_sectors_loaded(self):
        assert len(SECTORS) == 15

    def test_all_sector_ids_present(self):
        assert set(SECTORS.keys()) == ALL_SECTOR_IDS

    def test_list_sectors_returns_15(self):
        sectors = list_sectors()
        assert len(sectors) == 15
        ids = {s["id"] for s in sectors}
        assert ids == ALL_SECTOR_IDS


class TestCoverageLayersPresent:
    """AC6: Every sector must have keywords, exclusions, context gates, and signature terms."""

    @pytest.mark.parametrize("sector_id", sorted(ALL_SECTOR_IDS))
    def test_has_keywords(self, sector_id):
        s = get_sector(sector_id)
        assert len(s.keywords) >= 5, f"{sector_id} has only {len(s.keywords)} keywords"

    @pytest.mark.parametrize("sector_id", sorted(ALL_SECTOR_IDS))
    def test_has_exclusions(self, sector_id):
        s = get_sector(sector_id)
        assert len(s.exclusions) >= 5, f"{sector_id} has only {len(s.exclusions)} exclusions"

    @pytest.mark.parametrize("sector_id", sorted(ALL_SECTOR_IDS))
    def test_has_context_gates(self, sector_id):
        s = get_sector(sector_id)
        assert len(s.context_required_keywords) >= 1, (
            f"{sector_id} has no context_required_keywords"
        )

    @pytest.mark.parametrize("sector_id", sorted(ALL_SECTOR_IDS))
    def test_has_signature_terms(self, sector_id):
        s = get_sector(sector_id)
        assert len(s.signature_terms) >= 1, (
            f"{sector_id} has no signature_terms"
        )

    @pytest.mark.parametrize("sector_id", sorted(ALL_SECTOR_IDS))
    def test_has_co_occurrence_rules(self, sector_id):
        """All 15 sectors must now have co-occurrence rules (CRIT-FLT-007 expansion)."""
        s = get_sector(sector_id)
        assert len(s.co_occurrence_rules) >= 1, (
            f"{sector_id} has no co_occurrence_rules"
        )

    @pytest.mark.parametrize("sector_id", sorted(ALL_SECTOR_IDS))
    def test_has_domain_signals(self, sector_id):
        """All 15 sectors must now have domain signals (CRIT-FLT-007 expansion)."""
        s = get_sector(sector_id)
        ds = s.domain_signals
        has_any = bool(ds.ncm_prefixes or ds.unit_patterns or ds.size_patterns)
        assert has_any, f"{sector_id} has no domain_signals (ncm/unit/size all empty)"

    @pytest.mark.parametrize("sector_id", sorted(ALL_SECTOR_IDS))
    def test_has_viability_value_range(self, sector_id):
        s = get_sector(sector_id)
        assert s.viability_value_range is not None, (
            f"{sector_id} missing viability_value_range"
        )
        vmin, vmax = s.viability_value_range
        assert vmin < vmax, f"{sector_id} invalid range: {vmin} >= {vmax}"


# ============================================================================
# Phase 2: Co-Occurrence Rules Validation (CRIT-FLT-007 Expansion)
# ============================================================================


class TestCoOccurrenceRulesStructure:
    """Validate co-occurrence rules have valid structure for all expanded sectors."""

    @pytest.mark.parametrize("sector_id", sorted(EXPANDED_SECTORS))
    def test_rules_have_minimum_two(self, sector_id):
        """Each expanded sector should have at least 2 co-occurrence rules."""
        s = get_sector(sector_id)
        assert len(s.co_occurrence_rules) >= 2, (
            f"{sector_id} has only {len(s.co_occurrence_rules)} rules, expected >= 2"
        )

    @pytest.mark.parametrize("sector_id", sorted(EXPANDED_SECTORS))
    def test_rules_have_required_fields(self, sector_id):
        """Each rule must have trigger, negative_contexts, positive_signals."""
        s = get_sector(sector_id)
        for i, rule in enumerate(s.co_occurrence_rules):
            assert rule.trigger, f"{sector_id} rule[{i}] missing trigger"
            assert len(rule.negative_contexts) >= 2, (
                f"{sector_id} rule[{i}] has < 2 negative_contexts"
            )
            assert len(rule.positive_signals) >= 2, (
                f"{sector_id} rule[{i}] has < 2 positive_signals"
            )

    @pytest.mark.parametrize("sector_id", sorted(EXPANDED_SECTORS))
    def test_trigger_matches_sector_keyword(self, sector_id):
        """Each CRIT-FLT-007 expanded rule's trigger must match a sector keyword prefix."""
        s = get_sector(sector_id)
        for rule in s.co_occurrence_rules:
            trigger = rule.trigger.lower()
            # Check prefix match OR substring match (some triggers are semantic)
            matched = any(
                kw.lower().startswith(trigger) or trigger in kw.lower()
                for kw in s.keywords
            )
            assert matched, (
                f"{sector_id}: trigger '{rule.trigger}' doesn't match any keyword"
            )


# ============================================================================
# Phase 3: Domain Signals Validation (CRIT-FLT-007 Expansion)
# ============================================================================


class TestDomainSignalsStructure:
    """Validate domain signals have proper NCM prefixes, unit patterns, size patterns."""

    @pytest.mark.parametrize("sector_id", sorted(EXPANDED_SECTORS))
    def test_has_ncm_prefixes(self, sector_id):
        s = get_sector(sector_id)
        # Software is an exception — limited physical goods NCM codes
        min_ncm = 1 if sector_id == "software" else 3
        assert len(s.domain_signals.ncm_prefixes) >= min_ncm, (
            f"{sector_id} has only {len(s.domain_signals.ncm_prefixes)} NCM prefixes"
        )

    @pytest.mark.parametrize("sector_id", sorted(EXPANDED_SECTORS))
    def test_ncm_prefixes_are_numeric(self, sector_id):
        """NCM prefixes should be numeric strings (2-4 digits)."""
        s = get_sector(sector_id)
        for prefix in s.domain_signals.ncm_prefixes:
            assert prefix.isdigit(), f"{sector_id}: NCM '{prefix}' is not numeric"
            assert 2 <= len(prefix) <= 4, (
                f"{sector_id}: NCM '{prefix}' length {len(prefix)} not in [2,4]"
            )

    @pytest.mark.parametrize("sector_id", sorted(EXPANDED_SECTORS))
    def test_has_unit_patterns(self, sector_id):
        s = get_sector(sector_id)
        assert len(s.domain_signals.unit_patterns) >= 3, (
            f"{sector_id} has only {len(s.domain_signals.unit_patterns)} unit patterns"
        )

    # Sectors with physical goods that have measurable sizes (configured in YAML)
    SECTORS_WITH_SIZE_PATTERNS = {
        "vestuario", "materiais_eletricos", "materiais_hidraulicos",
    }

    @pytest.mark.parametrize("sector_id", sorted(SECTORS_WITH_SIZE_PATTERNS))
    def test_has_size_patterns(self, sector_id):
        """Only physical-goods sectors are expected to have size_patterns."""
        s = get_sector(sector_id)
        assert len(s.domain_signals.size_patterns) >= 2, (
            f"{sector_id} has only {len(s.domain_signals.size_patterns)} size patterns"
        )

    @pytest.mark.parametrize("sector_id", sorted(EXPANDED_SECTORS))
    def test_size_patterns_are_valid_regex(self, sector_id):
        """All size patterns must compile as valid regex."""
        s = get_sector(sector_id)
        for pattern in s.domain_signals.size_patterns:
            try:
                re.compile(pattern)
            except re.error as e:
                pytest.fail(f"{sector_id}: invalid regex '{pattern}': {e}")


# ============================================================================
# Phase 4: Synonym Dicts for New Sectors (CRIT-FLT-007 Expansion)
# ============================================================================


class TestNewSynonymDicts:
    """Validate synonym dicts added for engenharia_rodoviaria, materiais_eletricos, materiais_hidraulicos."""

    @pytest.mark.parametrize("sector_id", sorted(NEW_SYNONYM_SECTORS))
    def test_synonym_dict_exists(self, sector_id):
        assert sector_id in SECTOR_SYNONYMS, (
            f"SECTOR_SYNONYMS missing entry for {sector_id}"
        )

    @pytest.mark.parametrize("sector_id", sorted(NEW_SYNONYM_SECTORS))
    def test_synonym_dict_has_entries(self, sector_id):
        """Each new synonym dict should have at least 5 canonical entries."""
        canon_dict = SECTOR_SYNONYMS[sector_id]
        assert len(canon_dict) >= 5, (
            f"{sector_id} synonym dict has only {len(canon_dict)} canonical entries"
        )

    @pytest.mark.parametrize("sector_id", sorted(NEW_SYNONYM_SECTORS))
    def test_synonym_entries_have_synonyms(self, sector_id):
        """Each canonical entry should have at least 2 synonyms."""
        canon_dict = SECTOR_SYNONYMS[sector_id]
        for canonical, syns in canon_dict.items():
            assert len(syns) >= 2, (
                f"{sector_id}: canonical '{canonical}' has only {len(syns)} synonyms"
            )

    def test_engenharia_rodoviaria_synonym_match(self):
        """Synonym 'estrada' should near-miss match canonical 'rodovia'."""
        s = get_sector("engenharia_rodoviaria")
        matches = find_synonym_matches(
            "Conservacao de estrada rural",
            s.keywords,
            "engenharia_rodoviaria",
        )
        canonicals = [m[0] for m in matches]
        assert "rodovia" in canonicals, f"Expected 'rodovia' in matches, got {matches}"

    def test_materiais_eletricos_synonym_match(self):
        """Synonym 'fio eletrico' should near-miss match canonical 'cabo eletrico'."""
        s = get_sector("materiais_eletricos")
        matches = find_synonym_matches(
            "Aquisicao de fio eletrico para instalacao",
            s.keywords,
            "materiais_eletricos",
        )
        assert len(matches) > 0, "Expected at least one synonym match"

    def test_materiais_hidraulicos_synonym_match(self):
        """Synonym 'cano PVC' should near-miss match canonical 'tubo PVC'."""
        s = get_sector("materiais_hidraulicos")
        matches = find_synonym_matches(
            "Fornecimento de cano PVC para rede de distribuicao",
            s.keywords,
            "materiais_hidraulicos",
        )
        assert len(matches) > 0, "Expected at least one synonym match"


# ============================================================================
# Phase 5: Cross-Sector Collision Rate < 10% (AC7)
# ============================================================================


# Known true-positive test cases per sector for precision/recall estimation
# Each entry: (sector_id, description, expected_match: True/False)
AUDIT_TEST_CASES = [
    # --- vestuario (TP) ---
    ("vestuario", "Aquisicao de uniformes escolares para rede municipal", True),
    ("vestuario", "Registro de precos para jalecos e aventais para o hospital", True),
    ("vestuario", "Aquisicao de camisetas e calcas para os agentes comunitarios", True),
    ("vestuario", "Contratacao de servico de confeccao de fardamento militar", True),
    ("vestuario", "Aquisicao de notebooks para a secretaria de educacao", False),
    ("vestuario", "Material de limpeza para as escolas municipais", False),
    # --- alimentos (TP) ---
    ("alimentos", "Registro de precos para generos alimenticios para merenda escolar", True),
    ("alimentos", "Aquisicao de cafe e acucar para o refeitorio", True),
    ("alimentos", "Aquisicao de oleo diesel para frota municipal", False),
    ("alimentos", "Material de escritorio para a secretaria", False),
    # --- informatica (TP) ---
    ("informatica", "Aquisicao de notebooks e desktops para o laboratorio", True),
    ("informatica", "Registro de precos para cartuchos de toner", True),
    ("informatica", "Aquisicao de impressoras multifuncionais", True),
    ("informatica", "Pagamento dos servidores ativos e inativos da prefeitura", False),
    ("informatica", "Aquisicao de uniformes para guardas municipais", False),
    # --- software (TP) ---
    ("software", "Contratacao de licenciamento de software de gestao publica", True),
    ("software", "Desenvolvimento de sistema web para protocolo digital", True),
    ("software", "Aquisicao de licencas Microsoft Office 365", True),
    ("software", "Aquisicao de computadores e notebooks para laboratorio", False),
    ("software", "Fornecimento de balanca para pesagem de gado com sistema manual", False),
    # --- engenharia (TP) ---
    ("engenharia", "Aquisicao de materiais de construcao diversos", True),
    ("engenharia", "Contratacao de empresa para pavimentacao asfaltica de vias urbanas", True),
    ("engenharia", "Contratacao para execucao de obra de ampliacao do hospital", True),
    ("engenharia", "Contratacao de servicos de mao de obra terceirizada de limpeza", False),
    ("engenharia", "Aquisicao de computadores para o setor administrativo", False),
    # --- facilities (TP) ---
    ("facilities", "Contratacao de empresa para limpeza asseio e conservacao dos predios", True),
    ("facilities", "Prestacao de servicos de portaria recepcao e controle de acesso", True),
    ("facilities", "Contratacao de servicos de zeladoria para os predios da prefeitura", True),
    ("facilities", "Aquisicao de escavadeira hidraulica para desassoreamento da lagoa", False),
    ("facilities", "Aquisicao de lubrificantes e produtos de limpeza pesada para veiculos", False),
    # --- saude (TP) ---
    ("saude", "Aquisicao de medicamentos para a rede municipal de saude", True),
    ("saude", "Registro de preco para material medico hospitalar", True),
    ("saude", "Aquisicao de seringas e agulhas descartaveis", True),
    ("saude", "Contratacao de plano de saude para servidores municipais", False),
    ("saude", "Aquisicao de agulhas de costura e linhas para oficina de costura", False),
    # --- vigilancia (TP) ---
    ("vigilancia", "Contratacao de empresa de vigilancia patrimonial armada e desarmada", True),
    ("vigilancia", "Implantacao de sistema de CFTV com cameras de monitoramento", True),
    ("vigilancia", "Contratacao de postos de vigilante armado 24 horas", True),
    ("vigilancia", "Acoes de vigilancia sanitaria para fiscalizacao de alimentos", False),
    ("vigilancia", "Consultoria em seguranca da informacao e seguranca cibernetica", False),
    # --- transporte (TP) ---
    ("transporte", "Locacao de veiculos com motorista para a secretaria de educacao", True),
    ("transporte", "Registro de precos para aquisicao de combustivel gasolina e diesel", True),
    ("transporte", "Aquisicao de pneus para a frota de veiculos", True),
    ("transporte", "Contratacao de veiculo de comunicacao para publicidade institucional", False),
    ("transporte", "Aquisicao de ventilador mecanico para UTI neonatal", False),
    # --- mobiliario (TP) ---
    ("mobiliario", "Aquisicao eventual de 80 mesas de reuniao", True),
    ("mobiliario", "Aquisicao de armario vestiario de aco", True),
    ("mobiliario", "Aquisicao de estacoes de trabalho desktops equipamentos moveis notebooks", False),
    ("mobiliario", "Aquisicao de material de roupa de cama mesa e banho", False),
    # --- papelaria (TP) ---
    ("papelaria", "Abertura de ata de registro de precos para aquisicao de papel sulfite", True),
    ("papelaria", "Aquisicao de kits de material escolar", True),
    ("papelaria", "Aquisicao de material de consumo OPME clipes de aneurismas", False),
    # --- manutencao_predial (TP) ---
    ("manutencao_predial", "Contratacao de empresa especializada em manutencao predial preventiva e corretiva", True),
    ("manutencao_predial", "Servico de manutencao de elevadores da superintendencia regional", True),
    ("manutencao_predial", "Servico de manutencao preventiva e corretiva em ar condicionado", True),
    ("manutencao_predial", "Manutencao preventiva e corretiva da frota de veiculos oficiais", False),
    ("manutencao_predial", "Manutencao de estradas vicinais e rodovias municipais", False),
    # --- engenharia_rodoviaria (TP) ---
    ("engenharia_rodoviaria", "Contratacao de empresa para pavimentacao asfaltica da rodovia BR-101", True),
    ("engenharia_rodoviaria", "Servico de recapeamento asfaltico em vias urbanas do municipio", True),
    ("engenharia_rodoviaria", "Aquisicao de materiais para sinalizacao viaria horizontal e vertical", True),
    ("engenharia_rodoviaria", "Operacao tapa buraco em vias municipais danificadas", True),
    ("engenharia_rodoviaria", "Reforma do terminal rodoviario central para passageiros", False),
    ("engenharia_rodoviaria", "Aquisicao de passagem rodoviaria para servidores em viagem", False),
    # --- materiais_eletricos (TP) ---
    ("materiais_eletricos", "Aquisicao de disjuntores termomagneticos para quadro de distribuicao", True),
    ("materiais_eletricos", "Fornecimento de cabo eletrico flexivel 2,5mm para instalacoes", True),
    ("materiais_eletricos", "Modernizacao da iluminacao publica com tecnologia LED", True),
    ("materiais_eletricos", "Aquisicao de computadores e notebooks para o setor administrativo", False),
    ("materiais_eletricos", "Compra de guitarra eletrica para escola de musica municipal", False),
    # --- materiais_hidraulicos (TP) ---
    ("materiais_hidraulicos", "Aquisicao de tubo PVC para rede de distribuicao de agua", True),
    ("materiais_hidraulicos", "Fornecimento de bomba submersa para poco artesiano municipal", True),
    ("materiais_hidraulicos", "Registro de precos para aquisicao de material hidraulico", True),
    ("materiais_hidraulicos", "Aquisicao de prensa hidraulica para oficina mecanica industrial", False),
    ("materiais_hidraulicos", "Locacao de escavadeira hidraulica para obra de terraplanagem", False),
]


class TestPrecisionRecallPerSector:
    """AC7: Precision >= 85%, Recall >= 70% for each sector (estimated via audit test cases)."""

    @pytest.mark.parametrize("sector_id", sorted(ALL_SECTOR_IDS))
    def test_sector_precision(self, sector_id):
        """Precision = TP / (TP + FP). No false positives in our test set."""
        cases = [(desc, expected) for sid, desc, expected in AUDIT_TEST_CASES if sid == sector_id]
        if not cases:
            pytest.skip(f"No test cases for {sector_id}")

        tp = 0
        fp = 0
        for desc, expected in cases:
            ok, _ = _match(sector_id, desc)
            if ok and expected:
                tp += 1
            elif ok and not expected:
                fp += 1

        total_positive = tp + fp
        if total_positive == 0:
            pytest.skip(f"No positive predictions for {sector_id}")

        precision = tp / total_positive * 100
        assert precision >= 85, (
            f"{sector_id} precision {precision:.0f}% < 85%. "
            f"TP={tp}, FP={fp}"
        )

    @pytest.mark.parametrize("sector_id", sorted(ALL_SECTOR_IDS))
    def test_sector_recall(self, sector_id):
        """Recall = TP / (TP + FN). All true positives must be found."""
        cases = [(desc, expected) for sid, desc, expected in AUDIT_TEST_CASES if sid == sector_id]
        if not cases:
            pytest.skip(f"No test cases for {sector_id}")

        tp = 0
        fn = 0
        for desc, expected in cases:
            ok, _ = _match(sector_id, desc)
            if ok and expected:
                tp += 1
            elif not ok and expected:
                fn += 1

        total_relevant = tp + fn
        if total_relevant == 0:
            pytest.skip(f"No relevant cases for {sector_id}")

        recall = tp / total_relevant * 100
        assert recall >= 70, (
            f"{sector_id} recall {recall:.0f}% < 70%. "
            f"TP={tp}, FN={fn}"
        )


class TestCrossSectorCollision:
    """AC7: Cross-sector collision rate < 10%."""

    # Test descriptions designed to match exactly ONE sector each.
    # Uses highly sector-specific language to avoid legitimate multi-sector matches.
    # NOTE: Some keyword overlaps are inherent (e.g., "software" is in both software
    # and informatica sectors). We use the MOST unique terms per sector.
    SINGLE_SECTOR_CASES = [
        ("Aquisicao de uniformes escolares e jalecos para alunos", "vestuario"),
        ("Registro de precos para generos alimenticios para merenda escolar", "alimentos"),
        ("Aquisicao de notebooks e cartuchos de toner para o laboratorio", "informatica"),
        ("Contratacao de licenciamento SaaS em nuvem para gestao escolar", "software"),
        ("Servico de sinalizacao viaria horizontal e vertical", "engenharia_rodoviaria"),
        ("Aquisicao de disjuntores termomagneticos e eletrodutos", "materiais_eletricos"),
        ("Aquisicao de tubo PVC e registro hidraulico para rede de agua", "materiais_hidraulicos"),
        ("Contratacao de empresa de vigilancia patrimonial armada", "vigilancia"),
        ("Aquisicao de medicamentos e seringas para o hospital", "saude"),
        ("Locacao de veiculos com motorista e aquisicao de pneus para frota", "transporte"),
        ("Aquisicao de papel sulfite A4 e canetas para secretaria", "papelaria"),
        ("Servico de manutencao preventiva e corretiva de ar condicionado", "manutencao_predial"),
        ("Aquisicao de mesas de reuniao e armario vestiario", "mobiliario"),
        ("Contratacao de servicos de zeladoria e portaria predial", "facilities"),
        ("Contratacao para execucao de obra publica de pavimentacao urbana", "engenharia"),
    ]

    def test_collision_rate_below_10_percent(self):
        """Each test case should match at most 1 sector. Collision < 10%."""
        collisions = 0
        collision_details = []

        for desc, expected_sector in self.SINGLE_SECTOR_CASES:
            matching_sectors = []
            for sid in ALL_SECTOR_IDS:
                ok, _ = _match(sid, desc)
                if ok:
                    matching_sectors.append(sid)

            if len(matching_sectors) > 1:
                collisions += 1
                collision_details.append(
                    (desc[:80], expected_sector, matching_sectors)
                )

        rate = collisions / len(self.SINGLE_SECTOR_CASES) * 100
        if collision_details:
            detail_str = "\n".join(
                f"  '{d}' expected={e}, matched={m}"
                for d, e, m in collision_details
            )
            # Allow up to 10% collision — some overlap is inherent
            assert rate < 10, (
                f"Cross-sector collision rate {rate:.1f}% >= 10%.\n{detail_str}"
            )
        else:
            assert rate < 10

    def test_expected_sector_always_matches(self):
        """The expected sector must always match its test case."""
        for desc, expected_sector in self.SINGLE_SECTOR_CASES:
            ok, kws = _match(expected_sector, desc)
            assert ok, (
                f"'{desc[:80]}' did not match expected sector '{expected_sector}'"
            )


# ============================================================================
# Phase 6: YAML Structural Integrity
# ============================================================================


class TestYamlStructuralIntegrity:
    """Validate sectors_data.yaml structural completeness post-expansion."""

    @pytest.fixture(scope="class")
    def sectors_yaml(self):
        return _load_sectors_yaml()

    def test_yaml_has_15_sectors(self, sectors_yaml):
        assert len(sectors_yaml) == 15

    def test_all_sectors_have_name(self, sectors_yaml):
        for sid, cfg in sectors_yaml.items():
            assert "name" in cfg, f"{sid} missing 'name'"
            assert isinstance(cfg["name"], str), f"{sid} name is not str"

    def test_all_sectors_have_description(self, sectors_yaml):
        for sid, cfg in sectors_yaml.items():
            assert "description" in cfg, f"{sid} missing 'description'"

    def test_all_sectors_have_keywords_list(self, sectors_yaml):
        for sid, cfg in sectors_yaml.items():
            kws = cfg.get("keywords", [])
            assert isinstance(kws, list), f"{sid} keywords is not list"
            assert len(kws) >= 5, f"{sid} has only {len(kws)} keywords"

    def test_all_sectors_have_exclusions_list(self, sectors_yaml):
        for sid, cfg in sectors_yaml.items():
            excl = cfg.get("exclusions", [])
            assert isinstance(excl, list), f"{sid} exclusions is not list"
            assert len(excl) >= 5, f"{sid} has only {len(excl)} exclusions"

    def test_all_sectors_have_co_occurrence_rules(self, sectors_yaml):
        """CRIT-FLT-007: All 15 sectors must now have co_occurrence_rules."""
        for sid, cfg in sectors_yaml.items():
            rules = cfg.get("co_occurrence_rules", [])
            assert isinstance(rules, list), f"{sid} co_occurrence_rules is not list"
            assert len(rules) >= 1, f"{sid} has no co_occurrence_rules"
            for i, rule in enumerate(rules):
                assert "trigger" in rule, f"{sid} rule[{i}] missing trigger"
                assert "negative_contexts" in rule, f"{sid} rule[{i}] missing negative_contexts"

    def test_all_sectors_have_domain_signals(self, sectors_yaml):
        """CRIT-FLT-007: All 15 sectors must have domain_signals."""
        for sid, cfg in sectors_yaml.items():
            ds = cfg.get("domain_signals", {})
            assert isinstance(ds, dict), f"{sid} domain_signals is not dict"
            ncm = ds.get("ncm_prefixes", [])
            unit = ds.get("unit_patterns", [])
            size = ds.get("size_patterns", [])
            has_any = bool(ncm or unit or size)
            assert has_any, f"{sid} domain_signals is completely empty"

    def test_no_exact_duplicate_keywords_within_sector(self, sectors_yaml):
        """No sector should have exact duplicate keyword strings (pre-normalization)."""
        for sid, cfg in sectors_yaml.items():
            kws = cfg.get("keywords", [])
            # Check for exact string duplicates (not normalized — accented variants are OK)
            seen = set()
            dupes = set()
            for kw in kws:
                if kw in seen:
                    dupes.add(kw)
                seen.add(kw)
            assert len(dupes) == 0, (
                f"{sid} has exact duplicate keywords: {dupes}"
            )


# ============================================================================
# Phase 7: Synonym Coverage Validation
# ============================================================================


class TestSynonymCoverage:
    """Validate synonym dicts exist for sectors that need them most."""

    def test_all_15_sectors_have_synonyms(self):
        """All 15 sectors should have synonym dictionaries."""
        for sid in ALL_SECTOR_IDS:
            assert sid in SECTOR_SYNONYMS, (
                f"Sector '{sid}' missing from SECTOR_SYNONYMS"
            )

    @pytest.mark.parametrize("sector_id", sorted(ALL_SECTOR_IDS))
    def test_synonym_dict_not_empty(self, sector_id):
        """Each sector should have at least 2 canonical entries."""
        assert len(SECTOR_SYNONYMS[sector_id]) >= 2, (
            f"{sector_id} has fewer than 2 canonical entries"
        )

    @pytest.mark.parametrize("sector_id", sorted(NEW_SYNONYM_SECTORS))
    def test_new_synonym_dicts_have_5_entries(self, sector_id):
        """CRIT-FLT-007 new synonym dicts should have >= 5 canonical entries."""
        assert len(SECTOR_SYNONYMS[sector_id]) >= 5, (
            f"{sector_id} has fewer than 5 canonical entries (new dict)"
        )


# ============================================================================
# Phase 8: Specific Regression Tests — Known False Positives
# ============================================================================


class TestKnownFalsePositives:
    """Regression tests for known false positives that should be blocked by exclusions."""

    def test_software_excludes_sistema_climatizacao(self):
        ok, _ = _match("software", "Contratacao de empresa para locacao de sistema de climatizacao evaporativa")
        assert ok is False

    def test_software_excludes_sistema_sonorizacao(self):
        ok, _ = _match("software", "Manutencao de sistemas de sonorizacao e iluminacao cenica")
        assert ok is False

    def test_software_excludes_sistema_energia_solar(self):
        ok, _ = _match("software", "Fornecimento e instalacao de sistema de microgeracao de energia solar fotovoltaica")
        assert ok is False

    def test_software_excludes_sistema_videomonitoramento(self):
        ok, _ = _match("software", "Manutencao do sistema de videomonitoramento urbano do municipio")
        assert ok is False

    def test_engenharia_excludes_mao_de_obra_limpeza(self):
        ok, _ = _match("engenharia", "Contratacao de mao de obra terceirizada de limpeza")
        assert ok is False

    def test_engenharia_excludes_infraestrutura_telecom(self):
        ok, _ = _match("engenharia", "Modernizar a infraestrutura de comunicacao da prefeitura")
        assert ok is False

    def test_informatica_excludes_servidores_publicos(self):
        ok, _ = _match("informatica", "Aquisicao de EPIs para protecao dos servidores publicos")
        assert ok is False

    def test_facilities_excludes_limpeza_veiculos(self):
        ok, _ = _match("facilities", "Aquisicao de lubrificantes e produtos de limpeza pesada para veiculos")
        assert ok is False

    def test_vigilancia_excludes_vigilancia_sanitaria(self):
        ok, _ = _match("vigilancia", "Acoes de vigilancia sanitaria para fiscalizacao de alimentos")
        assert ok is False

    def test_transporte_excludes_veiculo_comunicacao(self):
        ok, _ = _match("transporte", "Contratacao de veiculo de comunicacao para publicidade institucional")
        assert ok is False

    def test_manutencao_predial_excludes_manutencao_veiculos(self):
        ok, _ = _match("manutencao_predial", "Manutencao preventiva e corretiva da frota de veiculos oficiais")
        assert ok is False

    def test_materiais_hidraulicos_excludes_prensa_hidraulica(self):
        ok, _ = _match("materiais_hidraulicos", "Aquisicao de prensa hidraulica para oficina mecanica industrial")
        assert ok is False

    def test_materiais_eletricos_excludes_guitarra_eletrica(self):
        ok, _ = _match("materiais_eletricos", "Compra de guitarra eletrica para escola de musica municipal")
        assert ok is False

    def test_engenharia_rodoviaria_excludes_terminal_rodoviario(self):
        ok, _ = _match("engenharia_rodoviaria", "Reforma do terminal rodoviario central para passageiros")
        assert ok is False

    def test_mobiliario_excludes_equipamentos_moveis(self):
        ok, _ = _match("mobiliario", "Aquisicao de estacoes de trabalho desktops equipamentos moveis notebooks")
        assert ok is False


# ============================================================================
# Phase 9: Aggregate Summary (informational)
# ============================================================================


class TestAuditSummary:
    """Run full audit and print summary (informational, never fails)."""

    def test_print_coverage_summary(self):
        """Print coverage summary for documentation (AC6)."""
        print("\n" + "=" * 100)
        print("CRIT-FLT-007 SECTOR COVERAGE AUDIT SUMMARY")
        print("=" * 100)
        header = (
            f"{'Sector':<25} {'KW':>4} {'Excl':>5} {'CTX':>4} {'CoOcc':>5} "
            f"{'Sig':>4} {'NCM':>4} {'Unit':>4} {'Size':>4} {'Syn':>4}"
        )
        print(header)
        print("-" * 100)

        for sid in sorted(ALL_SECTOR_IDS):
            s = get_sector(sid)
            ds = s.domain_signals
            has_syn = sid in SECTOR_SYNONYMS
            syn_count = len(SECTOR_SYNONYMS.get(sid, {}))
            print(
                f"{sid:<25} "
                f"{len(s.keywords):>4} "
                f"{len(s.exclusions):>5} "
                f"{len(s.context_required_keywords):>4} "
                f"{len(s.co_occurrence_rules):>5} "
                f"{len(s.signature_terms):>4} "
                f"{len(ds.ncm_prefixes):>4} "
                f"{len(ds.unit_patterns):>4} "
                f"{len(ds.size_patterns):>4} "
                f"{'Y(' + str(syn_count) + ')' if has_syn else '-':>4}"
            )

        print("-" * 100)

        # Aggregate stats
        total_kw = sum(len(get_sector(sid).keywords) for sid in ALL_SECTOR_IDS)
        total_excl = sum(len(get_sector(sid).exclusions) for sid in ALL_SECTOR_IDS)
        total_rules = sum(len(get_sector(sid).co_occurrence_rules) for sid in ALL_SECTOR_IDS)
        sectors_with_syn = sum(1 for sid in ALL_SECTOR_IDS if sid in SECTOR_SYNONYMS)
        print(f"\nTotal keywords: {total_kw}")
        print(f"Total exclusions: {total_excl}")
        print(f"Total co-occurrence rules: {total_rules}")
        print(f"Sectors with synonyms: {sectors_with_syn}/15")
        print("=" * 100)
