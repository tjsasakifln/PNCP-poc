"""DEBT-110 AC4: Density scoring, sector context analysis, and proximity checks.

Extracted from filter.py. Contains sector vocabulary analysis,
proximity context filtering, and co-occurrence pattern detection.
"""

import logging
import re
from typing import Dict, Optional, Tuple

from filter.keywords import normalize_text

logger = logging.getLogger(__name__)

# Sector-specific vocabulary mapping
SETOR_VOCABULARIOS = {
    "rodoviário": {
        "pavimentação",
        "asfalto",
        "estrada",
        "rodovia",
        "terraplanagem",
        "terraplenagem",
        "drenagem",
        "sinalização viária",
        "sinalizacao viaria",
        "ponte",
        "viaduto",
        "acostamento",
        "meio-fio",
        "meio fio",
        "guia",
        "sarjeta",
        "base",
        "sub-base",
        "sub base",
        "cbuq",
        "tsd",
        "imprimação",
        "imprimacao",
    },
    "hidroviário": {
        "dragagem",
        "porto",
        "atracação",
        "atracacao",
        "terminal hidroviário",
        "terminal hidroviario",
        "cais",
        "molhe",
        "píer",
        "pier",
        "dique",
        "eclusa",
        "bacia",
        "calado",
    },
    "edificações": {
        "construção civil",
        "construcao civil",
        "edificação",
        "edificacao",
        "reforma",
        "pintura",
        "alvenaria",
        "esquadria",
        "cobertura",
        "piso",
        "revestimento",
        "impermeabilização",
        "impermeabilizacao",
    },
    "elétrica": {
        "subestação",
        "subestacao",
        "transformador",
        "rede elétrica",
        "rede eletrica",
        "iluminação",
        "iluminacao",
        "poste",
        "cabo",
        "eletroduto",
        "disjuntor",
        "quadro elétrico",
        "quadro eletrico",
    },
    "saneamento": {
        "esgoto",
        "água",
        "agua",
        "tratamento",
        "estação elevatória",
        "estacao elevatoria",
        "rede coletora",
        "adutora",
        "reservatório",
        "reservatorio",
        "ete",
        "eta",
    },
    "tecnologia": {
        "software",
        "hardware",
        "computador",
        "servidor",
        "rede",
        "telecomunicação",
        "telecomunicacao",
        "fibra óptica",
        "fibra otica",
        "datacenter",
        "data center",
    },
}


def analisar_contexto_setor(termos_busca: list[str]) -> dict[str, float]:
    """
    Analyze search terms and return sector relevance scores.

    This function compares the normalized search terms against sector-specific
    vocabularies to determine which sectors are most relevant to the user's query.

    Args:
        termos_busca: List of search terms provided by the user

    Returns:
        Dictionary mapping sector names to relevance scores (0.0 to 1.0)

    Example:
        >>> analisar_contexto_setor(["pavimentação", "asfalto", "rodovia"])
        {"rodoviário": 1.0, "edificações": 0.0, ...}
    """
    if not termos_busca:
        return {}

    # Normalize all search terms
    termos_normalizados = [normalize_text(termo) for termo in termos_busca]

    # Calculate relevance score for each sector
    setor_scores: dict[str, float] = {}

    for setor_nome, vocabulario in SETOR_VOCABULARIOS.items():
        # Normalize vocabulary terms
        vocab_normalizado = {normalize_text(termo) for termo in vocabulario}

        # Count matches
        matches = 0
        for termo in termos_normalizados:
            # Check for exact matches or substring matches
            for vocab_term in vocab_normalizado:
                if termo in vocab_term or vocab_term in termo:
                    matches += 1
                    break

        # Calculate score as percentage of search terms that matched
        if termos_normalizados:
            score = matches / len(termos_normalizados)
        else:
            score = 0.0

        setor_scores[setor_nome] = score

    logger.debug(
        f"analisar_contexto_setor: termos={termos_busca} scores={setor_scores}"
    )

    return setor_scores


def obter_setor_dominante(
    termos_busca: list[str], threshold: float = 0.3
) -> str | None:
    """
    Return the dominant sector name or None if no clear sector detected.

    A sector is considered dominant if its relevance score exceeds the threshold
    and is higher than all other sectors.

    Args:
        termos_busca: List of search terms provided by the user
        threshold: Minimum score required to identify a dominant sector (default 0.3)

    Returns:
        Name of the dominant sector, or None if no sector is clearly dominant

    Example:
        >>> obter_setor_dominante(["pavimentação", "asfalto"])
        "rodoviário"
        >>> obter_setor_dominante(["software"])
        "tecnologia"
        >>> obter_setor_dominante(["algo genérico"])
        None
    """
    setor_scores = analisar_contexto_setor(termos_busca)

    if not setor_scores:
        return None

    # Find the sector with the highest score
    max_setor = max(setor_scores.items(), key=lambda x: x[1])
    setor_nome, score = max_setor

    # Only return if score meets threshold
    if score >= threshold:
        logger.debug(
            f"obter_setor_dominante: dominant sector='{setor_nome}' score={score:.2f}"
        )
        return setor_nome

    logger.debug(
        f"obter_setor_dominante: no dominant sector (max score={score:.2f} < {threshold})"
    )
    return None


