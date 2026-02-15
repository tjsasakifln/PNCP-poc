# Technical Debt Assessment - FINAL

**Projeto:** SmartLic / BidIQ
**Data:** 2026-02-15
**Versao:** 2.0
**Commit Base:** `b80e64a` (branch `main`)
**Autores:** @architect (Helix), @data-engineer (Datum), @ux-design-expert (Pixel), @qa (Quinn)
**Fontes:**
1. `docs/architecture/system-architecture.md` v2.0 -- @architect (Phase 1)
2. `supabase/docs/SCHEMA.md` + `supabase/docs/DB-AUDIT.md` -- @data-engineer (Phase 2)
3. `docs/frontend/frontend-spec.md` -- @ux-design-expert (Phase 3)
4. `docs/prd/technical-debt-DRAFT.md` v2.0 -- @architect (Phase 4 Consolidation)
5. `docs/reviews/db-specialist-review.md` v2.0 -- @data-engineer (Phase 5)
6. `docs/reviews/ux-specialist-review.md` v2.0 -- @ux-design-expert (Phase 6)
7. `docs/reviews/qa-review.md` v2.0 -- @qa (Phase 7)

**Substitui:** v1.0 (2026-02-11, commit `808cd05`, autores: @architect Aria, @data-engineer Dara, @ux-design-expert Uma, @qa)

---

## Resumo Executivo

O SmartLic/BidIQ e um SaaS em producao (POC v0.3) para descoberta automatizada de oportunidades de contratacao publica no PNCP. O sistema melhorou significativamente desde a auditoria v1.0 (Feb 11, commit `808cd05`), com decomposicao de monolitos backend e frontend, melhoria de RLS em tabelas legadas, infraestrutura de observabilidade (correlation ID, structured logging), e automacao de retencao via pg_cron. Porem, novas features (pipeline, cache, profile context) introduziram regressoes nos mesmos patterns que haviam sido corrigidos anteriormente.

**Numeros consolidados:**

| Metrica | Valor |
|---------|-------|
| Total de debitos | **87** (apos remocao de 2 falsos positivos e deduplicacao de 2 subsets) |
| Criticos (CRITICAL) | **3** |
| Altos (HIGH) | **14** |
| Medios (MEDIUM) | **36** |
| Baixos (LOW) | **34** |
| Esforco total estimado | **~360h** (~468-540h com buffer de 1.3-1.5x) |
| Items pendentes de verificacao em producao | **2** (DB-01, DB-02 -- queries V1-V5) |

**Avaliacao Geral de Saude:**

| Area | Nota v1.0 (Feb 11) | Nota v2.0 (Feb 15) | Tendencia |
|------|---------------------|---------------------|-----------|
| Backend/Arquitetura | MEDIO | MEDIO-ALTO | Melhoria (route decomposition, middleware, correlation ID) |
| Database | 6.5/10 | 7.5/10 | Melhoria (RLS fixes, pg_cron, indexes) com regressoes pontuais |
| Frontend/UX | MEDIO-ALTO | MEDIO-ALTO | Estavel (buscar decomposed, mas prop drilling + quarantine) |

**Distribuicao por severidade e area:**

| Severidade | Sistema | Database | Frontend/UX | Total |
|------------|---------|----------|-------------|-------|
| CRITICAL | 1 | 2 | 0 | **3** |
| HIGH | 5 | 2 | 7 | **14** |
| MEDIUM | 10 | 7 | 19 | **36** |
| LOW | 8 | 6 | 20 | **34** |
| **Total** | **24** | **17** | **46** | **87** |

**Mudancas vs DRAFT (v2.0):**
- 82 items originais -> 87 apos revisoes (+8 novos, -2 falsos positivos, -2 subsumidos em existentes, +1 expandido)
- Esforco: ~412h -> ~360h (-13%) por estimativas revisadas dos especialistas
- 4 mudancas de severidade em DB (DB-01 CRITICAL->MEDIUM, DB-06 MEDIUM->CRITICAL, DB-08 MEDIUM->LOW, DB-10 MEDIUM->LOW)
- 6 upgrades e 3 downgrades em Frontend/UX
- SYS-03 rebaixado de CRITICAL para LOW (parcialmente resolvido por STORY-251)
- SYS-10 corrigido: ruff ja esta no CI, apenas mypy faltando
- SYS-11 elevado de MEDIUM para HIGH (1318 linhas, bloqueia correcoes de pipeline)
- FE-08 movido para P0 (botao invisivel na pagina de erro)
- FE-04 contagem corrigida: 22 arquivos quarantined, nao 17

**Mudancas vs v1.0 Assessment (Feb 11):**
- Items resolvidos desde v1.0: SYS-C02 (main.py monolith), SYS-H03 (migrations), SYS-H04 (business logic extraction), SYS-M01 (correlation ID), SYS-M08 (API versioning), SYS-L04 (request logging), SYS-L06 (Redis health check), FE-C01 (buscar monolith), FE-H04 (native alert), FE-M08 (middleware auth), e 15+ DB items resolvidos por migrations 016-026
- Nova taxonomia: IDs renumerados (SYS-01 a SYS-24, DB-01 a DB-17, FE-01 a FE-19, A11Y-01 a A11Y-09, UX-01 a UX-05, IC-01 a IC-07, MF-01 a MF-04, UX-NEW-03 a UX-NEW-05)
- Areas Cross-Cutting e Testing da v1.0 foram absorvidas nas categorias Sistema/Database/Frontend

---

## 1. Inventario Completo de Debitos

### 1.1 Sistema (Backend/Infra) -- validado por @architect + @qa

**24 debitos | Esforco estimado: ~143h**

#### CRITICAL (1 item)

| ID | Debito | Localizacao | Impacto | Horas | Status |
|----|--------|-------------|---------|-------|--------|
| SYS-02 | **Dual HTTP client implementations (sync `requests` + async `httpx`)** -- logica de retry, rate limiting e error handling duplicada em ~1585 linhas. Sync client usado apenas em `PNCPLegacyAdapter.fetch()` como fallback single-UF. | `backend/pncp_client.py` linhas 223-1585 | Manutencao: toda mudanca de comportamento PNCP deve ser aplicada 2x. Reducao de ~785 linhas ao eliminar sync. | 16h | Ativo. Verificar se `PNCPLegacyAdapter.fetch()` e chamado em code path ativo antes de remover (CR-04). |

#### HIGH (5 items)

| ID | Debito | Localizacao | Impacto | Horas | Status |
|----|--------|-------------|---------|-------|--------|
| SYS-04 | **In-memory progress tracker nao escalavel horizontalmente** -- `_active_trackers` dict e registro primario. Redis pub/sub existe mas e secundario. | `backend/progress.py` | Duas instancias Railway dividiriam estado SSE. | 8h | Ativo |
| SYS-05 | **In-memory auth token cache nao compartilhado entre instancias** | `backend/auth.py` `_token_cache` dict | Fragmentacao de cache em multi-instance deploy. | 4h | Ativo |
| SYS-06 | **Legacy plan seeds vs current plan IDs** -- Migration 001 cria `free`, `pack_5`; codigo usa `free_trial`, `consultor_agil`. Traducao em `quota.py` linhas 525-531. | `supabase/migrations/001`, `backend/quota.py` | Mapeamento fragil, confuso para novos devs. | 8h | Ativo |
| SYS-08 | **Excel base64 fallback grava em tmpdir** -- nao limpo em crash, nao escalavel. | `frontend/app/api/buscar/route.ts` linhas 197-223 | Disco enche. Signed URL do Supabase Storage e o caminho correto. | 4h | Ativo |
| SYS-11 | **`search_pipeline.py` se tornou god module (1318 linhas)** -- 7 stages com helpers inline. Absorveu complexidade da decomposicao de main.py. Segundo maior arquivo do backend apos pncp_client.py (1584 linhas). | `backend/search_pipeline.py` | Dificulta teste de stages individuais. Qualquer correcao de pipeline requer navegar por 1318 linhas. | 16h | Ativo. Elevado de MEDIUM para HIGH por recomendacao da QA (CR-10, GAP-06). |

#### MEDIUM (10 items)

| ID | Debito | Localizacao | Impacto | Horas | Status |
|----|--------|-------------|---------|-------|--------|
| SYS-07 | **`save_search_session` usa `time.sleep(0.3)` sincrono em contexto async** -- bloqueia event loop no retry. | `backend/quota.py` linha 910 | Todas as requests concorrentes pausam 300ms durante retry. | 2h | Ativo. Atentar para CR-09 (race condition ao migrar para asyncio.sleep). |
| SYS-09 | **Backend routes montadas 2x** (root + `/v1/` prefix) -- dobra tabela de rotas. Sunset 2026-06-01. | `backend/main.py` linhas 242-278 | Confusao de debug, dobro de memoria de route dispatch. | 4h | Ativo. Deadline: 2026-06-01. |
| SYS-10 | **mypy nao configurado no CI** -- `ruff check .` ja esta em `backend-ci.yml` linhas 33-36. Apenas mypy falta. | `.github/workflows/backend-ci.yml` | Type checking nao enforced automaticamente. | 2h | Parcialmente resolvido (ruff ja ativo). Descricao corrigida por QA (R-06). |
| SYS-12 | **Feature flags apenas em env vars** -- 7+ flags requerem restart do container. POST reload e efemero. | `backend/config.py` | Sem toggle UI para operadores. Redeploy necessario. | 8h | Ativo |
| SYS-13 | **`dotenv` carregado antes de imports FastAPI** em nivel de modulo. | `backend/main.py` linha 33 | Env vars lidas em import time podem usar valores stale. | 2h | Ativo |
| SYS-14 | **User-Agent hardcoded "BidIQ/1.0"** -- produto renomeado para SmartLic. | `backend/pncp_client.py` linha 264 (+ AsyncPNCPClient) | Branding desatualizado no trafego de API. | 2h | Ativo |
| SYS-15 | **Sem connection pooling no Supabase client** -- instancia global unica. | `backend/supabase_client.py` | Depende de handling interno do supabase-py. Pode gargalar. | 8h | Ativo |
| SYS-16 | **Integration tests job e placeholder** -- echo skip message. | `.github/workflows/tests.yml` linhas 216-221 | Zero cobertura de integracao no CI. | 16h | Ativo |
| SYS-17 | **Sem request timeout para Stripe webhooks** -- handler sem timeout explicito. | `backend/webhooks/stripe.py` | DB ops longas podem bloquear worker, causando retries do Stripe. | 4h | Ativo |
| SYS-18 | **`datetime.now()` sem timezone** em excel.py e llm.py. | `backend/excel.py` linha 227, `backend/llm.py` linha 97 | Timestamps incorretos em ambientes nao-UTC. | 2h | Ativo |

