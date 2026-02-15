"""Querido Diario gazette text extraction pipeline.

This module extracts structured procurement data from raw gazette text
obtained via the Querido Diario API. It supports two extraction modes:

1. **LLM extraction** (primary): Uses GPT-4.1-nano with structured output
   (Pydantic) to identify and extract multiple procurement notices from
   a single gazette text. Confidence: 0.7-0.9.

2. **Regex fallback** (AC11): Pattern-based extraction for when the LLM
   is unavailable (no API key, API errors, cost limits). Extracts obvious
   fields like pregao number, R$ values, and opening dates.
   Confidence: 0.3.

Usage:
    from clients.qd_extraction import (
        extract_procurement_from_text,
        extract_procurement_regex_fallback,
        batch_extract_from_gazettes,
    )

    # LLM extraction
    results = extract_procurement_from_text(gazette_text)

    # Regex fallback
    results = extract_procurement_regex_fallback(
        text=gazette_text,
        municipality="Sao Paulo",
        uf="SP",
        source_url="https://...",
        gazette_date="2026-02-10",
    )

    # Batch processing (max 10 gazettes)
    unified = await batch_extract_from_gazettes(gazettes, fetch_fn)
"""

import logging
import os
import re
from datetime import datetime
from typing import Awaitable, Callable, List, Optional

from pydantic import BaseModel, Field

from clients.base import UnifiedProcurement
from schemas import ExtractedProcurement

logger = logging.getLogger(__name__)

# Maximum characters of gazette text to send to LLM (token budget control)
MAX_TEXT_LENGTH = 8000

# Maximum gazettes to process per search (AC10: cost control)
DEFAULT_MAX_GAZETTES = 10


# ============================================================================
# LLM Structured Output Wrapper
# ============================================================================

class ExtractionResult(BaseModel):
    """Wrapper for LLM structured output containing extracted procurements."""
    procurements: List[ExtractedProcurement] = Field(
        default_factory=list,
        description="List of procurement notices found in the gazette text"
    )


# ============================================================================
# LLM Extraction (AC7, AC9)
# ============================================================================

_EXTRACTION_SYSTEM_PROMPT = """Voce e um especialista em extracao de dados de licitacoes publicadas em diarios oficiais municipais brasileiros.

Seu trabalho e encontrar TODAS as licitacoes mencionadas no texto e extrair os dados estruturados de cada uma.

REGRAS:
1. Encontre TODOS os avisos de licitacao, editais, pregoes, concorrencias e dispensas no texto.
2. Para cada licitacao, extraia:
   - modality: modalidade (ex: "Pregao Eletronico", "Concorrencia", "Tomada de Precos", "Dispensa")
   - number: numero do processo/pregao/edital (ex: "023/2026", "001/2026")
   - object_description: descricao do objeto da licitacao (o que esta sendo comprado/contratado)
   - estimated_value: valor estimado em reais (numero decimal, sem R$). Converter "R$ 450.000,00" para 450000.0
   - opening_date: data de abertura em formato YYYY-MM-DD. Converter "28/02/2026" para "2026-02-28"
   - agency_name: nome do orgao contratante (prefeitura, secretaria, etc)
   - extraction_confidence: confianca na extracao de 0.0 a 1.0 (0.9 se todos os campos estao claros, 0.7 se alguns campos estao faltando, 0.5 se a extracao e incerta)

3. Formatos de valor brasileiros:
   - "R$ 450.000,00" -> 450000.0
   - "R$ 1.234.567,89" -> 1234567.89
   - "R$50.000" -> 50000.0

4. Formatos de data brasileiros:
   - "28/02/2026" -> "2026-02-28"
   - "28.02.2026" -> "2026-02-28"
   - "28-02-2026" -> "2026-02-28"

5. Se nenhuma licitacao for encontrada, retorne lista vazia.
6. NAO invente dados. Se um campo nao esta presente no texto, deixe como null.
7. O campo object_description e OBRIGATORIO - se nao conseguir identificar o objeto, use um trecho relevante do texto.
8. Cada aviso de licitacao separado deve gerar um registro separado.
"""