def check_proximity_context(
    texto: str,
    matched_terms: list,
    current_sector: str,
    other_sectors_signatures: Dict[str, set],
    window_size: int = 8,
) -> Tuple[bool, Optional[str]]:
    """Check if matched keywords appear near signature terms of other sectors.

    When a keyword from the current sector matches, extracts a window of N words
    around each match position. If the window contains signature terms of ANOTHER
    sector, the bid is rejected as a cross-sector false positive.

    Args:
        texto: The bid's objetoCompra text (raw, will be normalized).
        matched_terms: List of keywords that matched in this bid.
        current_sector: The sector ID being evaluated.
        other_sectors_signatures: Dict mapping other sector IDs to their signature terms.
        window_size: Number of words before/after match to examine (default 8).

    Returns:
        Tuple of (should_reject: bool, reason: str | None).
        If should_reject is True, reason contains the rejection detail
        (e.g., "keyword:confeccao near alimentos:merenda").
    """
    if not texto or not matched_terms or window_size <= 0:
        return (False, None)

    texto_norm = normalize_text(texto)
    words = texto_norm.split()

    if not words:
        return (False, None)

    for term in matched_terms:
        term_norm = normalize_text(term)
        term_words = term_norm.split()
        term_len = len(term_words)

        # Find all positions where this term starts in the word array
        positions = []
        for i in range(len(words) - term_len + 1):
            if words[i:i + term_len] == term_words:
                positions.append(i)

        for pos in positions:
            # Extract window around the matched term
            win_start = max(0, pos - window_size)
            win_end = min(len(words), pos + term_len + window_size)
            window_words = words[win_start:win_end]
            window_text = " ".join(window_words)

            # Check signature terms of each OTHER sector
            for other_sector, sigs in other_sectors_signatures.items():
                for sig in sigs:
                    sig_norm = normalize_text(sig)
                    # Multi-word signature: check substring in window text
                    if " " in sig_norm:
                        if sig_norm in window_text:
                            return (
                                True,
                                f"keyword:{term} near {other_sector}:{sig}",
                            )
                    else:
                        # Single-word signature: check membership in window words
                        if sig_norm in window_words:
                            return (
                                True,
                                f"keyword:{term} near {other_sector}:{sig}",
                            )

    return (False, None)


# GTM-RESILIENCE-D03: Co-occurrence Negative Pattern Engine (Camada 1B.5)
# ============================================================================
# Deterministic, zero-LLM-cost check that detects false positive keyword
# matches by evaluating trigger + negative_context combinations.
# Runs AFTER keyword match, BEFORE density zone.
# ============================================================================

def check_co_occurrence(
    texto: str,
    rules: list,
    setor_id: str,
) -> tuple:
    """Check if a bid text triggers any co-occurrence rejection rule.

    GTM-RESILIENCE-D03 AC2: Evaluates trigger + negative_context + positive_signal
    combinations to detect false positive keyword matches.

    Args:
        texto: The bid's objetoCompra text (raw, will be normalized internally).
        rules: List of CoOccurrenceRule objects for this sector.
        setor_id: Sector ID (for logging/tracking).

    Returns:
        Tuple of (should_reject: bool, reason: str | None).
        If should_reject is True, reason contains the rejection detail.
    """
    if not rules or not texto:
        return (False, None)

    texto_norm = normalize_text(texto)

    for rule in rules:
        trigger_norm = normalize_text(rule.trigger)

        # AC2: Word boundary match for trigger (prefix matching)
        trigger_pattern = re.compile(
            rf'\b{re.escape(trigger_norm)}\w*\b', re.UNICODE
        )
        if not trigger_pattern.search(texto_norm):
            continue

        # Check negative contexts (prefix word-boundary match for singles,
        # substring for multi-word)
        matched_negative = None
        for neg_ctx in rule.negative_contexts:
            neg_norm = normalize_text(neg_ctx)
            # Multi-word negative contexts use substring match,
            # single-word uses prefix word boundary (handles plurals)
            if " " in neg_norm:
                if neg_norm in texto_norm:
                    matched_negative = neg_ctx
                    break
            else:
                neg_pattern = re.compile(
                    rf'\b{re.escape(neg_norm)}\w*\b', re.UNICODE
                )
                if neg_pattern.search(texto_norm):
                    matched_negative = neg_ctx
                    break

        if matched_negative is None:
            continue

        # Check positive signals (substring match — more permissive, AC2)
        has_positive = False
        for pos_sig in rule.positive_signals:
            pos_norm = normalize_text(pos_sig)
            if pos_norm in texto_norm:
                has_positive = True
                break

        if not has_positive:
            reason = f"trigger:{rule.trigger} + negative:{matched_negative}"
            return (True, reason)

    return (False, None)
