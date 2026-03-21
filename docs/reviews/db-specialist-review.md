# Database Specialist Review
**Reviewer:** @data-engineer
**Date:** 2026-03-20
**DRAFT Reviewed:** docs/prd/technical-debt-DRAFT.md (Brownfield Discovery Phase 4 output)
**Supersedes:** db-specialist-review.md v2.0 (2026-03-12 GTM Readiness)

---

## Debitos Validados

| ID | Debito | Sev. Original | Sev. Ajustada | Horas | Complexidade | Notas |
|----|--------|:---:|:---:|:---:|:---:|-------|
| DB-01 | Stripe price IDs hardcoded em migrations | CRITICAL | CRITICAL | 3h | media | Confirmado: 5 migration files contem `price_1*` IDs. Estimativa ajustada 2h->3h porque alem de mover para config table, precisa atualizar fresh-install seed script. Ver analise completa nas respostas Q1. |
| DB-02 | `handle_new_user()` omite `trial_expires_at` | HIGH | HIGH | 1.5h | simples | Confirmado: migration `20260225110000` insere 10 colunas sem `trial_expires_at`. `quota.py` compensa (linhas ~428-439) calculando a partir de `created_at`. Risco real e baixo porque o fallback funciona, mas e uma dependencia implicita. Estimativa reduzida porque e um ALTER FUNCTION simples. |
| DB-03 | `get_conversations_with_unread_count()` COUNT(*) OVER() | HIGH | **MEDIUM** | 3h | media | Confirmado: migration 019 linha 28 usa `COUNT(*) OVER()` dentro da CTE antes de LIMIT/OFFSET. POREM: `conversations` e uma tabela de baixo volume (sistema de mensagens admin<->user, nao user-to-user chat). Em producao com <100 usuarios beta, provavelmente <500 rows. Downgrade para MEDIUM porque o impacto real e negligenciavel no estagio atual. Revisitar quando ultrapassar 5000 conversations. |
| DB-04 | `profiles.plan_type` sem reconciliacao | HIGH | **MEDIUM** | 1h | simples | Parcialmente invalido. O `stripe_reconciliation.py` JA sincroniza `profiles.plan_type` (linhas 225-231, 261-263, 385-389). O reconciliation job roda diariamente via cron. O que falta e uma METRICA de drift (contagem de correcoes por tipo) -- nao a reconciliacao em si. Reclassificado como MEDIUM, 1h para adicionar counter. |
| DB-05 | `partner_referrals` orfaos acumulam | HIGH | **LOW** | 0.5h | simples | Confirmado: nao ha pg_cron para partner_referrals. Porem, o volume e minimo (<50 rows em producao, pre-revenue). Risco de crescimento sem bound e teorico -- na pratica, acumula 1-2 orfaos/mes. Downgrade para LOW. Quick cron job quando escalar. |
| DB-06 | `user_subscriptions` sem retention | HIGH | HIGH | 1h | simples | Confirmado: sem pg_cron. Diferente de DB-05, cada mudanca de plano/billing cria nova row. Com dunning retries (past_due->active->past_due), pode acumular 5-10 rows/user/mes em cenarios de pagamento problematico. Manter HIGH. |
| DB-08 | `search_state_transitions.user_id` nullable | MEDIUM | MEDIUM | 1h | simples | Confirmado. Depende de verificacao em producao se existem rows com NULL user_id apos backfill. |
| DB-09 | `classification_feedback` FK ordering | MEDIUM | **LOW** | 0.5h | simples | Confirmado: DEBT-002 cria com `auth.users(id)`, DEBT-113 re-aponta para `profiles(id)`. Em fresh install, ambas migrations rodam em sequencia -- o re-apontamento e imediato. O unico cenario problematico e se DEBT-113 falhar em fresh install, o que e detectavel via CI. Downgrade para LOW. |
| DB-10 | System cache warmer em `auth.users` | MEDIUM | MEDIUM | 0.5h | simples | Confirmado. Estimativa reduzida: e um WHERE clause em admin queries. |
| DB-11 | OAuth tokens no public schema | MEDIUM | MEDIUM | 2h | media | Confirmado. Padrao industria (app-layer encryption). Nao ha acao imediata alem de documentar e verificar key rotation policy. |
| DB-12 | Tres convencoes de nomes para migrations | MEDIUM | **LOW** | 0h | - | Reclassificado para LOW com 0h de esforco. Nao recomendo migration squash neste estagio (ver resposta Q5). O custo-beneficio e negativo. |
| DB-13 | Sem down migrations | MEDIUM | MEDIUM | 2h | media | Confirmado. Recomendo criar rollback SQL apenas para migrations de billing e RLS. |
| DB-14 | `cleanup_search_cache_per_user()` COUNT a cada INSERT | MEDIUM | **LOW** | 0h | - | Confirmado o trigger, mas o short-circuit (<=5 early return) e um index scan em `user_id` que retorna em <1ms. O overhead por INSERT e negligenciavel. Nao vale o esforco de otimizar. |
| DB-15 | `alert_sent_items` retention scan | MEDIUM | **LOW** | 0h | - | `idx_alert_sent_items_sent_at` cobre o `DELETE WHERE sent_at < X`. Nao e full scan -- e index scan. Falso alarme no DRAFT. |
| DB-17 | `organizations.plan_type` CHECK permissivo | MEDIUM | MEDIUM | 0.5h | simples | Confirmado. CHECK permite 13 valores incluindo legacy. Facil de apertar. |
| DB-18 | `stripe_price_id` deprecated | LOW | LOW | 1h | simples | Confirmado: `routes/billing.py` linha 98-111 ainda faz SELECT da coluna em `plan_billing_periods` (NAO `plans`). A coluna deprecated em `plans` nao e mais usada como fallback (DEBT-114 removeu). Pode dropar a coluna em `plans` com seguranca. |
| DB-19 | `created_at` nullable inconsistente | LOW | LOW | 0.5h | simples | Confirmado. Estimativa reduzida: 2 ALTER TABLEs simples. |
| DB-21 | `trial_email_log` sem policy explicita | LOW | LOW | 0.5h | simples | Confirmado. service_role bypassa RLS, entao funciona. Apenas documentacao. |
| DB-22 | Org admins sem UPDATE | LOW | LOW | 0.5h | simples | Confirmado. Backend handles writes via service role. Nao e problema real. |
| DB-23 | Migration 027b superseded | LOW | LOW | 0h | - | Aceitar como esta. IF NOT EXISTS garante idempotencia. |
| DB-24 | Legacy `backend/migrations/` | LOW | LOW | 0.5h | simples | Confirmado. Adicionar DEPRECATED.md e suficiente. |
| DB-25 | Constraint names inconsistentes | LOW | LOW | 0h | - | Cosmetico. Enforce convention going forward. |
| DB-26 | Trigger names inconsistentes | LOW | LOW | 0h | - | Cosmetico. Enforce convention going forward. |
| DB-27 | `pipeline_items.search_id` TEXT vs UUID | LOW | LOW | 0.5h | simples | Confirmado: migration `20260315100000` define como TEXT. Na pratica, UUID auto-casts para TEXT em comparacoes. FK nao e necessaria (pipeline items podem sobreviver a delecao de search sessions). |

