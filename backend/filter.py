"""Keyword matching engine for uniform/apparel procurement filtering."""

import re
import unicodedata
from datetime import datetime
from typing import Set, Tuple, List, Dict, Optional


# Primary keywords for uniform/apparel procurement (PRD Section 4.1)
#
# Strategy: keep ALL clothing-related terms (including ambiguous ones like
# "camisa", "boné", "avental", "colete", "confecção") to avoid false
# negatives, but rely on an extensive KEYWORDS_EXCLUSAO set to filter out
# non-clothing contexts. This ensures we catch "Aquisição de camisas polo
# para guardas" while excluding "confecção de placas de sinalização".
KEYWORDS_UNIFORMES: Set[str] = {
    # Primary terms (high precision)
    "uniforme",
    "uniformes",
    "fardamento",
    "fardamentos",
    "farda",
    "fardas",
    # General apparel terms
    "vestuario",
    "vestimenta",
    "vestimentas",
    "indumentaria",
    "roupa",
    "roupas",
    "roupa profissional",
    "vestuario profissional",
    # Textile / manufacturing (ambiguous — guarded by exclusions)
    "confecção",
    "confecções",
    "confeccao",
    "confeccoes",
    "costura",
    # Specific clothing pieces
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
    "camisa",
    "camisas",
    "camisa polo",
    "camisas polo",
    "blusa",
    "blusas",
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
    "macacão",
    "macacoes",
    "jardineira",
    "jardineiras",
    "gandola",
    "gandolas",
    "boné",
    "bonés",
    "meia",
    "meias",
    "bota",
    "botas",
    "sapato",
    "sapatos",
    # Specific contexts
    "uniforme escolar",
    "uniforme hospitalar",
    "uniforme administrativo",
    "uniforme esportivo",
    "uniformes esportivos",
    "uniforme profissional",
    "fardamento militar",
    "fardamento escolar",
    "epi vestuario",
    "epi vestimenta",
    # EPI (Equipamento de Proteção Individual) — often includes apparel
    "epi",
    "epis",
    "equipamento de protecao individual",
    "equipamentos de protecao individual",
    # Common compositions in procurement notices
    "kit uniforme",
    "conjunto uniforme",
    "confecção de uniforme",
    "confecção de uniformes",
    "confeccao de uniforme",
    "confeccao de uniformes",
    "confecção de camiseta",
    "confecção de camisetas",
    "confeccao de camiseta",
    "confeccao de camisetas",
    "aquisição de uniforme",
    "aquisição de uniformes",
    "fornecimento de uniforme",
    "fornecimento de uniformes",
    "aquisição de vestuario",
    "fornecimento de vestuario",
    "aquisição de fardamento",
    "fornecimento de fardamento",
}