#### LOW (8 items)

| ID | Debito | Localizacao | Impacto | Horas | Status |
|----|--------|-------------|---------|-------|--------|
| SYS-01 | **Frontend test coverage abaixo do threshold (49.46% vs 60%)** -- 22 arquivos de teste quarantined. CI falha em todo push. Quality gate bypassado. | `frontend/__tests__/` | Pipeline CI quebrado; sem safety net de regressao. | 40h | Ativo. Contagem corrigida para 22 (R-03). Nota: e um QUALITY issue, nao producao. Esforco significativo, severidade de impacto baixa. |
| SYS-03 | **LLM Arbiter fallback generico para setores sem ID** -- STORY-251 adicionou lookup dinamico via `get_sector(setor_id)` em `_build_conservative_prompt()`. Prompt conservador agora usa `config.description` e gera exemplos SIM/NAO por setor. Nota obsoleta permanece em `config.py` linhas 261-263. Prompt de fallback `_build_standard_sector_prompt()` (linhas 112-123) nao usa descricao do setor. | `backend/llm_arbiter.py`, `backend/config.py` | Fallback generico so afeta setores sem ID (edge case). Nota obsoleta confunde devs. | 1h | **Parcialmente resolvido por STORY-251.** Rebaixado de CRITICAL para LOW (R-02). Esforco: 8h -> 1h. Se verificacao confirmar resolucao completa, reduz para 0.5h (apenas remover nota). |
| SYS-19 | **Screenshot .png files em git status** (18 untracked). | Repository root | Working tree poluida. Deveria ser gitignored. | 1h | Ativo |
| SYS-20 | **`_request_count` nunca resetado** -- contador cresce por instancia de client. | `backend/pncp_client.py` linha 237 | Apenas diagnostico; poderia overflow. | 1h | Ativo |
| SYS-21 | **`asyncio.get_event_loop().time()` deprecated** em Python 3.10+. | `backend/pncp_client.py` linha 861 | Usar `get_running_loop()`. | 1h | Ativo |
| SYS-22 | **`format_resumo_html` funcao nao usada** -- frontend renderiza a partir de JSON. | `backend/llm.py` linhas 232-300 | ~70 linhas de dead code. | 1h | Ativo |
| SYS-23 | **Arquivo de migration deprecated no diretorio.** | `006b_DEPRECATED_...DUPLICATE.sql` | Confunde compreensao do schema. Cross-ref: DB-12. | 1h | Ativo |
| SYS-24 | **`email_service.py` usa `time.sleep()` sincrono** -- mesmo anti-pattern de SYS-07 em quota.py. Encontrado tambem em `receita_federal_client.py:66` e `pncp_client.py` (6 ocorrencias no sync client). | `backend/email_service.py` linha 112 | Bloqueia event loop durante retry de envio de email. | 1h | **Novo.** Adicionado por QA (R-07). Mesma classe de problema que SYS-07. |

**Subtotal Sistema: 24 debitos | ~143h**

---

### 1.2 Database -- validado por @data-engineer + @qa

**17 debitos | Esforco estimado: ~23h**

#### CRITICAL (2 items)

| ID | Debito | Localizacao | Impacto | Horas | Status |
|----|--------|-------------|---------|-------|--------|
| DB-02 | **`handle_new_user()` trigger omite `plan_type` explicito apos migration 024** -- Column default permanece `'free'` (migration 001), que VIOLA o CHECK constraint da migration 020 (aceita apenas `free_trial`, `consultor_agil`, `maquina`, `sala_guerra`, `master`). `ON CONFLICT (id) DO NOTHING` mascara para usuarios pre-existentes. | `supabase/migrations/024_add_profile_context.sql`, `001_profiles_and_sessions.sql` | P0: Signup de novos usuarios potencialmente quebrado. | 2h | **Pendente verificacao em producao** (queries V1-V5). Se default foi corrigido manualmente, risco e ZERO e esforco cai para 1h (documentacao). |
| DB-06 | **`_ensure_profile_exists()` usa `plan_type: "free"` violando CHECK constraint** -- One-line fix mas impacto CRITICO: qualquer usuario cujo profile esteja ausente nao consegue criar fallback, quebrando todo o fluxo de busca. Dois code paths independentes produzem `plan_type = 'free'` invalido (este + DB-02). | `backend/quota.py` linha 791 | Fallback profile creation falha. | 0.5h | Ativo. **Elevado de MEDIUM para CRITICAL pelo DB specialist.** |

#### HIGH (2 items)

| ID | Debito | Localizacao | Impacto | Horas | Status |
|----|--------|-------------|---------|-------|--------|
| DB-03 | **`pipeline_items` RLS policy `FOR ALL USING(true)` sem `TO service_role`** -- Qualquer usuario autenticado pode ler/modificar/deletar pipeline items de outros usuarios via PostgREST. Mesmo bug corrigido para tabelas legadas na migration 016. | `supabase/migrations/025_create_pipeline_items.sql` linhas 102-105 | Acesso cross-user: vetor de data breach. | 1h | Ativo |
| DB-04 | **`search_results_cache` RLS policy `FOR ALL USING(true)` sem `TO service_role`** -- Mesmo pattern de DB-03. Qualquer usuario autenticado pode acessar resultados de busca cached de outros usuarios, contendo dados sensiveis de licitacoes. | `supabase/migrations/026_search_results_cache.sql` linhas 31-35 | Acesso cross-user: dados de negocio expostos. | 1h | Ativo |

#### MEDIUM (7 items)

| ID | Debito | Localizacao | Impacto | Horas | Status |
|----|--------|-------------|---------|-------|--------|
| DB-01 | **Missing `status` column em `user_subscriptions`** -- Trigger `sync_profile_plan_type()` (migration 017) referencia `NEW.status`. Nenhuma das 26 migrations define esta coluna. Backend ja faz sync manualmente via 3 webhook handlers, tornando o trigger redundante mesmo se funcional. | `supabase/migrations/017_sync_plan_type_trigger.sql` | Trigger e dead code ou coluna foi adicionada manualmente fora de migrations. Nao e crash de producao. | 2h | **Pendente verificacao em producao** (queries V1-V5). **Rebaixado de CRITICAL para MEDIUM** pelo DB specialist (backend handles sync manualmente). |
| DB-05 | **`stripe_webhook_events` INSERT policy nao scoped a `service_role`** -- Qualquer usuario autenticado pode inserir eventos fake. Mitigado parcialmente por CHECK `'^evt_'` e `GRANT INSERT TO service_role` (linha 72). | `supabase/migrations/010_stripe_webhook_events.sql` linhas 56-58 | Eventos fake podem causar skip de webhooks reais do Stripe. | 1h | Ativo |
| DB-07 | **`pipeline_items` e `search_results_cache` FK para `auth.users` em vez de `profiles`** -- Regressao da padronizacao feita na migration 018. Funcionalmente benigno (`profiles.id` = `auth.users.id` sempre, 1:1 com ON DELETE CASCADE). | `supabase/migrations/025`, `026` | Inconsistencia de FK pattern. Higiene de schema. | 2h | Ativo |
| DB-09 | **`search_sessions` time-series query carrega todas as rows em Python** -- Endpoint `time-series` filtra por `range_days`, mas `top-dimensions` (linhas 206-245) carrega TODAS as sessions sem date filter. | `backend/routes/analytics.py` linhas 148-245 | Pagina de analytics lenta para power users. Escopo expandido pelo DB specialist para incluir `top-dimensions`. | 6h | Ativo. Combinar com DB-17. |
| DB-11 | **`handle_new_user()` trigger redefinido 4 vezes** (migrations 001, 007, 016, 024) -- Versao 024 omitiu `plan_type = 'free_trial'` que existia na versao 016. Causa raiz de DB-02. Consolidar APOS correcao de DB-02. | Multiplos arquivos de migration | Evolucao fragil de trigger. | 3h | Ativo. Depende de DB-02. |
| DB-15 | **`admin.py` CreateUserRequest usa `plan_id: "free"` como default** -- Quando admin cria usuario sem plan explicito, trigger aplica column default `'free'`, violando CHECK. Impacto secundario de DB-02. | `backend/admin.py` linha 246 | Admin-created users falham por DB-02. | 0.5h | **Novo.** Adicionado pelo DB specialist. Depende de DB-02 estar corrigido. |
| DB-17 | **Endpoint `top-dimensions` carrega TODAS as search sessions sem date filter** -- Fetch sem limite temporal. Cresce linearmente com sessoes do usuario. Sem mitigacao (diferente do time-series que filtra). | `backend/routes/analytics.py` linhas 206-245 | Analytics lenta para usuarios de alto volume. | 4h | **Novo.** Adicionado pelo DB specialist. Combinar com DB-09. |

#### LOW (6 items)

