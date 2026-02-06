"""Keyword matching engine for uniform/apparel procurement filtering."""

import logging
import re
import unicodedata
from typing import Set, Tuple, List, Dict, Optional

# Configure logging
logger = logging.getLogger(__name__)


# ---------- Portuguese Stopwords ----------
# Prepositions, articles, conjunctions, and other function words that should
# be stripped from user-supplied custom search terms to avoid generic matches.
# E.g., "de" matches virtually any procurement description.
STOPWORDS_PT: Set[str] = {
    # Artigos (articles)
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    # Preposições (prepositions)
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "por", "pelo", "pela", "pelos", "pelas", "para", "pra", "pro",
    "com", "sem", "sob", "sobre", "entre", "ate", "desde", "apos",
    "perante", "contra", "ante",
    # Contrações (contractions)
    "ao", "aos", "num", "numa", "nuns", "numas",
    "dele", "dela", "deles", "delas", "nele", "nela", "neles", "nelas",
    "deste", "desta", "destes", "destas", "neste", "nesta", "nestes", "nestas",
    "desse", "dessa", "desses", "dessas", "nesse", "nessa", "nesses", "nessas",
    "daquele", "daquela", "daqueles", "daquelas",
    "naquele", "naquela", "naqueles", "naquelas",
    "disto", "disso", "daquilo", "nisto", "nisso", "naquilo",
    # Conjunções (conjunctions)
    "e", "ou", "mas", "porem", "todavia", "contudo", "entretanto",
    "que", "se", "como", "quando", "porque", "pois", "enquanto",
    "nem", "tanto", "quanto", "logo", "portanto",
    # Pronomes relativos / demonstrativos comuns
    "que", "quem", "qual", "quais", "cujo", "cuja", "cujos", "cujas",
    "esse", "essa", "esses", "essas", "este", "esta", "estes", "estas",
    "aquele", "aquela", "aqueles", "aquelas", "isto", "isso", "aquilo",
    # Advérbios / palavras funcionais muito comuns
    "nao", "mais", "muito", "tambem", "ja", "ainda", "so", "apenas",
    "bem", "mal", "assim", "la", "aqui", "ali", "onde",
    # Verbos auxiliares / muito comuns (formas curtas)
    "ser", "ter", "estar", "ir", "vir", "fazer", "dar", "ver",
    "ha", "foi", "sao", "era", "sera",
}


