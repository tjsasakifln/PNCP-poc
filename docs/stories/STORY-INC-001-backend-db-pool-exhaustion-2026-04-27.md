# STORY-INC-001: [P0] Backend DB pool exhaustion + queries hung sem statement_timeout

## Status

**Withdrawn (NO-GO @po 2026-04-27)** — duplicado por stories existentes; ver §"Verdict @po" abaixo

## Prioridade

🔴 **P0 — Outage operacional ativo** (incident response, não backlog grooming)

## Origem

- Inspeção GSC root-cause 2026-04-27 (`docs/sessions/2026-04/2026-04-27-gsc-rootcause-brief-for-sm.md`)
- Sentry: issue "Health incident: System status changed to degraded. Affected: pncp" — 713 eventos desde 22-abr 22:34 (5 dias sem resolução)
- Memory: `project_backend_outage_2026_04_27`, `feedback_build_hammers_backend_cascade`, `reference_railway_hobby_plan_actual`

## Tipo

Incident / Performance / Infrastructure

## Owner

@data-engineer (queries/indexes) + @devops (pool/workers/timeout config) + @dev (timeouts client se necessário)

## Story

**As a** time SmartLic operando produção com 5 dias de degradação contínua,
**I want** statement_timeout agressivo + queries sitemap/perfil otimizadas + pool DB recuperável,
**so that** `/buscar` (user-facing), `/health`, `/v1/sitemap/*` e `/v1/empresa/*` voltem a responder consistentemente em <5s e o alerta Sentry "Health degraded pncp" feche.

## Problema

Empiricamente medido em 2026-04-27 11:47–12:16 UTC (2 bursts curl 30s apart, 10/10 timeouts):

| Endpoint | Round 1 | Round 2 |
|----------|---------|---------|
| `GET /` | timeout 8s | timeout 8s |
| `GET /health` | timeout 8s | timeout 8s |
| `GET /buscar?q=teste&uf=SP` | timeout 8s | timeout 8s |
| `GET /v1/sitemap/cnpjs` | timeout 8s | timeout 8s |
| `GET /v1/empresa/{cnpj}/perfil-b2g` | timeout 8s | timeout 8s |

**Sentry top issues 24h (org=confenge, proj=smartlic-backend):**

| Count | Title |
|-------|-------|
| **713** | `Health incident: System status changed to degraded. Affected: pncp` (desde 22-abr) |
| 263 | `slow_request: GET /v1/orgao/{cnpj}/stats (692.6s)` — query DB 11 min |
| 153 | `slow_request: GET /v1/empresa/{cnpj}/perfil-b2g (160.9s)` |
| 120 | `[Itens] price_data query falhou: 'canceling statement due to ...'` |
| 51 | `slow_request: GET /health (160.9s)` |
| **48** | `orgao_stats DB query failed: ConnectionTerminated error_code:1` |
| 47 | `slow_request: GET /v1/sitemap/contratos-orgao-indexable (318.3s)` |
| 40 | `slow_request: GET /v1/sitemap/orgaos (1682.7s)` — **28 minutos** |
| 39 | `slow_request: GET /v1/sitemap/{itens,fornecedores-cnpj,cnpjs} (~1680s)` |
| 36 | `slow_request: GET /v1/me (160.9s)` |

**Root cause provável:** DB connection pool exhaustion + queries DB sem `statement_timeout` agressivo. Sitemap endpoints rodam até 28 minutos, ocupando connections; `/buscar` e `/me` cascateiam ao mesmo pool e travam.

**Combinatório:**
- 1 worker Railway Hobby (memory `reference_railway_hobby_plan_actual` — pode subir 2-4)
- 2M+ rows em `pncp_supplier_contracts`
- Build SSG hammers (memory `feedback_build_hammers_backend_cascade`)

## Critérios de Aceite

