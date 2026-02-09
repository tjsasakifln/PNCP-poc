"""
Módulo de ordenação de resultados de licitações.

Este módulo fornece funções para ordenar resultados de busca de licitações
por diferentes critérios: data, valor, prazo de abertura e relevância.

Opções de ordenação suportadas:
- data_desc: Mais recente primeiro (padrão)
- data_asc: Mais antigo primeiro
- valor_desc: Maior valor primeiro
- valor_asc: Menor valor primeiro
- prazo_asc: Prazo de abertura mais próximo
- relevancia: Score de matching com termos de busca
"""

import re
import unicodedata
from datetime import datetime
from typing import Any, Callable, Tuple


def parse_date(date_str: str | None) -> datetime:
    """
    Parse date string to datetime, with fallback to datetime.min.

    Handles multiple date formats commonly found in PNCP API responses:
    - ISO 8601 with timezone: "2026-02-06T10:00:00Z"
    - ISO 8601 with offset: "2026-02-06T10:00:00+00:00"
    - ISO 8601 date only: "2026-02-06"
    - Brazilian format: "06/02/2026"

    Args:
        date_str: Date string to parse, or None

    Returns:
        datetime: Parsed datetime or datetime.min if parsing fails

    Examples:
        >>> parse_date("2026-02-06T10:00:00Z")
        datetime(2026, 2, 6, 10, 0, 0)
        >>> parse_date(None)
        datetime.min
        >>> parse_date("invalid")
        datetime.min
    """
    if not date_str:
        return datetime.min

    if not isinstance(date_str, str):
        return datetime.min

    # Normalize common variations
    date_str = date_str.strip()

    # List of formats to try
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",      # 2026-02-06T10:00:00.000Z
        "%Y-%m-%dT%H:%M:%SZ",          # 2026-02-06T10:00:00Z
        "%Y-%m-%dT%H:%M:%S.%f",        # 2026-02-06T10:00:00.000
        "%Y-%m-%dT%H:%M:%S",           # 2026-02-06T10:00:00
        "%Y-%m-%d",                     # 2026-02-06
        "%d/%m/%Y",                     # 06/02/2026
        "%d/%m/%Y %H:%M:%S",           # 06/02/2026 10:00:00
    ]

    # Handle timezone offset (replace +00:00 style)
    if "+" in date_str and "T" in date_str:
        # Remove timezone offset for simpler parsing
        date_str = re.sub(r'[+-]\d{2}:\d{2}$', '', date_str)

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # Try fromisoformat as last resort
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00').replace('+00:00', ''))
    except ValueError:
        pass

    return datetime.min


def parse_valor(valor: Any) -> float:
    """
    Parse valor to float, handling Brazilian format (1.234,56).

    Handles multiple value formats:
    - Numeric types: int, float
    - String with dots as thousands separator: "1.234.567,89"
    - String with commas as decimal: "1234,56"
    - String with dots as decimal: "1234.56"
    - None or invalid values: returns 0.0

    Args:
        valor: Value to parse (any type)

    Returns:
        float: Parsed value or 0.0 if parsing fails

    Examples:
        >>> parse_valor(150000.00)
        150000.0
        >>> parse_valor("1.234.567,89")
        1234567.89
        >>> parse_valor("150000,50")
        150000.5
        >>> parse_valor(None)
        0.0
    """
    if valor is None:
        return 0.0

    # Already numeric
    if isinstance(valor, (int, float)):
        return float(valor)

    if not isinstance(valor, str):
        return 0.0

    valor_str = valor.strip()

    if not valor_str:
        return 0.0

    try:
        # Check if it's Brazilian format (has comma as decimal separator)
        # Brazilian: 1.234.567,89 -> 1234567.89
        # US/API: 1234567.89 -> 1234567.89

        has_comma = ',' in valor_str
        has_dot = '.' in valor_str

        if has_comma and has_dot:
            # Brazilian format: 1.234.567,89
            # Dots are thousands separators, comma is decimal
            valor_str = valor_str.replace('.', '')  # Remove thousands separator
            valor_str = valor_str.replace(',', '.')  # Convert decimal separator
        elif has_comma and not has_dot:
            # Only comma: 1234,56 (Brazilian decimal only)
            valor_str = valor_str.replace(',', '.')
        # If only dots or no separators, assume US format (dots as decimal)

        return float(valor_str)
    except ValueError:
        return 0.0


def _normalize_text(text: str) -> str:
    """
    Normalize text for relevance matching.

    Converts text to lowercase and removes accents for consistent matching.

    Args:
        text: Input text

    Returns:
        str: Normalized text
    """
    if not text:
        return ""

    text = text.lower()
    # Remove accents using NFD normalization
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text