def remove_stopwords(terms: list[str]) -> list[str]:
    """Remove Portuguese stopwords from a list of search terms.

    Terms are normalized (lowercased, accent-stripped) before comparison
    so that 'à', 'É', 'após' etc. are correctly identified as stopwords.

    Args:
        terms: List of user-supplied search terms (already lowercased).

    Returns:
        Filtered list with stopwords removed. Returns empty list if all
        terms are stopwords — caller should fall back to sector keywords.
    """
    return [t for t in terms if normalize_text(t) not in STOPWORDS_PT]


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

    # --- Military / defense (uniformes militares fora do escopo) ---
    "militar",
    "militares",
    "combate",
    "batalhão",
    "batalhao",
    "exercito",
    "exército",

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
    keywords: Set[str] | None = None,
    exclusions: Set[str] | None = None,
) -> Tuple[bool, Optional[str]]:
    """
    Apply all filters to a single procurement bid (fail-fast sequential filtering).

    Filter order (fastest to slowest for optimization):
    1. UF check (O(1) set lookup)
    2. Keyword matching (regex - most expensive)
    3. Status/deadline validation (datetime parsing)

    Note: Value range filter was REMOVED (2026-02-05) to return all results
    regardless of estimated value. This allows users to see all opportunities
    without arbitrary value restrictions.

    Args:
        licitacao: PNCP procurement bid dictionary
        ufs_selecionadas: Set of selected Brazilian state codes (e.g., {'SP', 'RJ'})

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

    # VALUE RANGE FILTER REMOVED (2026-02-05)
    # Previously filtered by valor_min/valor_max (R$ 10k - R$ 10M)
    # Now returns ALL results regardless of value to maximize opportunities

    # 2. Keyword Filter (most expensive - regex matching)
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
    keywords: Set[str] | None = None,
    exclusions: Set[str] | None = None,
) -> Tuple[List[dict], Dict[str, int]]:
    """
    Filter a batch of procurement bids and return statistics.

    Applies filter_licitacao() to each bid and tracks rejection reasons
    for observability and debugging.

    Note: Value range filter was REMOVED (2026-02-05) to return all results
    regardless of estimated value.

    Args:
        licitacoes: List of PNCP procurement bid dictionaries
        ufs_selecionadas: Set of selected Brazilian state codes

    Returns:
        Tuple containing:
        - List[dict]: Approved bids (passed all filters)
        - Dict[str, int]: Statistics dictionary with rejection counts

    Statistics Keys:
        - total: Total number of bids processed
        - aprovadas: Number of bids that passed all filters
        - rejeitadas_uf: Rejected due to UF not selected
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
        "rejeitadas_keyword": 0,
        "rejeitadas_prazo": 0,
        "rejeitadas_outros": 0,
    }

    for lic in licitacoes:
        aprovada, motivo = filter_licitacao(lic, ufs_selecionadas, keywords, exclusions)

        if aprovada:
            aprovadas.append(lic)
            stats["aprovadas"] += 1
        else:
            # Categorize rejection reason for statistics
            motivo_lower = (motivo or "").lower()
            if "uf" in motivo_lower and "não selecionada" in motivo_lower:
                stats["rejeitadas_uf"] += 1
            elif "keyword" in motivo_lower:
                stats["rejeitadas_keyword"] += 1
            elif "prazo" in motivo_lower:
                stats["rejeitadas_prazo"] += 1
            else:
                stats["rejeitadas_outros"] += 1

    return aprovadas, stats


# =============================================================================
# NEW FILTER FUNCTIONS (P0/P1 - Issue #xxx)
# =============================================================================


def filtrar_por_status(
    licitacoes: List[dict],
    status: str = "todos"
) -> List[dict]:
    """
    Filtra licitações por status do processo licitatório.

    Args:
        licitacoes: Lista de licitações da API PNCP
        status: Status desejado:
            - "recebendo_proposta": Licitações abertas para envio de propostas
            - "em_julgamento": Propostas encerradas, em análise
            - "encerrada": Processo finalizado
            - "todos": Sem filtro (retorna todas)

    Returns:
        Lista filtrada de licitações

    Examples:
        >>> bids = [
        ...     {"situacaoCompra": "Recebendo propostas"},
        ...     {"situacaoCompra": "Encerrada"},
        ... ]
        >>> filtrar_por_status(bids, "recebendo_proposta")
        [{'situacaoCompra': 'Recebendo propostas'}]
    """
    if not status or status == "todos":
        logger.debug("filtrar_por_status: status='todos', retornando todas")
        return licitacoes

    # Mapeamento de status interno para valores da API PNCP
    # A API pode retornar diferentes textos dependendo da versão
    status_map: Dict[str, List[str]] = {
        "recebendo_proposta": [
            "recebendo propostas",
            "aberta",
            "recebendo proposta",
            "em andamento",
            "publicada",
        ],
        "em_julgamento": [
            "propostas encerradas",
            "em julgamento",
            "julgamento",
            "análise",
            "analise",
            "avaliação",
            "avaliacao",
        ],
        "encerrada": [
            "encerrada",
            "finalizada",
            "homologada",
            "adjudicada",
            "concluída",
            "concluida",
            "anulada",
            "revogada",
            "fracassada",
            "deserta",
        ],
    }

    termos_aceitos = status_map.get(status.lower(), [])
    if not termos_aceitos:
        logger.warning(f"filtrar_por_status: status '{status}' desconhecido, retornando todas")
        return licitacoes

    resultado: List[dict] = []
    for lic in licitacoes:
        # Tenta diferentes campos que podem conter o status
        situacao = (
            lic.get("situacaoCompra", "")
            or lic.get("situacao", "")
            or lic.get("statusCompra", "")
            or ""
        ).lower()

        if any(termo in situacao for termo in termos_aceitos):
            resultado.append(lic)

    logger.debug(
        f"filtrar_por_status: {len(licitacoes)} -> {len(resultado)} "
        f"(status='{status}')"
    )
    return resultado


