# QA Review - Technical Debt Assessment v2.0

**Reviewer:** @qa
**Date:** 2026-02-15
**Status:** Phase 7 of Brownfield Discovery
**Previous Review:** v1.0 (2026-02-11, commit `808cd05`) -- SUPERSEDED by this document
**Codebase Commit:** `b80e64a` (branch `main`)
**Input Documents:**
1. `docs/prd/technical-debt-DRAFT.md` v2.0 (82 debitos, ~412h)
2. `docs/reviews/db-specialist-review.md` v2.0 (3 severity changes, 3 new items, revised to 23h)
3. `docs/reviews/ux-specialist-review.md` v2.0 (6 upgrades, 3 downgrades, 2 removals, 5 new items, revised to ~194h)

**Verification Method:** Direct codebase inspection via grep/read of source files, cross-referencing between all 3 documents, and validation of factual claims against actual code.

---

## Gate Status: NEEDS WORK

O assessment e substancialmente completo e de alta qualidade, mas possui **3 inconsistencias factuais verificadas contra o codebase** que devem ser corrigidas antes da publicacao final, **1 item potencialmente ja resolvido** (SYS-03), e **lacunas em areas de seguranca e observabilidade** que requerem ao menos documentacao explicita de que estao fora de escopo. Apos correcoes pontuais (estimativa: 2-4h de revisao documental), o assessment pode ser promovido a versao final.

---

## 1. Gaps Identificados

### 1.1 Areas Nao Cobertas

**GAP-01: Seguranca de API -- ausencia de analise de rate limiting por usuario**

O sistema tem rate limiting global (`rate_limiter.py`, 51 arquivos referenciam rate limiting), mas o assessment nao analisa se existe rate limiting **por usuario autenticado** alem da quota mensal. Um usuario malicioso poderia disparar centenas de buscas simultaneas antes da quota ser decrementada (race condition window). Isso e particularmente relevante porque o backend faz chamadas externas ao PNCP API, amplificando o impacto.

**GAP-02: Seguranca de dependencias -- analise incompleta**

O `backend-ci.yml` inclui `safety check` (scan de vulnerabilidades de dependencias Python), mas o frontend nao tem equivalente (`npm audit` nao esta no CI). O DRAFT menciona `dependabot-auto-merge.yml` mas nao analisa se as dependencias estao atualizadas ou se ha CVEs conhecidos. Verificacao: existem 13 workflows em `.github/workflows/`, incluindo `codeql.yml` e `dependabot-auto-merge.yml`, mas nenhum roda `npm audit` no frontend.

**GAP-03: Observabilidade -- Sentry nao avaliado**

O assessment menciona "PII masking in logs" e "Sentry scrubbing" como pontos positivos (Apendice B, item 10), mas nao avalia a configuracao do Sentry em si. `config.py` referencia `SENTRY_DSN` como variavel recomendada (linha 524). Nao ha analise de: (a) se a amostragem de traces esta configurada, (b) se os source maps do frontend estao enviados ao Sentry, (c) se alertas estao configurados para os erros criticos identificados. Verificacao: apenas `main.py` e `config.py` referenciam Sentry no backend.

**GAP-04: Backup e recuperacao de dados -- nao mencionado**

Para um SaaS em producao com dados de clientes (pipelines, sessoes de busca, assinaturas Stripe), nao ha analise de: (a) frequencia de backup do Supabase, (b) RTO/RPO definidos, (c) procedimento de recuperacao testado.

**GAP-05: `email_service.py` nao avaliado**

`backend/email_service.py` usa `time.sleep()` sincronamente (linha 112) -- o mesmo anti-pattern identificado em SYS-07 para `quota.py`. Porem o email service nao aparece no assessment. Verificacao: `time.sleep` encontrado em `email_service.py:112`, `pncp_client.py` (6 ocorrencias no sync client), `quota.py:910`, `receita_federal_client.py:66`. O assessment so lista `quota.py`.

**GAP-06: `search_pipeline.py` cresceu significativamente**

O DRAFT lista SYS-11 como MEDIUM ("search_pipeline.py becoming god module"). Verificacao: o arquivo tem agora **1318 linhas** -- nao simplesmente "growing", ja e um monolito comparavel ao `main.py` pre-decomposicao (1959 linhas que motivaram STORY-202). A severidade pode estar subestimada. `pncp_client.py` tem 1584 linhas (o maior arquivo do backend). Juntos, representam 2902 linhas de logica core.

**GAP-07: Testes E2E para fluxos de billing**

Verificacao dos 12 spec files de E2E confirma que nao ha NENHUM teste para: Stripe checkout, payment success callback, subscription management (upgrade/downgrade/cancel), e webhook-driven plan changes. Este gap ja foi identificado na v1.0 desta review (GAP-09) e permanece aberto.

### 1.2 Debitos Sem Estimativa

Todos os 82 debitos do DRAFT possuem estimativas. Os 3 items novos do DB Review e os 5 items novos do UX Review tambem possuem. No entanto, ha **divergencias significativas entre estimativas** que precisam ser reconciliadas:

