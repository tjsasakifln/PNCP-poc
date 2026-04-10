"""Sprint 2 Parte 13: enriquecimento de fornecedores com APIs publicas externas.

Fluxo diario (08:00 UTC, apos contracts crawl):
  1. Busca CNPJs unicos em pncp_supplier_contracts nao enriquecidos ha 30+ dias
  2. Para cada CNPJ: chama BrasilAPI /cnpj/v1/{cnpj}
  3. Upsert resultado em enriched_entities (entity_type='fornecedor')

Throttle: semaforo asyncio(10) — no maximo 10 chamadas concorrentes.
Taxa BrasilAPI: sem rate limit documentado; CDN 23 regioes.
Taxa Portal da Transparencia: 90 req/min (6h-23h59). Reservado para fases futuras.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_BRASILAPI_BASE = "https://brasilapi.com.br/api"
_ENRICH_STALENESS_DAYS = 30
_BATCH_SIZE = 500         # CNPJs por lote de busca no Supabase
_MAX_CNPJS_PER_RUN = 5000 # teto de seguranca por execucao
_HTTP_TIMEOUT = 10.0      # segundos por requisicao externa
_CONCURRENCY = 10         # requisicoes paralelas maximas


async def enrich_entities_job() -> dict[str, Any]:
    """Entry point do job ARQ.

    Enriquece fornecedores nao atualizados ha mais de _ENRICH_STALENESS_DAYS dias.
    Retorna: {enriched, skipped, failed, total_fetched, duration_s}
    """
    start = time.monotonic()

    try:
        stale = await _fetch_stale_fornecedores()
    except Exception as e:
        logger.error("[Enricher] Falha ao buscar CNPJs para enriquecer: %s", e, exc_info=True)
        return {"status": "failed", "error": str(e), "duration_s": round(time.monotonic() - start, 1)}

    if not stale:
        logger.info("[Enricher] Nenhum CNPJ desatualizado encontrado — job encerrado.")
        return {"status": "completed", "enriched": 0, "skipped": 0, "failed": 0,
                "total_fetched": 0, "duration_s": round(time.monotonic() - start, 1)}

    logger.info("[Enricher] %d CNPJs para enriquecer", len(stale))

    sem = asyncio.Semaphore(_CONCURRENCY)
    tasks = [_enrich_one_fornecedor(cnpj, sem) for cnpj in stale]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    records: list[dict] = []
    enriched = 0
    failed = 0
    skipped = 0

    for cnpj, res in zip(stale, results):
        if isinstance(res, Exception):
            logger.warning("[Enricher] CNPJ %s falhou: %s", cnpj, res)
            failed += 1
        elif res is None:
            skipped += 1
        else:
            records.append(res)
            enriched += 1

    if records:
        try:
            await _upsert_batch(records)
        except Exception as e:
            logger.error("[Enricher] Falha no upsert batch: %s", e, exc_info=True)
            # Nao propaga — resultado parcial e melhor que zero

    duration_s = round(time.monotonic() - start, 1)
    logger.info(
        "[Enricher] Concluido em %.1fs — enriquecidos=%d, ignorados=%d, falhas=%d",
        duration_s, enriched, skipped, failed,
    )
    return {
        "status": "completed",
        "enriched": enriched,
        "skipped": skipped,
        "failed": failed,
        "total_fetched": len(stale),
        "duration_s": duration_s,
    }


async def _fetch_stale_fornecedores() -> list[str]:
    """Retorna CNPJs unicos de pncp_supplier_contracts que precisam de enriquecimento.

    Criterio de staleness: sem registro em enriched_entities OU enriched_at
    mais antigo que _ENRICH_STALENESS_DAYS dias.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=_ENRICH_STALENESS_DAYS)
    cutoff_iso = cutoff.isoformat()

    from supabase_client import get_supabase
    sb = get_supabase()

    # Passo 1: CNPJs distintos no datalake de contratos (is_active=true)
    cnpj_set: set[str] = set()
    offset = 0
    while len(cnpj_set) < _MAX_CNPJS_PER_RUN:
        resp = (
            sb.table("pncp_supplier_contracts")
            .select("ni_fornecedor")
            .eq("is_active", True)
            .not_.is_("ni_fornecedor", "null")
            .neq("ni_fornecedor", "")
            .range(offset, offset + _BATCH_SIZE - 1)
            .execute()
        )
        rows = resp.data or []
        if not rows:
            break
        for row in rows:
            ni = (row.get("ni_fornecedor") or "").strip()
            if ni and len(ni) == 14 and ni.isdigit():
                cnpj_set.add(ni)
        if len(rows) < _BATCH_SIZE:
            break
        offset += _BATCH_SIZE

    if not cnpj_set:
        return []

    # Passo 2: quais ja foram enriquecidos recentemente?
    fresh_cnpjs: set[str] = set()
    cnpj_list = list(cnpj_set)
    for i in range(0, len(cnpj_list), _BATCH_SIZE):
        chunk = cnpj_list[i:i + _BATCH_SIZE]
        resp = (
            sb.table("enriched_entities")
            .select("entity_id, enriched_at")
            .eq("entity_type", "fornecedor")
            .in_("entity_id", chunk)
            .gte("enriched_at", cutoff_iso)
            .execute()
        )
        for row in (resp.data or []):
            fresh_cnpjs.add(row["entity_id"])

    stale = [cnpj for cnpj in cnpj_list if cnpj not in fresh_cnpjs]
    return stale[:_MAX_CNPJS_PER_RUN]