def filtrar_por_modalidade(
    licitacoes: List[dict],
    modalidades: List[int] | None
) -> List[dict]:
    """
    Filtra licitações por modalidade de contratação.

    Códigos de modalidade conforme PNCP:
        1 - Pregão Eletrônico
        2 - Pregão Presencial
        3 - Concorrência
        4 - Tomada de Preços
        5 - Convite
        6 - Dispensa de Licitação
        7 - Inexigibilidade
        8 - Credenciamento
        9 - Leilão
        10 - Diálogo Competitivo

    Args:
        licitacoes: Lista de licitações
        modalidades: Lista de códigos de modalidade (None = todas)

    Returns:
        Lista filtrada de licitações

    Examples:
        >>> bids = [
        ...     {"modalidadeId": 1, "objeto": "Pregão"},
        ...     {"modalidadeId": 6, "objeto": "Dispensa"},
        ... ]
        >>> filtrar_por_modalidade(bids, [1, 2])
        [{'modalidadeId': 1, 'objeto': 'Pregão'}]
    """
    if not modalidades:
        logger.debug("filtrar_por_modalidade: modalidades=None, retornando todas")
        return licitacoes

    resultado: List[dict] = []
    for lic in licitacoes:
        # A API PNCP pode usar diferentes nomes de campo para modalidade
        modalidade_id = (
            lic.get("modalidadeId")
            or lic.get("codigoModalidadeContratacao")
            or lic.get("modalidade_id")
        )

        # Tenta converter para int se for string
        if modalidade_id is not None:
            try:
                modalidade_id = int(modalidade_id)
            except (ValueError, TypeError):
                modalidade_id = None

        if modalidade_id in modalidades:
            resultado.append(lic)

    logger.debug(
        f"filtrar_por_modalidade: {len(licitacoes)} -> {len(resultado)} "
        f"(modalidades={modalidades})"
    )
    return resultado


def filtrar_por_valor(
    licitacoes: List[dict],
    valor_min: float | None = None,
    valor_max: float | None = None
) -> List[dict]:
    """
    Filtra licitações por faixa de valor estimado.

    Args:
        licitacoes: Lista de licitações
        valor_min: Valor mínimo (None = sem limite inferior)
        valor_max: Valor máximo (None = sem limite superior)

    Returns:
        Lista filtrada de licitações

    Examples:
        >>> bids = [
        ...     {"valorTotalEstimado": 50000},
        ...     {"valorTotalEstimado": 200000},
        ...     {"valorTotalEstimado": 1000000},
        ... ]
        >>> filtrar_por_valor(bids, valor_min=100000, valor_max=500000)
        [{'valorTotalEstimado': 200000}]
    """
    if valor_min is None and valor_max is None:
        logger.debug("filtrar_por_valor: sem limites, retornando todas")
        return licitacoes

    resultado: List[dict] = []
    for lic in licitacoes:
        # Tenta diferentes campos que podem conter o valor
        valor = (
            lic.get("valorTotalEstimado")
            or lic.get("valorEstimado")
            or lic.get("valor")
            or 0
        )

        # Converte string para float se necessário (formato brasileiro)
        if isinstance(valor, str):
            try:
                # Remove pontos de milhar e troca vírgula por ponto
                valor_limpo = valor.replace(".", "").replace(",", ".")
                valor = float(valor_limpo)
            except ValueError:
                valor = 0.0
        elif isinstance(valor, (int, float)):
            valor = float(valor)
        else:
            valor = 0.0

        # Aplica filtros de valor
        if valor_min is not None and valor < valor_min:
            continue
        if valor_max is not None and valor > valor_max:
            continue

        resultado.append(lic)

    logger.debug(
        f"filtrar_por_valor: {len(licitacoes)} -> {len(resultado)} "
        f"(min={valor_min}, max={valor_max})"
    )
    return resultado


