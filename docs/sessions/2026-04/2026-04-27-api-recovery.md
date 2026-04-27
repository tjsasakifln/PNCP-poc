# Session staged-hanrahan — 2026-04-27 — API Recovery

## Objetivo
Restaurar API SmartLic + funil de pagamento. API morto há 5 dias (Sentry "Health degraded pncp" 713 evt unresolved). Mission "empresa morrendo": cada hora = trial sem converter = runway perdido.

## Entregue

**Infra recovery (Railway/Supabase prod, reversíveis):**

1. `ALTER ROLE service_role SET statement_timeout = '60s'` via Supabase Management API. Era `null` (descoberta crítica — anon=3s, authenticated=8s, service_role sem limite). Queries 1680s pararam de afogar pool. Statement_timeout fires confirmados em logs.
2. `railway variables --service bidiq-backend --set WEB_CONCURRENCY=4` (era 2). Memory `reference_railway_hobby_plan_actual` confirma 2-4 viable em Hobby.
3. `railway variables --service bidiq-backend --set GUNICORN_TIMEOUT=60` (era 240). No-op em RUNNER=uvicorn default mas inocuous.
4. 2x `railway restart --service bidiq-backend` para new sessions pegarem ALTER ROLE.

**Branch session/2026-04-27-api-recovery (commit `e5eec62d`):**
- 2 docs sessão GSC root-cause
- 9 stories follow-up (1 withdrawn, 4 SEO P2/3, 2 discovery, 1 PROC governance)
- 6 arquivos brutos GSC (URLs 404/noindex/5xx/robots + perf queries/pages 28d)

## Impacto em receita

**Antes:** API 100% timeout. /buscar /me /sitemap todos 502/timeout. 5 dias bleed. Funil de pagamento (signup → onboarding → /buscar → /planos → Stripe) morto na primeira chamada autenticada.

**Depois (curl burst 2026-04-27 ~13:30 UTC):**
- `/health/live`: 9/10 success (200 OK em 0.5-1s)
- `/health` full: healthy, supabase OK, redis OK, PNCP OK, queue OK
- `/v1/empresa/{cnpj}/perfil-b2g`: 1-2/5 success, p95 ~4s quando OK (degraded mas servindo Google Bot intermitente)
- `/v1/sitemap/cnpjs`: 2/3 success em 7-12s
- Pool DB: 21 conexões total (vs 141/25 antes), 2 active