---

## Debitos Adicionados

### DB-28: `conversations` Correlated Subquery per Row (MEDIUM, 2h)

**Finding:** Em `get_conversations_with_unread_count()`, o `unread_count` e calculado via correlated subquery (linhas 46-53 da migration 019): `SELECT COUNT(*) FROM messages m WHERE m.conversation_id = fc.id AND ...`. Isso executa uma query por conversation na pagina. Com page_size=50, sao 50 subqueries.

**Impact:** Combinado com o COUNT(*) OVER() (DB-03), esta funcao tem dois problemas de performance. O correlated subquery e o mais impactante dos dois para uso diario, enquanto COUNT(*) OVER() so importa em volumes altos.

**Fix:** Substituir por LEFT JOIN com GROUP BY na CTE, ou usar lateral join. Agrupar com DB-03 na mesma rewrite.

### DB-29: `monthly_quota` Sem Retention (LOW, 0.5h)

**Finding:** `monthly_quota` cria uma row por user por mes (formato "YYYY-MM"). Nao ha pg_cron cleanup. Em 2 anos com 1000 usuarios, acumula 24,000 rows.

**Impact:** Baixo. Tabela e pequena por row. Mas e inconsistente com a politica de retention aplicada a outras tabelas.

**Fix:** Adicionar retention de 24 meses, alinhado com `user_subscriptions`.