- [ ] **AC1:** `statement_timeout` agressivo (≤30s) configurado em PostgREST/Supabase para conexões servindo API; documentar valor escolhido + rationale em `docs/adr/`
- [ ] **AC2:** Endpoints `/v1/sitemap/{cnpjs,orgaos,fornecedores-cnpj,itens,municipios,contratos-orgao-indexable}` retornam 200 em <30s — adicionar paginação/cache se query subjacente excede
- [ ] **AC3:** Endpoint `/v1/orgao/{cnpj}/stats` retorna 200 em <5s para CNPJs com dados — análise EXPLAIN + criar índice se faltante
- [ ] **AC4:** Endpoint `/v1/empresa/{cnpj}/perfil-b2g` retorna 200 em <5s — mesma análise
- [ ] **AC5:** Endpoint `/buscar` retorna 200 em <5s para queries básicas
- [ ] **AC6:** `/health` retorna 200 em <1s (sem dependência DB pesada)
- [ ] **AC7:** `ConnectionTerminated` em pool DB cai para 0 evt/24h (Sentry)
- [ ] **AC8:** Alerta Sentry "Health incident: System status changed to degraded. Affected: pncp" resolved
- [ ] **AC9:** Taxa `slow_request` < 5 evt/dia em janela de 48h pós-deploy
- [ ] **AC10:** Validação manual: 10/10 burst curls (mesmo protocolo do brief §P0) retornam 200 em <8s, 30s apart

### Anti-requisitos

- NÃO subir Railway Hobby → Pro sem antes esgotar fix de query/pool (memory `project_railway_runners_cost_2026_04` — bump prematuro de plano é eng theater se a raiz é query lenta)
- NÃO mascarar com cache stale infinito sem TTL — sitemaps precisam refresh diário
- NÃO desabilitar Sentry alerts para silenciar — o objetivo é fix, não silence

## Tasks / Subtasks

- [ ] Task 1 — Diagnóstico DB (AC: 3, 4)
  - [ ] @data-engineer roda `pg_stat_activity` durante reprodução para listar queries longas
  - [ ] EXPLAIN ANALYZE nas queries de `/v1/orgao/{cnpj}/stats`, `/v1/empresa/{cnpj}/perfil-b2g`, `/v1/sitemap/*`
  - [ ] Identificar índices faltantes em `pncp_supplier_contracts` e tabelas relacionadas
- [ ] Task 2 — statement_timeout (AC: 1)
  - [ ] @devops configura `statement_timeout=30s` no PostgREST/Supabase para role autenticador da API
  - [ ] ADR `docs/adr/NNN-postgrest-statement-timeout.md`
- [ ] Task 3 — Otimizar queries lentas (AC: 2, 3, 4)
  - [ ] @data-engineer cria/ajusta índices identificados na Task 1
  - [ ] @data-engineer pagina queries de sitemap se ainda excedem 30s pós-índice
  - [ ] Cache layer para sitemap endpoints (TTL 6h — alinhar com SEN-BE-005)
- [ ] Task 4 — Pool DB recovery (AC: 7)
  - [ ] @devops valida configuração PgBouncer/Supavisor (max_client_conn, default_pool_size)
  - [ ] @dev adiciona retry com backoff para `ConnectionTerminated` em camada DB do backend
- [ ] Task 5 — /health desacoplado (AC: 6)
  - [ ] @dev garante `/health` não toca DB pesado — apenas ping leve ou status cached
- [ ] Task 6 — Worker bump opcional (AC: 5)
  - [ ] Avaliar `WEB_CONCURRENCY=2` no Railway se Tasks 1-5 não restauram /buscar (memory `reference_railway_hobby_plan_actual`)
- [ ] Task 7 — Validação (AC: 8, 9, 10)
  - [ ] Executar burst curl 10/10 amostras 30s apart
  - [ ] Resolver issue Sentry "Health degraded pncp" manualmente após 1h sem novos eventos
  - [ ] Smoke teste em `/buscar`, `/v1/empresa`, `/v1/sitemap/*` por 48h
- [ ] Task 8 — Postmortem (pós-fix)
  - [ ] @architect documenta postmortem em `docs/incidents/2026-04-27-backend-db-pool-exhaustion.md`
  - [ ] Por que SEN-BE-005 ficou Ready 14+ dias sem ser puxada (lição organizacional)

## Referência de implementação

- `backend/routes/sitemap_orgaos.py::sitemap_contratos_orgao_indexable` (raiz SEN-BE-005)
- `backend/routes/sitemap_*.py` — todos endpoints sitemap
- `backend/routes/empresa.py::perfil_b2g` (verificar caminho real)
- `backend/routes/orgaos.py::stats`
- Migrations relevantes: `supabase/migrations/*pncp_supplier_contracts*`
- Brief raiz: `docs/sessions/2026-04/2026-04-27-gsc-rootcause-brief-for-sm.md`

