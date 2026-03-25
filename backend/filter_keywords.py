"""DEBT-110 AC4: Keyword matching engine — extracted from filter.py.

Contains text normalization, keyword constants, red flag detection,
and the core match_keywords() function.
"""

import logging
import re
import unicodedata
from typing import Set, Tuple, List, Dict, Optional

# Configure logging
logger = logging.getLogger(__name__)

# STORY-248 AC9: Lazy import to avoid circular dependency at module load time.
# The tracker is imported inside functions that need it.
_filter_stats_tracker = None


def _get_tracker():
    """Lazy-load the filter stats tracker singleton."""
    global _filter_stats_tracker
    if _filter_stats_tracker is None:
        from filter_stats import filter_stats_tracker
        _filter_stats_tracker = filter_stats_tracker
    return _filter_stats_tracker


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


def validate_terms(terms: list[str]) -> dict:
    """
    Valida termos de busca e retorna válidos/ignorados com motivos.

    CRITICAL: Esta função garante que cada termo está OU em 'valid' OU em 'ignored',
    NUNCA em ambos. Isso elimina o bug de mostrar termos como "usados" e "ignorados"
    simultaneamente.

    Args:
        terms: Lista de termos digitados pelo usuário (pode ter espaços extras)

    Returns:
        {
            'valid': [...],      # Termos que serão usados (normalizados)
            'ignored': [...],    # Termos que não serão usados (originais)
            'reasons': {...}     # {termo_original: motivo_da_rejeição}
        }

    Examples:
        >>> validate_terms(['uniforme escolar', ' jaleco', '  de', 'abc'])
        {
            'valid': ['uniforme escolar', 'jaleco'],
            'ignored': ['de', 'abc'],
            'reasons': {
                'de': 'Palavra comum não indexada (stopword)',
                'abc': 'Termo muito curto (mínimo 4 caracteres)'
            }
        }
    """
    MIN_LENGTH = 4

    valid = []
    ignored = []
    reasons = {}

    for term in terms:
        term_original = term  # Preserva para mensagens de erro
        term_clean = term.strip().lower()  # Normaliza para validação

        # VALIDAÇÃO 1: Termo vazio após strip
        if not term_clean:
            ignored.append(term_original)
            reasons[term_original] = 'Termo vazio ou apenas espaços'
            continue

        # VALIDAÇÃO 2: Stopword (word-boundary check para frases)
        # Para frases como "uniforme escolar", verifica se alguma palavra é stopword pura
        words = term_clean.split()
        if len(words) == 1 and normalize_text(term_clean) in STOPWORDS_PT:
            ignored.append(term_original)
            reasons[term_original] = 'Palavra comum não indexada (stopword)'
            continue

        # VALIDAÇÃO 3: Comprimento mínimo (para termos únicos)
        # Frases multi-palavra são permitidas mesmo se contiverem palavras curtas
        if len(words) == 1 and len(term_clean) < MIN_LENGTH:
            ignored.append(term_original)
            reasons[term_original] = f'Termo muito curto (mínimo {MIN_LENGTH} caracteres)'
            continue

        # VALIDAÇÃO 4: Caracteres especiais perigosos
        # Permite: letras, números, espaços, hífens, acentos
        if not all(c.isalnum() or c.isspace() or c in '-áéíóúàèìòùâêîôûãõñç' for c in term_clean):
            ignored.append(term_original)
            reasons[term_original] = 'Contém caracteres especiais não permitidos'
            continue

        # TERMO VÁLIDO: Adiciona normalizado (sem espaços extras)
        valid.append(term_clean)

    # INVARIANTE CRÍTICO: Garantir que não há interseção entre valid e ignored
    # Compara versões normalizadas para detectar duplicatas
    valid_normalized = {t.strip().lower() for t in valid}
    ignored_normalized = {t.strip().lower() for t in ignored}
    intersection = valid_normalized.intersection(ignored_normalized)

    if intersection:
        # BUG DETECTADO - deve ser IMPOSSÍVEL chegar aqui
        logger.error(
            f"CRITICAL BUG: Termos em ambas as listas (valid E ignored): {intersection}. "
            f"valid={valid}, ignored={ignored}"
        )
        raise AssertionError(
            f"BUG: Termo não pode estar em 'valid' E 'ignored': {intersection}"
        )

    return {
        'valid': valid,
        'ignored': ignored,
        'reasons': reasons
    }


