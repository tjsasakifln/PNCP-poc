"""
Synonym dictionaries for sector-based near-miss matching (STORY-179 AC12).

This module provides synonym mappings for each sector to recover false negatives
caused by keyword variants (e.g., "fardamento" ≈ "uniforme", "manutenção predial"
≈ "conservação").

Usage:
    from synonyms import SECTOR_SYNONYMS, find_synonym_matches

    synonyms_found = find_synonym_matches(
        objeto="Fardamento para guardas municipais",
        setor_keywords={"uniforme", "farda"},
        setor_id="vestuario"
    )
    # Returns: [("uniforme", "fardamento")]

Design:
    - Synonym dictionaries are sector-specific to avoid false positives
    - Bidirectional matching: "fardamento" → "uniforme" AND "uniforme" → "fardamento"
    - Unicode normalization ensures accent-insensitive matching
    - SequenceMatcher similarity threshold: 0.8 (high precision)
"""

import logging
from difflib import SequenceMatcher
from typing import Dict, Set, List, Tuple

from filter import normalize_text

logger = logging.getLogger(__name__)


# ============================================================================
# SECTOR SYNONYMS
# ============================================================================
#
# Format: Dict[setor_id, Dict[canonical_keyword, Set[synonyms]]]
#
# - canonical_keyword: The primary term from SectorConfig.keywords
# - synonyms: Alternative terms with similar meaning
#
# Guidelines:
# - Include common variations, abbreviations, regional terms
# - Focus on high-confidence synonyms to avoid false positives
# - Can be expanded incrementally based on user feedback
# ============================================================================