## Riscos

- **R1 (Alto):** statement_timeout=30s pode quebrar endpoints internos legítimos (ARQ jobs, exports). Mitigar: aplicar apenas no role da API exposta, manter role admin/job sem limite
- **R2 (Médio):** Paginação de sitemap pode demandar mudança no frontend (`app/sitemap.ts`) — coordenar com STORY-SEO-001 (sitemap-4 vazio InProgress)
- **R3 (Baixo):** Bump de worker custa marginalmente mais ($-credit metered)

## Dependências

- **Subsume / coordena com SEN-BE-005** (Status: Ready há 14+ dias) — possivelmente fechar SEN-BE-005 como duplicado dessa story
- **Coordena com SEN-BE-007** (slow sitemap endpoints) — verificar overlap
- **Bloqueia:** STORY-SEO-025, STORY-SEO-026, STORY-SEO-027, STORY-SEO-028, STORY-SEO-029 (medições SEO requerem backend funcional)
- **Não bloqueia:** STORY-DISC-001 (spike slug bug pode rodar em paralelo lendo Sentry quando endpoint subir)

## Verdict @po (2026-04-27)

**NO-GO — Withdrawn (IDS Article IV-A: REUSE > CREATE violado).**

100% do conteúdo desta story está coberto por stories existentes Status:Ready:

| INC-001 endpoint/issue | Story Ready prévia que cobre |
|------------------------|------------------------------|
| `/v1/sitemap/{cnpjs,orgaos,itens,fornecedores-cnpj,municipios}` 1680s | `SEN-BE-007` AC1-AC8 (P1) — TODAS listadas com IDs Sentry exatos |
| `/v1/sitemap/contratos-orgao-indexable` 318s + 502 | `SEN-BE-005` (P1) + `SEN-BE-007` |
| `/health` 160.9s | `SEN-BE-008` AC1 (**P0**) |
| `/v1/me` 160.9s | `SEN-BE-008` AC3 (P0) |
| `/v1/empresa/{cnpj}/perfil-b2g` 160.9s | `SEN-BE-008` AC6 (P0) |
| `/v1/orgao/{cnpj}/stats` 692.6s | `SEN-BE-008` AC5 (P0) + `SEN-BE-001` |
| `/v1/fornecedores/{cnpj}/profile` 148.2s | `SEN-BE-008` AC6 (P0) |
| `[Itens] price_data canceling statement` (SQLSTATE 57014) | `SEN-BE-001` AC1-AC6 (**P0**) |
| `orgao_stats ConnectionTerminated` | `SEN-BE-001` AC2 + `SEN-BE-008` AC5 |
| statement_timeout config | `SEN-BE-001` AC6 |
| Cache layer sitemap TTL 6h | `SEN-BE-005` AC4 + `SEN-BE-007` AC2 |

**Real gap não é story** — gap é organizacional. **SEN-BE-001 e SEN-BE-008 são P0 Status:Ready há 14+ dias sem ser puxadas.** Brief raiz (`docs/sessions/2026-04/2026-04-27-gsc-rootcause-brief-for-sm.md` §10.2) perguntava exatamente isso — pergunta válida mas não respondida.

**Ações recomendadas para PO/PM:**

1. **Não criar nova story** — pull existentes
2. **Rever priorização** — SEN-BE-001 e SEN-BE-008 são P0 mas não foram puxadas; descobrir por quê (capacidade? blocker técnico oculto? sinal organizacional?)
3. **Considerar** criar `STORY-PROC-001-incident-response-protocol-stale-p0.md` para tratar o meta-problema (P0 não-atendido = falha de processo, não de spec)
4. **Brief root-cause** atualizado §"P0 INCIDENTE VIVO" continua relevante como **evidence** de urgência para puxar SEN-BE-001/008 — anexar à conversa de priorização

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-27 | @sm (River) | Story criada a partir do brief GSC root-cause; P0 confirmado por 2 bursts curl + Sentry 800 evt/24h |
| 2026-04-27 | @po (Sarah) | **Validação 6-section: NO-GO** — duplicado integralmente por SEN-BE-001 + SEN-BE-005 + SEN-BE-007 + SEN-BE-008. Status: Draft → Withdrawn. Decisão IDS Article IV-A: REUSE > CREATE. Anexar evidência ao push para puxar SEN-BE-001/008 P0. |