| Item | DRAFT (h) | DB Review (h) | UX Review (h) | Discrepancia |
|------|-----------|---------------|----------------|-------------|
| DB-01 | 4h | 2h | -- | DB Review rebaixou para 2h por downgrade de severidade (CRITICAL -> MEDIUM) |
| DB-03 | 2h | 1h | -- | DB Review reduziu para 1h (corretamente -- single policy change) |
| DB-04 | 2h | 1h | -- | DB Review reduziu para 1h (corretamente -- same pattern) |
| DB-06 | 1h | 0.5h | -- | DB Review reduziu para 0.5h (one-line fix) |
| A11Y-01+02 | 8h | -- | 4h | UX Review identifica co-implementation (shared dialog primitive) |
| FE-01+02+03 | 48h | -- | 32h | UX Review identifica trabalho compartilhado (React Context + useReducer) |
| FE-07 | 8h | -- | 6h | UX Review reduz por natureza mecanica (next/dynamic) |
| UX-03 | 4h | -- | 2h | UX Review reduz por ser apenas mudanca de copy/calculo display |
| IC-06 | 8h | -- | 4h | UX Review reduz com pattern de dicionario de erros |
| FE-05 | 8h | -- | 6h | UX Review reduz por migracao mecanica para lucide-react |

**Recomendacao:** Adotar as estimativas revisadas dos especialistas em todos os casos. Ambos os specialists demonstraram analise mais detalhada que o DRAFT original. Reducao total: ~38h.

### 1.3 Informacoes Faltantes

**IF-01: Verificacao de producao pendente para DB-01 e DB-02**

Ambos os documentos (DRAFT e DB Review) concordam que queries de verificacao devem ser executadas ANTES de criar a migration 027. Estas queries NAO foram executadas. O resultado determina:
- DB-01: Se a coluna `status` existe em `user_subscriptions`, a acao e documentar. Se nao existe, a acao e remover o trigger `trg_sync_profile_plan_type`.
- DB-02: Se o default de `profiles.plan_type` foi corrigido manualmente para `'free_trial'`, o risco e ZERO. Se permanece `'free'`, novos signups podem estar falhando AGORA.

**O escopo real de P0 nao pode ser definido sem estas verificacoes.** Recomendo executar as queries V1-V5 do DB Review como primeiro passo da Phase 8.

**IF-02: Contagem de arquivos quarantined diverge entre documentos**

- DRAFT (FE-04): "17 test files quarantined"
- UX Review (FE-04): "22 quarantined files, not 17 as stated"
- **Verificacao codebase:** `find frontend/__tests__/quarantine/ -name "*.test.*"` retorna **22 arquivos** (13 diretorios/pastas + 22 arquivos de teste)

A contagem correta e **22**. O DRAFT precisa ser atualizado. Isso impacta a estimativa de FE-04 (24h pode estar subestimada para 22 arquivos vs 17).

**IF-03: SYS-03 pode estar parcialmente resolvido por STORY-251**

O DRAFT lista SYS-03 como CRITICAL (8h): "LLM Arbiter hardcoded 'Vestuario e Uniformes' sector description applied to ALL 15 sectors." Porem, a analise do codigo atual revela:

1. `llm_arbiter.py` linhas 45-109: `_build_conservative_prompt()` implementa lookup dinamico de setor via `get_sector(setor_id)` -- **STORY-251** adicionou esta funcionalidade
2. `filter.py` linha 2331: passa `setor_id=setor` para `classify_contract_primary_match()` -- o setor ID e propagado
3. O prompt conservador (linhas 93-109) agora usa `config.description` e gera exemplos SIM/NAO a partir dos keywords/exclusions de cada setor

O que **permanece** como problema:
- `config.py` linhas 261-263 contem uma nota dizendo que o problema existe (nota obsoleta)
- `_build_standard_sector_prompt()` (linhas 112-123) e generica e NAO usa descricao do setor -- mas esta e a funcao de **fallback**, usada apenas quando `setor_id` nao e fornecido ou nao e encontrado

**Veredicto:** SYS-03 esta **parcialmente resolvido**. A severidade deveria cair de CRITICAL para LOW (apenas nota obsoleta em `config.py` e fallback generico). Esforco cai de 8h para ~1h (remover nota obsoleta + melhorar prompt de fallback).

**IF-04: SYS-10 parcialmente resolvido**

O DRAFT lista SYS-10 como HIGH (4h): "No backend linting enforcement in CI." Porem:

- **Verificacao:** `backend-ci.yml` linhas 33-36 **JA incluem** `ruff check .` no CI (step "Run linting")
- O que falta: `mypy` nao esta configurado em nenhum workflow
- O workflow `tests.yml` (principal) nao tem linting, mas `backend-ci.yml` tem

**Veredicto:** SYS-10 esta parcialmente resolvido. Descricao deve ser corrigida para "mypy not configured in CI" e esforco reduzido de 4h para 2h.

---

## 2. Riscos Cruzados

