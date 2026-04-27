# RES-BE-013: Audit Env Vars Railway Pós-Incidente — CI Gate

**Priority:** P0
**Effort:** S (1 dia)
**Squad:** @devops + @dev
**Status:** Ready
**Epic:** [EPIC-RES-BE-2026-Q2](EPIC-RES-BE-2026-Q2.md)
**Sprint:** Sprint 1 (2026-04-29 → 2026-05-05)
**Dependências bloqueadoras:** Nenhuma (foundation)

---

## Contexto

Durante Stage 2 do incidente P0 (2026-04-27) foi descoberto que produção tinha **`PYTHONASYNCIODEBUG=1` ativo** — flag de debug que serializa execução assíncrona e amplifica saturação. Ninguém soube quando/por que foi setado. Memória `feedback_audit_env_vars_after_incident` documenta:

> "PYTHONASYNCIODEBUG=1 descoberto em prod durante Stage 2; debug flags persistem despercebidos. `--kv | grep -iE 'DEBUG|DEV|TRACE'` antes de declarar recovery"

Isso é **falha de governança operacional**: env vars são setados via Railway dashboard (manual), nunca auditados, e flags de dev escapam para prod silenciosamente.

Solução: gate CI que falha deploy se Railway prod tiver env vars proibidas (`PYTHONASYNCIODEBUG`, `DEBUG=true`, `DEV_MODE=true`, `TRACE=*`, `PYTHONDONTWRITEBYTECODE=*`, etc.). Allow-list explícita em `.github/audit/prod-env-allowlist.txt` cobre vars legítimas; tudo fora dela em pattern proibido bloqueia deploy.

P0 effort S — operacionaliza memory permanentemente em CI gate.

---

## Acceptance Criteria

### AC1: Lista de env vars proibidas em prod

- [ ] Criar `.github/audit/prod-env-blocklist.txt`:
  ```
  # Env vars NUNCA permitidas em produção
  # Uma var por linha. Suporta wildcards: PYTHON*DEBUG*

  PYTHONASYNCIODEBUG
  DEBUG
  DEV_MODE
  DEVELOPMENT
  PYTHONDONTWRITEBYTECODE
  TRACE_*
  PROFILE_*
  PYTHONVERBOSE
  PYTHON_VERBOSE
  FASTAPI_DEBUG
  PYDEVD_*
  ```
- [ ] Documentar cada entrada com comentário inline explicando por que é proibida
- [ ] Lista versionada via PR + review @architect

### AC2: Allow-list para vars legítimas

- [ ] `.github/audit/prod-env-allowlist.txt`:
  ```
  # Env vars ESPERADAS em produção
  # Lista taxativa — qualquer var em prod fora desta lista trigger warning (não block)

  # Database
  DATABASE_URL
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY
  SUPABASE_ANON_KEY
  SUPABASE_JWT_SECRET

  # Redis
  REDIS_URL

  # External APIs
  OPENAI_API_KEY
  STRIPE_SECRET_KEY
  STRIPE_WEBHOOK_SECRET
  RESEND_API_KEY
  RESEND_WEBHOOK_SECRET
  SENTRY_DSN
  MIXPANEL_TOKEN

  # Feature flags (resilience)
  ENABLE_BUDGET_WRAP
  ENABLE_NEGATIVE_CACHE
  ENABLE_BULKHEAD
  ENABLE_CIRCUIT_BREAKER
  CB_FAILURE_THRESHOLD
  CB_COOLDOWN_SECONDS
  BULKHEAD_DEFAULT_MAX
  NEGATIVE_CACHE_DEFAULT_TTL

  # Existing flags
  DATALAKE_ENABLED
  DATALAKE_QUERY_ENABLED
  LLM_ZERO_MATCH_ENABLED
  LLM_ARBITER_ENABLED
  LLM_FALLBACK_PENDING_ENABLED
  VIABILITY_ASSESSMENT_ENABLED
  SYNONYM_MATCHING_ENABLED

  # Pipeline tunables
  PIPELINE_TIMEOUT
  CONSOLIDATION_TIMEOUT
  PNCP_TIMEOUT_PER_SOURCE
  PNCP_TIMEOUT_PER_UF
  PNCP_BATCH_SIZE
  PNCP_BATCH_DELAY_S
  PNCP_CANARY_INTERVAL_S
  PNCP_CANARY_FAIL_THRESHOLD

  # Process
  PROCESS_TYPE
  WEB_CONCURRENCY
  GUNICORN_TIMEOUT
  PORT

  # CORS / runtime
  CORS_ORIGINS
  ENVIRONMENT
  RAILWAY_*
  ```
- [ ] @devops valida lista contra Railway prod atual via `railway variables --service bidiq-backend --kv`

### AC3: Script de audit