SECTOR_SYNONYMS: Dict[str, Dict[str, Set[str]]] = {
    "vestuario": {
        "uniforme": {
            "fardamento", "fardamentos",
            "indumentária", "indumentaria",
            "vestimenta", "vestimenta profissional",
            "roupa de trabalho", "roupa profissional",
            "vestimenta laboral",
        },
        "farda": {
            "fardas",  # Keep only plural, "fardamento" is under "uniforme"
        },
        "jaleco": {
            "guarda-pó", "guarda pó", "guarda-pos", "guarda pos",
            "avental hospitalar", "avental médico", "avental medico",
            "avental cirúrgico", "avental cirurgico",
        },
        "camisa": {
            "camisa polo", "camiseta", "blusa",
            "camisa social", "camisa de uniforme",
            "camisa de manga curta", "camisa de manga longa",
        },
        "calça": {
            "calca", "calças", "calcas",
            "calça de uniforme", "calca de uniforme",
            "calça profissional", "calca profissional",
        },
        "colete": {
            "colete de identificação", "colete de identificacao",
            "colete refletivo", "colete reflexivo",
        },
        "bota": {
            "botina", "botinas",
            "calçado de segurança", "calcado de seguranca",
            "calçado profissional", "calcado profissional",
        },
        "avental": {
            "jaleco", "guarda-pó", "guarda pó",
            "avental de proteção", "avental de protecao",
        },
    },

    "alimentos": {
        "merenda": {
            "merenda escolar",
            "alimentação escolar", "alimentacao escolar",
            "kit alimentação", "kit alimentacao",
            "kit merenda",
        },
        "refeição": {
            "refeicao", "refeições", "refeicoes",
            "almoço", "almoco", "jantar", "lanche",
            "alimentação", "alimentacao",
        },
        "carne": {
            "carne bovina", "carne suina", "carne suína",
            "proteína animal", "proteina animal",
        },
        "leite": {
            "laticinio", "laticinios", "laticínio", "laticínios",
            "produto lácteo", "produto lacteo",
        },
    },

    "informatica": {
        "computador": {
            "desktop", "desktops",
            "microcomputador", "microcomputadores",
            "estação de trabalho", "estacao de trabalho",
            "workstation",
        },
        "servidor": {
            "servidores",
            "servidor de rede", "servidores de rede",
            "servidor de dados", "servidores de dados",
            "servidor de arquivos",
            "servidor de aplicação", "servidor de aplicacao",
        },
        "impressora": {
            "impressoras",
            "multifuncional", "multifuncionais",
            "equipamento de impressão", "equipamento de impressao",
        },
        "notebook": {
            "notebooks", "laptop", "laptops",
            "computador portátil", "computador portatil",
        },
    },

    "facilities": {
        "limpeza": {
            "asseio", "higienização", "higienizacao",
            "zeladoria", "conservação", "conservacao",
        },
        "conservação": {
            "conservacao",
            "manutenção predial", "manutencao predial",
            "preservação", "preservacao",
            "manutenção e conservação", "manutencao e conservacao",
        },
        "zeladoria": {
            "zelador",
            "serviços de zeladoria", "servicos de zeladoria",
            "zeladoria predial",
        },
    },

    "mobiliario": {
        "mesa": {
            "mesa de escritório", "mesa de escritorio",
            "mesa de trabalho",
            "mesa para escritório", "mesa para escritorio",
            "escrivaninha", "escrivaninhas",
        },
        "cadeira": {
            "cadeira de escritório", "cadeira de escritorio",
            "cadeira giratória", "cadeira giratoria",
            "poltrona",
            "assento",
        },
        "armário": {
            "armario", "armários", "armarios",
            "arquivo", "arquivos",
            "gaveteiro", "gaveteiros",
        },
    },

    "papelaria": {
        "papel": {
            "papel a4", "papel sulfite",
            "papel ofício", "papel oficio",
            "papel branco",
        },
        "caneta": {
            "canetas",
            "caneta esferográfica", "caneta esferografica",
            "caneta esfero",
        },
    },

    "engenharia": {
        "pavimentação": {
            "pavimentacao",
            "asfaltamento", "asfalto",
            "recapeamento", "recapeamento asfaltico", "recapeamento asfáltico",
        },
        "reforma": {
            "reformas",
            "revitalização", "revitalizacao",
            "recuperação", "recuperacao",
            "restauração", "restauracao",
        },
        "drenagem": {
            "sistema de drenagem",
            "drenagem pluvial",
            "sistema de drenagem de águas pluviais",
            "sistema de drenagem de aguas pluviais",
        },
    },

    "software": {
        "sistema": {
            "sistema informatizado", "sistema informatizada",
            "solução", "solucao",
            "plataforma", "software",
        },
        "aplicativo": {
            "aplicativos", "app", "aplicação", "aplicacao",
            "aplicativo mobile", "aplicativo móvel", "aplicativo movel",
        },
    },

    "saude": {
        "medicamento": {
            "medicamentos", "remédio", "remedio", "remédios", "remedios",
            "fármaco", "farmaco", "fármacos", "farmacos",
            "produto farmacêutico", "produto farmaceutico",
        },
        "equipamento médico": {
            "equipamento medico", "equipamento hospitalar",
            "equipamento médico-hospitalar", "equipamento medico-hospitalar",
        },
    },

    "vigilancia": {
        "vigilância": {
            "vigilancia",
            "segurança", "seguranca",
            "monitoramento",
            "vigilância patrimonial", "vigilancia patrimonial",
            "segurança patrimonial", "seguranca patrimonial",
        },
        "câmera": {
            "camera", "câmeras", "cameras",
            "cftv",
            "circuito fechado de televisão", "circuito fechado de televisao",
            "videomonitoramento",
        },
    },

    "transporte": {
        "veículo": {
            "veiculo", "veículos", "veiculos",
            "automóvel", "automovel", "automóveis", "automoveis",
            "viatura", "viaturas",
        },
        "combustível": {
            "combustivel", "combustíveis", "combustiveis",
            "gasolina", "diesel", "etanol",
        },
    },

    "manutencao_predial": {
        "manutenção predial": {
            "manutencao predial",
            "conservação predial", "conservacao predial",
            "manutenção de imóveis", "manutencao de imoveis",
            "manutenção de edificações", "manutencao de edificacoes",
            "conservação de edificações", "conservacao de edificacoes",
        },
        "ar condicionado": {
            "climatização", "climatizacao",
            "climatização predial", "climatizacao predial",
            "sistema de ar condicionado",
        },
    },

    # CRIT-FLT-007: New synonym dicts for previously missing sectors
    "engenharia_rodoviaria": {
        "pavimentação": {
            "pavimentacao",
            "asfaltamento", "recapeamento",
            "pavimentação asfáltica", "pavimentacao asfaltica",
            "capa asfáltica", "capa asfaltica",
        },
        "rodovia": {
            "estrada", "via", "pista",
            "rodovia federal", "rodovia estadual",
            "trecho rodoviário", "trecho rodoviario",
        },
        "sinalização viária": {
            "sinalizacao viaria",
            "sinalização rodoviária", "sinalizacao rodoviaria",
            "sinalização horizontal", "sinalizacao horizontal",
            "sinalização vertical", "sinalizacao vertical",
            "demarcação viária", "demarcacao viaria",
        },
        "guard rail": {
            "defensa metálica", "defensa metalica",
            "defensas metálicas", "defensas metalicas",
            "barreira de proteção", "barreira de protecao",
        },
        "meio-fio": {
            "meio fio", "guia",
            "guia e sarjeta", "sarjeta",
        },
    },

    "materiais_eletricos": {
        "cabo elétrico": {
            "cabo eletrico",
            "fio elétrico", "fio eletrico",
            "condutor elétrico", "condutor eletrico",
            "fiação", "fiacao",
            "cabeamento elétrico", "cabeamento eletrico",
        },
        "luminária": {
            "luminaria",
            "ponto de luz", "aparelho de iluminação",
            "aparelho de iluminacao",
        },
        "disjuntor": {
            "dispositivo de proteção", "dispositivo de protecao",
            "chave de proteção", "chave de protecao",
        },
        "quadro elétrico": {
            "quadro eletrico",
            "quadro de distribuição", "quadro de distribuicao",
            "painel elétrico", "painel eletrico",
            "QDC", "QGBT",
        },
        "lâmpada": {
            "lampada",
            "lâmpada LED", "lampada LED",
            "lâmpada fluorescente", "lampada fluorescente",
            "bulbo", "tubo fluorescente",
        },
    },

    "materiais_hidraulicos": {
        "tubo PVC": {
            "tubo de PVC", "tubulação PVC", "tubulacao PVC",
            "cano PVC", "cano de PVC",
            "tubo PEAD",
        },
        "registro hidráulico": {
            "registro hidraulico",
            "válvula", "valvula",
            "válvula de gaveta", "valvula de gaveta",
            "válvula de esfera", "valvula de esfera",
            "registro de gaveta", "registro de esfera",
        },
        "bomba d'água": {
            "bomba d'agua", "bomba d agua",
            "bomba submersa", "bomba centrífuga", "bomba centrifuga",
            "motobomba", "moto bomba",
            "conjunto moto-bomba",
        },
        "caixa d'água": {
            "caixa d'agua", "caixa d agua",
            "reservatório", "reservatorio",
            "reservatório de água", "reservatorio de agua",
            "cisterna",
        },
        "conexão hidráulica": {
            "conexao hidraulica",
            "joelho PVC", "tê PVC", "te PVC",
            "luva PVC", "curva PVC",
            "adaptador PVC",
        },
    },
}