| # | Risco | Areas Afetadas | Probabilidade | Impacto | Mitigacao |
|---|-------|----------------|---------------|---------|-----------|
| CR-01 | **Migration 027 falha em producao** por conflito com estado real do banco (colunas adicionadas manualmente, triggers alterados fora de migrations) | DB, Backend | Media | CRITICAL | Executar queries V1-V5 do DB Review ANTES da migration. Preparar script de rollback. Aplicar primeiro em staging se disponivel. |
| CR-02 | **Refactor de prop drilling (FE-01/02/03) quebra testes existentes e E2E** ao alterar interfaces de componentes | Frontend (testes, E2E, componentes) | Alta | HIGH | Executar FE-01/02/03 APOS resolver parcialmente FE-04 (unquarantine de testes nao-dependentes). Cada fase do refactor deve ter testes green antes da proxima. |
| CR-03 | **Correcao de RLS (DB-03/04) bloqueia funcionalidade se backend nao usa service_role key em todas as queries** | DB, Backend | Baixa | HIGH | Auditar TODAS as queries do backend para `pipeline_items` e `search_results_cache`. Verificar que usam `supabase_client` com service_role key, nao anon key. Se alguma usa anon key, a correcao de RLS vai quebrar a funcionalidade. |
| CR-04 | **Eliminacao do sync client (SYS-02) quebra fallback de busca single-UF** se `PNCPLegacyAdapter.fetch()` e chamado em producao | Backend, PNCP Client | Media | HIGH | Verificar se `PNCPLegacyAdapter` e chamado em algum code path ativo. Se sim, migrar para async antes de remover sync. O pncp_client.py tem 1584 linhas -- a remocao do sync client (estimada ~785 linhas) e uma mudanca massiva. |
| CR-05 | **Atualizacao do `plan_type` default (DB-02) sem atualizar TODOS os code paths produz inconsistencia** | DB, Backend (`quota.py`, `admin.py`) | Media | CRITICAL | O DB Review identifica **4 code paths** que usam "free" invalido: DB-02 (column default), DB-06 (`quota.py` L790), DB-15 (`admin.py` L246), DB-16 (`quota.py` L522). Todos 4 devem ser corrigidos **atomicamente** -- corrigir parcialmente e pior que nao corrigir. |
| CR-06 | **Consolidacao de `handle_new_user()` trigger (DB-11) conflita com extensoes futuras** | DB, Frontend (signup), Backend | Baixa | MEDIUM | DB-11 deve ser feito APOS DB-02 e APOS validar que o fluxo de signup funciona com a nova default. Nao consolidar o trigger enquanto o signup nao estiver estavel. |
| CR-07 | **Dynamic imports (FE-07) causam loading spinners excessivos ou flash of unstyled content** | Frontend (UX, Performance) | Media | MEDIUM | Implementar skeletons adequados para cada componente lazy-loaded (recharts, @dnd-kit, shepherd.js). Testar com throttled connection (3G). O UX Review fornece pattern concreto (`{ ssr: false, loading: () => <ChartSkeleton /> }`). |
| CR-08 | **Error boundary (FE-08) e a unica forma de recuperacao para o usuario** -- botao invisivel bloqueia recuperacao | Frontend (error handling) | Baixa | CRITICAL | Verificado: `error.tsx` linha 67 usa `bg-[var(--brand-green)]` que **NAO esta definida** em `globals.css`. O botao renderiza sem background visivel. Este e o pior lugar para um CTA quebrado. Mover para P0. |
| CR-09 | **Mudanca de `time.sleep` para `asyncio.sleep` em `quota.py` (SYS-07) pode expor race condition** | Backend (async) | Baixa | MEDIUM | O `time.sleep(0.3)` atual bloqueia o event loop mas garante que nenhum outro coroutine interfere durante o retry. Ao mudar para `asyncio.sleep(0.3)`, outro coroutine pode executar durante o sleep, potencialmente alterando estado da sessao. Verificar se `save_search_session` depende de exclusao mutua. |
| CR-10 | **`search_pipeline.py` (1318 linhas) dificulta todas as correcoes de backend** | Backend (manutenibilidade) | Alta | MEDIUM | Qualquer correcao em stages do pipeline (filtro, enriquecimento, cache, Excel) requer navegar por 1318 linhas. A decomposicao (SYS-11) deveria ser elevada a HIGH e antecipada para antes dos refactors de backend, nao P3. |

---

## 3. Dependencias Validadas

### 3.1 Ordem de Resolucao

A ordem proposta no DRAFT (P0 -> P1 -> P2 -> P3) e **correta em principio**, com os seguintes ajustes necessarios baseados nas revisoes dos especialistas:

**P0 revisado (incorporando specialist reviews):**

| # | Item | Acao | Horas | Notas |
|---|------|------|-------|-------|
| 0 | **Verificar producao** | Executar queries V1-V5 do DB Review | 1h | PRE-REQUISITO absoluto. Determina escopo real de DB-01 e DB-02. |
| 1 | DB-02 + DB-06 + DB-16 | Backend code fixes + column default migration | 3h | 3 code paths com `"free"` invalido. Deploy backend ANTES de migration. |
| 2 | DB-03 + DB-04 | RLS fixes em migration 027 | 2h | Seguranca. Independente de DB-02. |
| 3 | FE-08 | Error boundary button fix | 0.5h | **Movido de P1 para P0** -- botao invisivel na pagina de erro (CR-08). |
| 4 | UX-03 + UX-NEW-02 | Pricing "9.6" display fix | 2h | Quick win, impacto direto em confianca do usuario. 5 ocorrencias em `planos/page.tsx`. |
| 5 | SYS-03 (reavaliar) | Verificar se STORY-251 resolveu | 1h | Se resolvido, apenas remover nota obsoleta. Se nao, manter como 8h. |

**Total P0 revisado:** ~9.5h (era 19h no DRAFT; reducao por reavaliacao de SYS-03 e estimativas ajustadas)

**P1 revisado:**

| # | Item | Acao | Horas | Notas |
|---|------|------|-------|-------|
| 6 | DB-05 | Webhook INSERT policy scope to service_role | 1h | Quick win. |
| 7 | DB-15 | Admin.py CreateUserRequest default | 0.5h | Depende de DB-02 estar feito. |
| 8 | DB-01 (part 2) | Documentar ou remover trigger baseado em verificacao | 1h | Depende de resultado das queries V1-V5. |
| 9 | A11Y-01 + A11Y-02 + UX-NEW-01 | Dialog primitive + focus trap | 4h | Co-implementation conforme UX Review. |
| 10 | UX-02 | Keyboard Escape conflict fix | 0h extra | Resolvido pela mesma infra de item 9. |
| 11 | SYS-07 | async sleep fix em quota.py | 2h | Atentar para CR-09 (race condition). |
| 12 | SYS-10 | Adicionar mypy ao CI | 2h | Ruff JA esta no backend-ci.yml (parcialmente resolvido). |