# Exclusion keywords (prevent false positives - PRD Section 4.1)
# Matches are checked FIRST; if any exclusion matches, the bid is rejected
# even if a primary keyword also matches.
#
# This list MUST be comprehensive because we keep ambiguous keywords
# (confecção, costura, camisa, colete, avental, boné, bota, meia, etc.)
# to avoid false negatives. Each exclusion blocks a known non-clothing
# context for those ambiguous terms.
KEYWORDS_EXCLUSAO: Set[str] = {
    # --- "uniforme/uniformização" in non-clothing context ---
    "uniformização de procedimento",
    "uniformização de entendimento",
    "uniformização de jurisprudência",
    "uniformização de jurisprudencia",
    "uniforme de trânsito",
    "uniforme de transito",
    "padrão uniforme",
    "padrao uniforme",
    "padronização de uniforme escolar",  # software platforms, not clothing
    "padronizacao de uniforme escolar",

    # --- "confecção" in non-clothing context (manufacturing/fabrication) ---
    "confecção de placa",
    "confecção de placas",
    "confeccao de placa",
    "confeccao de placas",
    "confecção de grade",
    "confecção de grades",
    "confeccao de grade",
    "confeccao de grades",
    "confecção de protese",
    "confecção de prótese",
    "confecção de proteses",
    "confecção de próteses",
    "confeccao de protese",
    "confeccao de proteses",
    "confecção de merenda",
    "confeccao de merenda",
    "confecção de material grafico",
    "confecção de material gráfico",
    "confecção de materiais graficos",
    "confecção de materiais gráficos",
    "confeccao de material grafico",
    "confecção de peças",
    "confeccao de pecas",
    "confecção de chave",
    "confecção de chaves",
    "confeccao de chave",
    "confeccao de chaves",
    "confecção de carimbo",
    "confecção de carimbos",
    "confecção de letras",
    "confeccao de letras",
    "confecção de plotagem",
    "confecção de plotagens",
    "confeccao de plotagem",
    "confecção de tampa",
    "confecção de tampas",
    "confeccao de tampa",
    "confecção de embalagem",
    "confecção de embalagens",
    "confeccao de embalagem",
    "confecção de mochilas",
    "confeccao de mochilas",
    "confecção e impressão",
    "confeccao e impressao",
    "confecção e instalação",
    "confeccao e instalacao",
    "confecção e fornecimento de placa",
    "confecção e fornecimento de placas",
    "confecção de portão",
    "confecção de portões",
    "confeccao de portao",
    "confeccao de portoes",
    "confecção de peças de ferro",
    "confeccao de pecas de ferro",

    # --- "costura" in non-procurement context (courses/training) ---
    "curso de corte",
    "oficina de corte",
    "aula de corte",
    "instrutor de corte",
    "instrutor de costura",
    "curso de costura",
    "oficina de costura",
    "aula de costura",

    # --- "malha" in non-textile context ---
    "malha viaria",
    "malha viária",
    "malha rodoviaria",
    "malha rodoviária",
    "malha tensionada",
    "malha de fibra optica",
    "malha de fibra óptica",

    # --- "avental" in non-clothing context ---
    "avental plumbifero",
    "avental plumbífero",

    # --- "chapéu/boné" in non-clothing context ---
    "chapéu pensador",
    "chapeu pensador",

    # --- "camisa" in non-clothing context ---
    "amor à camisa",
    "amor a camisa",

    # --- "bota" in non-footwear context ---
    "bota de concreto",
    "bota de cimento",

    # --- "meia" in non-clothing context ---
    "meia entrada",

    # --- Software / digital ---
    "software de uniforme",
    "plataforma de uniforme",
    "solução de software",
    "solucao de software",
    "plataforma web",

    # --- Decoration / events / costumes ---
    "decoração",
    "decoracao",
    "fantasia",
    "fantasias",
    "traje oficial",
    "trajes oficiais",

    # --- Non-apparel manufacturing ---
    "tapeçaria",
    "tapecaria",
    "forração",
    "forracao",

    # --- "roupa" in non-clothing context (bed/table linens) ---
    "roupa de cama",
    "roupa de mesa",
    "roupa de banho",
    "cama mesa e banho",
    "enxoval hospitalar",
    "enxoval hospital",

    # --- "colete" in non-apparel context ---
    "colete salva vidas",
    "colete salva vida",
    "colete balistico",
    "colete balístico",

    # --- "bota" in non-footwear context (expanded) ---
    "bota de borracha para construcao",

    # --- Construction / infrastructure that matches "bota", "colete" etc. ---
    "material de construção",
    "material de construcao",
    "materiais de construção",
    "materiais de construcao",
    "sinalização",
    "sinalizacao",
    "sinalização visual",
    "sinalizacao visual",
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
    objeto: str, keywords: Set[str], exclusions: Set[str] | None = None
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


def filter_licitacao(
    licitacao: dict,
    ufs_selecionadas: Set[str],
    valor_min: float = 50_000.0,
    valor_max: float = 5_000_000.0,
    keywords: Set[str] | None = None,
    exclusions: Set[str] | None = None,
) -> Tuple[bool, Optional[str]]:
    """
    Apply all filters to a single procurement bid (fail-fast sequential filtering).

    Filter order (fastest to slowest for optimization):
    1. UF check (O(1) set lookup)
    2. Value range check (simple numeric comparison)
    3. Keyword matching (regex - most expensive)
    4. Status/deadline validation (datetime parsing)

    Args:
        licitacao: PNCP procurement bid dictionary
        ufs_selecionadas: Set of selected Brazilian state codes (e.g., {'SP', 'RJ'})
        valor_min: Minimum bid value in BRL (default: R$ 50,000)
        valor_max: Maximum bid value in BRL (default: R$ 5,000,000)

    Returns:
        Tuple containing:
        - bool: True if bid passes all filters, False otherwise
        - Optional[str]: Rejection reason if rejected, None if approved

    Examples:
        >>> bid = {
        ...     "uf": "SP",
        ...     "valorTotalEstimado": 150000.0,
        ...     "objetoCompra": "Aquisição de uniformes escolares",
        ...     "dataAberturaProposta": "2026-12-31T10:00:00Z"
        ... }
        >>> filter_licitacao(bid, {"SP"})
        (True, None)

        >>> bid_rejected = {"uf": "RJ", "valorTotalEstimado": 100000.0}
        >>> filter_licitacao(bid_rejected, {"SP"})
        (False, "UF 'RJ' não selecionada")
    """
    # 1. UF Filter (fastest check)
    uf = licitacao.get("uf", "")
    if uf not in ufs_selecionadas:
        return False, f"UF '{uf}' não selecionada"

    # 2. Value Range Filter
    valor = licitacao.get("valorTotalEstimado")
    if valor is None:
        return False, "Valor não informado"

    if not (valor_min <= valor <= valor_max):
        return False, f"Valor R$ {valor:,.2f} fora da faixa"

    # 3. Keyword Filter (most expensive - regex matching)
    kw = keywords if keywords is not None else KEYWORDS_UNIFORMES
    exc = exclusions if exclusions is not None else KEYWORDS_EXCLUSAO
    objeto = licitacao.get("objetoCompra", "")
    match, keywords_found = match_keywords(objeto, kw, exc)

    if not match:
        return False, "Não contém keywords do setor"

    # 4. Deadline Filter - DESABILITADO
    # O campo dataAberturaProposta representa a data de ABERTURA das propostas,
    # NAO o prazo final para submissao. Licitacoes historicas sao validas para
    # analise, planejamento e identificacao de oportunidades recorrentes.
    #
    # Para filtrar por prazo de submissao, seria necessario usar o campo
    # dataFimReceberPropostas quando disponivel na API PNCP.
    #
    # Referencia: Investigacao 2026-01-28 - docs/investigations/
    #
    # TODO: Implementar filtro OPCIONAL por prazo quando usuario solicitar:
    # data_fim_str = licitacao.get("dataFimReceberPropostas")
    # if data_fim_str and filtrar_encerradas:
    #     data_fim = datetime.fromisoformat(data_fim_str.replace("Z", "+00:00"))
    #     if data_fim < datetime.now(data_fim.tzinfo):
    #         return False, "Prazo de submissao encerrado"

    return True, None


def filter_batch(
    licitacoes: List[dict],
    ufs_selecionadas: Set[str],
    valor_min: float = 50_000.0,
    valor_max: float = 5_000_000.0,
    keywords: Set[str] | None = None,
    exclusions: Set[str] | None = None,
) -> Tuple[List[dict], Dict[str, int]]:
    """
    Filter a batch of procurement bids and return statistics.

    Applies filter_licitacao() to each bid and tracks rejection reasons
    for observability and debugging.

    Args:
        licitacoes: List of PNCP procurement bid dictionaries
        ufs_selecionadas: Set of selected Brazilian state codes
        valor_min: Minimum bid value in BRL (default: R$ 50,000)
        valor_max: Maximum bid value in BRL (default: R$ 5,000,000)

    Returns:
        Tuple containing:
        - List[dict]: Approved bids (passed all filters)
        - Dict[str, int]: Statistics dictionary with rejection counts

    Statistics Keys:
        - total: Total number of bids processed
        - aprovadas: Number of bids that passed all filters
        - rejeitadas_uf: Rejected due to UF not selected
        - rejeitadas_valor: Rejected due to value outside range
        - rejeitadas_keyword: Rejected due to missing uniform keywords
        - rejeitadas_prazo: Rejected due to deadline passed
        - rejeitadas_outros: Rejected for other reasons

    Examples:
        >>> bids = [
        ...     {"uf": "SP", "valorTotalEstimado": 100000, "objetoCompra": "Uniformes"},
        ...     {"uf": "RJ", "valorTotalEstimado": 100000, "objetoCompra": "Uniformes"}
        ... ]
        >>> aprovadas, stats = filter_batch(bids, {"SP"})
        >>> stats["total"]
        2
        >>> stats["aprovadas"]
        1
        >>> stats["rejeitadas_uf"]
        1
    """
    aprovadas: List[dict] = []
    stats: Dict[str, int] = {
        "total": len(licitacoes),
        "aprovadas": 0,
        "rejeitadas_uf": 0,
        "rejeitadas_valor": 0,
        "rejeitadas_keyword": 0,
        "rejeitadas_prazo": 0,
        "rejeitadas_outros": 0,
    }

    for lic in licitacoes:
        aprovada, motivo = filter_licitacao(lic, ufs_selecionadas, valor_min, valor_max, keywords, exclusions)

        if aprovada:
            aprovadas.append(lic)
            stats["aprovadas"] += 1
        else:
            # Categorize rejection reason for statistics
            motivo_lower = (motivo or "").lower()
            if "uf" in motivo_lower and "não selecionada" in motivo_lower:
                stats["rejeitadas_uf"] += 1
            elif "valor" in motivo_lower and "fora da faixa" in motivo_lower:
                stats["rejeitadas_valor"] += 1
            elif "keyword" in motivo_lower:
                stats["rejeitadas_keyword"] += 1
            elif "prazo" in motivo_lower:
                stats["rejeitadas_prazo"] += 1
            else:
                stats["rejeitadas_outros"] += 1

    return aprovadas, stats
