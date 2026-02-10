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

    NOTE: Returns UNIQUE canonical keywords (deduplicated). If multiple synonyms
    for the same canonical keyword match (e.g., "farda", "fardamento", "fardamentos"),
    only the FIRST match is returned.

    Args:
        objeto: Procurement object description (e.g., "Fardamento para guardas municipais")
        setor_keywords: Set of canonical keywords from SectorConfig
        setor_id: Sector identifier (e.g., "vestuario", "alimentos")
        similarity_threshold: Minimum similarity ratio for fuzzy matching (0.0-1.0)

    Returns:
        List of (canonical_keyword, matched_synonym) tuples (deduplicated by canonical_keyword)

    Example:
        >>> find_synonym_matches(
        ...     objeto="Fardamento para guardas municipais",
        ...     setor_keywords={"uniforme", "farda"},
        ...     setor_id="vestuario"
        ... )
        [("uniforme", "fardamento")]
    """
    if setor_id not in SECTOR_SYNONYMS:
        logger.debug(f"No synonym dictionary for sector '{setor_id}'")
        return []

    objeto_norm = normalize_text(objeto)
    synonyms_dict = SECTOR_SYNONYMS[setor_id]
    near_misses: List[Tuple[str, str]] = []
    matched_canonicals: Set[str] = set()  # Track which canonicals already matched

    for canonical_keyword in setor_keywords:
        canonical_norm = normalize_text(canonical_keyword)

        # Skip if canonical keyword already matches (not a near-miss)
        if canonical_norm in objeto_norm:
            continue

        # Skip if we already found a synonym for this canonical keyword
        if canonical_keyword in matched_canonicals:
            continue

        # Check synonyms for this canonical keyword
        if canonical_keyword not in synonyms_dict:
            continue

        # Sort synonyms by length (longest first) to prioritize longer exact matches
        # E.g., "fardamento" before "farda" to avoid fuzzy matching "fardamento" with "farda"
        sorted_synonyms = sorted(synonyms_dict[canonical_keyword], key=len, reverse=True)

        for synonym in sorted_synonyms:
            synonym_norm = normalize_text(synonym)

            # Exact match
            if synonym_norm in objeto_norm:
                near_misses.append((canonical_keyword, synonym))
                matched_canonicals.add(canonical_keyword)
                logger.debug(
                    f"Exact synonym match: '{synonym}' ≈ '{canonical_keyword}' "
                    f"in '{objeto[:100]}...'"
                )
                break  # Stop after first match for this canonical

            # Fuzzy match using SequenceMatcher
            # Compare each word in objeto with synonym
            objeto_words = objeto_norm.split()
            for word in objeto_words:
                similarity = SequenceMatcher(None, word, synonym_norm).ratio()
                if similarity >= similarity_threshold:
                    near_misses.append((canonical_keyword, synonym))
                    matched_canonicals.add(canonical_keyword)
                    logger.debug(
                        f"Fuzzy synonym match: '{word}' ≈ '{synonym}' "
                        f"(similarity: {similarity:.2f}) → '{canonical_keyword}'"
                    )
                    break  # Stop after first fuzzy match

            # If we found a match for this canonical, move to next canonical
            if canonical_keyword in matched_canonicals:
                break

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
