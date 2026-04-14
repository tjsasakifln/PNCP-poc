"""Transform raw PNCP API responses into pncp_raw_bids row format.

Responsibilities:
- Extract and normalise all required fields from nested PNCP response dicts
- Compute a content_hash for change-detection (avoids redundant DB writes)
- Skip malformed items gracefully (log warning, continue batch)
- STORY-2.12 AC4: defensive fallback for NULL/empty dataPublicacaoPncp so
  newly-ingested rows are always searchable (pairs with the DB-side
  COALESCE wrapper in 20260414133000_search_datalake_coalesce_dates.sql).
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)


# STORY-2.12 AC4: conservative fallback — one day before "now" so the row is
# visible in the default 10-day search window but not masquerading as fresh.
def _date_fallback_iso() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()


# ---------------------------------------------------------------------------
# Hash helpers
# ---------------------------------------------------------------------------

def compute_content_hash(item: dict) -> str:
    """Return SHA-256 hex digest of the key business fields.

    Fields: objeto_compra + valor_total_estimado + situacao_compra.
    Canonicalised to lowercase + stripped whitespace so minor formatting
    differences don't generate spurious updates.
    """
    objeto = (item.get("objetoCompra") or "").lower().strip()
    valor = str(item.get("valorTotalEstimado") or "")
    situacao = (
        item.get("situacaoCompraNome") or item.get("situacaoCompra") or ""
    ).lower().strip()

    canonical = f"{objeto}|{valor}|{situacao}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Single-item transformer
# ---------------------------------------------------------------------------

def transform_pncp_item(
    raw_item: dict,
    *,
    source: str = "pncp",
    crawl_batch_id: str | None = None,
) -> dict:
    """Convert a raw PNCP API item to a pncp_raw_bids row dict.

    Args:
        raw_item: Single item from the PNCP ``data`` array.
        source: Data source tag stored on the row (default "pncp").
        crawl_batch_id: Batch identifier for the crawl run (nullable).

    Returns:
        Dict matching the pncp_raw_bids column schema.

    Raises:
        ValueError: If the item is missing the mandatory ``numeroControlePNCP`` field.
    """
    pncp_id: str = raw_item.get("numeroControlePNCP", "").strip()
    if not pncp_id:
        raise ValueError(
            "Raw item is missing 'numeroControlePNCP' — cannot build row without a unique key."
        )

    # ------------------------------------------------------------------
    # Orgao / unidade helpers — PNCP nests these differently per endpoint
    # ------------------------------------------------------------------
    orgao: dict[str, Any] = raw_item.get("orgaoEntidade") or {}
    unidade: dict[str, Any] = raw_item.get("unidadeOrgao") or {}

    # ------------------------------------------------------------------
    # Core identifiers
    # ------------------------------------------------------------------
    objeto_compra: str = raw_item.get("objetoCompra") or ""
    valor_total_estimado = raw_item.get("valorTotalEstimado")

    # modalidade can live in two different field names depending on API version
    modalidade_id = raw_item.get("modalidadeId") or raw_item.get("codigoModalidadeContratacao")
    modalidade_nome: str = raw_item.get("modalidadeNome") or ""

    situacao_compra: str = raw_item.get("situacaoCompraNome") or raw_item.get("situacaoCompra") or ""

    # ------------------------------------------------------------------
    # Geography
    # ------------------------------------------------------------------
    uf: str = unidade.get("ufSigla") or raw_item.get("uf") or ""
    municipio: str = unidade.get("municipioNome") or raw_item.get("municipioNome") or ""
    codigo_municipio_ibge: str = (
        unidade.get("codigoMunicipioIbge")
        or raw_item.get("codigoMunicipioIbge")
        or ""
    )

    # ------------------------------------------------------------------
    # Orgao / esfera
    # ------------------------------------------------------------------
    # esferaId may come from orgao or be inferrable from the orgao CNPJ prefix
    esfera_id = orgao.get("esferaId") or raw_item.get("esferaId")

    orgao_razao_social: str = (
        orgao.get("razaoSocial")
        or unidade.get("nomeUnidade")
        or raw_item.get("razaoSocial")
        or ""
    )
    orgao_cnpj: str = orgao.get("cnpj") or raw_item.get("cnpj") or ""
    unidade_nome: str = unidade.get("nomeUnidade") or raw_item.get("nomeUnidade") or ""

    # ------------------------------------------------------------------
    # Dates (keep as ISO strings; DB will cast to timestamptz)
    # ------------------------------------------------------------------
    # STORY-2.12 AC4: forward-looking defensive fallback. If PNCP ever
    # returns an empty/NULL dataPublicacaoPncp again, we substitute a safe
    # default so the row still gets indexed and searchable. data_abertura
    # then mirrors data_publicacao (when missing) because "when does this
    # bid open for proposals?" practically defaults to "today" for the
    # consumer-facing timeline.
    data_publicacao = raw_item.get("dataPublicacaoPncp")
    if not data_publicacao:
        data_publicacao = _date_fallback_iso()
        logger.warning(
            "transform_pncp_item: dataPublicacaoPncp missing for pncp_id=%s — applied STORY-2.12 fallback",
            pncp_id,
        )
    data_abertura = raw_item.get("dataAberturaProposta") or data_publicacao
    data_encerramento = raw_item.get("dataEncerramentoProposta")

    # ------------------------------------------------------------------
    # Links
    # ------------------------------------------------------------------
    link_sistema_origem: str = raw_item.get("linkSistemaOrigem") or ""
    link_pncp: str = (
        f"https://pncp.gov.br/app/editais/{pncp_id}" if pncp_id else ""
    )

    # ------------------------------------------------------------------
    # Content hash for change detection
    # ------------------------------------------------------------------
    content_hash = compute_content_hash(raw_item)

    return {
        "pncp_id": pncp_id,
        "objeto_compra": objeto_compra,
        "valor_total_estimado": valor_total_estimado,
        "modalidade_id": modalidade_id,
        "modalidade_nome": modalidade_nome,
        "situacao_compra": situacao_compra,
        "esfera_id": esfera_id,
        "uf": uf,
        "municipio": municipio,
        "codigo_municipio_ibge": codigo_municipio_ibge,
        "orgao_razao_social": orgao_razao_social,
        "orgao_cnpj": orgao_cnpj,
        "unidade_nome": unidade_nome,
        "data_publicacao": data_publicacao,
        "data_abertura": data_abertura,
        "data_encerramento": data_encerramento,
        "link_sistema_origem": link_sistema_origem,
        "link_pncp": link_pncp,
        "content_hash": content_hash,
        "source": source,
        "crawl_batch_id": crawl_batch_id,
        # Preserve raw payload for future enrichment / schema evolution
        "raw_payload": raw_item,
    }


# ---------------------------------------------------------------------------
# Batch helper
# ---------------------------------------------------------------------------

def transform_batch(
    items: list[dict],
    *,
    source: str = "pncp",
    crawl_batch_id: str | None = None,
) -> list[dict]:
    """Transform a list of raw items, skipping any that fail validation.

    Args:
        items: Raw items from a PNCP API response ``data`` array.
        source: Data source tag.
        crawl_batch_id: Batch identifier for the crawl run.

    Returns:
        List of successfully transformed row dicts (may be shorter than input).
    """
    transformed: list[dict] = []
    skipped = 0

    for idx, item in enumerate(items):
        try:
            row = transform_pncp_item(item, source=source, crawl_batch_id=crawl_batch_id)
            transformed.append(row)
        except Exception as exc:
            skipped += 1
            pncp_id_hint = item.get("numeroControlePNCP", f"index={idx}")
            logger.warning(
                "transform_batch: skipping item pncp_id=%s — %s: %s",
                pncp_id_hint,
                type(exc).__name__,
                exc,
            )

    if skipped:
        logger.info(
            "transform_batch: transformed %d items, skipped %d due to errors",
            len(transformed),
            skipped,
        )

    return transformed