| ID | Debito | Localizacao | Impacto | Horas | Status |
|----|--------|-------------|---------|-------|--------|
| DB-08 | **Stripe production price IDs hardcoded em migration 015** -- Nao environment-aware. Migration 021 documenta instrucoes por environment. Adequado para POC com 3 planos. | `supabase/migrations/015_add_stripe_price_ids_monthly_annual.sql` | Staging/dev recebem IDs de Stripe errados. | 1h | Ativo. **Rebaixado de MEDIUM para LOW** pelo DB specialist. |
| DB-10 | **`search_results_cache.results` JSONB pode ser 10-100KB por entry** -- Projecao: 5000 usuarios x 5 entries x 50KB = 1.25GB. Supabase Pro inclui 8GB. Max-5-per-user trigger e excelente mitigacao. | `supabase/migrations/026_search_results_cache.sql` | Bloat de banco a escala. Monitoramento suficiente ate >10K usuarios. | 2h | Ativo. **Rebaixado de MEDIUM para LOW** pelo DB specialist. |
| DB-12 | **Deprecated migration file 006b no diretorio** (cross-ref: SYS-23). | `006b_DEPRECATED_...DUPLICATE.sql` | Confusao durante schema review. Mover para `supabase/archive/`. | 0.5h | Ativo |
| DB-13 | **`pipeline_items` usa `update_pipeline_updated_at()` separada** em vez do compartilhado `update_updated_at()`. | `supabase/migrations/025` linha 57 | Duplicacao de funcao desnecessaria. | 0.5h | Ativo |
| DB-14 | **`search_results_cache` sem INSERT policy para usuarios** -- Todas as escritas dependem da policy overly-permissive (DB-04). Backend usa service_role, entao nao bloqueia. | `supabase/migrations/026` | Relevante apenas para futuro client-side caching. | 1h | Ativo |
| DB-16 | **`quota.py` fallback `get("plan_type", "free")` retorna valor invalido** -- `PLAN_TYPE_MAP` em L529 mapeia `"free" -> "free_trial"`, mitigando. Fragil se mapping for removido. | `backend/quota.py` linha 522 | Baixo (mitigado por mapping). Defense-in-depth. | 0.25h | **Novo.** Adicionado pelo DB specialist. |

**Subtotal Database: 17 debitos | ~23h**

---

### 1.3 Frontend/UX -- validado por @ux-design-expert + @qa

**46 debitos | Esforco estimado: ~194h**

**Nota de deduplicacao:** FE-20 e FE-21 removidos como falsos positivos. UX-NEW-01 subsumido em A11Y-01+A11Y-02. UX-NEW-02 subsumido em UX-03 (R-04). UX-NEW-03, UX-NEW-04, UX-NEW-05 adicionados como items independentes.

#### HIGH (7 items)

| ID | Debito | Localizacao | Impacto | Horas | Status |
|----|--------|-------------|---------|-------|--------|
| FE-01 | **SearchForm recebe ~42 props** via prop drilling. Interface SearchFormProps: 84 linhas (linhas 18-102). Qualquer mudanca de filtro cascadeia por 4+ camadas. | `buscar/components/SearchForm.tsx` | Manutencao: cascading changes bloqueiam iteracao de UX. | 16h* | Ativo. *Ver Cluster F: 32h para FE-01+02+03 juntos. |
| FE-02 | **SearchResults recebe ~35 props.** Interface SearchResultsProps: 73 linhas (linhas 21-94). Criado pela decomposicao do buscar monolith -- moveu complexidade de inline para interfaces. | `buscar/components/SearchResults.tsx` | Mesmo impacto de FE-01. | 16h* | Ativo. *Idem. |
| FE-03 | **`useSearchFilters` tem 528 linhas com 40+ state variables.** Single hook fazendo demais. Prerequisito para testabilidade. | `buscar/hooks/useSearchFilters.ts` | Impossivel testar/debugar logica de filtros individualmente. | 16h* | Ativo. *Idem. |
| FE-04 | **22 arquivos de teste quarantined** em `__tests__/quarantine/`. Inclui AuthProvider, useSearch, useSearchFilters, DashboardPage, MensagensPage, ContaPage, LicitacaoCard, LicitacoesPreview. | `frontend/__tests__/quarantine/` | Confianca de teste reduzida; fluxos criticos nao testados no CI. | 24h | Ativo. Contagem corrigida de 17 para 22 (R-03). |
| FE-08 | **Error boundary button usa `--brand-green` nao definida nos design tokens.** `app/error.tsx` linha 67: `bg-[var(--brand-green)]` NAO existe em `globals.css`. Botao renderiza SEM background visivel. Pagina de erro e o pior lugar para CTA quebrado. | `app/error.tsx` | Usuarios que encontram erro veem botao invisivel, ficando presos sem recuperacao. | 1h | Ativo. **Elevado de MEDIUM para HIGH, movido para P0** (R-05, CR-08). Quick win: substituir por `bg-[var(--brand-navy)]`. |
| A11Y-01 | **Modal dialogs (save search, keyboard help) sem focus trap** -- keyboard users podem Tab para tras do modal. Save search dialog: linhas 238-274, keyboard help: linhas 277-350. Ambos sao `<div>` com `fixed inset-0 z-50` sem focus trap. UpgradeModal.tsx (linhas 34-51) JA implementa pattern corretamente. | `/buscar` save dialog, keyboard help modal | WCAG 2.4.3 Focus Order violation. | 4h | Ativo. Co-implementacao com A11Y-02 (4h total para ambos). **UX-NEW-01 subsumido aqui** (R-04). |
| A11Y-02 | **Modals nao usam `role="dialog"` ou `aria-modal="true"`** -- Screen readers nao anunciam contexto de dialogo. UpgradeModal.tsx e CookieConsentBanner.tsx ja implementam corretamente. Fix: replicar pattern + adicionar focus trap (~30 linhas). | Multiplos modal dialogs | WCAG 4.1.2 Name/Role/Value violation. | (incl. em A11Y-01) | Ativo. Co-implementacao com A11Y-01. |

**Nota:** UX-03 e HIGH e P0 -- listado abaixo na categoria UX Issues por organizacao, mas priorizado como P0.

#### MEDIUM (19 items)

| ID | Debito | Localizacao | Impacto | Horas | Status |
|----|--------|-------------|---------|-------|--------|
| FE-05 | **Inline SVGs duplicados em 30+ arquivos** -- 162 ocorrencias SVG/viewBox. lucide-react instalado mas usado em apenas 5 arquivos. | Multiplos componentes | Bundle bloat, sizing inconsistente. | 6h | Ativo. Estimativa revisada pela UX specialist (8h -> 6h, migracao mecanica). |
| FE-06 | **Lista de setores hardcoded em dois lugares** -- `useSearchFilters.ts` (SETORES_FALLBACK) e `signup/page.tsx` (SECTORS) podem divergir. | `buscar/hooks/`, `app/signup/page.tsx` | Setores de signup podem nao corresponder a busca. | 4h | Ativo |
| FE-07 | **Sem dynamic imports para dependencias pesadas** -- recharts (~200KB), @dnd-kit (3 pacotes), framer-motion (~40KB), shepherd.js. Zero uso de `next/dynamic` ou `React.lazy`. | Dashboard, Pipeline, Landing, Search | JS bundle maior; degrada LCP/TTI. | 6h | Ativo. Estimativa revisada (8h -> 6h). Prioridade: recharts > @dnd-kit > shepherd.js > framer-motion. |
| FE-09 | **Sem testes para SearchResults.tsx (678 linhas)** -- componente core sem teste. Multiplos render paths condicionais. | `buscar/components/SearchResults.tsx` | Sem safety net de regressao para UI mais visivel. | 16h | Ativo. Escrever testes APOS refactor FE-01/02/03 (BLOQUEIO-03). |
| FE-10 | **Sem testes para pipeline drag-and-drop.** | `app/pipeline/page.tsx` | Interacao complexa sem teste. | 8h | Ativo |
| FE-11 | **Sem testes para onboarding wizard flow.** | `app/onboarding/page.tsx` | Formulario multi-step sem teste. | 8h | Ativo |
| FE-12 | **Sem testes para middleware.ts route protection.** Bugs de auth guard sao imediatamente visiveis (flash de conteudo protegido). | `frontend/middleware.ts` | Logica de auth guard sem teste. | 8h | Ativo |
| FE-17 | **PLAN_HIERARCHY e PLAN_FEATURES hardcoded em planos/page.tsx** -- duplicata de `lib/plans.ts`. Mudancas de plano requerem editar dois arquivos, arriscando drift de precos/features. | `app/planos/page.tsx` linhas 34-46, 55+; `lib/plans.ts` | Drift de precos afeta confianca do usuario. | 4h | Ativo. **Elevado de LOW para MEDIUM** pela UX specialist. |
| A11Y-03 | **Custom dropdowns (CustomSelect) podem nao anunciar mudancas de selecao** a screen readers. Usa `<div>` com `role="combobox"`. Precisa `aria-activedescendant` e `aria-selected`. | `app/components/CustomSelect.tsx` | Usuarios de AT perdem feedback de selecao. | 4h | Ativo |
| A11Y-05 | **Shepherd.js onboarding pode bloquear conteudo sem `inert` attribute** no background. | `/buscar` onboarding tour | Background permanece interativo durante tour. | 4h | Ativo |
| A11Y-08 | **Alguns icones SVG usam `aria-label="Icone"` generico** -- `planos/page.tsx` linha 366 tem `aria-label="Icone"` em icone shield/checkmark. Labels genericos pior que nada para AT users. Fix: `aria-hidden="true"` (decorativo) ou label descritiva. | Multiplos componentes | Confusao para AT users. | 2h | Ativo. **Elevado de LOW para MEDIUM** pela UX specialist. |
| UX-01 | **Search button abaixo do fold** em desktop com accordion aberto. Sticky mobile (`sticky bottom-4 sm:bottom-auto`) existe mas desabilitado em desktop. | `/buscar` SearchForm | CTA primario nao visivel. | 4h | Ativo |
| UX-02 | **Keyboard shortcuts modal sem focus trap; conflito de Escape** -- Escape handler global dispara `limparSelecao()` antes do close handler do modal. | `/buscar` keyboard help | Escape conflict confunde usuarios. Fix: capture-phase event listener como UpgradeModal (linha 45). | 0h extra | Ativo. Resolvido automaticamente pela mesma infra de A11Y-01+A11Y-02. |
| UX-03 | **Pricing page mostra multiplicador "9.6x"** -- 5 ocorrencias de `price_brl * 9.6` em `planos/page.tsx` (linhas 546, 555, 702, 738). Linha 738: "12 meses pelo preco de 9.6" confunde usuarios. Matematica: 12 * 0.8 = 9.6, mas exibir como multiplicador nao faz sentido. Questao de confianca. **UX-NEW-02 subsumido aqui** (R-04). | `/planos` pricing cards | Usuarios confusos com informacao financeira. | 2h | Ativo. **Elevado para HIGH, P0** pelo UX specialist. Estimativa revisada (4h -> 2h, copy change). Recomendacao: "2 meses gratis no plano anual" + valor economizado em R$. |
| UX-04 | **Pipeline page nao otimizada para mobile** -- `flex gap-4 overflow-x-auto` cria scroll horizontal. 5 colunas nao colapsam. DnD funcional via PointerSensor mas desajeitado. | `/pipeline` | Mobile users nao conseguem usar Kanban efetivamente. Recomendacao UX: lista vertical colapsavel abaixo de 768px com "Mover para..." dropdown. | 16h | Ativo |
| IC-06 | **Traducao de mensagens de erro apenas na pagina de login** -- Login mostra "E-mail ou senha incorretos", busca mostra "502 Bad Gateway" raw. Inconsistencia jarring. | Login vs outras paginas | UX de erro degradada fora do login. Solucao: dicionario `lib/error-messages.ts`. | 4h | Ativo. **Elevado de LOW para MEDIUM** pela UX specialist. Estimativa revisada (8h -> 4h). |
| MF-01 | **Sem confirmacao ao sair de `/buscar` com resultados** -- Busca leva 15-60s. Perder resultado ao navegar sem aviso e frustrante. | `/buscar` navigation | Usuarios perdem resultados acidentalmente. Usar `beforeunload` ou Next.js route change listener. | 4h | Ativo. **Elevado de LOW para MEDIUM** pela UX specialist. |
| UX-NEW-03 | **Admin page usa `window.confirm()` nativo** para delecao de usuario -- mesmo anti-pattern corrigido em FE-H04. Acao destrutiva deve usar modal proprio com consequencias explicadas. | `admin/page.tsx` linha 131 | Dialog nativo nao estilizavel, alienigena ao app. | 2h | **Novo.** Adicionado pela UX specialist. |
| UX-NEW-05 | **Pipeline column count forca horizontal scroll em tablet** -- 5 colunas em `flex gap-4`. Em 768-1024px, ultimas 1-2 colunas off-screen. Sem indicador de scroll. | `pipeline/page.tsx` linha 146 | Tablet users podem nao descobrir ultimas colunas. | 2h | **Novo.** Adicionado pela UX specialist. |

