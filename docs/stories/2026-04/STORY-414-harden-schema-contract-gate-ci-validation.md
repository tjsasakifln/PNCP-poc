# STORY-414: Harden Schema Contract Gate + CI Validation

**Priority:** P0 — Prevent Recurrence
**Effort:** M (1-2 days)
**Squad:** @data-engineer + @devops
**Status:** Draft
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

### AC2: Gate ativo em staging (fail-fast)
- [ ] Adicionar flag env `SCHEMA_CONTRACT_STRICT` (default `false` em prod, `true` em staging)
- [ ] Quando `true`, violação no gate deve **bloquear startup** com exit code 1
- [ ] Log estruturado: `{"level": "fatal", "event": "schema_contract_violation", "missing": [...], "action": "startup_blocked"}`
- [ ] Sentry event com `level=fatal` e tag `schema_contract_violation=true`

### AC3: CI workflow estendido
- [ ] Estender `.github/workflows/migration-check.yml` para executar `python -m backend.schemas.contract --validate` contra staging após `supabase db push`
- [ ] Job falha (exit 1) se schema contract não passa
- [ ] Posta comentário no PR listando colunas faltando
- [ ] Roda também como cron diário (3am UTC) para detectar drifts fora de PR

### AC4: Endpoint admin de status
- [ ] Nova rota `GET /admin/schema-contract-status` em `backend/routes/admin.py`
- [ ] Protegida por `require_admin` ou `require_master`
- [ ] Retorna JSON:
  ```json
  {
    "passed": true|false,
    "checked_at": "ISO-8601",
    "missing_columns": [],
    "extra_columns_detected": [],
    "critical_schema_version": "v1"
  }
  ```
- [ ] Cacheado em memória por 5 min para evitar sobrecarga

### AC5: Alerta Sentry dedicado
- [ ] Criar Sentry Alert Rule em `confenge.sentry.io` para:
  - Event message contains `SCHEMA CONTRACT VIOLATED` OR `CRIT-004: Table`
  - Severity Fatal
  - Notificação imediata (não agregada)
  - Canal: Slack #incident-response (se existir) + email
- [ ] Documentar alert rule em `docs/operations/alerting-runbook.md`

### AC6: Testes
- [ ] Unit tests em `backend/tests/test_schema_contract.py`:
  - [ ] Contract passa quando todas as colunas existem
  - [ ] Contract falha quando coluna removida (mock db response)
  - [ ] `SCHEMA_CONTRACT_STRICT=true` causa exit(1)
  - [ ] `SCHEMA_CONTRACT_STRICT=false` apenas loga warning
- [ ] Integration test simulando drift em staging

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