def find_synonym_matches(
    objeto: str,
    setor_keywords: Set[str],
    setor_id: str,
    similarity_threshold: float = 0.8,
) -> List[Tuple[str, str]]:
    """
    Find synonym matches between object description and sector keywords.

    Returns pairs of (canonical_keyword, synonym_found) where the synonym
    was found in the object but the canonical keyword was not.

    CRIT-FLT-006: Returns ALL distinct synonym matches, including multiple
    synonyms for the same canonical keyword. For example, if "fardamento" and
    "indumentária" both map to canonical "uniforme", both are returned as
    separate matches. This enables auto-approval when 2+ distinct synonyms
    are present in the object — even if they share the same canonical keyword.

    Previous behavior (pre-CRIT-FLT-006) deduplicated by canonical keyword,
    causing unnecessary LLM calls when multiple synonyms of the same canonical
    matched (e.g., "fardamento" + "indumentária" → 1 match instead of 2).

    Args:
        objeto: Procurement object description (e.g., "Fardamento para guardas municipais")
        setor_keywords: Set of canonical keywords from SectorConfig
        setor_id: Sector identifier (e.g., "vestuario", "alimentos")
        similarity_threshold: Minimum similarity ratio for fuzzy matching (0.0-1.0)

    Returns:
        List of (canonical_keyword, matched_synonym) tuples (deduplicated by synonym)

    Example:
        >>> find_synonym_matches(
        ...     objeto="Aquisição de fardamento e indumentária profissional",
        ...     setor_keywords={"uniforme"},
        ...     setor_id="vestuario"
        ... )
        [("uniforme", "fardamento"), ("uniforme", "indumentária")]
    """
    if setor_id not in SECTOR_SYNONYMS:
        logger.debug(f"No synonym dictionary for sector '{setor_id}'")
        return []

    objeto_norm = normalize_text(objeto)
    synonyms_dict = SECTOR_SYNONYMS[setor_id]
    near_misses: List[Tuple[str, str]] = []
    matched_synonyms: Set[str] = set()  # Track matched synonyms to avoid duplicates

    def _is_duplicate_synonym(syn_norm: str) -> bool:
        """Check if synonym is too similar to an already-matched one (e.g. singular/plural)."""
        for already in matched_synonyms:
            if SequenceMatcher(None, syn_norm, already).ratio() > 0.85:
                return True
        return False

    for canonical_keyword in setor_keywords:
        canonical_norm = normalize_text(canonical_keyword)

        # Skip if canonical keyword already matches (not a near-miss)
        if canonical_norm in objeto_norm:
            continue

        # Check synonyms for this canonical keyword
        if canonical_keyword not in synonyms_dict:
            continue

        # Sort synonyms by length (longest first) to prioritize longer exact matches
        sorted_synonyms = sorted(synonyms_dict[canonical_keyword], key=len, reverse=True)

        # Two-pass approach: exact matches first, then fuzzy.
        # This ensures "fardamento" (exact) always beats "fardamentos" (fuzzy).

        # Pass 1: Exact substring matches
        for synonym in sorted_synonyms:
            synonym_norm = normalize_text(synonym)

            if synonym_norm in matched_synonyms or _is_duplicate_synonym(synonym_norm):
                continue

            if synonym_norm in objeto_norm:
                near_misses.append((canonical_keyword, synonym))
                matched_synonyms.add(synonym_norm)
                logger.debug(
                    f"Exact synonym match: '{synonym}' ≈ '{canonical_keyword}' "
                    f"in '{objeto[:100]}...'"
                )

        # Pass 2: Fuzzy matches (single-word synonyms only)
        objeto_words = objeto_norm.split()
        for synonym in sorted_synonyms:
            synonym_norm = normalize_text(synonym)

            if synonym_norm in matched_synonyms or _is_duplicate_synonym(synonym_norm):
                continue

            # Multi-word synonyms should only match via exact substring (pass 1)
            if " " in synonym_norm:
                continue

            for word in objeto_words:
                similarity = SequenceMatcher(None, word, synonym_norm).ratio()
                if similarity >= similarity_threshold:
                    near_misses.append((canonical_keyword, synonym))
                    matched_synonyms.add(synonym_norm)
                    logger.debug(
                        f"Fuzzy synonym match: '{word}' ≈ '{synonym}' "
                        f"(similarity: {similarity:.2f}) → '{canonical_keyword}'"
                    )
                    break  # Stop checking words for this synonym

    # AC2: Audit log of all synonym matches
    if near_misses:
        logger.info(
            "synonym_matches_audit",
            extra={
                "synonym_matches": [
                    f"{syn}→{canon}" for canon, syn in near_misses
                ],
                "setor_id": setor_id,
                "distinct_count": len(near_misses),
                "objeto_preview": objeto[:120],
            },
        )

    return near_misses