def calcular_relevancia(licitacao: dict, termos: list[str]) -> float:
    """
    Calcula score de relevância (0.0 a 1.0) baseado nos termos de busca.

    NI-5: Wrapper de alto nível que:
    1. Extrai texto de objetoCompra, descricao, nomeOrgao
    2. Conta termos matchados (substring matching)
    3. Delega cálculo numérico para score_relevance() de relevance.py

    Inclui phrase_bonus para termos multi-palavra que matcham como sequência.

    Args:
        licitacao: Dicionário com dados da licitação
        termos: Lista de termos de busca

    Returns:
        float: Score de relevância entre 0.0 e 1.0

    Examples:
        >>> licitacao = {"objetoCompra": "Aquisição de uniformes escolares"}
        >>> calcular_relevancia(licitacao, ["uniforme", "escolar"])
        1.0
        >>> calcular_relevancia(licitacao, ["uniforme", "hospital"])
        0.5
        >>> calcular_relevancia(licitacao, [])
        0.0
    """
    # If the bid already has a pre-computed relevance_score (from main.py), use it
    if "_relevance_score" in licitacao:
        return licitacao["_relevance_score"]

    if not termos:
        return 0.0

    # Build combined text from relevant fields
    campos = [
        str(licitacao.get('objetoCompra', '') or ''),
        str(licitacao.get('descricao', '') or ''),
        str(licitacao.get('nomeOrgao', '') or ''),
    ]

    texto = ' '.join(campos)
    texto_norm = _normalize_text(texto)

    if not texto_norm:
        return 0.0

    # Count matching terms and phrase matches
    matches = 0
    phrase_matches = 0
    for termo in termos:
        termo_norm = _normalize_text(termo)
        if termo_norm and termo_norm in texto_norm:
            matches += 1
            # Count multi-word terms as phrase matches
            if " " in termo:
                phrase_matches += 1

    # Delegate to score_relevance() for the numerical calculation
    from relevance import score_relevance
    return score_relevance(matches, len(termos), phrase_matches)


def ordenar_licitacoes(
    licitacoes: list[dict],
    ordenacao: str = 'data_desc',
    termos_busca: list[str] | None = None
) -> list[dict]:
    """
    Ordena lista de licitações pelo critério especificado.

    Opções de ordenação:
    - data_desc: Mais recente primeiro (padrão)
    - data_asc: Mais antigo primeiro
    - valor_desc: Maior valor primeiro
    - valor_asc: Menor valor primeiro
    - prazo_asc: Prazo de abertura mais próximo
    - relevancia: Score de matching com termos de busca

    Campos utilizados para cada critério:
    - data_*: dataPublicacao ou dataPublicacaoPncp
    - valor_*: valorTotalEstimado ou valorEstimado
    - prazo_asc: dataAberturaProposta ou dataAberturaPropostas
    - relevancia: objetoCompra, descricao, nomeOrgao

    Args:
        licitacoes: Lista de licitações para ordenar
        ordenacao: Critério de ordenação (padrão: 'data_desc')
        termos_busca: Termos para cálculo de relevância (opcional)

    Returns:
        list[dict]: Lista ordenada de licitações

    Examples:
        >>> licitacoes = [
        ...     {"objetoCompra": "A", "dataPublicacao": "2026-01-01"},
        ...     {"objetoCompra": "B", "dataPublicacao": "2026-02-01"},
        ... ]
        >>> resultado = ordenar_licitacoes(licitacoes, "data_desc")
        >>> resultado[0]["objetoCompra"]
        'B'
    """
    if not licitacoes:
        return []

    # Create a copy to avoid mutating the original list
    licitacoes = list(licitacoes)

    def get_data_publicacao(lic: dict) -> datetime:
        """Extract publication date from licitacao."""
        # Try multiple field names used by PNCP API
        date_str = (
            lic.get('dataPublicacao') or
            lic.get('dataPublicacaoPncp') or
            lic.get('data_publicacao')
        )
        return parse_date(date_str)

    def get_valor(lic: dict) -> float:
        """Extract value from licitacao."""
        # Try multiple field names used by PNCP API
        valor = (
            lic.get('valorTotalEstimado') or
            lic.get('valorEstimado') or
            lic.get('valor') or
            0
        )
        return parse_valor(valor)

    def get_data_abertura(lic: dict) -> datetime:
        """Extract proposal opening date from licitacao."""
        # Try multiple field names used by PNCP API
        date_str = (
            lic.get('dataAberturaProposta') or
            lic.get('dataAberturaPropostas') or
            lic.get('data_abertura')
        )
        return parse_date(date_str)

    def get_relevancia(lic: dict) -> float:
        """Calculate relevance score for licitacao."""
        return calcular_relevancia(lic, termos_busca or [])

    # Define sort functions: (key_function, reverse)
    sort_functions: dict[str, Tuple[Callable[[dict], Any], bool]] = {
        'data_desc': (get_data_publicacao, True),   # Most recent first
        'data_asc': (get_data_publicacao, False),   # Oldest first
        'valor_desc': (get_valor, True),            # Highest value first
        'valor_asc': (get_valor, False),            # Lowest value first
        'prazo_asc': (get_data_abertura, False),    # Nearest deadline first
        'relevancia': (get_relevancia, True),       # Most relevant first
    }

    # Get sort function, default to data_desc
    key_func, reverse = sort_functions.get(
        ordenacao,
        sort_functions['data_desc']
    )

    # AC4.1: For relevance sort, use compound key with date tiebreaker
    if ordenacao == 'relevancia':
        def relevancia_with_tiebreaker(lic: dict) -> Tuple[float, datetime]:
            return (get_relevancia(lic), get_data_publicacao(lic))
        return sorted(licitacoes, key=relevancia_with_tiebreaker, reverse=True)

    return sorted(licitacoes, key=key_func, reverse=reverse)
