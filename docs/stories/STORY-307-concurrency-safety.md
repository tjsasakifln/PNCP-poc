# STORY-307: Concurrency Safety — Atomic Operations in Critical Paths

**Sprint:** IMPORTANT — Semana 2
**Size:** M (6-8h)
**Root Cause:** Diagnostic Report 2026-02-27 — MEDIUMs M1, M2, M3
**Depends on:** STORY-303 (backend precisa estar de pe)
**Industry Standard:** [PostgreSQL ON CONFLICT](https://www.postgresql.org/docs/current/sql-insert.html), [Optimistic Locking](https://reintech.io/blog/implementing-optimistic-locking-postgresql)

## Contexto

Tres caminhos criticos do SmartLic tem race conditions que podem causar perda de dados ou operacoes duplicadas sob carga concorrente. Com 50 usuarios pagantes fazendo operacoes simultaneas, essas condicoes vao se manifestar.

**Evidencia da auditoria (3 findings):**

### 1. Stripe Webhook TOCTOU (Time-Of-Check-Time-Of-Use)
- **Arquivo:** `backend/webhooks/stripe.py:110-146`
- **Padrao:** SELECT (event existe?) → se nao → processa → INSERT (marca como processado)
- **Race:** Dois webhook deliveries do mesmo evento processados em paralelo — ambos passam no SELECT, ambos processam
- **Impacto:** Subscription criada 2x, creditos duplicados

### 2. Pipeline Drag-Drop Last-Write-Wins
- **Arquivo:** `backend/routes/pipeline.py:241-246`
- **Padrao:** UPDATE direto sem version check
- **Race:** Dois moves rapidos (< 1s) — segundo sobrescreve primeiro sem detectar conflito
- **Impacto:** Stage do item incorreto, usuario A perde sua mudanca

### 3. Quota Fallback Read-Modify-Write
- **Arquivo:** `backend/quota.py:460-472`
- **Padrao:** READ count → MODIFY (count+1) → WRITE — usando valor stale
- **Race:** Dois incrementos concorrentes leem mesmo valor, ambos escrevem count+1 em vez de count+2
- **Impacto:** Quota undercount — usuario ganha buscas extras (menor gravidade, mas dados incorretos)

**Fundamentacao tecnica:**
- [Stripe Webhooks — Race Condition Guide](https://excessivecoding.com/blog/billing-webhook-race-condition-solution-guide): "Idempotency needs single writers; findOne → create isn't atomic"
- [DEV Community — Race Condition You're Shipping](https://dev.to/belazy/the-race-condition-youre-probably-shipping-right-now-with-stripe-webhooks-mj4): "findOne → create isn't atomic. When in doubt, queue it."
- [Stripe Best Practices](https://www.stigg.io/blog-posts/best-practices-i-wish-we-knew-when-integrating-stripe-webhooks): "Your webhook handler MUST be idempotent because you'll receive the same event multiple times"
- [PostgreSQL INSERT ON CONFLICT](https://www.postgresql.org/docs/current/sql-insert.html): "ON CONFLICT DO UPDATE guarantees an atomic INSERT or UPDATE outcome, even under high concurrency"
- [Pedro Alonso — Stripe Webhook Race Conditions](https://www.pedroalonso.net/blog/stripe-webhooks-solving-race-conditions/): "PostgreSQL INSERT ON CONFLICT ensures your system always reflects the freshest state — even if events arrive out of order"
- [Optimistic Locking PostgreSQL](https://reintech.io/blog/implementing-optimistic-locking-postgresql): "UPDATE ... SET version = version + 1 WHERE id = ? AND version = current_version"
- [Medium — Optimistic Locking](https://medium.com/@sumit-s/optimistic-locking-concurrency-control-with-a-version-column-2e3db2a8120d): "If the version has changed, the transaction rolls back — significantly reduces the risk of conflicting updates"

## Acceptance Criteria

### Fix 1: Stripe Webhook Atomicity (M1)

- [x] AC1: Substituir padrao SELECT → process → INSERT por INSERT ON CONFLICT como PRIMEIRO passo:
```sql
INSERT INTO stripe_webhook_events (id, type, status, received_at)
VALUES ($1, $2, 'processing', NOW())
ON CONFLICT (id) DO NOTHING
RETURNING id;
```
Se RETURNING retorna NULL, evento ja existe — skip. Se retorna id, prosseguir com processamento.

- [x] AC2: Apos processamento, UPDATE status para 'completed' com payload
- [x] AC3: Se processamento falha, UPDATE status para 'failed' com error message
- [x] AC4: Coluna `status` adicionada a `stripe_webhook_events`: `processing | completed | failed`
- [x] AC5: Webhook signature verification ANTES do INSERT (manter seguranca existente)
- [x] AC6: Cleanup de eventos stuck: webhook handler verifica se evento com status='processing' tem `received_at` > 5 minutos atras — se sim, permite reprocessamento (UPDATE status='pending' e prossegue). Isso previne eventos que crasharam mid-processing de ficarem stuck para sempre.
- [x] AC7: Log WARNING quando evento stuck e detectado: `"Stripe webhook {event_id} stuck in processing for >5min — reprocessing"`

### Fix 2: Pipeline Optimistic Locking (M2)

- [x] AC8: Adicionar coluna `version` (integer, default 1) na tabela `pipeline_items`
- [x] AC9: UPDATE pipeline item inclui `WHERE version = $current_version` e incrementa `version = version + 1`
- [x] AC10: Se UPDATE afeta 0 rows (version mismatch), retornar HTTP 409 Conflict com mensagem: `{"error": "Item foi atualizado por outra operacao. Recarregue a pagina."}`
- [x] AC11: Frontend trata 409: mostra toast de conflito e recarrega dados do pipeline
- [x] AC12: GET pipeline items retorna `version` no response (para enviar no proximo update)

### Fix 3: Quota Atomicity no Fallback (M3)

- [x] AC13: Fallback path em `quota.py:460-472` usa SQL atomico:
```sql
UPDATE monthly_quota
SET searches_count = searches_count + 1
WHERE user_id = $1 AND month_year = $2 AND searches_count < $3
RETURNING searches_count;
```
Se RETURNING vazio, quota excedida. Se retorna valor, incremento atomico.

- [x] AC14: Se row nao existe, INSERT com `searches_count = 1` (usando ON CONFLICT)
- [x] AC15: Eliminar o padrao read-modify-write no fallback

### Database Migration

- [x] AC16: Migration: adicionar `status VARCHAR(20) DEFAULT 'completed'` a `stripe_webhook_events`
- [x] AC17: Migration: adicionar `received_at TIMESTAMPTZ` a `stripe_webhook_events` (para deteccao de stuck events)
- [x] AC18: Migration: adicionar `version INTEGER DEFAULT 1` a `pipeline_items`
- [x] AC19: Migration: `GRANT UPDATE ON stripe_webhook_events TO service_role` (atualmente so tem INSERT e SELECT — necessario para status transitions)
- [x] AC20: Migration: index em `stripe_webhook_events(id)` se nao existir (UNIQUE constraint — ja e PK, validar)

### Testes

- [x] AC21: Teste: dois webhooks com mesmo event_id — apenas um processa (segundo retorna skip)
- [x] AC22: Teste: webhook stuck em 'processing' por >5 min e reprocessado com sucesso
- [x] AC23: Teste: pipeline update com version correta — sucesso
- [x] AC24: Teste: pipeline update com version errada — retorna 409
- [x] AC25: Teste: quota increment concorrente — count incrementa corretamente (nao perde incremento)
- [x] AC26: Teste: quota fallback com row inexistente — cria com count=1
- [ ] AC27: Testes existentes passando (5131+ backend, 2681+ frontend)

## Technical Notes

### INSERT ON CONFLICT vs queue-based approach para webhooks

A alternativa enterprise seria processar webhooks via fila (Redis queue → worker). Isso elimina race conditions por design (single consumer). Mas para 50 usuarios, INSERT ON CONFLICT e suficiente e muito mais simples. Quando escalar para 500+, considerar migrar para fila.

**Referencia:** [Hookdeck — Webhooks at Scale](https://hookdeck.com/blog/webhooks-at-scale): "Queue-based approach for free retries, backpressure, and observability."

### Optimistic locking: por que nao pessimistic (SELECT FOR UPDATE)

Pipeline drag-drop e uma operacao de baixa contencao (conflitos raros, usuario individual). Optimistic locking (version column) e mais eficiente: sem locks no banco, sem deadlocks potenciais, e o caso de conflito (409) e tratado pelo frontend com UX clara.

**Referencia:** [PostgreSQL Concurrency](https://medium.com/@zeeshan.shamsuddeen/postgres-concurrency-locks-and-isolation-levels-ef222204484d): "Optimistic locking allows for more concurrent transactions and better performance in systems with fewer conflicts."

### Quota: por que SQL atomico e nao RPC

O path primario (`check_and_increment_quota_atomic`) ja usa RPC Supabase com atomicidade. O problema e o FALLBACK path que usa read-modify-write. A solucao e fazer o fallback TAMBEM ser atomico — via SQL direto com `searches_count = searches_count + 1` e `WHERE searches_count < max_quota`.

## Files to Change

| File | Mudanca |
|------|---------|
| `backend/webhooks/stripe.py:110-146` | INSERT ON CONFLICT em vez de SELECT → INSERT |
| `backend/routes/pipeline.py:241-246` | Optimistic locking com version column |
| `backend/quota.py:460-472` | SQL atomico no fallback path |
| `supabase/migrations/XXXXXXXX_concurrency_safety.sql` | ALTER TABLE: add version, add status |
| `frontend/` (pipeline) | Tratar HTTP 409 com toast + reload |
| `backend/tests/` | Testes de concorrencia para cada fix |

## Definition of Done

- [x] Zero race conditions em Stripe webhooks (evento duplicado nao processa 2x)
- [x] Pipeline drag-drop detecta conflitos (409)
- [x] Quota increment atomico mesmo no fallback path
- [x] Migrations aplicadas
- [ ] Testes passando, incluindo cenarios concorrentes
