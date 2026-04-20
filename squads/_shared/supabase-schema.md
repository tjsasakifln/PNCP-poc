# Schema Supabase — Tabelas e RPCs Relevantes

Fonte de verdade: migrations em `supabase/migrations/*.sql`. Este arquivo é um **snapshot narrativo** para agentes de squad entenderem o domínio sem precisar ler cada migration.

> **Quando desatualizar:** se uma story criar/modificar tabela, atualize esta seção no mesmo PR.

## Tabelas principais

### Ingestão (Layer 1)

| Tabela | Propósito | Características |
|---|---|---|
| `pncp_raw_bids` | Editais abertos ingeridos do PNCP | ~50K linhas, `content_hash` dedup, GIN full-text Portuguese, **retenção 12 dias** (purge diário 4am BRT via `purge-old-bids` pg_cron) |
| `supplier_contracts` | Contratos históricos (feed SEO) | ~2M+ linhas, sem TTL, 3x/sem full crawl + incremental |
| `ingestion_checkpoints` | Progresso resumable da crawl | `{uf, modalidade, last_page, last_fetched_at}` |
| `ingestion_runs` | Audit log de runs de crawl | Status, duration, error |

### Produto

| Tabela | Propósito |
|---|---|
| `profiles` | Usuário + `plan_type` + `is_admin`/`is_master` + Google Sheets connection |
| `search_sessions` | Sessões de busca salvas |
| `search_results_cache` | L2 cache (24h TTL), passivo SWR |
| `pipeline_items` | Kanban — edital + stage + drag order |
| `conversations`, `messages` | Sistema de mensagens interno |
| `feedbacks` | Feedback de usuário por edital (👍/👎) |
| `first_analyses` | Onboarding — primeira análise do trial |
| `ingestion_checkpoints` | Mesmo da seção acima (duplicado por contexto) |

### Billing

| Tabela | Propósito |
|---|---|
| `plan_billing_periods` | Source of truth de preços (sync Stripe) |
| `subscriptions` | Assinatura ativa do usuário |

### Operacional

| Tabela | Propósito |
|---|---|
| `cron_job_health` (view) | Saúde do pg_cron (7d window) |
| `audit_logs` | Log de ações admin |

## RPCs críticas

| RPC | Propósito |
|---|---|
| `search_datalake(query, filters, ...)` | **Full-text search** em `pncp_raw_bids` — tsquery Portuguese, filtros UF/date/modality/value/esfera. p95 <100ms. Backend chama via `datalake_query.py`. |
| `upsert_pncp_raw_bids(rows jsonb)` | Batch upsert 500 linhas/batch, dedup por `content_hash` |
| `sitemap_orgaos()` | Gera sitemap de órgãos para SEO inbound |
| `check_and_increment_quota_atomic(user_id, plan, count)` | Quota check atômico — **tests mockando `/buscar` DEVEM mockar esta também** |
| `get_cron_health()` | SECURITY DEFINER — retorna snapshot da view `cron_job_health`. Backend-only. |

## RLS (Row Level Security)

**TODAS** as tabelas têm RLS habilitado. Políticas padrão:

- `profiles`: user vê apenas sua linha (`auth.uid() = id`)
- `search_sessions`, `pipeline_items`, `feedbacks`: user vê apenas próprias linhas
- `pncp_raw_bids`, `supplier_contracts`: SELECT público (read-only); INSERT/UPDATE apenas service_role
- Admin endpoints (`/v1/admin/*`) checam `profiles.is_admin OR is_master` no backend

## Índices relevantes

- `pncp_raw_bids`: GIN em `tsvector_portuguese(objeto_licitacao)` — tsquery PT full-text
- `pncp_raw_bids`: B-tree em `(uf, data_publicacao, is_active)` — filter fast-path
- `supplier_contracts`: B-tree em `(cnpj_fornecedor, data_assinatura)` — perfil CNPJ
- `search_results_cache`: B-tree em `(cache_key, expires_at)` — L2 lookup

## Conexão

- Direto via `supabase_client.get_supabase()` em backend
- Frontend: `@supabase/ssr` (auth) e proxy routes em `app/api/`
- Migration policy: **`supabase/migrations/` é source of truth** (não `backend/migrations/` que é legacy Alembic)

## Patch targets (tests)

- Auth: `app.dependency_overrides[require_auth]` (não `patch("routes.X.require_auth")`)
- Cache: patch `supabase_client.get_supabase` (não `search_cache.get_supabase`)
- Quota: mock `check_and_increment_quota_atomic` sempre que mockar `/buscar`