def find_term_synonym_matches(
    custom_terms: List[str],
    objeto: str,
) -> List[Tuple[str, str]]:
    """STORY-267 AC6: Find synonym matches for custom search terms across ALL sectors.

    Unlike find_synonym_matches() which is sector-specific, this searches
    synonym dictionaries of ALL 15 sectors for matches against user's custom terms.
    Supports reverse matching: if user searched "guarda-po" and "jaleco" is a
    synonym of "guarda-po" in some sector, find "jaleco" in the objeto.

    Args:
        custom_terms: User's custom search terms (e.g., ["guarda-po", "avental"])
        objeto: Procurement object description

    Returns:
        List of (custom_term, matched_synonym) tuples
    """
    objeto_norm = normalize_text(objeto)
    near_misses: List[Tuple[str, str]] = []
    matched_synonyms: Set[str] = set()

    for term in custom_terms:
        term_norm = normalize_text(term)

        # Skip if term itself already matches in objeto (not a near-miss)
        if term_norm in objeto_norm:
            continue

        # Search ALL sector synonym dicts for this term
        for _setor_id, synonyms_dict in SECTOR_SYNONYMS.items():
            # Case 1: term is a canonical keyword → check its synonyms in objeto
            if term in synonyms_dict or term_norm in {normalize_text(k) for k in synonyms_dict}:
                # Find the matching canonical key
                canonical_key = None
                for k in synonyms_dict:
                    if normalize_text(k) == term_norm:
                        canonical_key = k
                        break
                if canonical_key:
                    for synonym in sorted(synonyms_dict[canonical_key], key=len, reverse=True):
                        syn_norm = normalize_text(synonym)
                        if syn_norm in matched_synonyms:
                            continue
                        if syn_norm in objeto_norm:
                            near_misses.append((term, synonym))
                            matched_synonyms.add(syn_norm)

            # Case 2: term is a synonym → check if canonical or other synonyms match in objeto
            for canonical_keyword, syns in synonyms_dict.items():
                syns_normalized = {normalize_text(s) for s in syns}
                if term_norm in syns_normalized:
                    # Check if canonical keyword matches
                    canon_norm = normalize_text(canonical_keyword)
                    if canon_norm not in matched_synonyms and canon_norm in objeto_norm:
                        near_misses.append((term, canonical_keyword))
                        matched_synonyms.add(canon_norm)
                    # Check if other synonyms match
                    for other_syn in sorted(syns, key=len, reverse=True):
                        other_norm = normalize_text(other_syn)
                        if other_norm == term_norm:
                            continue  # Skip self
                        if other_norm in matched_synonyms:
                            continue
                        if other_norm in objeto_norm:
                            near_misses.append((term, other_syn))
                            matched_synonyms.add(other_norm)

    if near_misses:
        logger.info(
            "term_synonym_matches_audit",
            extra={
                "term_synonym_matches": [
                    f"{term}→{syn}" for term, syn in near_misses
                ],
                "custom_terms": custom_terms,
                "distinct_count": len(near_misses),
                "objeto_preview": objeto[:120],
            },
        )

    return near_misses