**Total P1 revisado:** ~10.5h (era 41h no DRAFT; reducao por estimativas ajustadas e itens movidos/corrigidos)

### 3.2 Dependencias Criticas

```
[PREREQUISITO: Queries V1-V5 de verificacao em producao]
        |
        v
DB-02 (column default) ---> DB-15 (admin.py) ---> DB-11 (trigger consolidation)
  |                                                        |
  +---> DB-06 (quota.py L790) ---> DB-16 (quota.py L522)  |
  |                                                        v
  +---> SYS-06 (legacy plan seeds) --- so apos DB-02 estavel
        |
        +---> DB-01 (status column decision)

DB-03 + DB-04 (RLS) --- independente de DB-02, paralelizavel
  |
  +---> DB-05 (webhook INSERT) -- mesma migration
  +---> DB-07 (FK standardization) -- migration seguinte
  +---> DB-14 (cache INSERT policy) -- apos DB-04

FE-04 (unquarantine) ---> SYS-01 (coverage 60%) ---> FE-09, FE-10, FE-11, FE-12
  |                                                     (testes de componentes)
  +---> FE-01+02+03 (refactor) -- NAO refatorar sem safety net de testes
           |
           +---> FE-07 (dynamic imports) -- apos refactor de componentes
           +---> FE-09 (SearchResults tests) -- apos refactor, nao antes

A11Y-01+02 (dialog) ---> UX-02 (Escape conflict) -- mesmo fix
                     +---> UX-NEW-03 (admin confirm) -- usa o Dialog component

SYS-02 (dual HTTP client) ---> SYS-20 + SYS-21 (cleanup)
                           ---> SYS-04 (progress scalability) -- precisa entender o client
```

### 3.3 Bloqueios Potenciais

**BLOQUEIO-01: Verificacao de producao (IF-01)**

Se as queries revelam que `plan_type` default ja foi corrigido manualmente, DB-02 se torna documentacao (1h). Se nao foi corrigido, e urgente (P0, 2h). **Esta incerteza bloqueia a definicao do escopo real de P0.**

Resolucao: Executar queries como primeiro passo da Phase 8.

**BLOQUEIO-02: Dependencia circular entre testes e refactor**

FE-04 (unquarantine) e requisito para SYS-01 (coverage). Porem, FE-01/02/03 (refactor) vai invalidar muitos dos testes existentes (especialmente os que testam `SearchFormProps` com 42 props). Se unquarantine ANTES do refactor, os testes serao novamente invalidados. Se refatorar ANTES de unquarantine, nao ha safety net.

**Resolucao recomendada (sequencia em 4 passos):**
1. Unquarantine testes que NAO dependem de SearchForm/SearchResults (AuthProvider, DashboardPage, MensagensPage, ContaPage, LicitacaoCard) -- ~8-10 dos 22 arquivos
2. Escrever testes E2E (Playwright) para comportamento externo de SearchResults (sobrevive ao refactor)
3. Executar refactor FE-01/02/03 (com E2E como safety net)
4. Escrever testes unitarios para a nova arquitetura (SearchContext, searchReducer, sub-hooks)

**BLOQUEIO-03: FE-09 timing relativo a FE-01/02/03**

O refactor de prop drilling vai mudar completamente `SearchResults.tsx` (de ~35 props para 0 props via Context). Escrever 16h de testes unitarios para SearchResults ANTES do refactor seria desperdicar 16h de trabalho. Escrever APOS significa que o componente mais visivel fica sem testes durante o refactor.

**Resolucao:** E2E Playwright para validacao de comportamento externo ANTES; testes unitarios APOS. Os E2E sobrevivem ao refactor porque testam output renderizado, nao estrutura interna.

---

## 4. Testes Requeridos

### 4.1 Testes de Seguranca

| # | Teste | Debito Relacionado | Tipo | Prioridade |
|---|-------|-------------------|------|-----------|
| SEC-T01 | Verificar que `pipeline_items` NAO permite SELECT cross-user via PostgREST com authenticated key | DB-03 | Integracao SQL | P0 |
| SEC-T02 | Verificar que `search_results_cache` NAO permite SELECT cross-user | DB-04 | Integracao SQL | P0 |
| SEC-T03 | Tentar INSERT em `pipeline_items` com `user_id` de outro usuario (deve falhar com RLS error) | DB-03 | Integracao SQL | P0 |
| SEC-T04 | Tentar INSERT em `stripe_webhook_events` com authenticated key (deve falhar) | DB-05 | Integracao SQL | P1 |
| SEC-T05 | Tentar INSERT em `stripe_webhook_events` com `id` nao-conformante a `'^evt_'` (deve falhar por CHECK) | DB-05 | Unitario | P1 |
| SEC-T06 | Verificar que CORS `allow_origins` nao inclui `*` em producao (verificar `config.py:get_cors_origins()`) | GAP-01 | Config audit | P2 |
| SEC-T07 | Verificar SecurityHeadersMiddleware inclui CSP, X-Frame-Options, X-Content-Type-Options | GAP-03 | Unitario | P2 |
| SEC-T08 | Verificar que nao ha `npm audit` com severidade high/critical no frontend | GAP-02 | CI | P2 |

### 4.2 Testes de Regressao