#### LOW (20 items)

| ID | Debito | Localizacao | Impacto | Horas | Status |
|----|--------|-------------|---------|-------|--------|
| FE-13 | Auth guard duplicado entre middleware.ts e `(protected)/layout.tsx`. | `middleware.ts`, `app/(protected)/layout.tsx` | Logica de redirect dupla. | 4h | Ativo |
| FE-14 | Console.log statements em AuthProvider -- debug OAuth em producao. | `app/components/AuthProvider.tsx` linhas 254-258 | Vaza detalhes de implementacao. | 1h | Ativo |
| FE-15 | `useEffect` com dependencies faltando -- 4 `eslint-disable-next-line`. | `login/page.tsx`, `planos/page.tsx`, `redefinir-senha/page.tsx`, `planos/obrigado/page.tsx` | Potencial stale closure bugs. | 8h | Ativo |
| FE-16 | Search state usa `window.location.href` -- 17+ ocorrencias, muitas legitimas (OAuth). | Search-related code | Full page reload em vez de client nav. | 2h | Ativo |
| FE-18 | `next.config.js` usa CommonJS enquanto resto e ESM/TypeScript. | `frontend/next.config.js` | Inconsistencia. | 2h | Ativo |
| FE-19 | Pull-to-refresh CSS hack desabilita pointer-events. Fragil. | `/buscar` CSS | Pode quebrar com mudancas de layout. | 4h | Ativo |
| A11Y-04 | Pull-to-refresh sem alternativa de keyboard (mobile-only). Botao de busca regular oferece mesma funcionalidade. | `/buscar` PullToRefresh | Desabilitado em desktop. Alternativa existe. | 4h | Ativo. **Rebaixado de MEDIUM para LOW** pela UX specialist. |
| A11Y-06 | UF buttons usam `title` mas sem `aria-label` para nome do estado. | `RegionSelector.tsx` | Maioria dos AT le `title`, inconsistente. | 2h | Ativo |
| A11Y-07 | Keyboard shortcuts sem opcao de desabilitar/customizar. | `/buscar` shortcuts | Risco de conflito com browser/OS. | 4h | Ativo |
| A11Y-09 | Dark mode `--ink-muted` a 4.9:1 -- borderline AA (minimo 4.5:1). Tecnicamente passa. | `globals.css` dark mode | Melhorar para 5.5:1+ seria ideal. | 1h | Ativo |
| UX-05 | Admin page table nao responsiva -- horizontal scroll em mobile. Admin usada por 1-2 pessoas. | `/admin` | Funcional com scroll. Audience minima. | 2h | Ativo. **Rebaixado de MEDIUM para LOW** pela UX specialist. Estimativa revisada (8h -> 2h). |
| IC-01 | "SmartLic" hardcoded no header apesar de `APP_NAME` env var. Versao hardcoded inclui sufixo `.tech` estilizado, intencional. | `buscar/page.tsx` linha 123 | Decisao de design documentavel. | 1h | Ativo |
| IC-02 | Mixed color approaches -- Tailwind tokens vs inline CSS vars. Output visual identico. | Multiplos arquivos | Issue de DX apenas. | 4h | Ativo |
| IC-03 | Icon sources mixed -- lucide-react vs inline SVGs. lucide em 5 arquivos apenas. | Multiplos componentes | Sem sistema de icones consistente. | 4h | Ativo |
| IC-04 | Loading spinner styles variam entre componentes. | Multiplos componentes | Inconsistencia visual menor. | 4h | Ativo |
| IC-05 | Link vs anchor tag misturados para navegacao interna. Relacionado a FE-16. | Multiplas paginas | Client nav inconsistente. | 2h | Ativo |
| IC-07 | Max-width container varia (4xl, 5xl, 7xl, landing) -- variacao intencional por pagina. | Multiplos layouts | Documentar rationale, nao normalizar. | 4h | Ativo |
| MF-02 | Sem feedback "Copiado para clipboard". Sonner toast trivial. | `LicitacaoCard` copy actions | Usuarios nao sabem se copia funcionou. | 2h | Ativo |
| MF-03 | Pipeline DnD sem feedback haptico/audio em mobile. | `/pipeline` | Nice-to-have para audience pequena. | 4h | Ativo |
| MF-04 | Mudanca de setor nao confirma que resultados foram limpos. | `/buscar` sector selector | Toast ou animacao sutil bastaria. | 2h | Ativo |
| UX-NEW-04 | Sem empty state para pagina de pipeline -- grid vazio sem orientacao. AddToPipelineButton esta na pagina de resultados. | `pipeline/page.tsx` | Usuarios novos veem colunas vazias sem explicacao. | 2h | **Novo.** Adicionado pela UX specialist. |

**Subtotal Frontend/UX: 46 debitos | ~194h**

---

## 2. Matriz de Priorizacao Final

### Legenda

- **Impacto:** SAFETY (seguranca/data breach), FUNCTIONAL (feature quebrada), QUALITY (experiencia degradada), MAINTENANCE (carga de manutencao)
- **[QW]**: Quick Win -- 4h ou menos
- **Prioridade:** P0 (imediato), P1 (proximo sprint), P2 (4-6 semanas), P3 (backlog)

### P0 -- Criticos: Resolver Imediatamente (~11.5h, 8 items)

| # | ID | Debito | Area | Impacto | Esforco |
|---|-----|--------|------|---------|---------|
| 0 | -- | **Executar queries V1-V5 de verificacao em producao** | DB | PRE-REQUISITO | 1h |
| 1 | DB-02 | `handle_new_user()` trigger + column default `'free'` viola CHECK | DB | FUNCTIONAL | 2h [QW] |
| 2 | DB-06 | `_ensure_profile_exists()` usa `plan_type: "free"` violando CHECK | Backend | FUNCTIONAL | 0.5h [QW] |
| 3 | DB-03 | `pipeline_items` RLS overly permissive -- cross-user access | DB | SAFETY | 1h [QW] |
| 4 | DB-04 | `search_results_cache` RLS overly permissive -- cross-user access | DB | SAFETY | 1h [QW] |
| 5 | FE-08 | Error boundary `--brand-green` nao definida -- botao invisivel | Frontend | FUNCTIONAL | 1h [QW] |
| 6 | UX-03 | Pricing "9.6x" multiplier confuso + texto "pelo preco de 9.6" | Frontend | QUALITY | 2h [QW] |
| 7 | SYS-03 | Verificar se STORY-251 resolveu; se sim, remover nota obsoleta | Backend | QUALITY | 1h [QW] |

**Subtotal P0: ~9.5h** (+ 1h verificacao producao = ~10.5h efetivo)

### P1 -- Altos: Resolver no Proximo Sprint (~35.5h, 10 items)

| # | ID | Debito | Area | Impacto | Esforco |
|---|-----|--------|------|---------|---------|
| 8 | DB-05 | `stripe_webhook_events` INSERT policy scope to service_role | DB | SAFETY | 1h [QW] |
| 9 | DB-15 | Admin.py CreateUserRequest default "free" -> "free_trial" | DB | FUNCTIONAL | 0.5h [QW] |
| 10 | DB-01 | Documentar ou remover trigger baseado em verificacao (V1-V5) | DB | MAINTENANCE | 2h |
| 11 | A11Y-01+02 | Dialog primitive com focus trap (extrair de UpgradeModal) + UX-02 | Frontend | QUALITY | 4h |
| 12 | SYS-07 | async sleep fix em quota.py (atentar para CR-09) | Backend | QUALITY | 2h |
| 13 | SYS-10 | Adicionar mypy ao CI (ruff ja ativo) | CI/CD | QUALITY | 2h |
| 14 | IC-06 | Dicionario centralizado de mensagens de erro em portugues | Frontend | QUALITY | 4h |
| 15 | MF-01 | Confirmacao de saida com resultados de busca ativos | Frontend | QUALITY | 4h |
| 16 | SYS-02 | Dual HTTP client consolidation (remover sync, manter async) | Backend | MAINTENANCE | 16h |