async def _enrich_one_fornecedor(cnpj: str, sem: asyncio.Semaphore) -> dict | None:
    """Busca dados cadastrais de um CNPJ na BrasilAPI.

    Retorna dict pronto para upsert em enriched_entities, ou None se nao encontrado.
    Levanta excecao em caso de erro de rede (sera capturada pelo gather).
    """
    async with sem:
        url = f"{_BRASILAPI_BASE}/cnpj/v1/{cnpj}"
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.get(url, follow_redirects=True)

        if resp.status_code == 404:
            return None  # CNPJ nao encontrado — ignorar silenciosamente

        if resp.status_code != 200:
            raise RuntimeError(f"BrasilAPI retornou HTTP {resp.status_code} para CNPJ {cnpj}")

        raw = resp.json()

    # Normaliza campos relevantes para as paginas de fornecedores
    data = {
        "razao_social": raw.get("razao_social") or raw.get("nome") or "",
        "nome_fantasia": raw.get("nome_fantasia") or "",
        "cnae_fiscal": raw.get("cnae_fiscal") or "",
        "cnae_fiscal_descricao": raw.get("cnae_fiscal_descricao") or "",
        "natureza_juridica": raw.get("natureza_juridica") or "",
        "porte": raw.get("porte") or "",
        "simples_nacional": bool(raw.get("opcao_pelo_simples")),
        "mei": bool(raw.get("opcao_pelo_mei")),
        "situacao_cadastral": raw.get("descricao_situacao_cadastral") or "",
        "data_situacao_cadastral": raw.get("data_situacao_cadastral") or "",
        "data_abertura": raw.get("data_inicio_atividade") or "",
        "municipio": raw.get("municipio") or "",
        "uf": raw.get("uf") or "",
        "cep": raw.get("cep") or "",
        "logradouro": raw.get("logradouro") or "",
        "numero": raw.get("numero") or "",
        "bairro": raw.get("bairro") or "",
        "email": raw.get("email") or "",
        "telefone": raw.get("telefone") or "",
        "capital_social": _safe_capital(raw.get("capital_social")),
        "qsa_count": len(raw.get("qsa") or []),
        "source": "brasilapi",
        "source_updated_at": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "entity_type": "fornecedor",
        "entity_id": cnpj,
        "data": data,
        "enriched_at": datetime.now(timezone.utc).isoformat(),
    }


async def _upsert_batch(records: list[dict]) -> None:
    """Upsert de registros em enriched_entities via Supabase.

    Usa upsert com on_conflict=(entity_type, entity_id) para idempotencia.
    """
    from supabase_client import get_supabase
    sb = get_supabase()

    # Chunk para evitar payloads muito grandes (Supabase limite ~1MB por request)
    chunk_size = 200
    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        sb.table("enriched_entities").upsert(
            chunk,
            on_conflict="entity_type,entity_id",
        ).execute()
        logger.debug("[Enricher] Upsert de %d registros concluido", len(chunk))


def _safe_capital(val: Any) -> float:
    """Converte capital_social da BrasilAPI (pode ser string com virgula) para float."""
    if val is None:
        return 0.0
    try:
        # BrasilAPI retorna strings como "1232000,00"
        return float(str(val).replace(",", ".").replace(" ", ""))
    except (ValueError, TypeError):
        return 0.0