- [ ] Criar `.github/scripts/audit-prod-env.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail

  # Args: $1 = service name (bidiq-backend ou bidiq-frontend)
  SERVICE="${1:-bidiq-backend}"
  BLOCKLIST=".github/audit/prod-env-blocklist.txt"
  ALLOWLIST=".github/audit/prod-env-allowlist.txt"

  # Fetch Railway env vars (assumes RAILWAY_TOKEN set)
  VARS=$(railway variables --service "$SERVICE" --kv | cut -d= -f1)

  EXIT=0
  while IFS= read -r blocked; do
    [[ -z "$blocked" || "$blocked" =~ ^# ]] && continue
    pattern="^${blocked//\*/.*}\$"
    if echo "$VARS" | grep -qE "$pattern"; then
      echo "::error::FORBIDDEN env var found in prod: $blocked"
      EXIT=1
    fi
  done < "$BLOCKLIST"

  # Warn (not block) for vars not in allowlist
  while IFS= read -r v; do
    [[ -z "$v" ]] && continue
    if ! grep -qE "^$(echo "$v" | sed 's/_*$//')(_.*)?\$" "$ALLOWLIST"; then
      echo "::warning::Env var not in allowlist: $v (verify intent)"
    fi
  done <<< "$VARS"

  exit $EXIT
  ```
- [ ] Ou versão Python equivalente em `.github/scripts/audit_prod_env.py` (preferência se mais robusto)

### AC4: Workflow CI/CD `audit-env-vars`

- [ ] Adicionar job em `.github/workflows/deploy.yml`:
  ```yaml
  jobs:
    audit-env-vars:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - name: Install Railway CLI
          run: |
            curl -fsSL https://railway.app/install.sh | sh
            echo "$HOME/.railway/bin" >> $GITHUB_PATH
        - name: Audit backend env vars
          env:
            RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
          run: bash .github/scripts/audit-prod-env.sh bidiq-backend
        - name: Audit frontend env vars
          env:
            RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
          run: bash .github/scripts/audit-prod-env.sh bidiq-frontend
  ```
- [ ] Job é **gate de deploy** — falha bloqueia merge para main
- [ ] Roda também daily via `schedule: cron: '0 14 * * *'` (11h BRT) para detectar drift fora de PRs

### AC5: Notificações Sentry/Slack em drift detection

- [ ] Job daily, em caso de falha:
  - Sentry `capture_message(level="error", tags={"audit": "prod_env_drift"})`
  - Fingerprint `["prod_env_audit_failure", service]`
  - Slack notification (se webhook configurado) — TODO @devops decidir storage do webhook URL

### AC6: Documentação

- [ ] `docs/runbooks/audit-prod-env.md`:
  - Como rodar localmente (auth Railway, run script)
  - Como adicionar var ao allowlist (PR review obrigatório)
  - O que fazer quando audit falha (não force-merge — investigar valor)
  - História: incidente 2026-04-27 PYTHONASYNCIODEBUG=1 que motivou esta gate
- [ ] `CLAUDE.md` seção "## Resilience CI Gates" referencia esta workflow + RES-BE-001

### AC7: Testes (script audit isolado)

- [ ] **Unit tests:** `.github/scripts/test_audit_prod_env.sh`
  - Mock `railway variables` output via fixture
  - Caso 1: env var em blocklist → exit 1
  - Caso 2: env var em allowlist → exit 0, sem warnings
  - Caso 3: env var nem em block nem em allow → exit 0, com warning
  - Caso 4: wildcard match (`TRACE_FOO` casa `TRACE_*`) → exit 1
- [ ] CI roda `bats` ou `shellcheck` no script (lint)

### AC8: Validação manual baseline

- [ ] Antes do merge, @devops roda script local contra prod atual:
  ```bash
  bash .github/scripts/audit-prod-env.sh bidiq-backend
  ```
- [ ] Confirma que prod **não** tem `PYTHONASYNCIODEBUG=1` nem outras vars proibidas (já removidas no Stage 2)
- [ ] Se falsos-positivos aparecem, ajustar listas e documentar
- [ ] PR só passa quando script roda clean em prod atual

---

## Scope

**IN:**
- Lista blocklist + allowlist em `.github/audit/`
- Script bash (ou Python) de audit
- Workflow CI gate de deploy
- Daily cron de drift detection
- Sentry alerting
- Runbook + documentação CLAUDE.md
- Validação baseline pré-merge

**OUT:**
- Audit de secrets (separação responsabilidade — feature de Railway/GitHub Secrets)
- Audit de env vars de outros serviços (e.g. Redis, Supabase config) — escopo separado
- Auto-remediation (delete var) — proibido (risco)
- Histórico de mudanças de env vars (Railway audit log já existe nativamente)

---

## Definition of Done

- [ ] Blocklist + allowlist criados e revisados
- [ ] Script de audit funcional (tested via shellcheck/bats)
- [ ] Workflow CI gate ativo
- [ ] Daily cron rodando
- [ ] Sentry alerting configurado
- [ ] Runbook criado
- [ ] CLAUDE.md atualizado
- [ ] Validação baseline: prod atual passa script sem `PYTHONASYNCIODEBUG`
- [ ] CodeRabbit clean
- [ ] PR review por @devops (Gage) e @architect (Aria) com verdict PASS
- [ ] Memory `feedback_audit_env_vars_after_incident` linkada na story como contexto