def filtrar_por_esfera(
    licitacoes: List[dict],
    esferas: List[str] | None
) -> List[dict]:
    """
    Filtra licitações por esfera governamental.

    Args:
        licitacoes: Lista de licitações
        esferas: Lista de códigos de esfera:
            - "F" = Federal (União, autarquias federais, empresas públicas federais)
            - "E" = Estadual (Estados, DF, autarquias estaduais)
            - "M" = Municipal (Prefeituras, câmaras, autarquias municipais)

    Returns:
        Lista filtrada de licitações

    Examples:
        >>> bids = [
        ...     {"esferaId": "F", "orgao": "Ministério da Saúde"},
        ...     {"esferaId": "M", "orgao": "Prefeitura de SP"},
        ... ]
        >>> filtrar_por_esfera(bids, ["M"])
        [{'esferaId': 'M', 'orgao': 'Prefeitura de SP'}]
    """
    if not esferas:
        logger.debug("filtrar_por_esfera: esferas=None, retornando todas")
        return licitacoes

    # Normaliza para uppercase
    esferas_upper = [e.upper() for e in esferas]

    # Mapeamento de fallback baseado no tipo/nome do órgão
    esfera_keywords: Dict[str, List[str]] = {
        "F": [
            "federal", "união", "ministerio", "ministério",
            "autarquia federal", "empresa pública federal",
            "universidade federal", "instituto federal",
            "agência", "agencia", "ibama", "inss", "receita federal",
        ],
        "E": [
            "estadual", "estado", "secretaria de estado",
            "autarquia estadual", "governador", "governo do estado",
            "tribunal de justiça", "detran", "polícia militar",
            "policia militar", "assembleia legislativa",
        ],
        "M": [
            "municipal", "prefeitura", "câmara municipal", "camara municipal",
            "secretaria municipal", "autarquia municipal",
            "prefeito", "vereador", "município", "municipio",
        ],
    }

    resultado: List[dict] = []
    for lic in licitacoes:
        # Primeiro tenta pelo campo esferaId direto
        esfera_id = (
            lic.get("esferaId", "")
            or lic.get("esfera", "")
            or lic.get("tipoEsfera", "")
            or ""
        ).upper()

        if esfera_id in esferas_upper:
            resultado.append(lic)
            continue

        # Fallback: analisa pelo tipo/nome do órgão
        tipo_orgao = (
            lic.get("tipoOrgao", "")
            or lic.get("nomeOrgao", "")
            or lic.get("orgao", "")
            or ""
        ).lower()

        for esfera in esferas_upper:
            keywords = esfera_keywords.get(esfera, [])
            if any(kw in tipo_orgao for kw in keywords):
                resultado.append(lic)
                break

    logger.debug(
        f"filtrar_por_esfera: {len(licitacoes)} -> {len(resultado)} "
        f"(esferas={esferas})"
    )
    return resultado


