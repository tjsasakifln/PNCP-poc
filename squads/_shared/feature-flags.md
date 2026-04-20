# Feature Flags — SmartLic

Fonte de verdade: `backend/config.py` (Python) + env vars em Railway. `.env.example` documenta nomes.

## DataLake (Layer 1 — ingestão ETL)

| Flag | Default | Propósito |
|---|---|---|
| `DATALAKE_ENABLED` | `true` | Habilita pipeline de ingestão periódica → `pncp_raw_bids` + `supplier_contracts` |
| `DATALAKE_QUERY_ENABLED` | `true` | `/buscar` consulta local DB via `search_datalake` RPC. Fallback para live API se retornar 0 |

## LLM (GPT-4.1-nano)

| Flag | Default | Propósito |
|---|---|---|
| `LLM_ZERO_MATCH_ENABLED` | `true` | Classificação zero-match (YES/NO) para editais com 0% keyword density |
| `LLM_ARBITER_ENABLED` | `true` | Gray-zone classifier (1-5% density) |
| `LLM_FALLBACK_PENDING_ENABLED` | `true` | Em falha do LLM, marca `PENDING_REVIEW` (em vez de REJECT hard) |

## Viabilidade + Matching

| Flag | Default | Propósito |
|---|---|---|
| `VIABILITY_ASSESSMENT_ENABLED` | `true` | Calcular score 4-fator (modalidade/timeline/valor/geografia) em cada resultado |
| `SYNONYM_MATCHING_ENABLED` | `true` | Expansão de sinônimos em keyword matching |

## Ingestão — tuning

| Flag | Default | Propósito |
|---|---|---|
| `PNCP_BATCH_SIZE` | `5` | UFs paralelas por batch |
| `PNCP_BATCH_DELAY_S` | `2.0` | Delay entre batches |
| `PNCP_CANARY_INTERVAL_S` | `600` | Canário PNCP: cada 10min (0 desabilita) |
| `PNCP_CANARY_FAIL_THRESHOLD` | `3` | N falhas consecutivas antes de alertar |

## Timeout Waterfall

Override em emergência via Railway vars — ver `api-contracts.md` §"Timeout Waterfall":

| Flag | Default |
|---|---|
| `PIPELINE_TIMEOUT` | 100 |
| `CONSOLIDATION_TIMEOUT` | 90 |
| `PNCP_TIMEOUT_PER_SOURCE` | 70 |
| `PNCP_TIMEOUT_PER_UF` | 25 |
| `GUNICORN_TIMEOUT` | 180 |

## Billing

| Flag | Default | Propósito |
|---|---|---|
| `SUBSCRIPTION_GRACE_DAYS` | `3` | Grace period em gaps de assinatura |

## Observabilidade

| Flag | Default | Propósito |
|---|---|---|
| `DEBUG_SQUADS` | unset | Se `=1`, squads-briefing.cjs log errors em `.synapse/logs/` |
| `SENTRY_DSN` | — | Error tracking (prod) |

## Patterns

- **Patch em tests:** `@patch("config.FLAG_NAME", False)` (não `os.environ`)
- **Verificação:** `if getattr(config, "FLAG_NAME", default): ...`
- **Nunca** adicionar flag sem documentar aqui + em `.env.example` + em `config.py`
- Flags **obsoletas**: remover do código ao invés de deixar comentado (evita bit rot)

## Removidos recentemente (para contexto — não referenciar)

- `CACHE_WARMING_ENABLED` — deprecated 2026-04-18 (STORY-CIG-BE-cache-warming-deprecate). DataLake <100ms tornou warming pure waste. Cache populate-on-demand via SWR passivo apenas.