### DB-30: `search_results_store` e `search_results_cache` JSONB Sem Versionamento (MEDIUM, 4h)

**Finding:** Ambas tabelas armazenam resultados de busca como JSONB em colunas `results` / `raw_results`. Nao ha CHECK constraint ou validation trigger que garanta a estrutura do JSON. Se o formato dos resultados mudar (ex: nova versao da API PNCP), dados antigos e novos coexistem sem versionamento.

**Impact:** Queries que assumem campos especificos no JSONB (ex: `results->>'valor_estimado'`) falham silenciosamente se o campo estiver ausente em rows antigas. O backend compensa com `.get()` + defaults, mas o schema nao garante nada.

**Fix:** Adicionar coluna `schema_version INTEGER DEFAULT 1` para versionamento de formato. Nao recomendo CHECK constraint em JSONB (caro demais em writes).

### DB-31: `profiles.plan_type` CHECK Nao Escala para Novos Planos (MEDIUM, 0.5h)

**Finding:** O CHECK em `profiles.plan_type` permite: `'free_trial','consultor_agil','maquina','sala_guerra','master','smartlic_pro','consultoria'`. Se um novo plano for criado (ex: `'enterprise'`), o INSERT falhara com CHECK violation. A tabela `plans` e a source of truth, mas `profiles.plan_type` tem CHECK hardcoded.

**Impact:** Adicionar novo plano requer migration para alterar CHECK. Nao bloqueia hoje, mas e uma armadilha para o futuro.

**Fix:** Aceitar e documentar que novo plano = nova migration. Alternativa futura: substituir CHECK por FK para `plans(id)`.

---

## Falsos Positivos Removidos

### DB-07: Verificar `reconciliation_log` policy em producao

**Motivo da remocao:** Migration TD-003 (`20260304200000`) ja corrigiu o pattern `auth.role()` para `TO service_role`. DEBT-113 (`20260311100000`) inclui runtime assertion que verificou em producao. Este item ja foi resolvido. Verificacao adicional nao e necessaria -- as migrations sao a prova.

### DB-16: `search_state_transitions.search_id` sem FK (by design)

**Motivo da remocao:** Nao e debito tecnico -- e uma decisao arquitetural documentada. `search_sessions.search_id` e nullable e nao-unico (retries compartilham IDs). FK requer a coluna referenciada ser UNIQUE, o que nao e o caso. Alem disso, a tabela e audit trail com retention de 30 dias. Manter sem FK e a decisao correta.

### DB-20: Indexes sobrepostos em `search_sessions`

**Motivo da remocao:** Migration `20260309200000` (DEBT-100 AC10) JA aborda isso. O `DO $$ ... END $$` block verifica `pg_stat_user_indexes.idx_scan` e dropa `idx_search_sessions_user` se scan_count=0. O DRAFT reporta como pendente algo que ja tem um fix condicional implementado. Note: `idx_search_sessions_user_id` (criado em DEBT-001) pode ser diferente de `idx_search_sessions_user` -- verificar em producao se ambos existem, mas o mecanismo de cleanup esta in place.

---

## Analise de Dependencias (DB)

### Cadeia 1: Billing Integrity
```
DB-01 (Stripe IDs em migrations) -- independente, P0
    |
    v
DB-18 (drop deprecated stripe_price_id column)
    |
    v  (somente apos confirmar que nenhum code path usa plans.stripe_price_id)
DB-31 (plan_type CHECK vs plans FK) -- futuro, pode aguardar
```

### Cadeia 2: Retention Jobs
```
DB-06 (user_subscriptions retention) -- independente
DB-05 (partner_referrals retention) -- independente
DB-29 (monthly_quota retention) -- independente
  |
  todos podem ser implementados em paralelo numa unica migration
```