def paginar_resultados(
    licitacoes: List[dict],
    pagina: int = 1,
    itens_por_pagina: int = 20
) -> Tuple[List[dict], Dict[str, int]]:
    """
    Pagina os resultados de licitações.

    Args:
        licitacoes: Lista completa de licitações
        pagina: Número da página (1-indexed). Padrão: 1.
        itens_por_pagina: Quantidade de itens por página. Padrão: 20.

    Returns:
        Tuple contendo:
        - List[dict]: Licitações da página solicitada
        - Dict[str, int]: Metadados de paginação com:
            - total: Total de itens
            - pagina: Página atual
            - itens_por_pagina: Itens por página
            - total_paginas: Total de páginas
            - inicio: Índice do primeiro item (0-indexed)
            - fim: Índice do último item (exclusivo)

    Examples:
        >>> bids = [{"id": i} for i in range(100)]
        >>> page, meta = paginar_resultados(bids, pagina=2, itens_por_pagina=20)
        >>> len(page)
        20
        >>> meta["total"]
        100
        >>> meta["total_paginas"]
        5
        >>> meta["inicio"]
        20
    """
    total = len(licitacoes)

    if total == 0:
        return [], {
            "total": 0,
            "pagina": 1,
            "itens_por_pagina": itens_por_pagina,
            "total_paginas": 0,
            "inicio": 0,
            "fim": 0,
        }

    # Calcula total de páginas
    total_paginas = (total + itens_por_pagina - 1) // itens_por_pagina

    # Garante que a página está dentro dos limites
    pagina = max(1, min(pagina, total_paginas))

    # Calcula índices de início e fim
    inicio = (pagina - 1) * itens_por_pagina
    fim = min(inicio + itens_por_pagina, total)

    # Extrai a página
    pagina_resultado = licitacoes[inicio:fim]

    metadata = {
        "total": total,
        "pagina": pagina,
        "itens_por_pagina": itens_por_pagina,
        "total_paginas": total_paginas,
        "inicio": inicio,
        "fim": fim,
    }

    logger.debug(
        f"paginar_resultados: página {pagina}/{total_paginas} "
        f"(itens {inicio+1}-{fim} de {total})"
    )

    return pagina_resultado, metadata


def filtrar_por_orgao(
    licitacoes: List[dict],
    orgaos: List[str] | None
) -> List[dict]:
    """
    Filtra licitações por nome do órgão/entidade contratante.

    Realiza busca parcial (contains) normalizada para encontrar licitações
    de órgãos específicos. A busca é case-insensitive e ignora acentos.

    Args:
        licitacoes: Lista de licitações
        orgaos: Lista de nomes de órgãos para filtrar (busca parcial).
                None = todos os órgãos.

    Returns:
        Lista filtrada de licitações

    Examples:
        >>> bids = [
        ...     {"nomeOrgao": "Prefeitura Municipal de São Paulo"},
        ...     {"nomeOrgao": "Ministério da Saúde"},
        ...     {"nomeOrgao": "INSS"},
        ... ]
        >>> filtrar_por_orgao(bids, ["Prefeitura"])
        [{'nomeOrgao': 'Prefeitura Municipal de São Paulo'}]
        >>> filtrar_por_orgao(bids, ["Ministerio", "INSS"])
        [{'nomeOrgao': 'Ministério da Saúde'}, {'nomeOrgao': 'INSS'}]
    """
    if not orgaos:
        logger.debug("filtrar_por_orgao: orgaos=None, retornando todas")
        return licitacoes

    # Normaliza os termos de busca
    orgaos_norm = [normalize_text(o) for o in orgaos if o]

    if not orgaos_norm:
        return licitacoes

    resultado: List[dict] = []
    for lic in licitacoes:
        # Tenta diferentes campos que podem conter o nome do órgão
        nome_orgao = (
            lic.get("nomeOrgao", "")
            or lic.get("orgao", "")
            or lic.get("nomeUnidade", "")
            or lic.get("entidade", "")
            or ""
        )
        nome_orgao_norm = normalize_text(nome_orgao)

        # Verifica se algum termo de busca está presente (busca parcial)
        for termo in orgaos_norm:
            if termo in nome_orgao_norm:
                resultado.append(lic)
                break  # Evita duplicatas

    logger.debug(
        f"filtrar_por_orgao: {len(licitacoes)} -> {len(resultado)} "
        f"(orgaos={len(orgaos)} termos)"
    )
    return resultado