| # | Teste | Debito Relacionado | Tipo | Prioridade |
|---|-------|-------------------|------|-----------|
| REG-T01 | Novo usuario pode se cadastrar; profile criado com `plan_type = 'free_trial'` | DB-02 | E2E | P0 |
| REG-T02 | `_ensure_profile_exists()` cria profile valido com `plan_type = 'free_trial'` (mock Supabase) | DB-06 | Unitario | P0 |
| REG-T03 | Admin pode criar usuario via `/admin` sem erro de constraint de `plan_type` | DB-15 | Integracao | P1 |
| REG-T04 | Stripe webhooks (subscription_updated, subscription_deleted, invoice_paid) continuam processando apos correcao de RLS | DB-03/04/05 | Integracao | P0 |
| REG-T05 | Busca completa (multi-UF) funciona apos remocao do sync client (SYS-02) | SYS-02 | E2E | P1 |
| REG-T06 | SSE progress tracking funciona apos mudanca de `time.sleep` para `asyncio.sleep` | SYS-07 | Integracao | P1 |
| REG-T07 | `save_search_session` retry funciona com `asyncio.sleep` sem race condition | SYS-07 | Unitario | P1 |
| REG-T08 | Error boundary renderiza botao visivel em ambos os temas (light/dark) | FE-08 | E2E + Visual | P0 |
| REG-T09 | Pagina de pricing NAO mostra "9.6" em texto visivel; mostra "2 meses gratis" ou equivalente | UX-03 | E2E text assertion | P1 |
| REG-T10 | Modais (save search, keyboard help) mantem focus trap ativo (Tab nao escapa do modal) | A11Y-01/02 | E2E accessibility | P1 |
| REG-T11 | Escape fecha modal em vez de limpar selecao de UF | UX-02 | E2E interaction | P1 |
| REG-T12 | LLM arbiter usa descricao correta do setor (nao "Vestuario" generico) para setores != vestuario | SYS-03 | Unitario | P1 |
| REG-T13 | Dynamic imports carregam componentes corretamente com skeleton/loading state | FE-07 | E2E | P2 |
| REG-T14 | Navegacao para fora de `/buscar` com resultados ativos mostra confirmacao | MF-01 | E2E | P2 |

### 4.3 Testes de Performance

| # | Teste | Debito Relacionado | Tipo | Metrica Alvo |
|---|-------|-------------------|------|-------------|
| PERF-T01 | Analytics page load para usuario com 500+ sessions | DB-09/DB-17 | Load test | < 2s (P95) |
| PERF-T02 | Bundle size total apos dynamic imports (FE-07) | FE-07 | Build metric | Initial JS < 200KB |
| PERF-T03 | LCP da pagina de busca (first visit, cold cache) | FE-07 | Lighthouse | < 2.5s |
| PERF-T04 | Busca paralela de 5 UFs sem blocking do event loop | SYS-07 | Load test | Nenhum stall > 300ms em concurrent requests |
| PERF-T05 | Pipeline page carrega em < 3s com 50 items | UX-04 | E2E timing | < 3s |
| PERF-T06 | `search_pipeline.py` execucao completa (7 stages) com 500 items | SYS-11 | Benchmark | < 10s end-to-end |

### 4.4 Criterios de Aceite por Debito

| Debt ID | Criterio de Aceite | Tipo de Teste |
|---------|-------------------|---------------|
| DB-02 | `SELECT column_default ... WHERE column_name = 'plan_type'` retorna `'free_trial'::text`; novo signup cria profile com `plan_type = 'free_trial'` | SQL verify + E2E signup |
| DB-03 | `SELECT * FROM pipeline_items` com authenticated key (nao service_role) retorna SOMENTE items do usuario autenticado | SQL integration |
| DB-04 | `SELECT * FROM search_results_cache` com authenticated key retorna SOMENTE cache do usuario autenticado | SQL integration |
| DB-05 | `INSERT INTO stripe_webhook_events` com authenticated key FALHA com RLS violation | SQL integration |
| DB-06 | `_ensure_profile_exists()` chamado para usuario sem profile: profile criado com `plan_type = 'free_trial'`, busca funciona | Unit test (mock supabase) |
| DB-15 | Admin cria usuario sem especificar plan; profile criado com `plan_type = 'free_trial'` | Integration test |
| DB-16 | `get_plan_from_profile()` retorna `'free_trial'` quando `plan_type` e NULL no resultado | Unit test |
| SYS-02 | `pncp_client.py` contem apenas `AsyncPNCPClient`; `import requests` removido; classe `PNCPClient` (sync) removida; todos os testes passam | Unit tests + grep source |
| SYS-03 | `_build_conservative_prompt(setor_id="alimentos", ...)` gera prompt com descricao do setor "Alimentos", nao "Vestuario" | Unit test |
| SYS-07 | `grep "time.sleep" quota.py` retorna 0 resultados; `asyncio.sleep` usado no retry; `save_search_session` funciona sem blocking | Unit test + source grep |
| SYS-10 | `mypy backend/` roda no CI sem erros bloqueantes; `backend-ci.yml` inclui step de mypy | CI verification |
| FE-01/02 | `SearchFormProps` e `SearchResultsProps` interfaces removidas; componentes consomem Context diretamente; 0 props passadas de page.tsx | Code review + TypeScript `npx tsc --noEmit` |
| FE-03 | `useSearchFilters.ts` removido ou < 100 linhas; logica dividida em 4+ sub-hooks; reducer e pura funcao testavel | Unit tests do reducer |
| FE-04 | Diretorio `__tests__/quarantine/` vazio ou removido; todos os 22 arquivos rodam no CI | CI green + test count |
| FE-08 | `error.tsx` usa variavel CSS definida em `globals.css`; botao visivel em light E dark mode | Visual test + CSS audit |
| UX-03 | Pagina `/planos` NAO contem string "9.6" em texto visivel; exibe calculo claro ("2 meses gratis" ou "economize R$ X") | E2E text search (`page.getByText`) |
| A11Y-01 | Modal aberto: Tab key cicla entre elementos focaveis DENTRO do modal; Shift+Tab tambem; focus nao escapa para background | E2E accessibility test |
| A11Y-02 | Todos os modais tem `role="dialog"` e `aria-modal="true"` no DOM renderizado | E2E DOM inspection |
| UX-02 | Keyboard help modal aberto: Escape fecha o modal; UF selection permanece intacta | E2E interaction test |
| IC-06 | Erro HTTP 502/503 mostra mensagem em portugues ("Servico temporariamente indisponivel"), nao "Bad Gateway" | E2E error simulation |
| MF-01 | Navegacao para `/planos` com resultados de busca ativos mostra dialog de confirmacao | E2E interaction test |