### Cadeia 3: Schema Integrity
```
DB-02 (handle_new_user + trial_expires_at)
    |
    v  (mesma migration)
DB-08 (search_state_transitions.user_id NOT NULL)
    |
    v  (mesma migration)
DB-19 (created_at NOT NULL fixes)
```

### Cadeia 4: Performance
```
DB-03 (COUNT(*) OVER()) + DB-28 (correlated subquery)
    |
    implementar juntos como rewrite de get_conversations_with_unread_count()
```

### Items Independentes (sem dependencias)
- DB-10, DB-11, DB-13, DB-17, DB-21, DB-22, DB-24, DB-27, DB-30

---

## Respostas ao Architect

### Q1: SEC-01 (DB-01) -- Stripe price IDs: env vars, config table, ou ambos?

**Recomendacao: Config table (`plan_billing_periods`) + seed via env vars.**

- As migrations ja aplicadas em producao NAO re-executam, entao nao ha risco de break em rollback. Os IDs hardcoded ficam como historia inerte no git.
- Para fresh installs (staging, dev local), criar um `seed.sql` que popula `plan_billing_periods` com price IDs vindos de env vars. A migration cria a tabela com schema mas sem dados sensiveis.
- Nao recomendo editar migrations existentes -- isso viola o principio de imutabilidade de migrations. Adicionar uma NOVA migration que faz `UPDATE plan_billing_periods SET stripe_price_id = coalesce(current_setting('app.stripe_price_id_pro_monthly', true), 'PLACEHOLDER')` e popula via `seed.sql` separado.
- Tempo: 3h (nova migration + seed script + documentacao).

### Q2: D-01 (DB-04) -- plan_type drift: frequencia e metricas

- **Drift e corrigido diariamente.** `stripe_reconciliation.py` roda via `cron_jobs.py` as 06:00 UTC. Linhas 225-231 ja fazem sync de `profiles.plan_type` quando detectam divergencia.
- **Nao temos metrica de drift frequency granular.** O reconciliation service incrementa `RECONCILIATION_DIVERGENCES` (Prometheus counter) mas nao diferencia tipo de divergencia (plan_type vs status vs billing_period).
- **"Fail to last known plan" fallback:** `quota.py` linhas 42-65 usa cache in-memory com TTL 5min. Quando Supabase CB abre, serve plano cached. Nao temos metrica de quantas vezes o fallback ativa.
- **Recomendacao:** Adicionar label `divergence_type` ao counter Prometheus (1h). Considerar adicionar `smartlic_plan_fallback_activations_total` counter em `quota.py`.

### Q3: P-01 (DB-03) -- COUNT(*) OVER(): volume e alternativa

- **Volume em producao:** Com <100 usuarios beta, estimativa de <500 conversations total. Para admins, volume medio e <200.
- **Impacto real agora: negligenciavel.** O full scan de 500 rows custa <5ms.
- **Alternativa recomendada quando escalar:** Separar em 2 queries (paginated results + count). Cache do count com TTL 60s (conversations nao mudam a cada segundo). Materialized view e overkill para esta tabela.
- **Bonus:** Resolver DB-28 (correlated subquery) junto, que e o gargalo mais significativo dos dois.
- **Priority:** MEDIUM agora, revisitar quando conversations > 5000.

### Q4: D-05/D-06 -- Retention: template e intervalos

- **pg_cron jobs existentes cobrem 12-13 tabelas:** search_sessions (90d), search_results_cache (30d), search_results_store (180d), search_state_transitions (30d), audit_events (365d), health_checks (30d), alert_sent_items (180d), alert_runs (90d), reconciliation_log (90d), stripe_webhook_events (90d), incidents (365d), mfa_recovery_attempts (30d).
- **Template padrao:**
  ```sql
  SELECT cron.schedule(
    'cleanup_TABLE_NAME',
    '0 4 * * *',  -- 04:00 UTC daily
    $$DELETE FROM public.TABLE_NAME
      WHERE CONDITION AND created_at < NOW() - INTERVAL 'Xd'$$
  );
  ```
