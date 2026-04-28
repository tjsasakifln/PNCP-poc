# SEN-BE-001b: service_role com `statement_timeout=NULL` permite queries ilimitadas (root cause complement)

**Status:** Draft
**Origem:** Reversa Audit 2026-04-27 (`_reversa_sdd/review-report.md` Gap-10) + Memory `reference_supabase_service_role_no_timeout_default.md` + incident pós-mortem 2026-04-27 (PR #529 Stage 2)
**Prioridade:** P0 — outage-prevention (causa raiz identificada do incident 2026-04-27)
**Complexidade:** XS (1 migration + smoke test)
**Owner:** @data-engineer + @devops
**Tipo:** Reliability / Defense-in-depth
**Companion de:** SEN-BE-001 (sintoma trate em paths quentes; este trata roles do pool)

---

## Problema

Roles padrão Supabase têm `statement_timeout` configurados:

| Role | statement_timeout default |
|------|---------------------------|
| `anon` | 3s |
| `authenticated` | 8s |
| `service_role` | **NULL (sem limite)** |

Backend SmartLic usa `SUPABASE_SERVICE_ROLE_KEY` em `supabase_client.py::get_supabase()` para queries server-side (admin, reconciliation, ARQ jobs, ingestion, RPCs internos). Sem timeout, qualquer query lenta:

1. Drena conexões do pool (Hobby tier: 60 conexões max)
2. Bloqueia event loop quando `.execute()` é chamado sync (tornou-se gargalo no incident 2026-04-27 Stage 2: `routes/perfil_b2g.py` + `routes/fornecedor_publico.py` saturaram pool durante crawl Googlebot)
3. Acumula sem cancelamento → cascade timeout em Railway proxy (120s hard kill)

Memory `reference_supabase_service_role_no_timeout_default.md` documenta: *"Backend que usa SERVICE_ROLE_KEY roda queries ilimitadas; setar 60s previne pool exhaustion"*.

PR #529 mitigou via budget timeouts em Python (asyncio.wait_for) + negative cache, mas a defesa root (timeout no role do PostgreSQL) **continua ausente**.

---

## Decisão

`ALTER ROLE service_role SET statement_timeout = '60s'` em migration paired (.sql + .down.sql).

60s alinha com:
- Budget pipeline 100s (margem 40s para serialização + Railway proxy 120s)
- Decisão CTO: queries legítimas server-side completam em <60s; >60s indica regressão a fix, não a tolerar

---

## Critérios de Aceite

- [ ] **AC1:** Migration `supabase/migrations/20260427210000_service_role_statement_timeout.sql` aplica:
  ```sql
  ALTER ROLE service_role SET statement_timeout = '60s';
  ```
- [ ] **AC2:** Migration paired `supabase/migrations/20260427210000_service_role_statement_timeout.down.sql`:
  ```sql
  ALTER ROLE service_role RESET statement_timeout;
  ```
- [ ] **AC3:** Smoke test pós-deploy: query intencionalmente lenta (`SELECT pg_sleep(65)` via service_role) aborta com SQLSTATE `57014` em ~60s
- [ ] **AC4:** Backend `supabase_client.py::sb_execute` handle `57014` graciosamente: log Sentry com tag `query_timeout=true` + retorna error 504 (não 500)
- [ ] **AC5:** Tests: `backend/tests/integration/test_service_role_timeout.py` valida AC3 + AC4 contra Supabase staging
- [ ] **AC6:** Documentar valor + rationale em `docs/adr/ADR-SEN-BE-001b-service-role-timeout.md` (1 página: por que 60s, alternativas consideradas, impacto)
- [ ] **AC7:** Memory `reference_supabase_service_role_no_timeout_default.md` atualizada com "fixed via SEN-BE-001b 2026-04-27"
- [ ] **AC8:** Verificar via SQL pós-deploy:
  ```sql
  SELECT rolname, rolconfig FROM pg_roles WHERE rolname = 'service_role';
  -- deve retornar: {statement_timeout=60s}
  ```

### Anti-requisitos

- NÃO setar timeout via `SET LOCAL` em código (per-request) — frágil, pode ser esquecido
- NÃO usar `0` (disable) como valor default — roleback strategy é RESET (volta ao NULL inicial)
- NÃO sobrepor timeouts existentes em SEN-BE-001 (que adiciona índices em queries quentes)

---

## Arquivos Impactados

**Novos:**
- `supabase/migrations/20260427210000_service_role_statement_timeout.sql`
- `supabase/migrations/20260427210000_service_role_statement_timeout.down.sql`
- `backend/tests/integration/test_service_role_timeout.py`
- `docs/adr/ADR-SEN-BE-001b-service-role-timeout.md`

**Modificados:**
- `backend/supabase_client.py` — `sb_execute` ganha handler `57014` → log + 504 response
- `~/.claude/projects/-mnt-d-pncp-poc/memory/reference_supabase_service_role_no_timeout_default.md` — append fix note

---

## Riscos

- **R1 (Médio):** Queries server-side legítimas longas (ex: ingestion full-crawl backfill) podem ser cortadas em 60s. **Mitigação:** ARQ workers podem usar `SET LOCAL statement_timeout` quando necessário em batch jobs específicos (documented in ADR)
- **R2 (Baixo):** Aplicação da migration via `ALTER ROLE` não bloqueia conexões existentes (efeito só em sessions novas). **Mitigação:** restart workers Railway após migration para garantir aplicação imediata
- **R3 (Baixo):** Reconciliation Stripe scripts podem exceder 60s em volume alto. **Mitigação:** chunking + `SET LOCAL statement_timeout='180s'` em scripts específicos

---

## Dependências

- SEN-BE-001 (story irmã — trata sintoma com índices) pode ser deployed em qualquer ordem; complementares
- Acesso Supabase produção para apply migration (`npx supabase db push`)

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-27 | @sm | Story criada via Reversa Audit Gap-10. CTO decision: timeout=60s alinhado com budget pipeline. Status=Draft → @po validation |