---

## 5. Validacao dos Clusters de Trabalho (A-G)

### Cluster A: Database Security Sprint -- VALIDADO com ajustes

**Proposta original (DRAFT):** DB-02 + DB-03 + DB-04 + DB-05 + DB-06 + DB-07 (13h, single migration)

**Ajuste DB Review:** P0 = DB-02 + DB-03 + DB-04 + DB-06 (3.5h); DB-05 + DB-07 movidos para P1/P2

**Parecer QA:** Concordo com o DB Review. A migration 027 deve ser minima e focada nos items P0. DB-05 e DB-07 podem ir em migration 028. Adicionar: DB-15 e DB-16 (backend code fixes) devem ser deployados ANTES ou JUNTO com migration 027 para evitar window de inconsistencia (CR-05).

### Cluster B: Backend Correctness Quick Wins -- PRECISA REVISAO

**Proposta original:** SYS-03 + SYS-07 + SYS-14 + SYS-18 (12h)

**Parecer QA:** SYS-03 precisa ser reavaliado contra STORY-251. Se confirmado como parcialmente resolvido (IF-03), cluster B cai para ~5h (SYS-07 2h + SYS-14 2h + SYS-18 2h - overlap). Recomendo verificar SYS-03 como primeiro passo antes de alocar as 8h.

### Cluster C: CI/Quality Gates -- PARCIALMENTE RESOLVIDO

**Proposta original:** SYS-10 + FE-08 (8h)

**Parecer QA:** SYS-10 e parcialmente resolvido -- `ruff` ja esta no `backend-ci.yml` (IF-04). FE-08 e ~30 minutos de trabalho real (trocar uma variavel CSS). Cluster C real: ~2.5h (2h mypy + 0.5h FE-08). **Mover FE-08 para P0** (CR-08).

### Cluster D: Accessibility Sprint -- VALIDADO

**Proposta original:** A11Y-01 + A11Y-02 (8h)

**Ajuste UX Review:** 4h (co-implementation via Dialog primitive extraido de UpgradeModal)

**Parecer QA:** Concordo. Adicionar UX-02 (Escape conflict) e UX-NEW-01 ao mesmo cluster -- todos sao consequencia da mesma causa raiz (ausencia de Dialog primitive reutilizavel). O UX Review detalha que UpgradeModal.tsx JA implementa o pattern corretamente (linhas 34-51), faltando apenas focus trap (~30 linhas).

### Cluster E: PNCP Client Consolidation -- VALIDADO com alerta

**Proposta original:** SYS-02 + SYS-20 + SYS-21 (18h)

**Parecer QA:** Validado, mas com dois alertas:
1. Verificar se `PNCPLegacyAdapter.fetch()` e chamado em producao antes de remover o sync client (CR-04)
2. `pncp_client.py` tem 1584 linhas -- a remocao do sync client (~785 linhas) e uma mudanca massiva. Recomendo review detalhado e testes extensivos.

### Cluster F: Frontend Architecture Refactor -- VALIDADO com ajustes

**Proposta original:** FE-01 + FE-02 + FE-03 (48h somadas)

**Ajuste UX Review:** 32h (trabalho compartilhado via React Context + useReducer)

**Parecer QA:** Concordo com 32h. O UX Review fornece pattern detalhado (SearchContext, searchReducer, sub-hooks). Dependencia critica: FE-04 deve ser parcialmente resolvido ANTES (BLOQUEIO-02); FE-09 testes unitarios devem ser escritos APOS o refactor (BLOQUEIO-03). Testes E2E ANTES do refactor como safety net.

### Cluster G: Test Coverage Campaign -- VALIDADO com sequenciamento revisado

**Proposta original:** SYS-01 + FE-04 + FE-09 + FE-10 + FE-11 + FE-12 (80h)

**Parecer QA:** O total de 80h permanece, mas o sequenciamento e crucial para evitar desperdicio (BLOQUEIO-02 e BLOQUEIO-03):

| Fase | Acao | Horas | Pre-requisito |
|------|------|-------|--------------|
| G.1 | Unquarantine 10-12 testes NAO-dependentes de SearchForm/SearchResults | 8h | -- |
| G.2 | Escrever E2E Playwright para SearchResults (comportamento externo) | 8h | G.1 |
| G.3 | Executar Cluster F (refactor FE-01/02/03) | 32h | G.2 (E2E como safety net) |
| G.4 | Testes unitarios para nova arquitetura (SearchContext, reducer, sub-hooks) | 16h | G.3 |
| G.5 | FE-10 (pipeline), FE-11 (onboarding), FE-12 (middleware) | 16h | G.1 |

---

## 6. Validacao de Ajustes de Severidade dos Especialistas

### 6.1 Ajustes do DB Specialist