- **Intervalos recomendados:**
  - `user_subscriptions` (is_active=false): **24 meses.** Necessario para auditorias fiscais e compliance de faturamento.
  - `partner_referrals` (referred_user_id IS NULL): **12 meses.** Orfaos nao tem valor apos churn confirmado.
  - `monthly_quota`: **24 meses.** Alinhado com user_subscriptions para analytics historicas.

### Q5: M-01 (DB-12) -- Migration squash: risco

**NAO recomendo migration squash neste estagio.** Razoes:

1. **Risco alto, beneficio baixo.** As 86 migrations rodam em <30s no fresh install. Squash economiza segundos de CI.
2. **Supabase CLI nao suporta squash nativo.** Teriamos que: (a) gerar schema dump via `pg_dump`, (b) criar unica migration baseline, (c) marcar 86 migrations como "applied" manualmente na tabela `supabase_migrations.schema_migrations`. Processo manual e propenso a erros.
3. **Staging e dev local usam fresh install.** Qualquer erro no squash = ambiente quebrado sem path facil de rollback.
4. **Migrations existentes sao idempotentes.** IF NOT EXISTS, IF EXISTS, ON CONFLICT -- protegem contra re-execucao. O unico "custo" e confusao visual no diretorio, nao funcional.
5. **Alternativa melhor:** Adicionar `README.md` em `supabase/migrations/` documentando as 3 eras (001-033 initial, 20260xxx timestamped, 006a/027b patches). Custo: 30min, risco: zero.

---

## Impacto Cross-Area

### SYS-01 (CORS `*`) -- Implicacao de database

Confirmado em `main.py` linhas 38-47: `allow_origins=["*"]` com `allow_credentials=True`. Se um site malicioso explorar o CORS aberto para fazer requests autenticados, o **RLS e a unica barreira no nivel de dados**. O RLS esta solido (DEBT-113 verificou em runtime), entao o risco e mitigado na camada de dados. Corrigir CORS nao requer mudancas no DB.

### SYS-12 (Multiplas implementacoes de cache) -- Implicacao de database

`search_cache.py` faz writes diretos na tabela `search_results_cache` (Supabase L2 cache). `cache.py` usa Redis. `quota.py` tem in-memory cache. Nao ha problema de integridade no DB -- cada cache layer e independente. Porem, se unificar caches no futuro, considerar que `search_results_cache` tem trigger (`cleanup_search_cache_per_user`) que limita a 5 entries/user. Essa logica nao existe nos outros cache layers.

### SYS-04 (Prometheus efemero) -- Implicacao de database

As metricas de reconciliacao (`RECONCILIATION_DIVERGENCES`, `RECONCILIATION_FIXES`) se perdem a cada deploy. O `reconciliation_log` table JA persiste resultados no DB. Sugestao: adicionar coluna `divergence_details JSONB` ao `reconciliation_log` para query historica granular sem depender do Prometheus.

### SYS-13 (Sem version tracking de migrations) -- Implicacao de database

Supabase ja rastreia migrations aplicadas na tabela `supabase_migrations.schema_migrations`. O CI (`migration-check.yml`) verifica pendentes. O que falta e uma verificacao RUNTIME (ex: ao iniciar o backend, assertar que a ultima migration aplicada e >= X). Isso e um check no backend startup, nao uma mudanca no database.

### SYS-02 (PNCP client sincrono) -- Sem implicacao de database

A migracao para httpx async NAO impacta o database. A chain e: PNCP fetch -> filter -> enrich -> persist (cache write). O cache write ja e async.

---

## Recomendacoes

### Quick Wins (< 2h cada)

| Item | Horas | Acao |
|------|:-----:|------|
| DB-19 | 0.5h | `ALTER TABLE user_oauth_tokens ALTER COLUMN created_at SET NOT NULL; ALTER TABLE plan_billing_periods ALTER COLUMN created_at SET NOT NULL;` |
| DB-17 | 0.5h | Tighten `organizations.plan_type` CHECK para 4 valores ativos |
| DB-24 | 0.5h | Criar `backend/migrations/DEPRECATED.md` |
| DB-10 | 0.5h | Adicionar `WHERE id != '00000000-...'` em admin user listing queries |
| DB-02 | 1.5h | Update `handle_new_user()` para setar `trial_expires_at = NOW() + INTERVAL '14 days'` |
| DB-06 | 1h | pg_cron: `DELETE FROM user_subscriptions WHERE is_active = false AND created_at < NOW() - INTERVAL '24 months'` |
| DB-04 | 1h | Adicionar label `divergence_type` ao Prometheus counter em `stripe_reconciliation.py` |