**Subtotal P1: ~35.5h** (ou ~19.5h sem SYS-02 se adiado para P2)

### P2 -- Medios: Resolver em 4-6 Semanas (~153h, 18 items)

| # | ID | Debito | Area | Impacto | Esforco |
|---|-----|--------|------|---------|---------|
| 17 | FE-01+02+03 | Search state refactor: React Context + useReducer (Cluster F) | Frontend | MAINTENANCE | 32h |
| 18 | FE-04 | Unquarantine 22 test files (independentes primeiro, Cluster G) | Frontend | QUALITY | 24h |
| 19 | FE-09 | Testes para SearchResults.tsx (APOS refactor FE-01/02/03) | Frontend | QUALITY | 16h |
| 20 | SYS-11 | Decomposicao de search_pipeline.py (1318 linhas) | Backend | MAINTENANCE | 16h |
| 21 | FE-07 | Dynamic imports: recharts, @dnd-kit, shepherd.js | Frontend | QUALITY | 6h |
| 22 | FE-17 | Consolidar PLAN_HIERARCHY/PLAN_FEATURES com lib/plans.ts | Frontend | QUALITY | 4h |
| 23 | UX-01 | Search button sticky em desktop | Frontend | QUALITY | 4h |
| 24 | DB-07 | FK standardization (auth.users -> profiles) | DB | MAINTENANCE | 2h |
| 25 | DB-09+17 | Analytics date filter + top-dimensions RPC | DB | QUALITY | 10h |
| 26 | DB-11 | Consolidar handle_new_user() trigger | DB | MAINTENANCE | 3h |
| 27 | SYS-08 | Excel tmpdir -> Supabase Storage signed URL | Backend | QUALITY | 4h |
| 28 | SYS-09 | Dual route mounting cleanup (sunset 2026-06-01) | Backend | MAINTENANCE | 4h |
| 29 | FE-05 | Icon migration para lucide-react | Frontend | QUALITY | 6h |
| 30 | SYS-04 | Progress tracker -> Redis pub/sub primario | Backend | FUNCTIONAL | 8h |
| 31 | SYS-05 | Auth token cache compartilhado | Backend | FUNCTIONAL | 4h |
| 32 | SYS-06 | Legacy plan seeds cleanup | Backend | MAINTENANCE | 8h |
| 33 | DB-16 | quota.py fallback default "free" -> "free_trial" | DB | QUALITY | 0.25h |
| 34 | DB-13 | Consolidar funcao update_pipeline_updated_at() | DB | MAINTENANCE | 0.5h |

**Subtotal P2: ~152.75h**

### P3 -- Backlog (~157h, 51 items restantes)

Todos os items LOW nao listados em P0-P2, alem de items MEDIUM de menor prioridade.

**Agrupados por area:**

- **Backend/Infra (14 items, ~89h):** SYS-01 (40h), SYS-12 (8h), SYS-13 (2h), SYS-14 (2h), SYS-15 (8h), SYS-16 (16h), SYS-17 (4h), SYS-18 (2h), SYS-19 (1h), SYS-20 (1h), SYS-21 (1h), SYS-22 (1h), SYS-23 (1h), SYS-24 (1h)
- **Database (4 items, ~4.5h):** DB-08 (1h), DB-10 (2h), DB-12 (0.5h), DB-14 (1h)
- **Frontend/UX (33 items, ~63.5h):** UX-04 (16h), FE-10 (8h), FE-11 (8h), FE-12 (8h), FE-13 (4h), FE-14 (1h), FE-15 (8h), FE-16 (2h), FE-18 (2h), FE-19 (4h), FE-06 (4h), A11Y-03 (4h), A11Y-04 (4h), A11Y-05 (4h), A11Y-06 (2h), A11Y-07 (4h), A11Y-09 (1h), UX-05 (2h), UX-NEW-03 (2h), UX-NEW-04 (2h), UX-NEW-05 (2h), IC-01 (1h), IC-02 (4h), IC-03 (4h), IC-04 (4h), IC-05 (2h), IC-07 (4h), MF-02 (2h), MF-03 (4h), MF-04 (2h)

**Subtotal P3: ~157h**

### Resumo de Esforco

| Prioridade | Items | Esforco Total |
|------------|-------|---------------|
| P0 | 8 (+verificacao) | ~11.5h |
| P1 | 10 | ~35.5h |
| P2 | 18 | ~153h |
| P3 | 51 | ~157h |
| **Total** | **87** | **~357h** |
| **Com buffer 1.3x** | -- | **~464h** |
| **Com buffer 1.5x** | -- | **~536h** |

---

## 3. Grafo de Dependencias

### 3.1 Cadeias de Dependencia

```
[PREREQUISITO ABSOLUTO: Queries V1-V5 de verificacao em producao]
        |
        v
DB-02 (column default) -----> DB-15 (admin.py) -----> DB-11 (trigger consolidation)
  |                                                           |
  +---> DB-06 (quota.py L790)                                 +---> DB-01 (status column decision)
  |       |
  |       +---> DB-16 (quota.py L522 fallback)
  |
  +---> SYS-06 (legacy plan seeds) --- so apos DB-02 estavel

DB-03 (pipeline RLS) ---independente, paralelizavel---> DB-04 (cache RLS)
  |                                                        |
  +---mesma migration---> DB-05 (webhook INSERT RLS) ------+
  |
  +---migration seguinte---> DB-07 (FK standardization)
  +---apos DB-04---> DB-14 (cache INSERT policy)

SYS-01 (test coverage) <---depende-de--- FE-04 (quarantined tests)
  |
  +---depende-de---> FE-09 (SearchResults tests)
  +---depende-de---> FE-10 (pipeline tests)
  +---depende-de---> FE-11 (onboarding tests)
  +---depende-de---> FE-12 (middleware tests)

FE-01 (SearchForm props) ---co-refactor---> FE-02 (SearchResults props)
  |                                           |
  +---depende-de---> FE-03 (useSearchFilters split)
  |
  +---FE-09 testes unitarios APOS refactor (BLOQUEIO-03)

SYS-02 (dual HTTP client) ---habilita---> SYS-04 (progress tracker scalability)
                                                   |
                                                   +---habilita---> SYS-05 (auth cache sharing)
  +---includes---> SYS-20 (_request_count) + SYS-21 (deprecated API)

SYS-09 (dual route mounting) ---deadline---> 2026-06-01 (sunset date)

A11Y-01 (focus trap) ---co-implementacao---> A11Y-02 (role="dialog")
  |
  +---resolve automaticamente---> UX-02 (Escape conflict)
  +---habilita---> UX-NEW-03 (admin confirm dialog usa shared Dialog)

SYS-11 (search_pipeline decomposition) ---facilita---> correcoes em stages

DB-09 (time-series) ---mesmo fix pattern---> DB-17 (top-dimensions)
```

### 3.2 Clusters de Trabalho (A-G) -- Revisados

**Cluster A: Database Security Sprint (P0, ~5.5h, migration 027)**

Items: DB-02 + DB-03 + DB-04 + DB-06

Validado unanimemente por todos os especialistas. Migration 027 minima e focada em P0:
1. Backend code fixes ANTES da migration: DB-06 (quota.py L790) + DB-16 (quota.py L522)
2. Migration 027: ALTER column default, CREATE OR REPLACE handle_new_user(), DROP+CREATE RLS policies
3. Pre-condicao ABSOLUTA: executar queries V1-V5

DB-05, DB-07, DB-15 para migration 028 (P1/P2). Rollback strategy documentada na Secao 4, Sprint 0.

**Cluster B: Backend Quick Wins (P0-P1, ~7h)**

Items: SYS-03 (verificar) + SYS-07 + SYS-14 + SYS-18

SYS-03 rebaixado para 1h se STORY-251 confirmado. Items independentes. Atentar para CR-09 em SYS-07.

**Cluster C: CI/Quality Gates (P0-P1, ~3h)**

Items: FE-08 + SYS-10

FE-08 quick win de 1h com impacto critico (P0). SYS-10 parcialmente resolvido (ruff ja ativo, apenas mypy falta, 2h).

**Cluster D: Accessibility Sprint (P1, ~4h)**

Items: A11Y-01 + A11Y-02 + UX-02 + (habilita UX-NEW-03)

Extrair `<Dialog>` de UpgradeModal.tsx (ja tem aria-modal, role, Escape capture-phase). Adicionar focus trap (~30 linhas). Refatorar 3 modais. Total: 4h.

**Cluster E: PNCP Client Consolidation (P1, ~18h)**

Items: SYS-02 + SYS-20 + SYS-21

Verificar PNCPLegacyAdapter.fetch() usage (CR-04). Reducao de ~1585 para ~800 linhas. Requer review detalhado.

**Cluster F: Frontend Architecture Refactor (P2, ~32h)**

Items: FE-01 + FE-02 + FE-03

Pattern: React Context + useReducer scoped a `/buscar`. SearchForm/SearchResults -> 0 props. Reducer testavel como pure function. Pre-requisito: E2E como safety net (BLOQUEIO-02). Estimativa revisada: 48h -> 32h (trabalho compartilhado).

**Cluster G: Test Coverage Campaign (P2-P3, ~80h)**

Items: SYS-01 + FE-04 + FE-09 + FE-10 + FE-11 + FE-12

Sequenciamento otimizado:
- G.1: Unquarantine 10-12 testes independentes de SearchForm/SearchResults (8h)
- G.2: E2E Playwright para SearchResults -- sobrevive a refactor (8h)
- G.3: Executar Cluster F (32h com E2E como safety net)
- G.4: Testes unitarios para nova arquitetura (SearchContext, reducer, sub-hooks) (16h)
- G.5: Pipeline, onboarding, middleware tests (16h)

---

## 4. Plano de Resolucao (4 Sprints)

### Sprint 0: Verificacao e Quick Wins (1 semana, ~15h)

**Objetivo:** Confirmar estado real de producao, eliminar riscos criticos, quick wins de alto impacto.