| Item | Ajuste | Veredicto QA | Justificativa |
|------|--------|-------------|--------------|
| DB-01 CRITICAL -> MEDIUM | **CONCORDO** | Analise convincente: backend handles sync manualmente via 3 webhook handlers. Trigger e redundante/dead code, nao crash. |
| DB-06 MEDIUM -> CRITICAL | **CONCORDO** | One-line fix mas impacto cascading: qualquer usuario sem profile fica bloqueado. Dois code paths independentes produzem `plan_type = 'free'` invalido. |
| DB-08 MEDIUM -> LOW | **CONCORDO** | POC com 3 planos. Migration 021 ja documenta instrucoes por environment. |
| DB-10 MEDIUM -> LOW | **CONCORDO** | Max-5-per-user trigger e boa mitigacao. Projecao: 1.25GB a 5000 usuarios. Monitoramento suficiente. |

### 6.2 Ajustes do UX Specialist

| Item | Ajuste | Veredicto QA | Justificativa |
|------|--------|-------------|--------------|
| FE-08 MEDIUM -> HIGH | **CONCORDO e ELEVO** | Deveria ser P0. Verificado: `bg-[var(--brand-green)]` NAO esta definida em `globals.css`. Botao invisivel na pagina de erro = usuario preso. |
| UX-03 MEDIUM -> HIGH | **CONCORDO** | Verificado: "12 meses pelo preco de 9.6" em `planos/page.tsx` linha 738. 5 ocorrencias de "9.6". Confunde usuarios e prejudica confianca. |
| FE-17 LOW -> MEDIUM | **CONCORDO** | `PLAN_HIERARCHY` em `planos/page.tsx` E `PLAN_CONFIGS` em `lib/plans.ts` = risco de drift de precos. |
| IC-06 LOW -> MEDIUM | **CONCORDO** | Login traduz erros ("E-mail ou senha incorretos"), mas busca mostra "502 Bad Gateway". Jarring. |
| MF-01 LOW -> MEDIUM | **CONCORDO** | Busca leva 15-60s. Perder resultado sem warning e frustrante. |
| A11Y-08 LOW -> MEDIUM | **CONCORDO** | `aria-label="Icone"` e pior que nada -- cria confusao para AT users. |
| A11Y-04 MEDIUM -> LOW | **CONCORDO** | Pull-to-refresh e mobile-only com alternativa (botao de busca). |
| UX-05 MEDIUM -> LOW | **CONCORDO** | Admin page usada por 1-2 pessoas. Horizontal scroll funciona. |
| FE-20 remover | **CONCORDO** | `sr-only` e uso correto de Tailwind utility. Nao e debito. |
| FE-21 remover | **CONCORDO** | `dangerouslySetInnerHTML` para FOUC prevention e padrao documentado e necessario. |

### 6.3 Itens Novos Adicionados -- Validacao

| Item | Specialist | Severidade | Veredicto QA |
|------|-----------|-----------|-------------|
| DB-15 | DB | MEDIUM | **CONCORDO.** Impacto secundario de DB-02. One-line fix apos DB-02. |
| DB-16 | DB | LOW | **CONCORDO.** Mitigado por `PLAN_TYPE_MAP` em `quota.py`. Defense-in-depth. |
| DB-17 | DB | MEDIUM | **CONCORDO.** Mesma classe de problema que DB-09 mas sem date filter. Combinar com DB-09 em mesmo fix. |
| UX-NEW-01 | UX | HIGH | **CONCORDO mas REDUNDANTE.** O UX Review diz "Co-fix with A11Y-01 and A11Y-02". Se co-fixado via Dialog primitive, UX-NEW-01 NAO e um item separado -- e a descricao detalhada do que A11Y-01+A11Y-02 significam na pratica. Recomendo: subsumir em A11Y-01+A11Y-02 para evitar double-counting de horas. |
| UX-NEW-02 | UX | HIGH | **CONCORDO mas SUBSET de UX-03.** O UX Review diz "This is a subset of UX-03." Recomendo: incorporar em UX-03 (nao contar horas separadamente). |
| UX-NEW-03 | UX | MEDIUM | **CONCORDO.** `window.confirm()` em acao destrutiva (delete user) e anti-pattern ja corrigido em outro lugar (FE-H04 -> toast system). |
| UX-NEW-04 | UX | LOW | **CONCORDO.** Empty state para pipeline e nice-to-have. |
| UX-NEW-05 | UX | MEDIUM | **CONCORDO.** 5 colunas em `flex gap-4` no tablet force scroll horizontal sem indicador. |

**Nota sobre double-counting:** UX-NEW-01 (3h) e UX-NEW-02 (1h) sao subsets de items existentes. Incorporando-os, o esforco liquido de novos items e 6h (UX-NEW-03: 2h + UX-NEW-04: 2h + UX-NEW-05: 2h), nao 10h.

---

## 7. Parecer Final

### Pontos Fortes do Assessment

1. **Cobertura abrangente.** 82+ items across 3 areas (sistema, database, frontend/UX) com priorizacao clara em 4 niveis (P0-P3). Os specialist reviews adicionaram 8 items genuinamente novos.

2. **Especialistas qualificados e rigorosos.** Ambos os reviews sao de alta qualidade:
   - DB Review: Reduziu esforco de 39h para 23h (-41%) com justificativas detalhadas por item. Respondeu todas as 7 perguntas com analise de codigo-fonte.
   - UX Review: Reduziu esforco de 218h para 194h (-11%) com patterns concretos de implementacao. Identificou 5 novos items e recomendou remocao de 2 falsos positivos.

3. **Grafo de dependencias.** O DRAFT inclui grafo explicito com clusters de trabalho (A-G), facilitando planejamento de sprints. Os clusters sao logicamente coerentes.