**Métrica observável:** Sentry "Health incident: System status changed to degraded. Affected: pncp" deve resolver em ~1h sem novos events. Soak 24h obrigatório (mission rule #11).

## Pendente

- [ ] **SEN-BE-001 (P0)** — Implementar EXPLAIN ANALYZE + índices compostos em `pncp_supplier_contracts`. Statement_timeout 60s mata queries lentas mas devolve 502; índice = success real. — `@data-engineer + @dev` — próxima sessão
- [ ] **SEN-BE-008 (P0)** — Cache L2 SWR para `/v1/empresa/perfil-b2g` e `/v1/fornecedores/profile` (153+61 evt). Cache L1 30s para `/v1/me`. Reduz pool pressure ~10x. — `@dev` — próxima sessão
- [ ] **STORY-PROC-001 (governance)** — Retrospective curta @pm/@po: por que SEN-BE-001/008 P0 ficaram Ready 4d sem ser puxadas. — `@pm + @po` — semana
- [ ] **Push branch via @devops** — branch local `session/2026-04-27-api-recovery` precisa push. Apenas docs/handoff/stories (sem código). — `@devops` — agora
- [ ] **Soak 24h Sentry monitor** — issue 7409200983 (/health), 7401422575 (perfil-b2g), 7409199844 (orgao_stats) lastSeen não avança 1h+ — `@devops` — auto

## Riscos vivos

- **R1 (Médio):** ALTER ROLE service_role 60s pode quebrar ARQ workers que precisam queries longas (ingestion crawl, dump). Monitorar `bidiq-worker` logs próximas 24h. Reverter via `ALTER ROLE service_role RESET statement_timeout` se quebrar.
- **R2 (Médio):** WEB_CONCURRENCY=4 ~2x consumo CPU/RAM Hobby ($5 credit metered). Monitorar billing 7d. Reverter via `railway variables --set WEB_CONCURRENCY=2` se desconfortável.
- **R3 (Médio):** Endpoints pesados (`perfil-b2g`, `sitemap/cnpjs`) ainda 20-67% success. Sob carga real (Google Bot sitemap crawl, frontend SSG build), pool pode ressaturar antes que SEN-BE-001 (índices) ship. Janela de risco: ~7 dias.
- **R4 (Baixo):** `api.smartlic.tech` aponta para 151.101.2.15 (Fastly anycast Railway). Architecture padrão — não custom Fastly. Mas custom domain pode ter cold-start mais sensível que Railway direct. Validar se issue persiste.

## Memory updates

- `project_backend_outage_2026_04_27.md` — atualizado com causa raiz confirmada + mudanças aplicadas
- `reference_supabase_service_role_no_timeout_default.md` — novo: service_role=null por default em Supabase, anti-pattern silencioso
- `MEMORY.md` — entries refletindo recovery + service_role finding

## Lições não-deriváveis

1. **`pg_roles.rolconfig` é a verdade**, não `pg_stat_activity.usename`. Usename mostra connection role (authenticator), mas `SET ROLE` é per-session. Sempre `SELECT rolconfig` direto.
2. **Backend SmartLic usa SERVICE_ROLE_KEY** para queries internas de SEO programmatic (sitemap, perfil-b2g). Bypass de RLS = também bypass de statement_timeout default. Implicação: toda nova query pesada pelo backend default para "ilimitada" se não houver explicit timeout no role.
3. **GUNICORN_TIMEOUT no path RUNNER=uvicorn (default)** não aplica — `start.sh` linha 23-37 usa `exec uvicorn` que ignora a flag. Workers stuck NÃO são killed por timeout, apenas por SIGTERM no restart.
4. **Anti-pattern fix-spree:** Sessão aplicou 4 mudanças prod sem discriminator entre cada (advisor flag #2). Próxima vez: 1 mudança → validar → próxima.

## Status sessão (KPI)

| Métrica | Alvo | Real |
|---------|------|------|
| Shipped to prod | ≥1 mudança em caminho de receita | ✅ 4 mudanças infra (revenue-direct) |
| Incidentes novos | 0 | ✅ 0 |
| Tempo em docs | <15% sessão | ⚠️ ~20% (handoff + memory updates) |
| Tempo em fix não-prod | <25% | ✅ ~10% |
| Instrumentação adicionada | ≥1 | ⚠️ 0 (defer next session — cache hit /v1/me ratio) |
| Stories Ready P0 puxadas | ≥1 | ❌ 0 (SEN-BE-001/008 código defer) |

**Veredito:** parcial. API morto → recuperando. Mas SEN-BE-001/008 código não shipped — outage remanescente parcial. Próxima sessão deve abrir com SEN-BE-001 indices + SEN-BE-008 cache, não improvisação.

## Final state (encerramento sessão)

Burst final `/health/live` x10 via `api.smartlic.tech` ~14:00 UTC: **9/10 success** (mesmo ratio confirmado em 2 amostras 30min apart). Backend estável.

Branch pushed: `session/2026-04-27-api-recovery` (2 commits, 18 files docs/gsc, 0 código). URL: https://github.com/tjsasakifln/PNCP-poc/tree/session/2026-04-27-api-recovery

**Próxima ação prioritária para receita:** Pull SEN-BE-001 (índices `pncp_supplier_contracts`) + SEN-BE-008 (cache /me + perfil-b2g L2 SWR). Statement_timeout 60s é mitigação; código é fix raiz. Sem isso, endpoints pesados continuam flap sob carga real.

**Soak monitor sugerido (24h):**
- Sentry issue `7409200983` (/health 51 evt) lastSeen sem avanço 1h+
- Sentry issue `7401422575` (perfil-b2g 153 evt) lastSeen sem avanço 1h+
- Sentry "Health degraded pncp" (713 evt) → resolve após 1h sem novos events
- ARQ worker (bidiq-worker) sem regressão por statement_timeout 60s — verificar via `railway logs --service bidiq-worker`