| Dia | Acao | Items | Horas |
|-----|------|-------|-------|
| 1 (manha) | Executar queries V1-V5 em producao (Supabase SQL Editor) | PRE-REQ | 1h |
| 1 (tarde) | Backend code fixes: quota.py L790 + L522 (`"free"` -> `"free_trial"`) | DB-06, DB-16 | 0.75h |
| 1 (tarde) | Deploy backend com fixes | -- | 0.5h |
| 2 (manha) | Criar e aplicar migration 027 (column default + trigger + RLS) | DB-02, DB-03, DB-04 | 3h |
| 2 (tarde) | Executar queries V6-V8 (post-deployment validation) | -- | 0.5h |
| 3 (manha) | Fix error boundary button (`--brand-green` -> `--brand-navy`) | FE-08 | 1h |
| 3 (tarde) | Fix pricing "9.6" display: substituir por "2 meses gratis" + R$ economizado | UX-03 | 2h |
| 4 (manha) | Verificar SYS-03 contra STORY-251; remover nota obsoleta se resolvido | SYS-03 | 1h |
| 4 (tarde) | Fix admin.py CreateUserRequest default | DB-15 | 0.5h |
| 5 | Testes de regressao para todos os fixes (REG-T01 a REG-T04, REG-T08, REG-T09) | -- | 4h |

**Rollback Strategy para Migration 027:**

```sql
-- ROLLBACK migration 027 (executar na ordem inversa)

-- 1. Restaurar RLS de search_results_cache (REINTRODUZ DB-04)
DROP POLICY IF EXISTS "Service role full access on search_results_cache"
  ON search_results_cache;
CREATE POLICY "Service role full access on search_results_cache"
  ON search_results_cache FOR ALL
  USING (true) WITH CHECK (true);

-- 2. Restaurar RLS de pipeline_items (REINTRODUZ DB-03)
DROP POLICY IF EXISTS "Service role full access on pipeline_items"
  ON public.pipeline_items;
CREATE POLICY "Service role full access on pipeline_items"
  ON public.pipeline_items FOR ALL
  USING (true) WITH CHECK (true);

-- ATENCAO: NAO reverter column default de plan_type.
-- Manter 'free_trial' pois 'free' viola o CHECK constraint.
-- Reverter seria PIOR que nao reverter.

-- ATENCAO: NAO reverter handle_new_user() para versao 024.
-- Reintroduziria DB-02. So reverter se versao 027 causar
-- problemas que 024 nao causava.
```

**ALERTA:** Rollback de RLS reintroduz vulnerabilidade cross-user (DB-03/DB-04). Usar como ultimo recurso e corrigir rapidamente.

### Sprint 1: Seguranca e Correcoes (2 semanas, ~24h)

**Objetivo:** Fechar gaps de seguranca restantes, infraestrutura de acessibilidade, CI quality gates.

| Semana | Acao | Items | Horas |
|--------|------|-------|-------|
| 1 | Webhook INSERT policy + DB-01 resolution baseado em V1-V5 | DB-05, DB-01 | 3h |
| 1 | Dialog primitive (focus trap + role + aria-modal) | A11Y-01+02, UX-02 | 4h |
| 1 | Dicionario de mensagens de erro + unsaved changes warning | IC-06, MF-01 | 8h |
| 2 | async sleep fix (quota.py) | SYS-07 | 2h |
| 2 | mypy no CI | SYS-10 | 2h |
| 2 | SYS-02 investigacao + inicio da consolidacao | SYS-02 (parcial) | 5h |

### Sprint 2: Consolidacao e Refatoracao Frontend (3 semanas, ~72h)

**Objetivo:** Eliminar prop drilling, consolidar state management, iniciar test coverage.

| Semana | Acao | Items | Horas |
|--------|------|-------|-------|
| 1 | Unquarantine testes independentes (G.1) | FE-04 (parcial) | 8h |
| 1 | E2E Playwright para SearchResults (G.2) | FE-09 (parcial) | 8h |
| 2-3 | Search state refactor: Context + useReducer (G.3 = Cluster F) | FE-01+02+03 | 32h |
| 3 | search_pipeline.py decomposicao | SYS-11 | 16h |

**Nota:** SYS-02 restante (~11h) tambem neste sprint se nao completado no Sprint 1.

### Sprint 3: Qualidade e Cobertura (2 semanas, ~56h)

**Objetivo:** Testes para nova arquitetura, dynamic imports, polimento.

| Semana | Acao | Items | Horas |
|--------|------|-------|-------|
| 1 | Testes unitarios: SearchContext, reducer, sub-hooks (G.4) | FE-09, SYS-01 | 16h |
| 1 | Dynamic imports + plan data consolidation + icons | FE-07, FE-17, FE-05 | 16h |
| 2 | Pipeline, onboarding, middleware tests (G.5) | FE-10, FE-11, FE-12 | 24h |

### Sprints Futuros: Backlog

Items P3 (~157h) trabalhados incrementalmente, priorizados por clusters:
1. Backend scalability: SYS-04, SYS-05, SYS-06
2. Backend cleanup: SYS-12 through SYS-24
3. DB optimization: DB-07 through DB-14, DB-16
4. Frontend polish: FE-06, FE-13 through FE-19
5. UX/Accessibility: UX-04, UX-05, UX-NEW-03/04/05, A11Y-03 through A11Y-09
6. Consistency: IC-01 through IC-07, MF-02 through MF-04

---

## 5. Riscos Cruzados

| # | Risco | Areas | Probabilidade | Impacto | Mitigacao |
|---|-------|-------|---------------|---------|-----------|
| CR-01 | **Migration 027 falha em producao** por conflito com estado real do banco (colunas adicionadas manualmente, triggers alterados fora de migrations) | DB, Backend | Media | CRITICAL | Executar queries V1-V5 ANTES. Preparar rollback script (Secao 4). Aplicar em staging se disponivel. |
| CR-02 | **Refactor de prop drilling (FE-01/02/03) quebra testes e E2E** ao alterar interfaces | Frontend | Alta | HIGH | Executar apos FE-04 parcial (unquarantine independentes). E2E como safety net. Testes green entre fases. |
| CR-03 | **Correcao de RLS (DB-03/04) bloqueia funcionalidade se backend nao usa service_role key** | DB, Backend | Baixa | HIGH | Auditar queries para `pipeline_items` e `search_results_cache`. Confirmar uso de service_role key. |
| CR-04 | **Eliminacao do sync client (SYS-02) quebra fallback single-UF** | Backend | Media | HIGH | Verificar `PNCPLegacyAdapter.fetch()` em code paths ativos. Migrar para async antes de remover. ~785 linhas de mudanca. |
| CR-05 | **Atualizacao parcial de `plan_type` default produz inconsistencia** | DB, Backend | Media | CRITICAL | 4 code paths com "free" invalido: DB-02, DB-06, DB-15, DB-16. Corrigir **atomicamente**. |
| CR-06 | **Consolidacao de trigger (DB-11) conflita com extensoes** | DB, Frontend, Backend | Baixa | MEDIUM | Fazer APOS DB-02 estavel e signup validado. |
| CR-07 | **Dynamic imports (FE-07) causam loading spinners excessivos** | Frontend | Media | MEDIUM | Skeletons adequados. Testar em 3G throttled. |
| CR-08 | **Error boundary (FE-08) e unica recuperacao** -- botao invisivel bloqueia usuario | Frontend | Baixa | CRITICAL | `bg-[var(--brand-green)]` NAO definida. Fix P0. |
| CR-09 | **`time.sleep` -> `asyncio.sleep` (SYS-07) expoe race condition** | Backend | Baixa | MEDIUM | `time.sleep` garante exclusao mutua bloqueando event loop. `asyncio.sleep` permite interleaving. Verificar `save_search_session`. |
| CR-10 | **`search_pipeline.py` (1318 linhas) dificulta TODAS as correcoes backend** | Backend | Alta | MEDIUM | Qualquer mudanca em stages requer navegar 1318 linhas. SYS-11 elevado a HIGH, Sprint 2. |

---

## 6. Testes Requeridos

### 6.1 Seguranca (SEC-T01 -- SEC-T08)

| # | Teste | Debito | Tipo | Prioridade |
|---|-------|--------|------|-----------|
| SEC-T01 | `pipeline_items` NAO permite SELECT cross-user via PostgREST com authenticated key | DB-03 | Integracao SQL | P0 |
| SEC-T02 | `search_results_cache` NAO permite SELECT cross-user | DB-04 | Integracao SQL | P0 |
| SEC-T03 | INSERT em `pipeline_items` com `user_id` de outro usuario FALHA com RLS error | DB-03 | Integracao SQL | P0 |
| SEC-T04 | INSERT em `stripe_webhook_events` com authenticated key FALHA | DB-05 | Integracao SQL | P1 |
| SEC-T05 | INSERT em `stripe_webhook_events` com `id` nao-`'^evt_'` FALHA por CHECK | DB-05 | Unitario | P1 |
| SEC-T06 | CORS `allow_origins` nao inclui `*` em producao | GAP-01 | Config audit | P2 |
| SEC-T07 | SecurityHeadersMiddleware inclui CSP, X-Frame-Options, X-Content-Type-Options | GAP-03 | Unitario | P2 |
| SEC-T08 | `npm audit` sem high/critical no frontend | GAP-02 | CI | P2 |

### 6.2 Regressao (REG-T01 -- REG-T14)