4. **Deduplicacao cuidadosa.** O Apendice A documenta 12 items que apareciam em multiplos documentos e foram consolidados com rastreabilidade.

5. **Pontos positivos preservados.** O Apendice B lista 34 aspectos de qualidade a preservar -- essencial para evitar regressoes durante resolucao de debitos.

6. **Queries de verificacao prontas.** O DB Review fornece SQL executavel para validar cada finding em producao, incluindo pre-deployment e post-deployment checks.

### Pontos de Atencao

1. **3 inconsistencias factuais verificadas no codebase:**
   - SYS-03 (LLM Arbiter) pode estar parcialmente resolvido por STORY-251
   - SYS-10 (linting CI) parcialmente resolvido -- ruff ja esta no backend-ci.yml
   - FE-04 contagem de quarantine: 22 arquivos, nao 17

2. **Verificacao de producao nao realizada.** DB-01 e DB-02 requerem queries no banco real. O escopo de P0 depende dos resultados. Se `plan_type` default ja foi corrigido manualmente, DB-02 e apenas documentacao.

3. **Double-counting em novos items.** UX-NEW-01 e subset de A11Y-01+A11Y-02. UX-NEW-02 e subset de UX-03. Contagem inflada se nao ajustada.

4. **`search_pipeline.py` (1318 linhas) subestimado.** O DRAFT classifica como MEDIUM (SYS-11). E o segundo maior arquivo do backend e absorveu complexidade da decomposicao de main.py. Considerar elevacao a HIGH.

5. **Gaps em seguranca e observabilidade.** Rate limiting por usuario, dependency scanning do frontend, configuracao de Sentry, e backup/recovery nao foram analisados.

6. **Estimativas otimistas.** O total revisado (~360h) assume execucao sem surpresas. Historicamente, debt resolution leva 1.3-1.5x a estimativa. Budget para ~470-540h seria mais realista.

### Recomendacoes Antes de Proceder a Phase 8

**Obrigatorias (bloqueantes para publicacao final):**

| # | Acao | Esforco | Impacto |
|---|------|---------|---------|
| R-01 | Executar queries V1-V5 do DB Review no banco de producao | 1h | Define escopo real de DB-01 e DB-02 |
| R-02 | Verificar se SYS-03 esta resolvido por STORY-251 (testar `_build_conservative_prompt` com setor != vestuario) | 0.5h | Pode remover 8h de trabalho de P0 |
| R-03 | Corrigir contagem de quarantine de 17 para 22 no DRAFT | 5min | Precisao factual |
| R-04 | Resolver double-counting de UX-NEW-01 e UX-NEW-02 (subsumir em items existentes) | 5min | Precisao de estimativas |

**Recomendadas (nao-bloqueantes mas importantes):**

| # | Acao | Esforco | Impacto |
|---|------|---------|---------|
| R-05 | Mover FE-08 para P0 (botao invisivel na pagina de erro) | 0h (reordenacao) | Quick win critico (30min de fix, alto impacto) |
| R-06 | Corrigir descricao de SYS-10 para "mypy not in CI" (ruff ja esta) | 5min | Precisao factual |
| R-07 | Adicionar `email_service.py` time.sleep como item (SYS-07 expandido ou SYS-24) | 5min | Completude |
| R-08 | Considerar elevar SYS-11 (search_pipeline.py, 1318 linhas) de MEDIUM para HIGH | N/A | Priorizacao |
| R-09 | Reconciliar estimativas usando valores revisados dos especialistas | 30min | Total cai de ~412h para ~360h |
| R-10 | Documentar que backup, Sentry config, e npm audit estao fora de escopo deste assessment | 10min | Transparencia sobre gaps |
| R-11 | Criar checklist de rollback para migration 027 | 1h | Safety net para P0 |

### Totais Revisados (apos incorporacao de specialist reviews e ajustes QA)

| Area | DRAFT Original | Apos Specialists | Apos QA Adjustments | Delta |
|------|---------------|------------------|---------------------|-------|
| Sistema (Backend/Infra) | ~155h | ~155h | ~147h | -8h (SYS-03 resolvido, SYS-10 parcial) |
| Database | ~39h | ~23h | ~23h | -16h |
| Frontend/UX | ~218h | ~194h | ~190h | -28h (double-counting) |
| **Total** | **~412h** | **~372h** | **~360h** | **-52h (-13%)** |

---

*Review completado por @qa em 2026-02-15.*
*Todos os achados validados contra o codebase no commit `b80e64a` (branch `main`).*
*Verificacoes de codebase realizadas:*
*- Quarantine count: 22 arquivos (nao 17 como no DRAFT)*
*- SYS-03: STORY-251 adicionou lookup dinamico de setor em `llm_arbiter.py` (parcialmente resolvido)*
*- SYS-10: `ruff check .` ja configurado em `backend-ci.yml` linhas 33-36*
*- FE-08: `bg-[var(--brand-green)]` confirmado ausente em `globals.css`*
*- UX-03: "9.6" confirmado em 5 locais em `planos/page.tsx`*
*- SYS-07: `time.sleep(0.3)` confirmado em `quota.py` linha 910*
*- search_pipeline.py: 1318 linhas (SYS-11)*
*- pncp_client.py: 1584 linhas (SYS-02)*
*- email_service.py: `time.sleep` em linha 112 (nao coberto pelo assessment)*
*Documentos de entrada analisados: 3 (DRAFT v2.0 + DB specialist review v2.0 + UX specialist review v2.0).*
*Esta review substitui a v1.0 (2026-02-11) integralmente.*
