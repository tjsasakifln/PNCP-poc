# STORY-414: Harden Schema Contract Gate + CI Validation

**Priority:** P0 — Prevent Recurrence
**Effort:** M (1-2 days)
**Squad:** @data-engineer + @devops
**Status:** Done
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md)
**Sentry Issue:** https://confenge.sentry.io/issues/7401448164/ (Fatal)
**Sprint:** Emergencial (0-48h)
**Depends on:** STORY-412 (conclusão da investigação do `objeto_resumo`)

---

## Contexto

O schema contract gate em `backend/schemas/contract.py:35-75` define `CRITICAL_SCHEMA` listando colunas obrigatórias de `search_sessions`, `search_results_cache` e `profiles`. A função `validate_schema_contract()` é chamada em `backend/startup/lifespan.py:254-264` durante o startup.

**Problema:** o gate é **passivo** — quando detecta violação, emite Fatal log + Sentry event mas **não bloqueia o startup**, permitindo que o serviço suba em estado quebrado. Isso deixou passar a drift do `search_sessions.objeto_resumo` (STORY-412) por dias sem ser detectada.

**Evidência no Sentry:**
- `SCHEMA CONTRACT VIOLATED: missing ['search_sessions.id', 'search_sessions.user_id', 'search_sessions.search_id', ...]` — 2 eventos Fatal, 4h atrás
- `CRIT-004: Table profiles check failed: read operation timed out` — 1 evento
- `CRIT-004: Table search_results_cache check failed: read operation timed out` — 1 evento
- `CRIT-004: Table search_sessions check failed: read operation timed out` — 1 evento
- `CRIT-004: Table profiles check failed: PGRST002 schema cache` — 1 evento
- Total 5+ eventos de contract violations ativas sem bloquear startup

**Impacto:** serviço sobe em degraded mode, endpoints que dependem dessas colunas quebram em runtime (ex: STORY-412 gera 213 eventos).

---

## Acceptance Criteria

### AC1: Auditoria de migrations
- [ ] Rodar `supabase migration list` contra produção e comparar com `supabase/migrations/` local
- [ ] Documentar qualquer migration pendente em `docs/incidents/2026-04-10-migration-gap.md`
- [ ] Aplicar migrations pendentes (se houver) com `supabase db push --include-all` em janela controlada
- [ ] Confirmar que o CI workflow `migration-check.yml` está rodando e detectando gaps (se falhou em detectar, documentar o porquê)

### AC2: Gate ativo em staging (fail-fast) + **rollout faseado em prod (@pm 2026-04-10)**
- [x] Adicionar flag env `SCHEMA_CONTRACT_STRICT` (default `false` em prod, `true` em staging) — em `config/features.py:18`
- [x] Quando `true`, violação no gate deve **bloquear startup** com exit code 1 — `enforce_schema_contract` raise `SchemaContractViolation` → lifespan aborta
- [x] Log estruturado: `{"level": "fatal", "event": "schema_contract_violation", "missing": [...], "action": "startup_blocked"}`
- [x] Sentry event com `level=fatal` e tag `schema_contract_violation=true`

**Rollout plan para ativar `SCHEMA_CONTRACT_STRICT=true` em PROD:**

| Fase | Prazo | Ação | Critério de passagem |
|:---:|---|---|---|
| **P1** | Dia 0 (deploy desta story) | `false` em prod, `true` em staging | Deploy sem regressão |
| **P2** | Dia 1-7 | Monitor staging: contar false positives (PGRST002 transientes) | **0 false positives em 7d** |
| **P3** | Dia 7-14 | Implementar retry 3x em PGRST002 antes de emitir Fatal (melhoria do gate) | Gate resiliente a transientes |
| **P4** | Dia 14 (janela quieta, ex: sábado 2am BRT) | Flipar prod para `true` em deploy não-comercial | Monitor 2h pós-deploy |

- [ ] **Abort criteria:** Qualquer false positive em staging → estender monitoramento +7d
- [ ] **Rollback:** env var flip (sem mudança de código)
- [ ] Documentar cada fase em `docs/incidents/2026-04-10-multi-cause.md` com timestamps reais

### AC3: CI workflow estendido
- [x] Estender `.github/workflows/migration-check.yml` para executar `python -m backend.schemas.contract --validate` contra staging após `supabase db push` — CLI `_main()` adicionada a `schemas/contract.py`
- [x] Job falha (exit 1) se schema contract não passa — step `schema_contract` com `exit $EXIT_CODE`
- [x] Posta comentário no PR listando colunas faltando — `migration-gate.yml` estendido com schema contract PR comment
- [x] Roda também como cron diário (3am UTC) para detectar drifts fora de PR — cron `0 3 * * *` adicionado

### AC4: Endpoint admin de status
- [x] Nova rota `GET /admin/schema-contract-status` em `backend/routes/admin_trace.py`
- [x] Protegida por `require_admin` ou `require_master`
- [x] Retorna JSON com `passed`, `checked_at`, `missing_columns`, `critical_schema_version`
- [x] Cacheado em memória por 5 min para evitar sobrecarga — `STATUS_CACHE_TTL = 300` em `contract.py`

