"""Keyword matching engine for uniform/apparel procurement filtering."""

import logging
import random
import re
import unicodedata
import uuid
from datetime import datetime, timezone
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


def has_red_flags(
    objeto_norm: str,
    red_flag_sets: List[Set[str]],
    threshold: int = 2,
) -> Tuple[bool, List[str]]:
    """
    Check if a contract description contains red flag terms (STORY-181 AC6).

    A contract is flagged when it contains 2+ terms from any single red flag
    category, indicating the object is probably NOT about the matched sector.

    Args:
        objeto_norm: Normalized procurement object description
        red_flag_sets: List of red flag term sets to check
        threshold: Minimum matches in any single set to trigger flag

    Returns:
        Tuple of (has_flags, matched_flags)
    """
    all_matched: List[str] = []
    for red_flags in red_flag_sets:
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


def filter_licitacao(
    licitacao: dict,
    ufs_selecionadas: Set[str],
    keywords: Set[str] | None = None,
    exclusions: Set[str] | None = None,
    context_required: Dict[str, Set[str]] | None = None,
    filter_closed: bool = False,
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
    match, keywords_found = match_keywords(objeto, kw, exc, context_required)

    if not match:
        return False, "Não contém keywords do setor"

    # 4. Deadline Filter - OPTIONAL
    # When filter_closed=True, reject bids whose proposal submission deadline
    # (dataEncerramentoProposta) has already passed. This is used when the user
    # explicitly filters by status="recebendo_proposta" to ensure only truly
    # open bids are returned.
    #
    # Note: dataAberturaProposta is the OPENING date for proposals, NOT the
    # deadline. The correct deadline field from the PNCP API is
    # dataEncerramentoProposta.
    #
    # Referencia: Investigacao 2026-01-28 - docs/investigations/
    if filter_closed:
        data_fim_str = licitacao.get("dataEncerramentoProposta")
        if data_fim_str:
            try:
                data_fim = datetime.fromisoformat(
                    data_fim_str.replace("Z", "+00:00")
                )
                agora = datetime.now(data_fim.tzinfo)
                if data_fim < agora:
                    return False, "Prazo de submissao encerrado"
            except (ValueError, AttributeError):
                # If date parsing fails, don't reject (conservative approach)
                logger.warning(
                    f"Data de encerramento invalida: '{data_fim_str}'"
                )

    return True, None


def filter_batch(
    licitacoes: List[dict],
    ufs_selecionadas: Set[str],
    keywords: Set[str] | None = None,
    exclusions: Set[str] | None = None,
    context_required: Dict[str, Set[str]] | None = None,
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
        aprovada, motivo = filter_licitacao(
            lic, ufs_selecionadas, keywords, exclusions, context_required
        )

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

    IMPORTANTE: Esta função usa INFERÊNCIA DE STATUS baseada em múltiplos campos
    (datas, valores, situação textual) porque a API PNCP não retorna um campo
    de status padronizado. Ver status_inference.py para detalhes da lógica.

    Args:
        licitacoes: Lista de licitações da API PNCP (deve ter `_status_inferido`)
        status: Status desejado:
            - "recebendo_proposta": Licitações abertas para envio de propostas
            - "em_julgamento": Propostas encerradas, em análise
            - "encerrada": Processo finalizado
            - "todos": Sem filtro (retorna todas)

    Returns:
        Lista filtrada de licitações

    Examples:
        >>> from status_inference import enriquecer_com_status_inferido
        >>> bids = [
        ...     {"dataEncerramentoProposta": "2026-12-31T10:00:00"},
        ...     {"valorTotalHomologado": 100000},
        ... ]
        >>> enriquecer_com_status_inferido(bids)  # Adiciona _status_inferido
        >>> filtrar_por_status(bids, "recebendo_proposta")
        [{'dataEncerramentoProposta': '2026-12-31T10:00:00', '_status_inferido': 'recebendo_proposta'}]
    """
    if not status or status == "todos":
        logger.debug("filtrar_por_status: status='todos', retornando todas")
        return licitacoes

    # Importa função de inferência (lazy import para evitar circular dependency)
    from status_inference import inferir_status_licitacao

    resultado: List[dict] = []
    inferencias_realizadas = 0

    for lic in licitacoes:
        # Usa status inferido se já existir (enriquecido previamente)
        # Caso contrário, infere on-the-fly
        if "_status_inferido" in lic:
            status_lic = lic["_status_inferido"]
        else:
            status_lic = inferir_status_licitacao(lic)
            lic["_status_inferido"] = status_lic  # Cache para próximos filtros
            inferencias_realizadas += 1

        # Compara com status solicitado
        if status_lic == status.lower():
            resultado.append(lic)

    if inferencias_realizadas > 0:
        logger.debug(
            f"filtrar_por_status: realizadas {inferencias_realizadas} "
            f"inferências on-the-fly"
        )

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


# ============================================================================
# Semantic Sector Context Analysis (STORY-183 AC3)
# ============================================================================
# These functions analyze search terms to determine the dominant sector based
# on semantic similarity to sector-specific vocabularies. This enables better
# filtering and result ranking based on user intent.
# ============================================================================

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


def filtrar_por_prazo_aberto(
    licitacoes: List[dict],
) -> Tuple[List[dict], int]:
    """
    STORY-240 AC3: Filter out bids whose proposal deadline has already passed.

    Rejects bids where dataEncerramentoProposta <= now().
    Bids without a deadline date are KEPT (conservative approach).

    Args:
        licitacoes: List of raw PNCP bid dictionaries

    Returns:
        Tuple of (approved bids list, count of rejected bids)
    """
    from datetime import datetime, timezone

    aprovadas: List[dict] = []
    rejeitadas = 0

    for lic in licitacoes:
        data_fim_str = lic.get("dataEncerramentoProposta")
        if not data_fim_str:
            # No deadline date → keep (conservative)
            aprovadas.append(lic)
            continue

        try:
            data_fim = datetime.fromisoformat(
                data_fim_str.replace("Z", "+00:00")
            )
            # GTM-FIX-031: Ensure both datetimes are tz-aware to avoid crash
            if data_fim.tzinfo is None:
                data_fim = data_fim.replace(tzinfo=timezone.utc)
            agora = datetime.now(timezone.utc)
            if data_fim <= agora:
                rejeitadas += 1
                logger.debug(
                    f"filtrar_por_prazo_aberto: rejeitada (encerrada em {data_fim_str}): "
                    f"{lic.get('objetoCompra', '')[:80]}"
                )
                continue
        except (ValueError, AttributeError):
            # If date parsing fails, keep (conservative)
            logger.warning(f"filtrar_por_prazo_aberto: data inválida: '{data_fim_str}'")

        aprovadas.append(lic)

    logger.info(
        f"filtrar_por_prazo_aberto: {len(aprovadas)} aprovadas, {rejeitadas} rejeitadas "
        f"(total: {len(licitacoes)})"
    )
    return aprovadas, rejeitadas


# ============================================================================
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
    context_required: Dict[str, Set[str]] | None = None,
    min_match_floor: Optional[int] = None,
    setor: Optional[str] = None,  # STORY-179 AC1: sector ID for max_contract_value check
    modo_busca: str = "publicacao",  # STORY-240 AC4: "publicacao" or "abertas"
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
        "rejeitadas_valor_alto": 0,  # STORY-179 AC1: Camada 1A (value threshold)
        "rejeitadas_keyword": 0,
        "rejeitadas_min_match": 0,
        "rejeitadas_prazo": 0,
        "rejeitadas_prazo_aberto": 0,  # STORY-240 AC4: bids with passed deadline
        "rejeitadas_outros": 0,
        # STORY-179 AC2: Camada 2A (term density ratio)
        "aprovadas_alta_densidade": 0,  # density > 5% (high confidence, no LLM)
        "rejeitadas_baixa_densidade": 0,  # density < 1% (low confidence, reject)
        "duvidosas_llm_arbiter": 0,  # 1% ≤ density ≤ 5% (send to LLM)
    }

    logger.debug(
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
            # STORY-248 AC9: Record UF mismatch
            try:
                _get_tracker().record_rejection(
                    "uf_mismatch",
                    sector=setor,
                    description_preview=lic.get("objetoCompra", "")[:100],
                )
            except Exception:
                pass

    logger.debug(
        f"  Após filtro UF: {len(resultado_uf)} "
        f"(rejeitadas: {stats['rejeitadas_uf']})"
    )

    # Etapa 2: Filtro de Status
    # CRITICAL FIX (2026-02-06): Use inferred status (_status_inferido) instead of
    # raw API fields (situacaoCompra, etc.) because PNCP returns values like
    # "Divulgada no PNCP" which don't match simple string patterns.
    # The status_inference.py module correctly infers status from dates and values.
    if status and status != "todos":
        resultado_status: List[dict] = []
        status_lower = status.lower()
        # GTM-FIX-030 AC13: Diagnostic counters for status_mismatch analysis
        _status_distribution: Dict[str, int] = {}

        for lic in resultado_uf:
            # Use inferred status if available (set by enriquecer_com_status_inferido)
            status_inferido = lic.get("_status_inferido", "")

            if status_inferido:
                _status_distribution[status_inferido] = _status_distribution.get(status_inferido, 0) + 1
                # Direct comparison with inferred status
                if status_inferido == status_lower:
                    resultado_status.append(lic)
                else:
                    stats["rejeitadas_status"] += 1
                    # STORY-248 AC9: Record status mismatch
                    try:
                        _get_tracker().record_rejection(
                            "status_mismatch",
                            sector=setor,
                            description_preview=lic.get("objetoCompra", "")[:100],
                        )
                    except Exception:
                        pass
            else:
                # Fallback: try raw API fields (legacy behavior)
                situacao = (
                    lic.get("situacaoCompraNome", "")
                    or lic.get("situacaoCompra", "")
                    or lic.get("situacao", "")
                    or lic.get("statusCompra", "")
                    or ""
                ).lower()

                status_map = {
                    "recebendo_proposta": [
                        "recebendo propostas", "aberta", "publicada",
                        "divulgada", "vigente", "ativa", "em andamento"
                    ],
                    "em_julgamento": [
                        "propostas encerradas", "em julgamento", "julgamento",
                        "análise", "analise", "classificação", "classificacao"
                    ],
                    "encerrada": [
                        "encerrada", "finalizada", "homologada", "adjudicada",
                        "anulada", "revogada", "cancelada", "fracassada",
                        "deserta", "suspensa", "concluída", "concluida"
                    ],
                }
                termos = status_map.get(status_lower, [])

                if any(t in situacao for t in termos):
                    resultado_status.append(lic)
                else:
                    stats["rejeitadas_status"] += 1
                    # STORY-248 AC9: Record status mismatch (fallback path)
                    try:
                        _get_tracker().record_rejection(
                            "status_mismatch",
                            sector=setor,
                            description_preview=lic.get("objetoCompra", "")[:100],
                        )
                    except Exception:
                        pass

        # GTM-FIX-030 AC13: Log status distribution for diagnostics
        logger.debug(
            f"  Status filter: wanted='{status_lower}', "
            f"distribution={_status_distribution}, "
            f"passed={len(resultado_status)}, rejected={stats['rejeitadas_status']}"
        )
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

    # Etapa 7.5: Filtro de Prazo Aberto (STORY-240 AC4)
    # When modo_busca="abertas", reject bids whose proposal deadline has passed.
    # Applied BEFORE keywords filter (fail-fast: eliminates closed bids before heavy regex).
    if modo_busca == "abertas":
        resultado_valor, rejeitadas_prazo = filtrar_por_prazo_aberto(resultado_valor)
        stats["rejeitadas_prazo_aberto"] = rejeitadas_prazo
        logger.debug(
            f"  Após filtro Prazo Aberto: {len(resultado_valor)} "
            f"(rejeitadas: {rejeitadas_prazo})"
        )

    # STORY-179 AC1.3: Camada 1A - Value Threshold (Anti-False Positive)
    # Apply sector-specific max_contract_value check BEFORE keyword matching
    # to reject obvious false positives (e.g., R$ 47.6M "melhorias urbanas" + uniformes)
    if setor:
        from sectors import get_sector

        try:
            setor_config = get_sector(setor)
            max_value = setor_config.max_contract_value

            if max_value is not None:
                resultado_valor_teto: List[dict] = []
                for lic in resultado_valor:
                    valor = lic.get("valorTotalEstimado") or lic.get("valorEstimado") or 0

                    if isinstance(valor, str):
                        try:
                            valor = float(valor.replace(".", "").replace(",", "."))
                        except ValueError:
                            valor = 0.0
                    else:
                        valor = float(valor) if valor else 0.0

                    if valor > max_value:
                        stats["rejeitadas_valor_alto"] += 1
                        logger.debug(
                            f"  Rejeitada por Camada 1A (valor > R$ {max_value:,.2f}): "
                            f"valor=R$ {valor:,.2f} setor={setor} "
                            f"objeto={lic.get('objetoCompra', '')[:80]}"
                        )
                        # STORY-248 AC9: Record value exceed
                        try:
                            _get_tracker().record_rejection(
                                "value_exceed",
                                sector=setor,
                                description_preview=lic.get("objetoCompra", "")[:100],
                            )
                        except Exception:
                            pass
                        continue

                    resultado_valor_teto.append(lic)

                logger.debug(
                    f"  Após Camada 1A (Value Threshold): {len(resultado_valor_teto)} "
                    f"(rejeitadas_valor_alto: {stats['rejeitadas_valor_alto']})"
                )
                resultado_valor = resultado_valor_teto
        except KeyError:
            logger.warning(f"Setor '{setor}' não encontrado - pulando Camada 1A")

    # Etapa 8: Filtro de Keywords (mais lento - regex)
    # AC9.1: Pre-compile regex patterns once for the batch
    kw = keywords if keywords is not None else KEYWORDS_UNIFORMES
    exc = exclusions if exclusions is not None else KEYWORDS_EXCLUSAO

    compiled_patterns: Dict[str, re.Pattern] = {}
    for keyword in kw:
        try:
            escaped = re.escape(keyword)
            compiled_patterns[keyword] = re.compile(
                rf'\b{escaped}\b', re.IGNORECASE | re.UNICODE
            )
        except re.error:
            logger.warning(f"Failed to compile regex for keyword: {keyword}")

    resultado_keyword: List[dict] = []
    for lic in resultado_valor:
        objeto = lic.get("objetoCompra", "")
        match, matched_terms = match_keywords(
            objeto, kw, exc, context_required,
            compiled_patterns=compiled_patterns,
        )

        if match:
            # Store matched terms on the bid for later scoring
            lic["_matched_terms"] = matched_terms

            # STORY-179 AC2.1: Calculate term density ratio
            # Count how many times matched terms appear in the text
            objeto_norm = normalize_text(objeto)
            total_words = len(objeto_norm.split())
            term_count = 0
            for term in matched_terms:
                term_norm = normalize_text(term)
                # Count exact occurrences of this term in the text
                term_count += objeto_norm.count(term_norm)

            term_density = term_count / total_words if total_words > 0 else 0
            lic["_term_density"] = term_density

            resultado_keyword.append(lic)
        else:
            stats["rejeitadas_keyword"] += 1
            # STORY-248 AC9: Record keyword miss
            try:
                _get_tracker().record_rejection(
                    "keyword_miss",
                    sector=setor,
                    description_preview=objeto[:100],
                )
            except Exception:
                pass

    # ========================================================================
    # GTM-RESILIENCE-D03: Camada 1B.5 — Co-occurrence Negative Patterns
    # ========================================================================
    # After keyword match, before density zone. Rejects bids where a trigger
    # keyword co-occurs with a negative context and no positive signal.
    # Overrides auto-accept: even density >5% bids are rejected.
    # 100% deterministic, zero LLM cost.
    from config import get_feature_flag

    stats["co_occurrence_rejections"] = 0
    stats["co_occurrence_rejections_by_sector"] = {}

    if get_feature_flag("CO_OCCURRENCE_RULES_ENABLED") and setor:
        from sectors import get_sector as _get_sector_co

        try:
            setor_config_co = _get_sector_co(setor)
            co_rules = setor_config_co.co_occurrence_rules

            if co_rules:
                resultado_after_co: List[dict] = []
                for lic in resultado_keyword:
                    objeto = lic.get("objetoCompra", "")
                    should_reject, rejection_detail = check_co_occurrence(
                        objeto, co_rules, setor
                    )

                    if should_reject:
                        stats["co_occurrence_rejections"] += 1
                        stats["co_occurrence_rejections_by_sector"][setor] = (
                            stats["co_occurrence_rejections_by_sector"].get(setor, 0) + 1
                        )
                        lic["_rejection_reason"] = "co_occurrence"
                        lic["_rejection_detail"] = rejection_detail
                        logger.debug(
                            f"Camada 1B.5: REJECT (co-occurrence) "
                            f"detail={rejection_detail} "
                            f"objeto={objeto[:80]}"
                        )
                        # AC4: Record in filter stats tracker
                        try:
                            _get_tracker().record_rejection(
                                "co_occurrence",
                                sector=setor,
                                description_preview=objeto[:100],
                            )
                        except Exception:
                            pass
                    else:
                        resultado_after_co.append(lic)

                if stats["co_occurrence_rejections"] > 0:
                    logger.info(
                        f"Camada 1B.5 (Co-occurrence): rejected "
                        f"{stats['co_occurrence_rejections']} bids in sector '{setor}'"
                    )
                resultado_keyword = resultado_after_co
        except KeyError:
            pass  # Sector not found — skip co-occurrence

    # ========================================================================
    # GTM-FIX-028: LLM Zero Match Classification
    # ========================================================================
    # Instead of auto-rejecting bids with 0 keyword matches, collect them
    # and send to LLM for sector-aware classification.
    from config import LLM_ZERO_MATCH_ENABLED

    resultado_llm_zero: List[dict] = []
    stats["llm_zero_match_calls"] = 0
    stats["llm_zero_match_aprovadas"] = 0
    stats["llm_zero_match_rejeitadas"] = 0
    stats["llm_zero_match_skipped_short"] = 0

    if LLM_ZERO_MATCH_ENABLED and setor:
        # Collect bids that were rejected by keyword gate (in resultado_valor but not in resultado_keyword)
        keyword_approved_ids = {id(lic) for lic in resultado_keyword}
        zero_match_pool: List[dict] = []
        for lic in resultado_valor:
            if id(lic) not in keyword_approved_ids:
                objeto = lic.get("objetoCompra", "")
                # AC3: Skip bids with objeto < 20 chars (PCP short resumo, insufficient signal)
                if len(objeto) < 20:
                    stats["llm_zero_match_skipped_short"] += 1
                    logger.debug(
                        f"LLM zero_match: SKIP (objeto < 20 chars) objeto={objeto!r}"
                    )
                    continue
                zero_match_pool.append(lic)

        if zero_match_pool:
            from llm_arbiter import classify_contract_primary_match as _classify_zm
            from sectors import get_sector as _get_sector_zm
            from concurrent.futures import ThreadPoolExecutor, as_completed

            try:
                setor_config_zm = _get_sector_zm(setor)
                setor_name_zm = setor_config_zm.name
            except (KeyError, Exception):
                setor_name_zm = setor

            # AC6: Concurrent LLM calls with max 10 threads (equivalent to Semaphore(10))
            def _classify_one(lic_item: dict) -> tuple[dict, bool]:
                obj = lic_item.get("objetoCompra", "")
                val = lic_item.get("valorTotalEstimado") or lic_item.get("valorEstimado") or 0
                if isinstance(val, str):
                    try:
                        val = float(val.replace(".", "").replace(",", "."))
                    except ValueError:
                        val = 0.0
                else:
                    val = float(val) if val else 0.0
                result = _classify_zm(
                    objeto=obj,
                    valor=val,
                    setor_name=setor_name_zm,
                    prompt_level="zero_match",
                    setor_id=setor,
                )
                return lic_item, result

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {
                    executor.submit(_classify_one, lic): lic
                    for lic in zero_match_pool
                }
                for future in as_completed(futures):
                    stats["llm_zero_match_calls"] += 1
                    try:
                        lic_item, is_relevant = future.result()
                        if is_relevant:
                            stats["llm_zero_match_aprovadas"] += 1
                            # AC8: Tag relevance source
                            lic_item["_relevance_source"] = "llm_zero_match"
                            lic_item["_term_density"] = 0.0
                            lic_item["_matched_terms"] = []
                            resultado_llm_zero.append(lic_item)
                            logger.debug(
                                f"LLM zero_match: ACCEPT objeto={lic_item.get('objetoCompra', '')[:80]}"
                            )
                        else:
                            stats["llm_zero_match_rejeitadas"] += 1
                            logger.debug(
                                f"LLM zero_match: REJECT objeto={lic_item.get('objetoCompra', '')[:80]}"
                            )
                    except Exception as e:
                        # AC9: Fallback on LLM failure = REJECT
                        stats["llm_zero_match_rejeitadas"] += 1
                        logger.error(f"LLM zero_match: FAILED (REJECT fallback): {e}")

            logger.info(
                f"GTM-FIX-028 LLM Zero Match: "
                f"{stats['llm_zero_match_calls']} calls, "
                f"{stats['llm_zero_match_aprovadas']} approved, "
                f"{stats['llm_zero_match_rejeitadas']} rejected, "
                f"{stats['llm_zero_match_skipped_short']} skipped (short)"
            )

    # STORY-181 AC2: Camada 2A - Calibrated Term Density Decision Thresholds
    # Using configurable thresholds from config.py (env-var adjustable)
    from config import (
        TERM_DENSITY_HIGH_THRESHOLD,
        TERM_DENSITY_MEDIUM_THRESHOLD,
        TERM_DENSITY_LOW_THRESHOLD,
        QA_AUDIT_SAMPLE_RATE,
    )

    resultado_densidade: List[dict] = []
    resultado_llm_standard: List[dict] = []  # density 2-5%: LLM standard prompt
    resultado_llm_conservative: List[dict] = []  # density 1-2%: LLM conservative prompt
    stats["rejeitadas_red_flags"] = 0

    for lic in resultado_keyword:
        density = lic.get("_term_density", 0)
        trace_id = str(uuid.uuid4())[:8]
        lic["_trace_id"] = trace_id
        objeto_preview = lic.get("objetoCompra", "")[:100]

        if density > TERM_DENSITY_HIGH_THRESHOLD:
            # High confidence (>5%) - dominant term, accept without LLM
            stats["aprovadas_alta_densidade"] += 1
            # GTM-FIX-028 AC8: Tag relevance source
            lic["_relevance_source"] = "keyword"
            logger.debug(
                f"[{trace_id}] Camada 2A: ACCEPT (alta densidade) "
                f"density={density:.1%} objeto={objeto_preview}"
            )
            resultado_densidade.append(lic)
        elif density < TERM_DENSITY_LOW_THRESHOLD:
            # Low confidence (<1%) - peripheral term, reject
            stats["rejeitadas_baixa_densidade"] += 1
            logger.debug(
                f"[{trace_id}] Camada 2A: REJECT (baixa densidade) "
                f"density={density:.1%} objeto={objeto_preview}"
            )
            # STORY-248 AC9: Record density low rejection
            try:
                _get_tracker().record_rejection(
                    "density_low",
                    sector=setor,
                    description_preview=objeto_preview,
                )
            except Exception:
                pass
        elif density >= TERM_DENSITY_MEDIUM_THRESHOLD:
            # Medium-high zone (2-5%) - LLM with standard prompt
            # STORY-181 AC6: Check red flags BEFORE sending to LLM
            objeto_norm = normalize_text(lic.get("objetoCompra", ""))
            flagged, flag_terms = has_red_flags(
                objeto_norm,
                [RED_FLAGS_MEDICAL, RED_FLAGS_ADMINISTRATIVE, RED_FLAGS_INFRASTRUCTURE],
            )
            if flagged:
                stats["rejeitadas_red_flags"] += 1
                logger.debug(
                    f"[{trace_id}] Camada 2A: REJECT (red flags: {flag_terms}) "
                    f"density={density:.1%} objeto={objeto_preview}"
                )
                continue

            stats["duvidosas_llm_arbiter"] += 1
            lic["_llm_prompt_level"] = "standard"
            resultado_llm_standard.append(lic)
        else:
            # Low-medium zone (1-2%) - LLM with conservative prompt
            # STORY-181 AC6: Check red flags BEFORE sending to LLM
            objeto_norm = normalize_text(lic.get("objetoCompra", ""))
            flagged, flag_terms = has_red_flags(
                objeto_norm,
                [RED_FLAGS_MEDICAL, RED_FLAGS_ADMINISTRATIVE, RED_FLAGS_INFRASTRUCTURE],
            )
            if flagged:
                stats["rejeitadas_red_flags"] += 1
                logger.debug(
                    f"[{trace_id}] Camada 2A: REJECT (red flags: {flag_terms}) "
                    f"density={density:.1%} objeto={objeto_preview}"
                )
                continue

            stats["duvidosas_llm_arbiter"] += 1
            lic["_llm_prompt_level"] = "conservative"
            resultado_llm_conservative.append(lic)

    resultado_llm_candidates = resultado_llm_standard + resultado_llm_conservative

    logger.debug(
        f"  Após Camada 2A (Term Density): "
        f"{len(resultado_densidade)} aprovadas (alta densidade), "
        f"{len(resultado_llm_standard)} duvidosas (LLM standard), "
        f"{len(resultado_llm_conservative)} duvidosas (LLM conservative), "
        f"{stats.get('rejeitadas_red_flags', 0)} rejeitadas (red flags), "
        f"{stats['rejeitadas_baixa_densidade']} rejeitadas (baixa densidade)"
    )

    # STORY-179 AC3: Camada 3A - LLM Arbiter (GPT-4o-mini)
    # For contracts in the uncertain zone (1-5% density), use LLM to determine
    # if the contract is PRIMARILY about the sector/terms or just a tangential mention
    stats["aprovadas_llm_arbiter"] = 0
    stats["rejeitadas_llm_arbiter"] = 0
    stats["llm_arbiter_calls"] = 0

    if resultado_llm_candidates:
        from llm_arbiter import classify_contract_primary_match

        for lic in resultado_llm_candidates:
            objeto = lic.get("objetoCompra", "")
            valor = lic.get("valorTotalEstimado") or lic.get("valorEstimado") or 0
            trace_id = lic.get("_trace_id", "unknown")
            prompt_level = lic.get("_llm_prompt_level", "standard")

            # Convert valor to float if needed
            if isinstance(valor, str):
                try:
                    valor = float(valor.replace(".", "").replace(",", "."))
                except ValueError:
                    valor = 0.0
            else:
                valor = float(valor) if valor else 0.0

            # Determine mode: sector-based or custom-terms-based
            setor_name = None
            termos = None

            if setor:
                from sectors import get_sector
                try:
                    setor_config = get_sector(setor)
                    setor_name = setor_config.name
                except KeyError:
                    logger.warning(f"Setor '{setor}' não encontrado para LLM arbiter")

            if not setor_name:
                termos = lic.get("_matched_terms", [])

            # STORY-181 AC3 + STORY-251 AC2: Call LLM arbiter with prompt level and setor_id
            stats["llm_arbiter_calls"] += 1
            is_primary = classify_contract_primary_match(
                objeto=objeto,
                valor=valor,
                setor_name=setor_name,
                termos_busca=termos,
                prompt_level=prompt_level,
                setor_id=setor if setor_name else None,
            )

            if is_primary:
                stats["aprovadas_llm_arbiter"] += 1
                # GTM-FIX-028 AC8: Tag relevance source based on prompt level
                lic["_relevance_source"] = f"llm_{prompt_level}"
                resultado_densidade.append(lic)
                logger.debug(
                    f"[{trace_id}] Camada 3A: ACCEPT (LLM={prompt_level}) "
                    f"density={lic.get('_term_density', 0):.1%} "
                    f"objeto={objeto[:80]}"
                )
            else:
                stats["rejeitadas_llm_arbiter"] += 1
                logger.debug(
                    f"[{trace_id}] Camada 3A: REJECT (LLM={prompt_level}) "
                    f"density={lic.get('_term_density', 0):.1%} "
                    f"valor=R$ {valor:,.2f} objeto={objeto[:80]}"
                )
                # STORY-248 AC9: Record LLM rejection
                try:
                    _get_tracker().record_rejection(
                        "llm_reject",
                        sector=setor,
                        description_preview=objeto[:100],
                    )
                except Exception:
                    pass

            # STORY-181 AC7: QA Audit sampling
            if random.random() < QA_AUDIT_SAMPLE_RATE:
                lic["_qa_audit"] = True
                lic["_qa_audit_decision"] = {
                    "trace_id": trace_id,
                    "llm_response": "SIM" if is_primary else "NAO",
                    "prompt_level": prompt_level,
                    "density": lic.get("_term_density", 0),
                    "matched_terms": lic.get("_matched_terms", []),
                    "valor": valor,
                }

        logger.info(
            f"Camada 3A resultado: "
            f"{stats['aprovadas_llm_arbiter']} aprovadas, "
            f"{stats['rejeitadas_llm_arbiter']} rejeitadas, "
            f"{stats['llm_arbiter_calls']} chamadas LLM"
        )

    resultado_keyword = resultado_densidade

    # GTM-FIX-028: Merge LLM zero-match approved bids into the keyword results
    if resultado_llm_zero:
        resultado_keyword.extend(resultado_llm_zero)
        logger.info(
            f"GTM-FIX-028: Merged {len(resultado_llm_zero)} LLM zero-match bids "
            f"into resultado_keyword (total now: {len(resultado_keyword)})"
        )

    # Etapa 8b: Minimum Match Floor (STORY-178 AC2.2)
    # When min_match_floor is provided, apply additional filtering
    if min_match_floor is not None and min_match_floor > 1:
        from relevance import should_include, count_phrase_matches

        resultado_min_match: List[dict] = []
        for lic in resultado_keyword:
            matched_terms = lic.get("_matched_terms", [])
            matched_count = len(matched_terms)
            has_phrase = count_phrase_matches(matched_terms) > 0

            if should_include(matched_count, len(kw), has_phrase):
                resultado_min_match.append(lic)
            else:
                stats["rejeitadas_min_match"] += 1

        resultado_keyword = resultado_min_match

    logger.debug(
        f"  Após filtro Keywords: {len(resultado_keyword)} "
        f"(rejeitadas_keyword: {stats['rejeitadas_keyword']}, "
        f"rejeitadas_min_match: {stats['rejeitadas_min_match']})"
    )

    # Etapa 9: Filtro de Prazo (safety net for "recebendo_proposta")
    # When the user explicitly filters by status="recebendo_proposta", apply a
    # HARD deadline check using dataEncerramentoProposta. If the encerramento
    # date is in the past, the bid is NOT open regardless of what _status_inferido
    # says. This catches edge cases where status inference is wrong.
    #
    # CREDIBILITY FIX (2026-02-09): Tightened all heuristics significantly.
    # Showing closed bids as "open" destroys user trust. It's better to miss
    # a few legitimate open bids than to show clearly closed ones.
    #
    # Policy: If we can't PROVE a bid is open, don't show it as open.
    # - Has future dataEncerramentoProposta → KEEP (proven open)
    # - Has past dataEncerramentoProposta → REJECT (proven closed)
    # - No deadline, abertura <= 15 days → KEEP (very likely still open)
    # - No deadline, abertura 16-30 days → KEEP only if situação says "recebendo"
    # - No deadline, abertura > 30 days → REJECT (probably closed)
    # - No deadline, no abertura, publication <= 15 days → KEEP (very recent)
    # - No deadline, no abertura, publication > 15 days → REJECT
    # - No dates at all → REJECT (cannot prove it's open)
    if status and status.lower() == "recebendo_proposta":
        aprovadas: List[dict] = []
        agora = datetime.now(timezone.utc)

        for lic in resultado_keyword:
            data_enc_str = lic.get("dataEncerramentoProposta")

            # Case 1: dataEncerramentoProposta exists — HARD deadline check
            if data_enc_str:
                try:
                    data_enc = datetime.fromisoformat(
                        data_enc_str.replace("Z", "+00:00")
                    )
                    # GTM-FIX-031: Ensure both datetimes are tz-aware
                    if data_enc.tzinfo is None:
                        data_enc = data_enc.replace(tzinfo=timezone.utc)
                    if data_enc < agora:
                        stats["rejeitadas_prazo"] += 1
                        logger.debug(
                            f"  Rejeitada por prazo: encerramento={data_enc.date()} "
                            f"objeto={lic.get('objetoCompra', '')[:80]}"
                        )
                        continue
                except (ValueError, AttributeError):
                    logger.warning(
                        f"Data de encerramento invalida no safety net: '{data_enc_str}'"
                    )
                aprovadas.append(lic)
                continue

            # Case 2: No dataEncerramentoProposta — strict heuristics
            # Without a deadline, we cannot be CERTAIN the bid is open.
            data_ab_str = lic.get("dataAberturaProposta")
            if data_ab_str:
                try:
                    data_ab = datetime.fromisoformat(
                        data_ab_str.replace("Z", "+00:00")
                    )
                    # GTM-FIX-031: Ensure tz-aware for safe comparison
                    if data_ab.tzinfo is None:
                        data_ab = data_ab.replace(tzinfo=timezone.utc)
                    dias_desde_abertura = (agora - data_ab).days

                    if dias_desde_abertura <= 15:
                        # Very recent opening — likely still open
                        aprovadas.append(lic)
                        continue
                    elif dias_desde_abertura <= 30:
                        # Recent but not brand new — only keep if situação
                        # explicitly says "recebendo" (actively receiving)
                        situacao = (
                            lic.get("situacaoCompraNome", "")
                            or lic.get("situacao", "")
                            or ""
                        ).lower()
                        if "recebendo" in situacao:
                            aprovadas.append(lic)
                            continue
                        else:
                            stats["rejeitadas_prazo"] += 1
                            logger.debug(
                                f"  Rejeitada por heurística (abertura 16-30d sem 'recebendo'): "
                                f"abertura={data_ab.date()} ({dias_desde_abertura}d) "
                                f"situação='{situacao}' "
                                f"objeto={lic.get('objetoCompra', '')[:80]}"
                            )
                            continue
                    else:
                        # > 30 days old without deadline — almost certainly closed
                        stats["rejeitadas_prazo"] += 1
                        logger.debug(
                            f"  Rejeitada por heurística (abertura antiga): "
                            f"abertura={data_ab.date()} ({dias_desde_abertura}d atrás) "
                            f"objeto={lic.get('objetoCompra', '')[:80]}"
                        )
                        continue
                except (ValueError, AttributeError):
                    pass

            # Case 3: No deadline, no opening date — check publication
            data_pub_str = lic.get("dataPublicacaoPncp") or lic.get("dataPublicacao")
            if data_pub_str:
                try:
                    data_pub = datetime.fromisoformat(
                        data_pub_str.replace("Z", "+00:00")
                    )
                    # GTM-FIX-031: Ensure tz-aware for safe comparison
                    if data_pub.tzinfo is None:
                        data_pub = data_pub.replace(tzinfo=timezone.utc)
                    dias_desde_pub = (agora - data_pub).days
                    if dias_desde_pub <= 15:
                        # Very recently published, no other dates — give benefit of doubt
                        aprovadas.append(lic)
                        continue
                    else:
                        stats["rejeitadas_prazo"] += 1
                        logger.debug(
                            f"  Rejeitada por heurística (publicação sem datas): "
                            f"publicação={data_pub.date()} ({dias_desde_pub}d atrás) "
                            f"objeto={lic.get('objetoCompra', '')[:80]}"
                        )
                        continue
                except (ValueError, AttributeError):
                    pass

            # Case 4: No dates at all — REJECT
            # Cannot prove this bid is open without any date information
            stats["rejeitadas_prazo"] += 1
            logger.debug(
                f"  Rejeitada por falta de datas: "
                f"objeto={lic.get('objetoCompra', '')[:80]}"
            )

        logger.debug(
            f"  Após filtro Prazo (safety net + heurísticas): {len(aprovadas)} "
            f"(rejeitadas: {stats['rejeitadas_prazo']})"
        )
    else:
        aprovadas = resultado_keyword

    # ========================================================================
    # STORY-179 FLUXO 2: Anti-False Negative Recovery Pipeline
    # ========================================================================
    # Recover contracts that were incorrectly rejected by keyword filters.
    # This happens when:
    # 1. Exclusion keywords reject legitimate contracts (Camada 1B)
    # 2. Synonym near-misses not covered by keyword set (Camada 2B)
    # 3. LLM recovery for ambiguous rejections (Camada 3B)
    # 4. Zero results relaxation (Camada 4)

    # Initialize FLUXO 2 stats
    stats["recuperadas_exclusion_recovery"] = 0
    stats["aprovadas_synonym_match"] = 0
    stats["recuperadas_llm_fn"] = 0
    stats["recuperadas_zero_results"] = 0
    stats["llm_arbiter_calls_fn_flow"] = 0
    stats["zero_results_relaxation_triggered"] = False

    # GTM-FIX-028 AC10: When LLM zero-match is enabled, skip FLUXO 2 to avoid
    # double-classification (zero-match bids already went through LLM)
    _skip_fluxo_2 = LLM_ZERO_MATCH_ENABLED and stats.get("llm_zero_match_calls", 0) > 0
    if _skip_fluxo_2:
        logger.info(
            "GTM-FIX-028 AC10: FLUXO 2 DISABLED — LLM zero-match already classified "
            f"{stats['llm_zero_match_calls']} bids"
        )

    # Only run recovery when we have a sector (synonym dictionaries are sector-specific)
    if setor and not _skip_fluxo_2:
        from synonyms import find_synonym_matches, should_auto_approve_by_synonyms
        from sectors import get_sector as _get_sector

        try:
            setor_config = _get_sector(setor)
            setor_keywords = setor_config.keywords
            setor_name = setor_config.name

            # Collect IDs of already-approved contracts to avoid duplicates
            aprovadas_ids = {id(lic) for lic in aprovadas}

            # ------------------------------------------------------------------
            # Camada 1B + 2B: Re-scan contracts rejected at keyword stage
            # ------------------------------------------------------------------
            # We look at contracts that passed UF/status/value filters but were
            # rejected by keyword matching (they exist in resultado_valor but
            # not in resultado_keyword).
            rejeitadas_keyword_pool: List[dict] = []
            for lic in resultado_valor:
                if id(lic) not in aprovadas_ids:
                    rejeitadas_keyword_pool.append(lic)

            logger.debug(
                f"FLUXO 2 iniciando: {len(rejeitadas_keyword_pool)} contratos no pool de "
                f"recuperação (rejeitados após filtros rápidos)"
            )

            recuperadas: List[dict] = []
            llm_candidates_fn: List[dict] = []

            for lic in rejeitadas_keyword_pool:
                objeto = lic.get("objetoCompra", "")
                if not objeto:
                    continue

                # Camada 2B: Check synonym matches
                synonym_matches = find_synonym_matches(
                    objeto=objeto,
                    setor_keywords=setor_keywords,
                    setor_id=setor,
                )

                if not synonym_matches:
                    continue  # No synonyms found, skip

                # Check if auto-approve threshold is met (2+ synonyms)
                should_approve, matches = should_auto_approve_by_synonyms(
                    objeto=objeto,
                    setor_keywords=setor_keywords,
                    setor_id=setor,
                    min_synonyms=2,
                )

                if should_approve:
                    # High confidence: 2+ synonym matches → auto-approve
                    stats["aprovadas_synonym_match"] += 1
                    lic["_recovered_by"] = "synonym_auto_approve"
                    lic["_synonym_matches"] = [
                        f"{canon}≈{syn}" for canon, syn in matches
                    ]
                    recuperadas.append(lic)
                    logger.debug(
                        f"  Recuperada por sinônimos (auto): {matches} "
                        f"objeto={objeto[:80]}"
                    )
                else:
                    # 1 synonym match → ambiguous, send to LLM (Camada 3B)
                    lic["_near_miss_synonyms"] = synonym_matches
                    llm_candidates_fn.append(lic)

            # ------------------------------------------------------------------
            # Camada 3B: LLM Recovery for ambiguous synonym matches
            # ------------------------------------------------------------------
            if llm_candidates_fn:
                from llm_arbiter import classify_contract_recovery

                for lic in llm_candidates_fn:
                    objeto = lic.get("objetoCompra", "")
                    valor = lic.get("valorTotalEstimado") or lic.get("valorEstimado") or 0
                    if isinstance(valor, str):
                        try:
                            valor = float(valor.replace(".", "").replace(",", "."))
                        except ValueError:
                            valor = 0.0
                    else:
                        valor = float(valor) if valor else 0.0

                    near_miss = lic.get("_near_miss_synonyms", [])
                    near_miss_info = ", ".join(
                        f"{canon}≈{syn}" for canon, syn in near_miss
                    )

                    stats["llm_arbiter_calls_fn_flow"] += 1
                    should_recover = classify_contract_recovery(
                        objeto=objeto,
                        valor=valor,
                        rejection_reason="keyword_no_match + synonym_near_miss",
                        setor_name=setor_name,
                        near_miss_info=near_miss_info,
                    )

                    if should_recover:
                        stats["recuperadas_llm_fn"] += 1
                        lic["_recovered_by"] = "llm_recovery"
                        lic["_synonym_matches"] = [
                            f"{canon}≈{syn}" for canon, syn in near_miss
                        ]
                        recuperadas.append(lic)
                        logger.debug(
                            f"  Recuperada por LLM (FN flow): near_miss={near_miss_info} "
                            f"objeto={objeto[:80]}"
                        )

            # Add recovered contracts to approved list
            if recuperadas:
                aprovadas.extend(recuperadas)
                logger.info(
                    f"FLUXO 2: {len(recuperadas)} contratos recuperados "
                    f"(synonym_auto: {stats['aprovadas_synonym_match']}, "
                    f"llm_recovery: {stats['recuperadas_llm_fn']})"
                )

            # ------------------------------------------------------------------
            # Camada 4: Zero Results Relaxation
            # ------------------------------------------------------------------
            if len(aprovadas) == 0 and len(rejeitadas_keyword_pool) > 0:
                stats["zero_results_relaxation_triggered"] = True
                logger.info(
                    "FLUXO 2 Camada 4: Zero results detected, attempting relaxation"
                )

                # Relaxation: accept any contract with at least 1 synonym match
                for lic in rejeitadas_keyword_pool:
                    if id(lic) in {id(r) for r in recuperadas}:
                        continue  # Already recovered

                    objeto = lic.get("objetoCompra", "")
                    if not objeto:
                        continue

                    synonym_matches = find_synonym_matches(
                        objeto=objeto,
                        setor_keywords=setor_keywords,
                        setor_id=setor,
                    )

                    if synonym_matches:
                        stats["recuperadas_zero_results"] += 1
                        lic["_recovered_by"] = "zero_results_relaxation"
                        lic["_synonym_matches"] = [
                            f"{canon}≈{syn}" for canon, syn in synonym_matches
                        ]
                        aprovadas.append(lic)

                if stats["recuperadas_zero_results"] > 0:
                    logger.info(
                        f"Camada 4 relaxation: recovered {stats['recuperadas_zero_results']} "
                        f"contracts via single-synonym matching"
                    )

        except KeyError:
            logger.warning(f"Setor '{setor}' não encontrado - pulando FLUXO 2")
        except Exception as e:
            logger.error(f"FLUXO 2 recovery failed: {e}", exc_info=True)

    logger.debug(
        f"FLUXO 2 resultado: "
        f"synonym_auto={stats['aprovadas_synonym_match']}, "
        f"llm_recovery={stats['recuperadas_llm_fn']}, "
        f"zero_results={stats['recuperadas_zero_results']}, "
        f"llm_calls_fn={stats['llm_arbiter_calls_fn_flow']}"
    )
    # ========================================================================

    stats["aprovadas"] = len(aprovadas)

    logger.info(
        f"aplicar_todos_filtros: concluído - {stats['aprovadas']}/{stats['total']} aprovadas "
        f"(FLUXO 1: {stats.get('aprovadas_llm_arbiter', 0)} via LLM arbiter, "
        f"FLUXO 2: {stats.get('recuperadas_llm_fn', 0)} recuperadas)"
    )
    logger.debug(f"  Estatísticas completas: {stats}")

    return aprovadas, stats