def count_synonym_matches(
    objeto: str,
    setor_keywords: Set[str],
    setor_id: str,
) -> int:
    """
    Count number of unique synonym matches (convenience function).

    Args:
        objeto: Procurement object description
        setor_keywords: Set of canonical keywords from SectorConfig
        setor_id: Sector identifier

    Returns:
        Number of unique (canonical_keyword, synonym) pairs matched
    """
    return len(find_synonym_matches(objeto, setor_keywords, setor_id))


def should_auto_approve_by_synonyms(
    objeto: str,
    setor_keywords: Set[str],
    setor_id: str,
    min_synonyms: int = 2,
) -> Tuple[bool, List[Tuple[str, str]]]:
    """
    Determine if contract should be auto-approved based on synonym matches.

    High-confidence auto-approval rule (AC12.3):
    - 2+ synonym matches → APPROVED without LLM (high confidence)
    - 1 synonym match → ambiguous, send to LLM for validation (Camada 3B)
    - 0 synonym matches → not applicable

    Args:
        objeto: Procurement object description
        setor_keywords: Set of canonical keywords from SectorConfig
        setor_id: Sector identifier
        min_synonyms: Minimum number of synonym matches for auto-approval

    Returns:
        Tuple of (should_approve: bool, synonym_matches: List[Tuple[str, str]])

    Example:
        >>> should_auto_approve_by_synonyms(
        ...     objeto="Fardamento e jaleco para servidores",
        ...     setor_keywords={"uniforme", "jaleco"},
        ...     setor_id="vestuario",
        ...     min_synonyms=2
        ... )
        (True, [("uniforme", "fardamento"), ("jaleco", "jaleco")])
    """
    synonym_matches = find_synonym_matches(objeto, setor_keywords, setor_id)

    should_approve = len(synonym_matches) >= min_synonyms

    if should_approve:
        logger.info(
            f"Auto-approved by synonyms: {len(synonym_matches)} matches "
            f"(threshold: {min_synonyms}) - {synonym_matches}"
        )

    return should_approve, synonym_matches