def filtrar_por_municipio(
    licitacoes: List[dict],
    municipios: List[str] | None
) -> List[dict]:
    """
    Filtra licitações por código IBGE do município.

    Args:
        licitacoes: Lista de licitações
        municipios: Lista de códigos IBGE de municípios (7 dígitos)

    Returns:
        Lista filtrada de licitações

    Examples:
        >>> bids = [
        ...     {"codigoMunicipioIbge": "3550308", "municipio": "São Paulo"},
        ...     {"codigoMunicipioIbge": "3304557", "municipio": "Rio de Janeiro"},
        ... ]
        >>> filtrar_por_municipio(bids, ["3550308"])
        [{'codigoMunicipioIbge': '3550308', 'municipio': 'São Paulo'}]
    """
    if not municipios:
        logger.debug("filtrar_por_municipio: municipios=None, retornando todas")
        return licitacoes

    # Normaliza códigos para string
    municipios_str = [str(m).strip() for m in municipios]

    resultado: List[dict] = []
    for lic in licitacoes:
        # A API PNCP pode usar diferentes campos para código do município
        codigo_ibge = (
            lic.get("codigoMunicipioIbge")
            or lic.get("municipioId")
            or lic.get("codigoMunicipio")
            or lic.get("ibge")
            or ""
        )
        codigo_ibge = str(codigo_ibge).strip()

        if codigo_ibge in municipios_str:
            resultado.append(lic)

    logger.debug(
        f"filtrar_por_municipio: {len(licitacoes)} -> {len(resultado)} "
        f"(municipios={len(municipios)} códigos)"
    )
    return resultado