| # | Teste | Debito | Tipo | Prioridade |
|---|-------|--------|------|-----------|
| REG-T01 | Novo usuario signup: profile com `plan_type = 'free_trial'` | DB-02 | E2E | P0 |
| REG-T02 | `_ensure_profile_exists()` cria profile com `plan_type = 'free_trial'` | DB-06 | Unitario | P0 |
| REG-T03 | Admin cria usuario sem erro de constraint | DB-15 | Integracao | P1 |
| REG-T04 | Stripe webhooks processam apos correcao de RLS | DB-03/04/05 | Integracao | P0 |
| REG-T05 | Busca multi-UF funciona apos remocao sync client | SYS-02 | E2E | P1 |
| REG-T06 | SSE progress funciona apos asyncio.sleep | SYS-07 | Integracao | P1 |
| REG-T07 | `save_search_session` retry sem race condition | SYS-07 | Unitario | P1 |
| REG-T08 | Error boundary botao visivel em light E dark mode | FE-08 | E2E + Visual | P0 |
| REG-T09 | Pricing NAO mostra "9.6" em texto visivel | UX-03 | E2E text assertion | P1 |
| REG-T10 | Modais mantem focus trap (Tab nao escapa) | A11Y-01/02 | E2E accessibility | P1 |
| REG-T11 | Escape fecha modal, UF selection permanece | UX-02 | E2E interaction | P1 |
| REG-T12 | LLM arbiter usa descricao do setor, nao "Vestuario" generico | SYS-03 | Unitario | P1 |
| REG-T13 | Dynamic imports carregam com skeleton/loading | FE-07 | E2E | P2 |
| REG-T14 | Navegacao com resultados ativos mostra confirmacao | MF-01 | E2E | P2 |

### 6.3 Performance (PERF-T01 -- PERF-T06)

| # | Teste | Debito | Tipo | Metrica Alvo |
|---|-------|--------|------|-------------|
| PERF-T01 | Analytics page load, usuario 500+ sessions | DB-09/DB-17 | Load test | < 2s (P95) |
| PERF-T02 | Bundle size apos dynamic imports | FE-07 | Build metric | Initial JS < 200KB |
| PERF-T03 | LCP pagina de busca (first visit, cold cache) | FE-07 | Lighthouse | < 2.5s |
| PERF-T04 | Busca 5 UFs sem event loop blocking | SYS-07 | Load test | Nenhum stall > 300ms |
| PERF-T05 | Pipeline page com 50 items | UX-04 | E2E timing | < 3s |
| PERF-T06 | search_pipeline.py 7 stages com 500 items | SYS-11 | Benchmark | < 10s end-to-end |

### 6.4 Criterios de Aceite por Debito

| Debt ID | Criterio de Aceite | Tipo de Teste |
|---------|-------------------|---------------|
| DB-02 | `column_default` retorna `'free_trial'::text`; signup cria `plan_type = 'free_trial'` | SQL verify + E2E |
| DB-03 | `SELECT * FROM pipeline_items` com authenticated key retorna SOMENTE items do usuario | SQL integration |
| DB-04 | `SELECT * FROM search_results_cache` com authenticated key retorna SOMENTE cache do usuario | SQL integration |
| DB-05 | `INSERT INTO stripe_webhook_events` com authenticated key FALHA | SQL integration |
| DB-06 | `_ensure_profile_exists()` cria `plan_type = 'free_trial'`; busca funciona | Unit (mock supabase) |
| DB-15 | Admin cria usuario sem plan -> `plan_type = 'free_trial'` | Integration |
| DB-16 | `get_plan_from_profile()` retorna `'free_trial'` quando NULL | Unit |
| SYS-02 | Apenas `AsyncPNCPClient`; `import requests` removido; testes passam | Unit + grep |
| SYS-03 | `_build_conservative_prompt(setor_id="alimentos")` -> "Alimentos", nao "Vestuario" | Unit |
| SYS-07 | `grep "time.sleep" quota.py` = 0; asyncio.sleep no retry | Unit + grep |
| SYS-10 | `mypy backend/` no CI; backend-ci.yml inclui step | CI verify |
| FE-01/02 | `SearchFormProps`/`SearchResultsProps` removidas; 0 props via Context | Code review + tsc |
| FE-03 | `useSearchFilters.ts` < 100 linhas; 4+ sub-hooks; reducer puro | Unit tests |
| FE-04 | `quarantine/` vazio; 22 arquivos no CI | CI green |
| FE-08 | `error.tsx` usa CSS var definida; botao visivel light+dark | Visual + CSS audit |
| UX-03 | `/planos` sem "9.6"; mostra "2 meses gratis" ou "economize R$ X" | E2E text search |
| A11Y-01 | Tab cicla DENTRO do modal; Shift+Tab tambem | E2E accessibility |
| A11Y-02 | Modais com `role="dialog"` + `aria-modal="true"` | E2E DOM inspection |

---

## 7. Metricas de Qualidade

### Alvos por Sprint

| Metrica | Atual | Pos-Sprint 0 | Pos-Sprint 1 | Pos-Sprint 3 |
|---------|-------|-------------|-------------|-------------|
| Backend test coverage | 96.69% | 96.69% | 97%+ | 97%+ |
| Frontend test coverage | 49.46% | 49.46% | 52%+ | 60%+ (threshold) |
| Quarantined test files | 22 | 22 | 22 | 0 |
| CRITICAL debitos | 3 | 0 | 0 | 0 |
| HIGH debitos | 14 | 10 | 4 | 2 |
| RLS vulnerabilities | 2 | 0 | 0 | 0 |
| P0 items abertos | 8 | 0 | 0 | 0 |
| Lighthouse LCP (busca) | TBD | TBD | TBD | < 2.5s |
| Initial JS bundle | TBD | TBD | TBD | < 200KB |

### Quality Gates para CI/CD

| Gate | Threshold | Status Atual | Apos Plano |
|------|-----------|-------------|-----------|
| Backend coverage (pytest --cov) | 70% | 96.69% PASS | PASS |
| Frontend coverage (jest --coverage) | 60% | 49.46% FAIL | PASS (Sprint 3) |
| Backend linting (ruff) | 0 errors | PASS (backend-ci.yml) | PASS |
| Backend type checking (mypy) | -- | NOT CONFIGURED | PASS (Sprint 1) |
| E2E tests (Playwright) | 0 failures | PASS | PASS |
| npm audit (high/critical) | 0 | NOT CONFIGURED | PASS (Sprint 2) |

---

## 8. Itens Fora de Escopo

Os seguintes topicos foram identificados mas estao **explicitamente fora do escopo** deste assessment. Documentados aqui para transparencia (R-10).

| # | Topico | Justificativa | Quando Enderecar |
|---|--------|---------------|-----------------|
| OOS-01 | **Backup e recuperacao de dados** -- Frequencia de backup Supabase, RTO/RPO, procedimento de recuperacao | Infraestrutura/DevOps, nao debito de codigo | Plano de disaster recovery separado |
| OOS-02 | **Configuracao detalhada do Sentry** -- Amostragem de traces, source maps frontend, alertas | Observabilidade operacional | Sprint de observabilidade dedicado |
| OOS-03 | **`npm audit` no CI do frontend** -- Nenhum workflow roda `npm audit`. `dependabot-auto-merge.yml` existe mas nao substitui scan ativo. | Seguranca de dependencias. SEC-T08 adicionado nos testes requeridos. | Estabilizacao de CI pipeline |
| OOS-04 | **Rate limiting por usuario autenticado** -- Rate limiting global existe, mas nao per-user alem da quota mensal. | Protecao adequada para POC com rate limiter global + quota mensal. | Escalar para >1000 usuarios |
| OOS-05 | **E2E tests para fluxos de billing** -- Nenhum teste E2E cobre Stripe checkout, payment success, subscription management. | Requer infraestrutura de Stripe test mode. | Sprint de testes de billing |
| OOS-06 | **Migration squash** -- 26 migrations acumuladas. DB specialist recomenda NAO squashar ate v1.0 ou >50 migrations. | Valor documental das migrations supera custo. | Apos v1.0 milestone |

---

## 9. Pontos Positivos a Preservar

Aspectos de qualidade destacados pelos especialistas que DEVEM ser preservados durante resolucao de debitos. PRs que degradem estes items requerem justificativa explicita.

### Backend/Arquitetura (14 items)

1. Route decomposition (STORY-202) em 14 route modules
2. Pipeline de busca em 7 stages com error handling independente por stage
3. Circuit breaker com degraded mode (8 falhas / 120s cooldown)
4. Fetch paralelo de UFs com asyncio.Semaphore para controle de concorrencia
5. Health canary probe antes de busca completa
6. Auto-retry de UFs falhas com 5s delay
7. Filtragem fail-fast sequencial (filtros mais baratos primeiro)
8. LLM Arbiter pattern (auto-accept/reject + LLM para ambiguos)
9. Fallback de subscription multi-camada (4 camadas, "fail to last known plan")
10. Mascaramento de PII em logs (log_sanitizer.py) + Sentry scrubbing
11. Idempotencia de webhook Stripe via tabela `stripe_webhook_events`
12. Correlation ID middleware para distributed tracing
13. Headers de depreciacao RFC 8594 em rotas legadas
14. Structured JSON logging com python-json-logger

### Database (9 items)

15. Funcoes atomicas de quota com `SELECT ... FOR UPDATE` (prevencao de race condition)
16. 100% RLS coverage em todas as 14 tabelas
17. Evolucao de schema via migrations documentadas (26 migrations com STORY references)
18. Partial indexes para patterns de query comuns
19. GIN trigram index para busca de email no admin
20. Automacao de retencao via pg_cron (3 jobs staggered)
21. Audit logging privacy-first com PII hashed em SHA-256
22. Trigger de auto-limitacao do search cache (max 5 por usuario)
23. Funcoes RPC eliminando N+1 queries (conversations, analytics)

### Frontend (11 items)

24. Design system completo com CSS custom properties e ratios WCAG documentados
25. Dark/light mode com prevencao de FOUC (inline script)
26. Skip navigation link (WCAG 2.4.1) e focus-visible (WCAG 2.2 AAA)
27. `prefers-reduced-motion` respeitado globalmente
28. SSE real-time progress com grid de status per-UF
29. Keyboard shortcuts (Ctrl+K, Ctrl+A, Escape)
30. Client-side search retry (2 retries com delays 3s/8s)
31. LGPD compliance: Cookie consent banner, data export, account deletion
32. Persistencia de estado de busca para recuperacao apos auth
33. Componentes de resiliencia UX (CacheBanner, DegradationBanner, PartialResultsPrompt)
34. 14 E2E Playwright specs cobrindo fluxos criticos de usuario

---

## 10. Changelog vs DRAFT

### Items Removidos (2)