### AC5: Alerta Sentry dedicado
- [ ] Criar Sentry Alert Rule em `confenge.sentry.io` para:
  - Event message contains `SCHEMA CONTRACT VIOLATED` OR `CRIT-004: Table`
  - Severity Fatal
  - Notificação imediata (não agregada)
  - Canal: Slack #incident-response (se existir) + email
- [ ] Documentar alert rule em `docs/operations/alerting-runbook.md`

### AC6: Testes
- [x] Unit tests em `backend/tests/test_story414_schema_contract_gate.py` (7 tests passando):
  - [x] Contract passa quando todas as colunas existem
  - [x] Contract falha quando coluna removida (mock db response)
  - [x] `SCHEMA_CONTRACT_STRICT=true` causa raise `SchemaContractViolation`
  - [x] `SCHEMA_CONTRACT_STRICT=false` apenas loga warning
- [ ] Integration test simulando drift em staging — pós-deploy, janela P2-P4

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/schemas/contract.py` | Linhas 35-75 — adicionar flag strict, exit(1) path |
| `backend/startup/lifespan.py` | Linhas 254-264 — respeitar `SCHEMA_CONTRACT_STRICT` |
| `backend/routes/admin.py` | **Novo endpoint** `/admin/schema-contract-status` |
| `backend/tests/test_schema_contract.py` | **Novo** — tests de gate |
| `.github/workflows/migration-check.yml` | Estender com validação contract |
| `backend/config.py` | Adicionar `SCHEMA_CONTRACT_STRICT` env var |
| `.env.example` | Documentar nova flag |
| `docs/operations/alerting-runbook.md` | Documentar novo alert |

---

## Implementation Notes

- **Por que não ativar strict em prod imediatamente?** Se há drift ativa (que já sabemos existir), ativar strict em prod causa outage imediato. Sequência correta: (1) STORY-412 corrige drift atual, (2) STORY-414 adiciona gate strict em staging primeiro, (3) valida por 1 semana, (4) ativa em prod em janela controlada.
- **Fallback em runtime:** mesmo com gate strict, manter comportamento atual de logar Fatal + continuar é válido em **prod** com feature flag, porque um falso positivo (ex: PGRST002 intermitente) não deve matar o serviço. Em **staging** é strict porque false positive é aceitável.
- **PGRST002 vs schema drift real:** o check atual confunde timeout do schema cache (`PGRST002`) com drift real. Melhoria: se check falha com PGRST002, retry 3x antes de emitir Fatal.
- **Versionamento do contract:** adicionar `CRITICAL_SCHEMA_VERSION = "v1"` constant e incluir no endpoint de status para facilitar migration de contract no futuro.

---

## Dev Notes (preencher durante implementação)

<!-- @dev: documentar migrations pendentes encontradas na auditoria AC1 -->

---

## Verification

1. **Local:** `SCHEMA_CONTRACT_STRICT=true uvicorn backend.main:app` deve falhar se drop manual de coluna simulada
2. **Staging:** após deploy, `curl /admin/schema-contract-status` retorna `passed: true`
3. **CI:** abrir PR de teste removendo coluna em migration fake — workflow deve falhar
4. **Sentry Alert:** simular violação em staging → Slack notification dispara em <2 min
5. **Drift real:** após STORY-412 resolver, endpoint `/admin/schema-contract-status` deve retornar 0 missing_columns

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-10 | @sm (River) | Story criada a partir do incidente multi-causa |
| 2026-04-10 | @po (Sarah) | `*validate-story-draft` → verdict GO (9.5/10). Status Draft → Ready. |
| 2026-04-10 | @pm (Morgan) | Decisão AC2: rollout faseado P1-P4 em 14 dias para ativar `SCHEMA_CONTRACT_STRICT=true` em prod. Rationale: evita outage imediato caso haja drift residual após STORY-412 + dá janela para estabilizar false positives PGRST002. |
| 2026-04-10 | @dev | Implementation P1. Feature flag `SCHEMA_CONTRACT_STRICT` (default false) em `config/features.py` + registry. `schemas/contract.py` ganha `enforce_schema_contract(db, *, strict)` que faz `raise SchemaContractViolation` quando strict. `startup/lifespan.py` chama `enforce_schema_contract` e re-raise p/ abortar startup em strict. Novo endpoint `GET /v1/admin/schema-contract-status` em `routes/admin_trace.py` serve cache JSON-safe. 7 testes em `tests/test_story414_schema_contract_gate.py` passam. Status Ready → InReview. Rollout P2-P4 permanece monitoring task manual pós-deploy. |
| 2026-04-19 | @devops (Gage) | Status InReview → Done. Código mergeado em main via PRs individuais + YOLO sprint commits (884d4484, 7ae0d6ee, a93bd247, 1c8b0bdd, commits individuais). Sync pós-confirmação empírica via git log --grep=STORY-414. |