def aplicar_todos_filtros(
    licitacoes: List[dict],
    ufs_selecionadas: Set[str],
    status: str = "todos",
    modalidades: List[int] | None = None,
    valor_min: float | None = None,
    valor_max: float | None = None,
    esferas: List[str] | None = None,
    municipios: List[str] | None = None,
    orgaos: List[str] | None = None,
    keywords: Set[str] | None = None,
    exclusions: Set[str] | None = None,
) -> Tuple[List[dict], Dict[str, int]]:
    """
    Aplica todos os filtros em sequência otimizada (fail-fast).

    A ordem dos filtros é otimizada para descartar licitações o mais cedo
    possível, priorizando filtros rápidos (O(1)) antes dos lentos (regex):

    1. UF (O(1) - set lookup) - mais rápido
    2. Status (O(1) - string comparison)
    3. Esfera (O(1) - string comparison)
    4. Modalidade (O(1) - int comparison)
    5. Município (O(1) - string comparison)
    6. Órgão (O(n) - string contains) - P2 filter
    7. Valor (O(1) - numeric comparison)
    8. Keywords (O(n) - regex matching) - mais lento

    Args:
        licitacoes: Lista de licitações da API PNCP
        ufs_selecionadas: Set de UFs selecionadas (ex: {"SP", "RJ"})
        status: Status desejado ("recebendo_proposta", "em_julgamento", "encerrada", "todos")
        modalidades: Lista de códigos de modalidade (None = todas)
        valor_min: Valor mínimo (None = sem limite)
        valor_max: Valor máximo (None = sem limite)
        esferas: Lista de esferas ("F", "E", "M") (None = todas)
        municipios: Lista de códigos IBGE (None = todos)
        orgaos: Lista de nomes de órgãos para filtrar (None = todos)
        keywords: Set de keywords para matching (None = usa KEYWORDS_UNIFORMES)
        exclusions: Set de exclusões (None = usa KEYWORDS_EXCLUSAO)

    Returns:
        Tuple contendo:
        - List[dict]: Licitações aprovadas em todos os filtros
        - Dict[str, int]: Estatísticas detalhadas de rejeição

    Examples:
        >>> bids = [
        ...     {"uf": "SP", "valorTotalEstimado": 100000, "objetoCompra": "Uniformes"},
        ...     {"uf": "RJ", "valorTotalEstimado": 500000, "objetoCompra": "Outros"},
        ... ]
        >>> aprovadas, stats = aplicar_todos_filtros(
        ...     bids,
        ...     ufs_selecionadas={"SP"},
        ...     valor_min=50000,
        ...     valor_max=200000
        ... )
        >>> stats["total"]
        2
        >>> stats["aprovadas"]
        1
    """
    stats: Dict[str, int] = {
        "total": len(licitacoes),
        "aprovadas": 0,
        "rejeitadas_uf": 0,
        "rejeitadas_status": 0,
        "rejeitadas_esfera": 0,
        "rejeitadas_modalidade": 0,
        "rejeitadas_municipio": 0,
        "rejeitadas_orgao": 0,
        "rejeitadas_valor": 0,
        "rejeitadas_keyword": 0,
        "rejeitadas_outros": 0,
    }

    logger.info(
        f"aplicar_todos_filtros: iniciando com {len(licitacoes)} licitações"
    )

    # Etapa 1: Filtro de UF (mais rápido - O(1))
    resultado_uf: List[dict] = []
    for lic in licitacoes:
        uf = lic.get("uf", "")
        if uf in ufs_selecionadas:
            resultado_uf.append(lic)
        else:
            stats["rejeitadas_uf"] += 1

    logger.debug(
        f"  Após filtro UF: {len(resultado_uf)} "
        f"(rejeitadas: {stats['rejeitadas_uf']})"
    )

    # Etapa 2: Filtro de Status
    if status and status != "todos":
        resultado_status: List[dict] = []
        for lic in resultado_uf:
            situacao = (
                lic.get("situacaoCompra", "")
                or lic.get("situacao", "")
                or lic.get("statusCompra", "")
                or ""
            ).lower()

            status_map = {
                "recebendo_proposta": ["recebendo propostas", "aberta", "publicada"],
                "em_julgamento": ["propostas encerradas", "em julgamento", "julgamento"],
                "encerrada": ["encerrada", "finalizada", "homologada", "adjudicada"],
            }
            termos = status_map.get(status.lower(), [])

            if any(t in situacao for t in termos):
                resultado_status.append(lic)
            else:
                stats["rejeitadas_status"] += 1

        logger.debug(
            f"  Após filtro Status: {len(resultado_status)} "
            f"(rejeitadas: {stats['rejeitadas_status']})"
        )
    else:
        resultado_status = resultado_uf

    # Etapa 3: Filtro de Esfera
    if esferas:
        resultado_esfera: List[dict] = []
        esferas_upper = [e.upper() for e in esferas]

        for lic in resultado_status:
            esfera_id = (
                lic.get("esferaId", "")
                or lic.get("esfera", "")
                or ""
            ).upper()

            if esfera_id in esferas_upper:
                resultado_esfera.append(lic)
            else:
                # Fallback por tipo de órgão
                tipo_orgao = (lic.get("tipoOrgao", "") or lic.get("nomeOrgao", "")).lower()
                matched = False
                for esf in esferas_upper:
                    if esf == "F" and any(k in tipo_orgao for k in ["federal", "ministério", "ministerio"]):
                        matched = True
                    elif esf == "E" and any(k in tipo_orgao for k in ["estadual", "estado"]):
                        matched = True
                    elif esf == "M" and any(k in tipo_orgao for k in ["municipal", "prefeitura"]):
                        matched = True
                if matched:
                    resultado_esfera.append(lic)
                else:
                    stats["rejeitadas_esfera"] += 1

        logger.debug(
            f"  Após filtro Esfera: {len(resultado_esfera)} "
            f"(rejeitadas: {stats['rejeitadas_esfera']})"
        )
    else:
        resultado_esfera = resultado_status

    # Etapa 4: Filtro de Modalidade
    if modalidades:
        resultado_modalidade: List[dict] = []
        for lic in resultado_esfera:
            mod_id = lic.get("modalidadeId") or lic.get("codigoModalidadeContratacao")
            try:
                mod_id = int(mod_id) if mod_id is not None else None
            except (ValueError, TypeError):
                mod_id = None

            if mod_id in modalidades:
                resultado_modalidade.append(lic)
            else:
                stats["rejeitadas_modalidade"] += 1

        logger.debug(
            f"  Após filtro Modalidade: {len(resultado_modalidade)} "
            f"(rejeitadas: {stats['rejeitadas_modalidade']})"
        )
    else:
        resultado_modalidade = resultado_esfera

    # Etapa 5: Filtro de Município
    if municipios:
        resultado_municipio: List[dict] = []
        municipios_str = [str(m).strip() for m in municipios]

        for lic in resultado_modalidade:
            codigo = str(
                lic.get("codigoMunicipioIbge")
                or lic.get("municipioId")
                or ""
            ).strip()

            if codigo in municipios_str:
                resultado_municipio.append(lic)
            else:
                stats["rejeitadas_municipio"] += 1

        logger.debug(
            f"  Após filtro Município: {len(resultado_municipio)} "
            f"(rejeitadas: {stats['rejeitadas_municipio']})"
        )
    else:
        resultado_municipio = resultado_modalidade

    # Etapa 6: Filtro de Órgão (P2)
    if orgaos:
        resultado_orgao: List[dict] = []
        orgaos_norm = [normalize_text(o) for o in orgaos if o]

        for lic in resultado_municipio:
            nome_orgao = (
                lic.get("nomeOrgao", "")
                or lic.get("orgao", "")
                or lic.get("nomeUnidade", "")
                or ""
            )
            nome_orgao_norm = normalize_text(nome_orgao)

            matched = False
            for termo in orgaos_norm:
                if termo in nome_orgao_norm:
                    matched = True
                    break

            if matched:
                resultado_orgao.append(lic)
            else:
                stats["rejeitadas_orgao"] += 1

        logger.debug(
            f"  Após filtro Órgão: {len(resultado_orgao)} "
            f"(rejeitadas: {stats['rejeitadas_orgao']})"
        )
    else:
        resultado_orgao = resultado_municipio

    # Etapa 7: Filtro de Valor
    if valor_min is not None or valor_max is not None:
        resultado_valor: List[dict] = []
        for lic in resultado_orgao:
            valor = lic.get("valorTotalEstimado") or lic.get("valorEstimado") or 0

            if isinstance(valor, str):
                try:
                    valor = float(valor.replace(".", "").replace(",", "."))
                except ValueError:
                    valor = 0.0
            else:
                valor = float(valor) if valor else 0.0

            if valor_min is not None and valor < valor_min:
                stats["rejeitadas_valor"] += 1
                continue
            if valor_max is not None and valor > valor_max:
                stats["rejeitadas_valor"] += 1
                continue

            resultado_valor.append(lic)

        logger.debug(
            f"  Após filtro Valor: {len(resultado_valor)} "
            f"(rejeitadas: {stats['rejeitadas_valor']})"
        )
    else:
        resultado_valor = resultado_orgao

    # Etapa 8: Filtro de Keywords (mais lento - regex)
    kw = keywords if keywords is not None else KEYWORDS_UNIFORMES
    exc = exclusions if exclusions is not None else KEYWORDS_EXCLUSAO

    aprovadas: List[dict] = []
    for lic in resultado_valor:
        objeto = lic.get("objetoCompra", "")
        match, _ = match_keywords(objeto, kw, exc)

        if match:
            aprovadas.append(lic)
        else:
            stats["rejeitadas_keyword"] += 1

    stats["aprovadas"] = len(aprovadas)

    logger.info(
        f"aplicar_todos_filtros: concluído - {stats['aprovadas']}/{stats['total']} aprovadas"
    )
    logger.debug(f"  Estatísticas completas: {stats}")

    return aprovadas, stats