| ID | Descricao | Razao | Removido por |
|----|-----------|-------|-------------|
| FE-20 | CSS class `sr-only` hardcoded inline em layout.tsx | Falso positivo: `sr-only` e uso correto de Tailwind utility | @ux-design-expert |
| FE-21 | `dangerouslySetInnerHTML` para theme script | Falso positivo: tecnica documentada e necessaria para FOUC prevention | @ux-design-expert |

### Items Adicionados (8 liquidos)

| ID | Descricao | Severidade | Horas | Adicionado por |
|----|-----------|-----------|-------|---------------|
| DB-15 | admin.py CreateUserRequest default "free" | MEDIUM | 0.5h | @data-engineer |
| DB-16 | quota.py fallback "free" (mitigado por mapping) | LOW | 0.25h | @data-engineer |
| DB-17 | top-dimensions sem date filter | MEDIUM | 4h | @data-engineer |
| UX-NEW-03 | Admin window.confirm() nativo | MEDIUM | 2h | @ux-design-expert |
| UX-NEW-04 | Pipeline sem empty state | LOW | 2h | @ux-design-expert |
| UX-NEW-05 | Pipeline tablet scroll | MEDIUM | 2h | @ux-design-expert |
| SYS-24 | email_service.py time.sleep | LOW | 1h | @qa |
| -- | UX-NEW-01 subsumido em A11Y-01+02 | -- | 0h | @qa (R-04) |
| -- | UX-NEW-02 subsumido em UX-03 | -- | 0h | @qa (R-04) |

### Mudancas de Severidade (14)

| ID | Original | Final | Razao | Alterado por |
|----|----------|-------|-------|-------------|
| DB-01 | CRITICAL | **MEDIUM** | Backend handles sync manualmente; trigger e dead code | @data-engineer |
| DB-06 | MEDIUM | **CRITICAL** | Bloqueia fallback profile creation | @data-engineer |
| DB-08 | MEDIUM | **LOW** | Adequado para POC; migration 021 documenta | @data-engineer |
| DB-10 | MEDIUM | **LOW** | Max-5-per-user trigger mitiga; 1.25GB a 5K users | @data-engineer |
| FE-08 | MEDIUM | **HIGH** | Botao invisivel na pagina de erro (CR-08) | @ux-design-expert |
| UX-03 | MEDIUM | **HIGH** | "9.6" confuso em info financeira; confianca | @ux-design-expert |
| FE-17 | LOW | **MEDIUM** | Drift de precos entre arquivos | @ux-design-expert |
| IC-06 | LOW | **MEDIUM** | Traducao de erros inconsistente | @ux-design-expert |
| MF-01 | LOW | **MEDIUM** | Perda de resultados sem aviso, frustrante | @ux-design-expert |
| A11Y-08 | LOW | **MEDIUM** | aria-label generico pior que nada | @ux-design-expert |
| A11Y-04 | MEDIUM | **LOW** | Mobile-only com alternativa | @ux-design-expert |
| UX-05 | MEDIUM | **LOW** | Admin usada por 1-2 pessoas | @ux-design-expert |
| SYS-03 | CRITICAL | **LOW** | Parcialmente resolvido por STORY-251 | @qa |
| SYS-11 | MEDIUM | **HIGH** | 1318 linhas; bloqueia correcoes de pipeline | @qa |

### Mudancas de Estimativa (12)

| ID | Original | Final | Razao |
|----|----------|-------|-------|
| DB-01 | 4h | 2h | Downgrade de severidade |
| DB-03 | 2h | 1h | Single policy change |
| DB-04 | 2h | 1h | Same pattern |
| DB-06 | 1h | 0.5h | One-line fix |
| SYS-03 | 8h | 1h | Parcialmente resolvido |
| SYS-10 | 4h | 2h | Ruff ja ativo |
| FE-01+02+03 | 48h | 32h | Trabalho compartilhado (Context + useReducer) |
| A11Y-01+02 | 8h | 4h | Co-implementacao via Dialog primitive |
| FE-07 | 8h | 6h | Mecanico |
| UX-03 | 4h | 2h | Copy change |
| IC-06 | 8h | 4h | Pattern de dicionario |
| FE-05 | 8h | 6h | Migracao mecanica lucide-react |
| UX-05 | 8h | 2h | Scope reduzido |

### Correcoes Factuais (3)

| Item | Antes | Depois | Verificacao |
|------|-------|--------|------------|
| FE-04 | "17 test files quarantined" | "22 test files quarantined" | `find frontend/__tests__/quarantine/ -name "*.test.*"` |
| SYS-10 | "No backend linting in CI" | "mypy not in CI (ruff already active)" | `backend-ci.yml` linhas 33-36 |
| SYS-03 | "LLM Arbiter hardcoded sector" | "Partially resolved by STORY-251" | `llm_arbiter.py` linhas 45-109 dynamic lookup |

### Esforco Total

| Fase | DRAFT | Final | Delta |
|------|-------|-------|-------|
| Sistema | ~155h | ~143h | -12h |
| Database | ~39h | ~23h | -16h |
| Frontend/UX | ~218h | ~194h | -24h |
| **Total** | **~412h** | **~360h** | **-52h (-13%)** |

---

## Apendice A: Items Deduplicados

| Item nos Documentos Fonte | ID Consolidado | Notas |
|---------------------------|----------------|-------|
| system-arch TD-C01 + frontend-spec TD-04 | SYS-01 + FE-04 | Split: SYS-01 = coverage gap, FE-04 = quarantine |
| system-arch TD-H02 + DB-AUDIT TD-11 | SYS-23 / DB-12 | Cross-reference mantida |
| DB-AUDIT SEC-01 + SCHEMA pipeline_items RLS | DB-03 | Audit mais detalhado |
| DB-AUDIT SEC-02 + SCHEMA cache RLS | DB-04 | Audit mais detalhado |
| DB-AUDIT INTEGRITY-04 + system usage | DB-06 | Backend code + DB constraint |
| frontend-spec A-10 + TD-08 | FE-08 | Acessibilidade + visual = mesma root cause |
| frontend-spec UX-03 + A-01 | A11Y-01 | Mesma issue subjacente |
| frontend-spec IC-03 ~ TD-05 | FE-05 + IC-03 | Relacionados mas distintos |
| system-arch TD-H06 = frontend observation | SYS-08 | Cross-cutting |
| UX-NEW-01 + A11Y-01+A11Y-02 | A11Y-01+A11Y-02 | UX-NEW-01 subsumido (R-04) |
| UX-NEW-02 + UX-03 | UX-03 | UX-NEW-02 subsumido (R-04) |

## Apendice B: Queries de Verificacao em Producao

### Pre-Deployment (executar ANTES da migration 027)

```sql
-- V1: Coluna status existe em user_subscriptions?
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'user_subscriptions'
  AND column_name = 'status';
-- Esperado: 0 rows (ausente) ou 1 row (adicionada manualmente)

-- V2: Default de profiles.plan_type?
SELECT column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'profiles'
  AND column_name = 'plan_type';
-- Esperado: 'free'::text (nao corrigido) ou 'free_trial'::text (corrigido)

-- V3: Profiles com plan_type invalido?
SELECT plan_type, COUNT(*) FROM profiles GROUP BY plan_type ORDER BY count DESC;

-- V4: Criacoes recentes (signups funcionam?)
SELECT id, email, plan_type, created_at
FROM profiles ORDER BY created_at DESC LIMIT 10;

-- V5: Trigger de sync ativo?
SELECT tgname, tgenabled FROM pg_trigger
WHERE tgrelid = 'public.user_subscriptions'::regclass;
```

### Post-Deployment (executar APOS migration 027)

```sql
-- V6: RLS policies scoped por role
SELECT policyname, roles, cmd
FROM pg_policies
WHERE tablename IN ('pipeline_items', 'search_results_cache', 'stripe_webhook_events')
ORDER BY tablename, policyname;

-- V7: Column default atualizado
SELECT column_default FROM information_schema.columns
WHERE table_name = 'profiles' AND column_name = 'plan_type';
-- Esperado: 'free_trial'::text

-- V8: Teste de criacao de usuario
SELECT plan_type FROM profiles ORDER BY created_at DESC LIMIT 1;
-- Esperado: 'free_trial'
```

### Monitoramento (periodico)

```sql
-- V9: pg_cron saude
SELECT jobname, schedule, active FROM cron.job;
SELECT jobname, status, start_time, return_message
FROM cron.job_run_details ORDER BY start_time DESC LIMIT 20;

-- V10: Tamanho da tabela de cache
SELECT
  pg_size_pretty(pg_total_relation_size('search_results_cache')) as table_size,
  COUNT(*) as row_count, COUNT(DISTINCT user_id) as unique_users
FROM search_results_cache;

-- V11: Sessoes por usuario (urgencia DB-09)
SELECT
  AVG(cnt)::int as avg_sessions, MAX(cnt) as max_sessions,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY cnt) as p95
FROM (SELECT COUNT(*) as cnt FROM search_sessions GROUP BY user_id) s;

-- V12: Tamanho de tabelas
SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) as total_size,
  n_live_tup as rows
FROM pg_stat_user_tables WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(relid) DESC;
```

---

## Sign-off

| Reviewer | Role | Contribuicao | Data |
|----------|------|-------------|------|
| @architect (Helix) | Technical Architect | Phase 1 (system arch), Phase 4 (consolidation), Phase 8 (final) | 2026-02-15 |
| @data-engineer (Datum) | Database Specialist | Phase 2 (schema/audit), Phase 5 (review) | 2026-02-15 |
| @ux-design-expert (Pixel) | UX Specialist | Phase 3 (frontend spec), Phase 6 (review) | 2026-02-15 |
| @qa (Quinn) | Quality Assurance | Phase 7 (full review, cross-area risks, test requirements) | 2026-02-15 |

---

*Documento final consolidado por @architect (Helix) em 2026-02-15.*
*Brownfield Discovery Phase 8 -- Final Consolidation.*
*Incorpora revisoes de @data-engineer (Datum, Phase 5), @ux-design-expert (Pixel, Phase 6), @qa (Quinn, Phase 7).*
*Commit de referencia: `b80e64a` (branch `main`).*
*Proximo passo: Executive Summary Report (Phase 9) e Story Creation (Phase 10).*