### Prioridade Alta (resolver primeiro)

| Item | Horas | Justificativa |
|------|:-----:|---------------|
| DB-01 | 3h | Stripe price IDs em migrations -- risco de staging cobrar producao. Unico CRITICAL validado. |
| DB-06 | 1h | `user_subscriptions` sem bound -- pode crescer rapido com dunning retries. |
| DB-02 | 1.5h | `trial_expires_at` NULL para novos usuarios -- dependencia implicita no app layer. |
| DB-30 | 4h | JSONB sem versionamento -- problema composto que piora com cada mudanca de formato. |

### Pode Esperar (baixo risco)

| Item | Horas | Justificativa |
|------|:-----:|---------------|
| DB-03 + DB-28 | 5h | Performance de conversations -- volume muito baixo agora (<500 rows). Revisitar com >5000. |
| DB-05 | 0.5h | `partner_referrals` orfaos -- volume minimo (<50 rows). |
| DB-08 | 1h | `search_state_transitions` NOT NULL -- requer verificacao de producao primeiro. |
| DB-11 | 2h | OAuth tokens encryption -- padrao industria, risco aceito. |
| DB-13 | 2h | Down migrations -- criar apenas para billing/RLS. |
| DB-12 | 0h | Migration naming -- aceitar como esta, adicionar README. |
| DB-09 | 0.5h | FK ordering -- funciona na pratica. |
| DB-18 | 1h | Drop deprecated column -- sem urgencia. |
| DB-21/22/23/25/26/27 | ~2h total | Cosmeticos e documentacao. |
| DB-29 | 0.5h | `monthly_quota` retention -- crescimento lento. |
| DB-31 | 0.5h | `plan_type` CHECK escalabilidade -- documentar agora, resolver quando necessario. |

---

## Resumo

| Metrica | Valor |
|---------|-------|
| **Total no DRAFT** | 27 items |
| **Validados (mantidos)** | 21 items |
| **Removidos (falsos positivos)** | 3 items (DB-07, DB-16, DB-20) |
| **Adicionados** | 4 items (DB-28, DB-29, DB-30, DB-31) |
| **Total revisado** | 25 items |
| **Severidade ajustada** | 8 items tiveram severidade alterada |
| **Esforco original (DRAFT)** | 40h |
| **Esforco revisado** | **~27h** (reducao por remocao de falsos positivos e ajuste de estimativas) |

### Mudancas de Severidade

| Item | Original | Ajustado | Motivo |
|------|:--------:|:--------:|--------|
| DB-03 | HIGH | MEDIUM | Volume de conversations negligenciavel no estagio atual |
| DB-04 | HIGH | MEDIUM | Reconciliacao JA existe via stripe_reconciliation.py -- falta apenas metrica |
| DB-05 | HIGH | LOW | Volume minimo (<50 rows), crescimento lento |
| DB-09 | MEDIUM | LOW | Funciona na pratica, cenario de falha e raro e detectavel via CI |
| DB-12 | MEDIUM | LOW | Squash nao recomendado, custo-beneficio negativo |
| DB-14 | MEDIUM | LOW | Overhead negligenciavel -- index scan <1ms |
| DB-15 | MEDIUM | LOW | Index cobre a query adequadamente, nao e full scan |
| DB-07 | MEDIUM | REMOVIDO | Ja corrigido por TD-003 + DEBT-113 runtime assertion |
| DB-16 | MEDIUM | REMOVIDO | Decisao arquitetural correta, nao e debito |
| DB-20 | LOW | REMOVIDO | DEBT-100 ja implementou cleanup condicional |

---

*Revisado 2026-03-20 por @data-engineer durante Brownfield Discovery Phase 5.*