---

## Dev Notes

### Paths absolutos

- `/mnt/d/pncp-poc/.github/audit/prod-env-blocklist.txt` (novo)
- `/mnt/d/pncp-poc/.github/audit/prod-env-allowlist.txt` (novo)
- `/mnt/d/pncp-poc/.github/scripts/audit-prod-env.sh` (novo)
- `/mnt/d/pncp-poc/.github/scripts/test_audit_prod_env.sh` (novo) — testes
- `/mnt/d/pncp-poc/.github/workflows/deploy.yml` (modificar — adicionar job audit-env-vars)
- `/mnt/d/pncp-poc/docs/runbooks/audit-prod-env.md` (novo)

### Padrão referência

- RES-BE-001 (audit `.execute()` sem budget) — pattern de CI gate + baseline + allowlist
- Memory `feedback_audit_env_vars_after_incident` (2026-04-27) — origem desta story
- Railway CLI docs: https://docs.railway.app/develop/cli

### Frameworks de teste

- bats (Bash Automated Testing System) ou shellcheck
- File location: `.github/scripts/test_audit_prod_env.sh`
- Fixtures: variáveis env mocked via `RAILWAY_VARS_OVERRIDE=...` (env injection)

### Convenções

- Bash strict mode: `set -euo pipefail`
- Wildcards via regex: `${var//\*/.*}`
- Logger: `echo "::error::"` e `echo "::warning::"` para GitHub Actions annotations
- Comentários explicando rationale de cada entrada nas listas

### Como auth Railway no GH Action

- Secret `RAILWAY_TOKEN` já existe (referência: secrets.RAILWAY_TOKEN usado em outros workflows)
- Token é Account Token (não Project Token); não expira
- Nunca logar token em stdout (`set +x` se necessário)

---

## Risk & Rollback

| Trigger | Ação |
|---|---|
| Daily cron falha por bug em script | Investigar via Sentry; revert se persistente |
| False positive (var legítima detectada como proibida) | Ajustar blocklist (remover entrada ofensiva) ou allowlist (adicionar var); PR review |
| False negative (var maliciosa passa) | Adicionar à blocklist; investigar como entrou em prod |
| Railway CLI quebra/auth expira | Smoke test antes de cada release; backup: HTTP API direto |
| Workflow lento (>2min) | Cache CLI install; só rodar se PR muda env-related files |

**Rollback completo:** revert PR + remover job do workflow. Não há mudança de runtime.

---

## Dependencies

**Entrada:** Nenhuma — foundation.

**Saída:** Habilita confiança operacional para todas stories restantes do epic (env vars de feature flags como `ENABLE_BUDGET_WRAP`, `ENABLE_NEGATIVE_CACHE` etc. ficam protegidas contra drift).

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | ✓/✗ | Notes |
|---|---|---|---|
| 1 | Clear and objective title | ✓ | "Audit Env Vars Railway Pós-Incidente — CI Gate" — escopo + entrega claros. |
| 2 | Complete description | ✓ | Liga `PYTHONASYNCIODEBUG=1` em Stage 2 → falha governança operacional → solução determinística. |
| 3 | Testable acceptance criteria | ✓ | 8 ACs incluindo 4 casos de teste do script (block/allow/wildcard/warn). |
| 4 | Well-defined scope | ✓ | IN/OUT delimitados; OUT exclui audit secrets (separação de responsabilidade) e auto-remediation (risco). |
| 5 | Dependencies mapped | ✓ | Foundation (sem entrada); saída habilita confiança operacional para todas stories restantes. |
| 6 | Complexity estimate | ✓ | S (1 dia) — script bash + 2 arquivos lista + workflow + tests bats. |
| 7 | Business value | ✓ | Operacionaliza memory pós-incidente diretamente em CI — previne reincidência classe-de-defeito. |
| 8 | Risks documented | ✓ | 5 riscos incluindo Railway CLI auth expira; rollback = revert PR (sem mudança runtime). |
| 9 | Criteria of Done | ✓ | 11 itens DoD incluindo validação baseline pré-merge e memory linkada na story. |
| 10 | Alignment with PRD/Epic | ✓ | Sprint 1 P0 anti-reincidência conforme EPIC sequenciamento. |

### Required Fixes

Nenhuma.

### Observations

- Allow-list explicita inclui novas flags de feature (ENABLE_BUDGET_WRAP, ENABLE_NEGATIVE_CACHE, ENABLE_BULKHEAD, ENABLE_CIRCUIT_BREAKER) — alinhamento com stories downstream do epic.
- Wildcard pattern `TRACE_*` cobre famílias de vars (boa prática).
- Sentry alerting + daily cron + PR gate = 3 camadas de detecção de drift.
- Memory `feedback_audit_env_vars_after_incident` (2026-04-27) → CI gate é exemplo claro de "memory promovida a sistema".

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — operacionaliza memory `feedback_audit_env_vars_after_incident` em CI gate | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). Memory promovida a CI gate, allow-list inclui flags do epic. Status: Draft → Ready. | @po (Pax) |