def extract_procurement_from_text(
    text: str,
    municipality: str = "",
    uf: str = "",
    source_url: str = "",
    gazette_date: str = "",
) -> List[ExtractedProcurement]:
    """
    Extract procurement data from raw gazette text using GPT-4.1-nano.

    Uses structured output (Pydantic) to extract multiple procurement notices
    from a single gazette text. Falls back to regex if OpenAI is unavailable.

    Args:
        text: Raw gazette text content (may contain multiple notices).
        municipality: Municipality name for populating extracted records.
        uf: State code (e.g., 'SP') for populating extracted records.
        source_url: URL to the gazette text for provenance.
        gazette_date: Publication date (YYYY-MM-DD) of the gazette.

    Returns:
        List of ExtractedProcurement records found in the text.
        Returns empty list if no procurements are found.

    Examples:
        >>> text = "PREGAO ELETRONICO N. 023/2026 - Objeto: uniformes..."
        >>> results = extract_procurement_from_text(text, "Sao Paulo", "SP", "", "2026-02-10")
        >>> len(results) >= 0
        True
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning(
            "OPENAI_API_KEY not set, falling back to regex extraction"
        )
        return extract_procurement_regex_fallback(
            text=text,
            municipality=municipality,
            uf=uf,
            source_url=source_url,
            gazette_date=gazette_date,
        )

    # Truncate text to stay within token limits
    truncated_text = text[:MAX_TEXT_LENGTH]
    if len(text) > MAX_TEXT_LENGTH:
        logger.info(
            "Gazette text truncated from %d to %d chars for LLM extraction",
            len(text), MAX_TEXT_LENGTH,
        )

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        user_prompt = (
            f"Extraia todas as licitacoes do seguinte texto de diario oficial "
            f"de {municipality or 'municipio nao informado'} ({uf or 'UF'}):\n\n"
            f"{truncated_text}"
        )

        response = client.beta.chat.completions.parse(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format=ExtractionResult,
            temperature=0.1,
            max_tokens=2000,
        )

        result = response.choices[0].message.parsed
        if not result:
            logger.warning("OpenAI returned empty parsed response for gazette extraction")
            return []

        # Populate context fields not available in the text itself
        for proc in result.procurements:
            if not proc.municipality:
                proc.municipality = municipality
            if not proc.uf:
                proc.uf = uf
            if not proc.source_url:
                proc.source_url = source_url
            if not proc.gazette_date:
                proc.gazette_date = gazette_date
            # Store the truncated source text as raw excerpt
            if not proc.raw_excerpt:
                proc.raw_excerpt = truncated_text[:500]

        logger.info(
            "LLM extracted %d procurements from gazette (%s, %s)",
            len(result.procurements), municipality, gazette_date,
        )
        return result.procurements

    except Exception as e:
        logger.error(
            "LLM extraction failed, falling back to regex: %s", str(e)
        )
        return extract_procurement_regex_fallback(
            text=text,
            municipality=municipality,
            uf=uf,
            source_url=source_url,
            gazette_date=gazette_date,
        )


# ============================================================================
# Regex Fallback Extraction (AC11)
# ============================================================================

# --- Regex patterns for Brazilian procurement texts ---

# Boundaries to split gazette text into individual notice sections
_SECTION_BOUNDARIES = re.compile(
    r"(?:AVISO\s+DE\s+LICITA[CÇ][AÃ]O|"
    r"EXTRATO\s+DE\s+CONTRATO|"
    r"PREG[AÃ]O\s+(?:ELETR[OÔ]NICO|PRESENCIAL)|"
    r"EDITAL\s+DE\s+LICITA[CÇ][AÃ]O|"
    r"CONCORR[EÊ]NCIA|"
    r"TOMADA\s+DE\s+PRE[CÇ]OS|"
    r"DISPENSA\s+DE\s+LICITA[CÇ][AÃ]O|"
    r"CHAMADA\s+P[UÚ]BLICA)",
    re.IGNORECASE | re.UNICODE,
)

# Pregao / procurement number
_RE_PREGAO_NUMBER = re.compile(
    r"(?:preg[aã]o|pregao)\s+(?:eletr[oô]nico|eletronico|presencial)?\s*"
    r"(?:n[.ºo°]?\s*)?(\d{1,4}[/.\-]\d{4})",
    re.IGNORECASE | re.UNICODE,
)

# Generic procurement number (edital, concorrencia, etc.)
_RE_EDITAL_NUMBER = re.compile(
    r"(?:edital|concorr[eê]ncia|tomada\s+de\s+pre[cç]os|dispensa|processo)"
    r"\s*(?:n[.ºo°]?\s*)?(\d{1,4}[/.\-]\d{4})",
    re.IGNORECASE | re.UNICODE,
)

# Brazilian currency value: R$ 450.000,00
_RE_VALUE = re.compile(
    r"R\$\s*([\d.]+,\d{2})",
    re.UNICODE,
)

# Opening date patterns
_RE_OPENING_DATE = re.compile(
    r"(?:abertura|data\s+de\s+abertura|sess[aã]o|sess[aã]o\s+p[uú]blica)"
    r"[:\s]+(\d{2}[/.\-]\d{2}[/.\-]\d{4})",
    re.IGNORECASE | re.UNICODE,
)

# Generic date pattern (fallback)
_RE_DATE_GENERIC = re.compile(
    r"(\d{2}/\d{2}/\d{4})",
)

# Modality
_RE_MODALITY = re.compile(
    r"(preg[aã]o\s+eletr[oô]nico|preg[aã]o\s+presencial|"
    r"pregao\s+eletronico|pregao\s+presencial|"
    r"concorr[eê]ncia|concorrencia|"
    r"tomada\s+de\s+pre[cç]os|tomada\s+de\s+precos|"
    r"concurso|"
    r"dispensa(?:\s+de\s+licita[cç][aã]o)?|"
    r"chamada\s+p[uú]blica|chamada\s+publica)",
    re.IGNORECASE | re.UNICODE,
)

# Object description: text after "OBJETO:" or "Objeto:"
_RE_OBJECT = re.compile(
    r"(?:OBJETO|Objeto)\s*:\s*(.+?)(?:\n\n|\n[A-Z]{2,}|\.\s*(?:VALOR|PRAZO|DATA|ABERTURA|EDITAL))",
    re.IGNORECASE | re.DOTALL | re.UNICODE,
)

# Simpler object pattern (single line)
_RE_OBJECT_SIMPLE = re.compile(
    r"(?:OBJETO|Objeto)\s*:\s*(.+?)(?:\.|$)",
    re.IGNORECASE | re.UNICODE,
)


def _parse_brazilian_value(value_str: str) -> Optional[float]:
    """
    Parse Brazilian currency format to float.

    Handles formats like:
    - "450.000,00" -> 450000.0
    - "1.234.567,89" -> 1234567.89
    - "50.000" -> 50000.0 (no decimal separator)

    Args:
        value_str: Value string without "R$" prefix.

    Returns:
        Parsed float value, or None if parsing fails.
    """
    try:
        # Remove thousands separators (dots) and replace decimal comma
        cleaned = value_str.replace(".", "").replace(",", ".")
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def _parse_brazilian_date(date_str: str) -> Optional[str]:
    """
    Parse Brazilian date format (DD/MM/YYYY) to ISO format (YYYY-MM-DD).

    Handles separators: /, ., -

    Args:
        date_str: Date string in DD/MM/YYYY, DD.MM.YYYY, or DD-MM-YYYY format.

    Returns:
        Date in YYYY-MM-DD format, or None if parsing fails.
    """
    try:
        # Normalize separators to /
        normalized = date_str.replace(".", "/").replace("-", "/")
        dt = datetime.strptime(normalized, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return None


def extract_procurement_regex_fallback(
    text: str,
    municipality: str,
    uf: str,
    source_url: str,
    gazette_date: str,
) -> List[ExtractedProcurement]:
    """
    Extract procurement data from gazette text using regex patterns.

    This is the fallback extraction method when LLM is unavailable (AC11).
    It uses pattern matching to find procurement notices and extract
    obvious fields like pregao numbers, R$ values, and opening dates.

    The extraction confidence is set to 0.3 (lower than LLM's 0.7-0.9)
    to reflect the lower accuracy of pattern-based extraction.

    Args:
        text: Raw gazette text content.
        municipality: Municipality name.
        uf: State code (e.g., 'SP').
        source_url: URL to the gazette.
        gazette_date: Publication date (YYYY-MM-DD).

    Returns:
        List of ExtractedProcurement records found via regex.
        Returns empty list if no procurement patterns are found.

    Examples:
        >>> text = "PREGAO ELETRONICO N. 023/2026 OBJETO: uniformes R$ 100.000,00"
        >>> results = extract_procurement_regex_fallback(
        ...     text, "Sao Paulo", "SP", "https://example.com", "2026-02-10"
        ... )
        >>> len(results) >= 1
        True
    """
    results: List[ExtractedProcurement] = []

    # Split text into sections by notice boundaries
    sections = _split_into_sections(text)

    for section in sections:
        extracted = _extract_from_section(
            section=section,
            municipality=municipality,
            uf=uf,
            source_url=source_url,
            gazette_date=gazette_date,
        )
        if extracted:
            results.append(extracted)

    # If no section-based extraction worked, try the whole text as one block
    if not results and len(text.strip()) > 50:
        extracted = _extract_from_section(
            section=text,
            municipality=municipality,
            uf=uf,
            source_url=source_url,
            gazette_date=gazette_date,
        )
        if extracted:
            results.append(extracted)

    logger.info(
        "Regex fallback extracted %d procurements from gazette (%s, %s)",
        len(results), municipality, gazette_date,
    )
    return results


def _split_into_sections(text: str) -> List[str]:
    """
    Split gazette text into individual notice sections.

    Uses known procurement-related headers as boundaries
    (AVISO DE LICITACAO, PREGAO, EDITAL, etc.).

    Args:
        text: Full gazette text.

    Returns:
        List of text sections, each potentially containing one notice.
    """
    # Find all boundary positions
    matches = list(_SECTION_BOUNDARIES.finditer(text))

    if not matches:
        return []

    sections = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section = text[start:end].strip()
        if len(section) > 20:  # Skip trivially short fragments
            sections.append(section)

    return sections


def _extract_from_section(
    section: str,
    municipality: str,
    uf: str,
    source_url: str,
    gazette_date: str,
) -> Optional[ExtractedProcurement]:
    """
    Extract procurement data from a single text section using regex.

    Args:
        section: Text section (typically one procurement notice).
        municipality: Municipality name.
        uf: State code.
        source_url: URL to gazette.
        gazette_date: Publication date (YYYY-MM-DD).

    Returns:
        ExtractedProcurement if any procurement data was found, else None.
    """
    # Try to extract procurement number
    number = None
    number_match = _RE_PREGAO_NUMBER.search(section)
    if number_match:
        number = number_match.group(1)
    else:
        edital_match = _RE_EDITAL_NUMBER.search(section)
        if edital_match:
            number = edital_match.group(1)

    # Extract modality
    modality = None
    modality_match = _RE_MODALITY.search(section)
    if modality_match:
        modality = modality_match.group(1).strip()

    # Extract value (take the largest value found, likely the estimated total)
    estimated_value = None
    value_matches = _RE_VALUE.findall(section)
    if value_matches:
        parsed_values = [_parse_brazilian_value(v) for v in value_matches]
        valid_values = [v for v in parsed_values if v is not None and v > 0]
        if valid_values:
            estimated_value = max(valid_values)

    # Extract opening date
    opening_date = None
    date_match = _RE_OPENING_DATE.search(section)
    if date_match:
        opening_date = _parse_brazilian_date(date_match.group(1))

    # Extract object description
    object_description = None
    obj_match = _RE_OBJECT.search(section)
    if obj_match:
        object_description = obj_match.group(1).strip()
    else:
        obj_simple = _RE_OBJECT_SIMPLE.search(section)
        if obj_simple:
            object_description = obj_simple.group(1).strip()

    # If we could not extract even a minimal description, use a section snippet
    if not object_description:
        # Use first 200 chars of the section as a description fallback
        clean_section = " ".join(section.split())
        object_description = clean_section[:200].strip()
        if not object_description:
            return None  # Nothing useful to extract

    # We need at least one meaningful field beyond just the description
    has_meaningful_data = any([number, modality, estimated_value, opening_date])
    if not has_meaningful_data and len(object_description) < 30:
        return None

    return ExtractedProcurement(
        modality=modality,
        number=number,
        object_description=object_description,
        estimated_value=estimated_value,
        opening_date=opening_date,
        agency_name=None,
        municipality=municipality,
        uf=uf,
        source_url=source_url,
        gazette_date=gazette_date,
        extraction_confidence=0.3,
        raw_excerpt=section[:500],
    )


# ============================================================================
# Conversion to UnifiedProcurement (AC12)
# ============================================================================

def to_unified_procurement(
    extracted: ExtractedProcurement,
    gazette_id: str,
) -> UnifiedProcurement:
    """
    Convert an ExtractedProcurement to the canonical UnifiedProcurement format.

    This bridges the Querido Diario extraction pipeline with the existing
    multi-source procurement pipeline used by the search endpoint.

    Args:
        extracted: Structured data extracted from gazette text.
        gazette_id: Unique gazette identifier from Querido Diario API.

    Returns:
        UnifiedProcurement compatible with existing filter/excel pipeline.

    Examples:
        >>> from schemas import ExtractedProcurement
        >>> ep = ExtractedProcurement(
        ...     object_description="Uniformes escolares",
        ...     municipality="Sao Paulo",
        ...     uf="SP",
        ...     source_url="https://example.com",
        ...     gazette_date="2026-02-10",
        ... )
        >>> up = to_unified_procurement(ep, "gazette-123")
        >>> up.source_name
        'QUERIDO_DIARIO'
    """
    # Build source_id from gazette_id and procurement number
    number_slug = extracted.number or "unknown"
    source_id = f"QD-{gazette_id}-{number_slug}"

    # Parse gazette_date to datetime
    data_publicacao = None
    if extracted.gazette_date:
        try:
            data_publicacao = datetime.strptime(
                extracted.gazette_date, "%Y-%m-%d"
            )
        except ValueError:
            logger.warning(
                "Could not parse gazette_date: %s", extracted.gazette_date
            )

    # Parse opening_date to datetime
    data_abertura = None
    if extracted.opening_date:
        try:
            data_abertura = datetime.strptime(
                extracted.opening_date, "%Y-%m-%d"
            )
        except ValueError:
            logger.warning(
                "Could not parse opening_date: %s", extracted.opening_date
            )

    return UnifiedProcurement(
        source_id=source_id,
        source_name="QUERIDO_DIARIO",
        objeto=extracted.object_description,
        valor_estimado=extracted.estimated_value or 0.0,
        orgao=extracted.agency_name or "",
        cnpj_orgao="",
        uf=extracted.uf,
        municipio=extracted.municipality,
        data_publicacao=data_publicacao,
        data_abertura=data_abertura,
        numero_edital=extracted.number or "",
        modalidade=extracted.modality or "",
        esfera="M",  # Querido Diario = municipal gazettes
        link_edital=extracted.source_url,
        link_portal=extracted.source_url,
    )


# ============================================================================
# Batch Processing (AC10)
# ============================================================================

async def batch_extract_from_gazettes(
    gazettes: List[dict],
    fetch_text_fn: Callable[[str], Awaitable[str]],
    max_gazettes: int = DEFAULT_MAX_GAZETTES,
) -> List[UnifiedProcurement]:
    """
    Extract procurements from multiple gazettes, converting to UnifiedProcurement.

    Orchestrates the full extraction pipeline:
    1. Takes first max_gazettes gazettes (AC10: cost control)
    2. Fetches text content for each gazette via fetch_text_fn
    3. Attempts LLM extraction, falls back to regex on error
    4. Converts all ExtractedProcurement records to UnifiedProcurement
    5. Returns flat list ready for the existing filter/dedup pipeline

    Args:
        gazettes: List of gazette dicts from Querido Diario API.
            Expected keys: 'txt_url', 'territory_name', 'state_code',
            'date', 'territory_id' (or 'id').
        fetch_text_fn: Async function that fetches gazette text given a URL.
            Signature: async (url: str) -> str
        max_gazettes: Maximum number of gazettes to process (default 10).

    Returns:
        Flat list of UnifiedProcurement records extracted from all gazettes.

    Examples:
        >>> async def mock_fetch(url: str) -> str:
        ...     return "PREGAO ELETRONICO N. 001/2026 OBJETO: uniformes R$ 50.000,00"
        >>> gazettes = [{"txt_url": "http://...", "territory_name": "SP",
        ...              "state_code": "SP", "date": "2026-02-10", "id": "g1"}]
        >>> # results = await batch_extract_from_gazettes(gazettes, mock_fetch)
    """
    unified_results: List[UnifiedProcurement] = []

    # Limit to max_gazettes (AC10: avoid excessive LLM cost)
    gazettes_to_process = gazettes[:max_gazettes]

    logger.info(
        "Starting batch extraction: %d of %d gazettes (max=%d)",
        len(gazettes_to_process), len(gazettes), max_gazettes,
    )

    for i, gazette in enumerate(gazettes_to_process):
        txt_url = gazette.get("txt_url", "")
        if not txt_url:
            logger.warning("Gazette %d has no txt_url, skipping", i)
            continue

        municipality = gazette.get("territory_name", "")
        uf = gazette.get("state_code", "")
        gazette_date = gazette.get("date", "")
        gazette_id = gazette.get("id", gazette.get("territory_id", f"unknown-{i}"))

        try:
            # Fetch gazette text content
            text = await fetch_text_fn(txt_url)
            if not text or len(text.strip()) < 20:
                logger.warning(
                    "Gazette %d (%s) returned empty/short text, skipping",
                    i, gazette_id,
                )
                continue

            # Extract procurements (LLM first, regex fallback)
            extracted_list = extract_procurement_from_text(
                text=text,
                municipality=municipality,
                uf=uf,
                source_url=txt_url,
                gazette_date=gazette_date,
            )

            # Convert to UnifiedProcurement
            for extracted in extracted_list:
                unified = to_unified_procurement(extracted, str(gazette_id))
                unified_results.append(unified)

            logger.info(
                "Gazette %d/%d (%s): extracted %d procurements",
                i + 1, len(gazettes_to_process), gazette_id,
                len(extracted_list),
            )

        except Exception as e:
            logger.error(
                "Failed to process gazette %d (%s): %s",
                i, gazette_id, str(e),
            )
            # Continue with remaining gazettes -- don't let one failure
            # block the entire batch
            continue

    logger.info(
        "Batch extraction complete: %d unified procurements from %d gazettes",
        len(unified_results), len(gazettes_to_process),
    )
    return unified_results
