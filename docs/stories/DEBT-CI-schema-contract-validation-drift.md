# DEBT-CI — Schema Contract Validation Drift (Migration Check Post-Merge Alert)

**Status:** Ready
**Type:** Debt (CI failure recorrente, low-blast-radius)
**Priority:** P2 — não bloqueia merges (post-merge alert, não required check)
**Owner:** @data-engineer ou @devops
**Origem:** sessão transient-hellman 2026-04-21
**Depende de:** —

---

## Problema

Workflow `Migration Check (Post-Merge Alert)` (`.github/workflows/migration-check.yml`) falha consistentemente em main pós-merge (4+ runs em <24h em 2026-04-21: runs 24739043492, 24740657751, 24740668827, 24743290364). Falha no step **"Validate schema contract"**:

```bash
python -m backend.schemas.contract --validate
# Exit code 1 = schema contract violated
```

O workflow `check-migrations` (Supabase CLI `migration list --linked`) passa — todas as migrations listadas como aplicadas. **Apenas a validação de colunas específicas falha.**

## Context

`backend/schemas/contract.py:22-33` define o contrato:

```python
CRITICAL_SCHEMA: dict[str, list[str]] = {
    "search_sessions": [
        "id", "user_id", "search_id", "status", "started_at",
        "completed_at", "created_at",
    ],
    "search_results_cache": [
        "id", "params_hash", "results", "created_at",
    ],
    "profiles": [
        "id", "plan_type", "email",
    ],
}
```

O script roda via RPC `get_table_columns_simple(p_table_name)` ou fallback direct table query. Se RPC está indisponível, loga warning mas não falha. Se tabela não existe ou coluna falta, soma em `missing_items` e retorna exit 1.

## Hipóteses (priority order)

1. **Coluna nova renomeada/removida** em uma das 3 tabelas críticas sem update correspondente em `CRITICAL_SCHEMA`. Ex: migração recente renomeou `started_at` → `created_at_session` e a lista em contract.py ainda referencia o nome antigo.

2. **RPC `get_table_columns_simple` quebrado/não criado** em produção. O fallback "direct query" então continua sem conseguir validar colunas.

3. **SECRET incorreto em Actions.** Se `SUPABASE_SERVICE_ROLE_KEY` está expired/rotated, o workflow sai com exit 2 (config error), mas a mensagem `::error::Found unapplied migrations` seria `::warning::Schema contract check skipped`. Como o status é `failure`, não é esse.

4. **Handoff prancy-pudding disse "fix via PR #445 (awk stderr leakage)" mas falha persiste** — talvez o fix do awk cobriu o check-migrations mas não o schema contract check, que tem seu próprio exit path.

## Passos para investigação (15min)

```bash
# 1. Obter credenciais staging Supabase
export SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=...  # use Railway vars staging

# 2. Rodar localmente o validator
cd backend
python -m backend.schemas.contract --validate
# Saída esperada: lista exata de missing items
```

Se o output for:
```
SCHEMA CONTRACT VIOLATED — missing columns:
  - search_sessions.completed_at
  - profiles.email
  ...
```

Significa drift real em uma das tabelas. Opções:
- Aplicar migration faltando (`supabase db push --include-all`)
- Remover coluna da lista `CRITICAL_SCHEMA` se não for mais obrigatória (decisão @data-engineer)

Se output for erro de conexão:
- SUPABASE_SERVICE_ROLE_KEY está incorreto/expirado
- Rotate key + update GitHub Actions secret

## Workaround temporário (se necessário)

Desabilitar o step "Validate schema contract" temporariamente em `.github/workflows/migration-check.yml`:

```yaml
      - name: Validate schema contract
        id: schema_contract
        if: false  # TODO(DEBT-CI-schema-contract-validation-drift): re-enable after investigation
        run: |
          ...
```

Isso para o alerta sem remover o código de validação. Story fecha quando drift for resolvido e `if: false` removido.

## Acceptance Criteria

- [ ] AC1: Reproduzir failure localmente com credentials staging
- [ ] AC2: Identificar lista exata de missing items (log ou screenshot)
- [ ] AC3: Aplicar fix:
  - (Opção A) Migration que adiciona coluna faltando + `supabase db push`
  - (Opção B) Update `CRITICAL_SCHEMA` em `backend/schemas/contract.py` para alinhar com estado atual
  - (Opção C) Rotate SUPABASE_SERVICE_ROLE_KEY secret
- [ ] AC4: Next Migration Check run em main completa com `conclusion=success`
- [ ] AC5: Se fix for Opção A: rodar Sentry/Grafana alerta para regression (`post-merge-alert-failure`)

## Files potencialmente envolvidos

- `backend/schemas/contract.py:22-33` — `CRITICAL_SCHEMA` definition
- `supabase/migrations/*` — migrations recentes em search_sessions / search_results_cache / profiles
- `.github/workflows/migration-check.yml:95-134` — step que falha
- Produção Supabase — schema real

## Relacionados

- CRIT-004 (origem do schema contract) — referenciado em comentários do código
- STORY-414 (schema contract strict mode) — referenciado em rollout plan do contract.py
- PR #445 — fix prévio documentado mas aparentemente incompleto

## Notas

- **Não bloqueia merges** — este workflow é Post-Merge Alert (roda após push em main), não required check em PRs. Falha envia notificação mas não impede trabalho.
- **Não bloqueia deploys** — `SCHEMA_CONTRACT_STRICT=false` em produção (default) significa que o app startup não lança `SchemaContractViolation`; só loga CRITICAL. STORY-414 P4 ainda não ativou STRICT em prod.
- **Bloqueia confiança em pós-merge observability** — alertas cascateados em Slack/email criam fadiga de alerta. Prioridade elevada se ruído for percebido como problemático.
