"""Keyword matching engine for uniform/apparel procurement filtering."""
import re
import unicodedata
from typing import Set, Tuple, List


# Primary keywords for uniform/apparel procurement (PRD Section 4.1)
KEYWORDS_UNIFORMES: Set[str] = {
    # Primary terms (high precision)
    "uniforme",
    "uniformes",
    "fardamento",
    "fardamentos",

    # Specific pieces
    "jaleco",
    "jalecos",
    "guarda-pó",
    "guarda-pós",
    "avental",
    "aventais",
    "colete",
    "coletes",
    "camiseta",
    "camisetas",
    "camisa polo",
    "camisas polo",
    "calça",
    "calças",
    "bermuda",
    "bermudas",
    "saia",
    "saias",
    "agasalho",
    "agasalhos",
    "jaqueta",
    "jaquetas",
    "boné",
    "bonés",
    "chapéu",
    "chapéus",
    "meia",
    "meias",

    # Specific contexts
    "uniforme escolar",
    "uniforme hospitalar",
    "uniforme administrativo",
    "fardamento militar",
    "fardamento escolar",
    "roupa profissional",
    "vestuário profissional",
    "vestimenta",
    "vestimentas",

    # Common compositions in procurement notices
    "kit uniforme",
    "conjunto uniforme",
    "confecção de uniforme",
    "aquisição de uniforme",
    "fornecimento de uniforme",
    "bota",
    "botas",
    "sapato",
    "sapatos",
}


# Exclusion keywords (prevent false positives - PRD Section 4.1)
KEYWORDS_EXCLUSAO: Set[str] = {
    "uniformização de procedimento",
    "uniformização de entendimento",
    "uniforme de trânsito",  # traffic signs/signals
    "padrão uniforme"        # technical/engineering context
}


def normalize_text(text: str) -> str:
    """
    Normalize text for keyword matching.

    Normalization steps:
    - Convert to lowercase
    - Remove accents (NFD + remove combining characters)
    - Remove excessive punctuation
    - Normalize whitespace

    Args:
        text: Input text to normalize

    Returns:
        Normalized text (lowercase, no accents, clean whitespace)

    Examples:
        >>> normalize_text("Jáleco Médico")
        'jaleco medico'
        >>> normalize_text("UNIFORME-ESCOLAR!!!")
        'uniforme escolar'
        >>> normalize_text("  múltiplos   espaços  ")
        'multiplos espacos'
    """
    if not text:
        return ""

    # Lowercase
    text = text.lower()

    # Remove accents using NFD normalization
    # NFD = Canonical Decomposition (separates base chars from combining marks)
    text = unicodedata.normalize("NFD", text)
    # Remove combining characters (category "Mn" = Mark, nonspacing)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")

    # Remove punctuation (keep only word characters and spaces)
    # Replace non-alphanumeric with spaces
    text = re.sub(r"[^\w\s]", " ", text)

    # Normalize multiple spaces to single space
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def match_keywords(
    objeto: str,
    keywords: Set[str],
    exclusions: Set[str] | None = None
) -> Tuple[bool, List[str]]:
    """
    Check if procurement object description contains uniform-related keywords.

    Uses word boundary matching to prevent partial matches:
    - "uniforme" matches "Aquisição de uniformes"
    - "uniforme" does NOT match "uniformemente" or "uniformização"

    Args:
        objeto: Procurement object description (objetoCompra from PNCP API)
        keywords: Set of keywords to search for (KEYWORDS_UNIFORMES)
        exclusions: Optional set of exclusion keywords (KEYWORDS_EXCLUSAO)

    Returns:
        Tuple containing:
        - bool: True if at least one keyword matched (and no exclusions found)
        - List[str]: List of matched keywords (original form, not normalized)

    Examples:
        >>> match_keywords("Aquisição de uniformes escolares", KEYWORDS_UNIFORMES)
        (True, ['uniformes', 'uniforme escolar'])

        >>> match_keywords("Uniformização de procedimento", KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO)
        (False, [])

        >>> match_keywords("Software de gestão", KEYWORDS_UNIFORMES)
        (False, [])
    """
    objeto_norm = normalize_text(objeto)

    # Check exclusions first (fail-fast optimization)
    if exclusions:
        for exc in exclusions:
            exc_norm = normalize_text(exc)
            # Use word boundary for exclusions too
            pattern = rf"\b{re.escape(exc_norm)}\b"
            if re.search(pattern, objeto_norm):
                return False, []

    # Search for matching keywords
    matched: List[str] = []
    for kw in keywords:
        kw_norm = normalize_text(kw)

        # Match by complete word (word boundary)
        # \b ensures we don't match partial words
        pattern = rf"\b{re.escape(kw_norm)}\b"
        if re.search(pattern, objeto_norm):
            matched.append(kw)

    return len(matched) > 0, matched