def remove_stopwords(terms: list[str]) -> list[str]:
    """Remove Portuguese stopwords from a list of search terms.

    DEPRECATED: Use validate_terms() for new code. This function is kept
    for backward compatibility with existing code.

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

    # --- STORY-181 AC5.1: Medical/health context (EPI != uniforme profissional) ---
    "assistencia ao paciente",
    "assistência ao paciente",
    "material hospitalar",
    "materiais hospitalares",
    "material de saude",
    "material de saúde",
    "materiais de saude",
    "materiais de saúde",
    "uti",
    "unidade de terapia intensiva",
    "centro cirurgico",
    "centro cirúrgico",
    "ambulatorio",
    "ambulatório",
    "pronto-socorro",
    "pronto socorro",
    "produtos para saude",
    "produtos para saúde",
    "equipamento medico",
    "equipamento médico",
    "equipamentos medicos",
    "equipamentos médicos",
    "equipamento hospitalar",
    "equipamentos hospitalares",

    # --- STORY-181 AC5.2: HR/Administrative context ---
    "processo seletivo",
    "selecao de pessoal",
    "seleção de pessoal",
    "recrutamento",
    "contratacao de pessoal",
    "contratação de pessoal",
    "concurso publico",
    "concurso público",
    "teste seletivo",
    "avaliacao de candidatos",
    "avaliação de candidatos",
    "admissão de pessoal",
    "admissao de pessoal",

    # --- STORY-181 AC5.3: Engineering/infrastructure context ---
    "obra de infraestrutura",
    "obra de pavimentacao",
    "obra de pavimentação",
    "obra de drenagem",
    "obra de saneamento",
    "execucao de obra",
    "execução de obra",
    "servicos de engenharia",
    "serviços de engenharia",

    # --- STORY-248 AC5: Cross-sector ambiguity exclusions ---
    # These prevent false positives where a keyword from one sector
    # matches text that clearly belongs to a different domain.

    # "papel" (papelaria) in non-stationery context
    "papel de parede",
    "papel moeda",

    # "cola" (papelaria) in non-stationery context
    "cola de contato",
    "cola epóxi",
    "cola epoxi",

    # "pasta" (papelaria) in non-stationery context
    "pasta térmica",
    "pasta termica",

    # "ferro" (engenharia) in non-construction context
    "ferro de solda",

    # "areia" (engenharia) in non-construction context
    "areia para gato",
    "areia sanitária",
    "areia sanitaria",

    # "bota" (vestuario) in medical context
    "bota ortopédica",
    "bota ortopedica",

    # "luva" (multiple sectors) in sports context
    "luva de boxe",
    "luva de goleiro",

    # "meia" (vestuario) in idiomatic/non-clothing context
    "meia idade",
    "meia pensão",
    "meia pensao",

    # "saia" (vestuario) in idiomatic context
    "saia justa",

    # "agenda" (papelaria) in non-product context
    "agenda política",
    "agenda politica",
    "agenda regulatória",
    "agenda regulatoria",

    # "grampo" (papelaria) in surveillance context
    "grampo telefônico",
    "grampo telefonico",

    # "tesoura" (papelaria) in medical context
    "tesoura cirúrgica",
    "tesoura cirurgica",

    # "piso" (engenharia) in HR context
    "piso salarial",

    # "monitor" (informatica) in medical context
    "monitor cardíaco",
    "monitor cardiaco",

    # "revestimento" (engenharia) in biological context
    "revestimento celular",

    # "transformador" (materiais_eletricos) in figurative context
    "transformador social",
    "transformador de vidas",

    # "diesel" (transporte) in generator context
    "motor diesel estacionário",
    "motor diesel estacionario",
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


# =============================================================================
# STORY-328: Strip org context clauses from objetoCompra
# =============================================================================
# ~30% of PNCP objetoCompra fields include the buying agency name in the
# description text.  Keywords that match on the agency name (e.g. "saúde"
# matching "Secretaria de Saúde") produce false positives across ALL sectors.
# This function strips those trailing context clauses BEFORE keyword matching
# so that density calculation and keyword gates operate only on the actual
# object being procured.

# Pre-compiled regex patterns for org context clauses (applied on normalized text)
_ORG_CONTEXT_PATTERNS: List[re.Pattern] = [
    # "para atender/atendimento (às) necessidades/demandas da/do ..." to end
    re.compile(
        r'\bpara\s+atend(?:er|imento)\s+(?:a|as?)\s*(?:necessidades?|demandas?)\s+'
        r'(?:da|das|do|dos)\b.*',
        re.IGNORECASE,
    ),
    # "em atendimento (às) demandas/necessidades da/do ..." to end
    re.compile(
        r'\bem\s+atendimento\s+(?:a|as?)\s*(?:demandas?|necessidades?)\s+'
        r'(?:da|das|do|dos)\b.*',
        re.IGNORECASE,
    ),
    # "visando atender ..." to end
    re.compile(
        r'\bvisando\s+atender\b.*',
        re.IGNORECASE,
    ),
    # "de interesse da/do ..." to end
    re.compile(
        r'\bde\s+interesse\s+(?:da|das|do|dos)\b.*',
        re.IGNORECASE,
    ),
    # "pertencente(s) a/à/ao(s) ... secretaria/prefeitura/município ..." to end
    re.compile(
        r'\bpertencentes?\s+(?:a|as?|ao|aos)\b.*',
        re.IGNORECASE,
    ),
    # "a pedido da/do ..." to end
    re.compile(
        r'\ba\s+pedido\s+(?:da|do)\b.*',
        re.IGNORECASE,
    ),
    # "através da/do ... Secretaria/Prefeitura/Instituto ..." to end
    re.compile(
        r'\batraves\s+(?:da|do)\s+(?:secretaria|prefeitura|municipio|instituto|'
        r'ministerio|fundacao|departamento|diretoria|superintendencia|'
        r'coordenadoria|gerencia|consorcio|autarquia)\b.*',
        re.IGNORECASE,
    ),
    # "conforme demanda da/do ..." to end
    re.compile(
        r'\bconforme\s+demanda\s+(?:da|das|do|dos)\b.*',
        re.IGNORECASE,
    ),
    # "destinado(s/a/as) a/à/ao(s) Secretaria/Prefeitura ..." to end
    re.compile(
        r'\bdestinados?\s*(?:a|as?|ao|aos)\s+(?:secretaria|prefeitura|municipio|'
        r'hospital|instituto|fundacao|departamento|diretoria|consorcio)\b.*',
        re.IGNORECASE,
    ),
    # "no âmbito da/do ..." to end
    re.compile(
        r'\bno\s+ambito\s+(?:da|das|do|dos)\b.*',
        re.IGNORECASE,
    ),
]

# AC2: PCP source prefixes to strip (handles both accented and unaccented)
_PCP_PREFIX_PATTERNS: List[re.Pattern] = [
    re.compile(r'^\s*\[?\s*portal\s+de\s+compras\s+p[uú]blicas\s*\]?\s*[-–—:]\s*', re.IGNORECASE),
    re.compile(r'^\s*\[?\s*pcp\s*\]?\s*[-–—:]\s*', re.IGNORECASE),
]


def _strip_org_context(texto: str) -> str:
    """Strip buying-agency context clauses from objetoCompra text.

    Removes trailing clauses like "para atender às necessidades da Secretaria
    de Saúde" that cause cross-sector false positives when the agency name
    contains a sector keyword.

    STORY-328 AC1-AC3: Operates on normalized text (no accents) for matching
    but returns cleaned text so downstream keyword matching is accurate.

    Args:
        texto: Raw objetoCompra text from PNCP/PCP/ComprasGov.

    Returns:
        Text with org context clauses removed. If no clauses found, returns
        the original text unchanged.
    """
    if not texto:
        return ""

    result = texto

    # AC2: Strip PCP source prefixes first
    for pat in _PCP_PREFIX_PATTERNS:
        result = pat.sub("", result)

    # AC3: Normalize for matching (work on accent-free copy)
    result_norm = normalize_text(result)

    # Apply each org context pattern to find the earliest match
    earliest_start = len(result_norm)
    for pat in _ORG_CONTEXT_PATTERNS:
        m = pat.search(result_norm)
        if m and m.start() < earliest_start:
            earliest_start = m.start()

    if earliest_start < len(result_norm):
        # Trim the original (non-normalized) text at the same position
        result = result[:earliest_start].rstrip(" ,;-–—")

    return result.strip()


def _strip_org_context_with_detail(texto: str) -> tuple:
    """Strip org context and return both cleaned text and the removed clause.

    Used for logging and metrics (AC23-AC24).

    Returns:
        (stripped_text, removed_clause_or_None)
    """
    if not texto:
        return ("", None)

    stripped = _strip_org_context(texto)
    if stripped != texto.strip():
        removed = texto[len(stripped):].strip() if len(stripped) < len(texto) else None
        return (stripped, removed)
    return (stripped, None)


# =============================================================================
# STORY-328 AC7-AC8: Global exclusions (cross-sector generic purchases)
# =============================================================================
# These categories of procurement generate false positives in ALL sectors
# because they are generic purchases that happen to mention the agency name.

GLOBAL_EXCLUSIONS: Set[str] = {
    # Vehicle rental/leasing
    "locacao de veiculo", "locacao de veiculos", "locação de veículo",
    "locação de veículos", "aluguel de veiculo", "aluguel de veiculos",
    # Office supplies
    "material de escritorio", "material de papelaria", "materiais de escritorio",
    "material de escritório", "material de papelaria",
    # Food/cleaning (generic government purchases)
    "generos alimenticios", "genero alimenticio", "gêneros alimentícios",
    "gênero alimentício",
    # Generic IT equipment (cross-sector)
    "equipamentos de informatica", "equipamento de informatica",
    "insumos de informatica",
    # Fuel
    "combustivel", "combustível", "abastecimento de combustivel",
    "abastecimento de combustível",
    # Cleaning services
    "servico de limpeza", "servicos de limpeza", "serviço de limpeza",
    "serviços de limpeza", "servico de conservacao", "serviço de conservação",
    # Construction (generic)
    "construcao de muro", "construção de muro", "construcao de cerca",
    "construção de cerca",
    # Kitchen/break room
    "material de copa e cozinha", "material de copa", "materiais de copa",
    # Travel
    "passagem aerea", "passagens aereas", "passagem aérea", "passagens aéreas",
    # Telecom
    "servico de telefonia", "serviço de telefonia", "servicos de telefonia",
    "serviços de telefonia",
}

# Normalized version for matching (computed once at module load)
GLOBAL_EXCLUSIONS_NORMALIZED: Set[str] = {normalize_text(exc) for exc in GLOBAL_EXCLUSIONS}

# AC10: Per-sector overrides — sectors that should NOT apply certain global exclusions
# e.g., "alimentos" sector should NOT exclude "gêneros alimentícios"
GLOBAL_EXCLUSION_OVERRIDES: Dict[str, Set[str]] = {
    "alimentos": {
        "generos alimenticios", "genero alimenticio",
    },
    "informatica": {
        "equipamentos de informatica", "equipamento de informatica",
        "insumos de informatica",
    },
    "facilities": {
        "servico de limpeza", "servicos de limpeza",
        "servico de conservacao",
    },
    "transporte": {
        "combustivel", "abastecimento de combustivel",
        "locacao de veiculo", "locacao de veiculos",
        "aluguel de veiculo", "aluguel de veiculos",
    },
    "engenharia": {
        "construcao de muro", "construcao de cerca",
    },
    "engenharia_rodoviaria": {
        "construcao de muro", "construcao de cerca",
    },
    "materiais_eletricos": {
        "servico de telefonia", "servicos de telefonia",
    },
    "papelaria": {
        "material de escritorio", "materiais de escritorio",
        "material de papelaria",
    },
    "mobiliario": {
        "material de copa e cozinha", "material de copa",
        "materiais de copa",
    },
}


# =============================================================================
# STORY-181 AC6: Red Flags Secondary Validation
# =============================================================================
# After keyword matching passes, check for "red flag" terms that indicate
# the contract is NOT primarily about the matched sector.

RED_FLAGS_MEDICAL: Set[str] = {
    "paciente", "hospitalar", "ambulatorial", "medicamento",
    "cirurgico", "diagnostico", "tratamento", "terapia",
    "clinica", "enfermagem", "leito", "internacao",
}

RED_FLAGS_ADMINISTRATIVE: Set[str] = {
    "processo licitatorio", "processo administrativo",
    "auditoria", "consultoria", "assessoria", "capacitacao",
    "treinamento", "curso", "palestra", "seminario",
}

RED_FLAGS_INFRASTRUCTURE: Set[str] = {
    "pavimentacao", "drenagem", "saneamento", "terraplanagem",
    "recapeamento", "asfalto", "esgoto", "bueiro",
}

# CRIT-020 + CRIT-024: Sectors exempt from specific red flag categories
# Infrastructure red flags are the PRIMARY keywords for these sectors
_INFRA_EXEMPT_SECTORS: Set[str] = {
    "engenharia", "engenharia_rodoviaria", "manutencao_predial", "materiais_hidraulicos",
}
# Medical red flags are the PRIMARY keywords for saude;
# CRIT-024: facilities has "material de limpeza hospitalar" (contains "hospitalar");
# CRIT-024: transporte has "ambulância" (descriptions naturally contain "paciente", "hospitalar")
_MEDICAL_EXEMPT_SECTORS: Set[str] = {
    "saude", "facilities", "transporte",
}
# CRIT-024: Administrative red flags overlap with software sector keywords
# (software has "consultoria de software", "consultoria de ti", "assessoria de ti")
_ADMIN_EXEMPT_SECTORS: Set[str] = {
    "software",
}

# =============================================================================
# CRIT-FLT-010: Per-Sector Red Flags (Cross-Domain False Positive Prevention)
# =============================================================================
# Each sector has specific "impostor" phrases — terms that match sector keywords
# but actually belong to a different domain. Threshold=1 (more specific than
# generic red flags which need 2+).

# NOTE: All terms MUST be pre-normalized (no accents, lowercase) since they
# are compared against normalize_text() output.
RED_FLAGS_PER_SECTOR: Dict[str, List[str]] = {
    "alimentos": [
        "alimentacao de dados", "alimentacao ininterrupta",
        "fonte de alimentacao", "alimentacao eletrica",
        "alimentar processo", "alimentar sistema",
    ],
    "informatica": [
        "equipamento medico", "equipamento hospitalar",
        "equipamento odontologico", "equipamento laboratorial",
        "equipamento de protecao", "equipamento esportivo",
    ],
    "software": [
        "sistema de registro de precos", "sistema de ar condicionado",
        "sistema de combate a incendio", "sistema de irrigacao",
        "sistema viario", "sistema de drenagem", "sistema de esgoto",
    ],
    "engenharia": [
        "engenharia de software", "engenharia genetica",
        "engenharia financeira", "engenharia reversa",
    ],
    "facilities": [
        "manutencao de veiculos", "manutencao de software",
        "manutencao de equipamentos medicos", "manutencao rodoviaria",
    ],
    "vigilancia": [
        "vigilancia sanitaria", "vigilancia epidemiologica",
        "vigilancia ambiental", "vigilancia em saude",
    ],
    "transporte": [
        "transporte de dados", "transporte de residuos",
        "transporte de materiais perigosos", "transporte de energia",
    ],
    "mobiliario": [
        "cadeira de rodas", "cadeira odontologica",
        "cadeira cirurgica", "mesa cirurgica", "mesa de bilhar",
    ],
    "papelaria": [
        "material cirurgico", "material de construcao",
        "material eletrico", "material hidraulico",
        "material hospitalar", "material belico",
    ],
    "manutencao_predial": [
        "manutencao de software", "manutencao de veiculos",
        "manutencao de equipamentos de ti",
    ],
    "materiais_eletricos": [
        "cabo de rede ethernet", "cabo de aco",
        "material eletronico", "equipamento eletronico",
    ],
    "materiais_hidraulicos": [
        "hidratante", "hidromassagem", "hidroterapia",
    ],
    # Sectors with sufficiently specific keywords — generic red flags are enough
    "vestuario": [],
    "saude": [],
    "engenharia_rodoviaria": [],
}


def has_sector_red_flags(
    objeto_norm: str,
    setor: str,
) -> Tuple[bool, List[str]]:
    """
    Check sector-specific red flags (CRIT-FLT-010).

    Unlike generic red flags (threshold=2), sector red flags are highly specific
    phrases that unambiguously indicate cross-domain context. Threshold=1.

    Args:
        objeto_norm: Normalized procurement object description.
        setor: Sector ID to look up per-sector red flags.

    Returns:
        Tuple of (has_flags, matched_flags).
    """
    flags = RED_FLAGS_PER_SECTOR.get(setor, [])
    if not flags:
        return False, []
    matched = [flag for flag in flags if flag in objeto_norm]
    return len(matched) > 0, matched


def has_red_flags(
    objeto_norm: str,
    red_flag_sets: List[Set[str]],
    threshold: int = 2,
    setor: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    """
    Check if a contract description contains red flag terms (STORY-181 AC6).

    A contract is flagged when it contains 2+ terms from any single red flag
    category, indicating the object is probably NOT about the matched sector.

    CRIT-020: Exempts infrastructure sectors from RED_FLAGS_INFRASTRUCTURE
    and saude from RED_FLAGS_MEDICAL, since those terms are the primary
    keywords of those sectors.
    CRIT-024: Extends exemptions to facilities/transporte (medical) and software (admin).

    Args:
        objeto_norm: Normalized procurement object description
        red_flag_sets: List of red flag term sets to check
        threshold: Minimum matches in any single set to trigger flag
        setor: Sector ID — used to skip exempted red flag sets

    Returns:
        Tuple of (has_flags, matched_flags)
    """
    all_matched: List[str] = []
    for red_flags in red_flag_sets:
        # CRIT-020: Skip red flag sets when sector is exempt
        if setor:
            if red_flags is RED_FLAGS_INFRASTRUCTURE and setor in _INFRA_EXEMPT_SECTORS:
                continue
            if red_flags is RED_FLAGS_MEDICAL and setor in _MEDICAL_EXEMPT_SECTORS:
                continue
            if red_flags is RED_FLAGS_ADMINISTRATIVE and setor in _ADMIN_EXEMPT_SECTORS:
                continue
        matches = [flag for flag in red_flags if flag in objeto_norm]
        if len(matches) >= threshold:
            all_matched.extend(matches)
    return len(all_matched) > 0, all_matched


def match_keywords(
    objeto: str,
    keywords: Set[str],
    exclusions: Set[str] | None = None,
    context_required: Dict[str, Set[str]] | None = None,
    compiled_patterns: Dict[str, re.Pattern] | None = None,
) -> Tuple[bool, List[str]]:
    """
    Check if procurement object description contains uniform-related keywords.

    Uses flexible word boundary matching to handle plural variations:
    - "uniforme" matches "uniforme" and "uniformes" (plural -s or -es suffix)
    - "notebook" matches "notebook" and "notebooks" (plural -s suffix)
    - "uniforme" does NOT match "uniformemente" or "uniformização" (different words)

    Algorithm:
    1. Try exact match with word boundaries: \\b{keyword}\\b
    2. If no match, try plural variations: \\b{keyword}s\\b or \\b{keyword}es\\b
    3. If context_required is provided, validate that generic/ambiguous keywords
       have at least one confirming context keyword present in the text.

    Args:
        objeto: Procurement object description (objetoCompra from PNCP API)
        keywords: Set of keywords to search for (KEYWORDS_UNIFORMES)
        exclusions: Optional set of exclusion keywords (KEYWORDS_EXCLUSAO)
        context_required: Optional dict mapping generic keywords to sets of
            context keywords.  A generic keyword only counts as a match if
            at least one of its context keywords is also found in the text.

    Returns:
        Tuple containing:
        - bool: True if at least one keyword matched (and no exclusions found)
        - List[str]: List of matched keywords (original form, not normalized)

    Examples:
        >>> match_keywords("Aquisição de uniformes escolares", KEYWORDS_UNIFORMES)
        (True, ['uniformes', 'uniforme escolar'])

        >>> match_keywords("Aquisição de notebooks", {"notebook"})
        (True, ['notebook'])

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
            # Use strict word boundary for exclusions (exact match required)
            pattern = rf"\b{re.escape(exc_norm)}\b"
            if re.search(pattern, objeto_norm):
                # STORY-248 AC9: Record exclusion hit
                try:
                    _get_tracker().record_rejection(
                        "exclusion_hit",
                        description_preview=objeto[:100],
                    )
                except Exception:
                    pass  # Never let stats recording break filter logic
                return False, []

    # Search for matching keywords
    # AC9.1: Use pre-compiled patterns when available for batch performance
    matched: List[str] = []
    for kw in keywords:
        kw_norm = normalize_text(kw)

        # Use pre-compiled pattern if available
        if compiled_patterns and kw in compiled_patterns:
            if compiled_patterns[kw].search(objeto_norm):
                matched.append(kw)
                continue
            # Also try plural forms with pre-compiled pattern
            if not kw_norm.endswith('s'):
                pattern_plural_s = rf"\b{re.escape(kw_norm)}s\b"
                if re.search(pattern_plural_s, objeto_norm):
                    matched.append(kw)
                    continue
                pattern_plural_es = rf"\b{re.escape(kw_norm)}es\b"
                if re.search(pattern_plural_es, objeto_norm):
                    matched.append(kw)
                    continue
        else:
            # Fallback: compile on the fly (backward compatible)
            pattern_exact = rf"\b{re.escape(kw_norm)}\b"
            if re.search(pattern_exact, objeto_norm):
                matched.append(kw)
                continue

            # Try plural forms if exact match failed
            if not kw_norm.endswith('s'):
                pattern_plural_s = rf"\b{re.escape(kw_norm)}s\b"
                if re.search(pattern_plural_s, objeto_norm):
                    matched.append(kw)
                    continue
                pattern_plural_es = rf"\b{re.escape(kw_norm)}es\b"
                if re.search(pattern_plural_es, objeto_norm):
                    matched.append(kw)
                    continue

    # Context validation: generic/ambiguous keywords must have confirming context
    if context_required and matched:
        # Pre-compute normalized lookup: normalized_key -> set of context keywords
        context_lookup: Dict[str, Set[str]] = {}
        for crk, crv in context_required.items():
            context_lookup[normalize_text(crk)] = crv

        validated: List[str] = []
        for kw in matched:
            kw_norm = normalize_text(kw)
            if kw_norm in context_lookup:
                # This is a context-required keyword -- verify context exists
                context_found = False
                for ctx in context_lookup[kw_norm]:
                    ctx_norm = normalize_text(ctx)
                    if ctx_norm in objeto_norm:
                        context_found = True
                        break
                if context_found:
                    validated.append(kw)
                # else: drop this keyword (no confirming context in text)
            else:
                # Not a context-required keyword -- keep unconditionally
                validated.append(kw)

        matched = validated

    return len(matched) > 0, matched
