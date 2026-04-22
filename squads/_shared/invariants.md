# Invariantes — SmartLic

Regras não-negociáveis que todo agente de squad deve respeitar. Violação = PR rejeitado.

## 1. Timeout Waterfall

**Invariante:** `pipeline(100) > consolidation(90) > per_source(70) > per_uf(25) > (per_modality 20 + httpx 15)`.

Enforced por `backend/tests/test_timeout_invariants.py`. Cada TimeoutError incrementa `smartlic_pipeline_budget_exceeded_total{phase,source}`.

Railway mata request >120s — sempre deixar ~20s headroom para serialização de response.

## 2. Zero-Failure Test Policy

- Backend: **5131+ passing, 0 failures**
- Frontend: **2681+ passing, 0 failures**

**0 failures é o único baseline aceitável.** Corrija, nunca trate como "pre-existing failure".

## 3. RLS em toda tabela

**TODA** tabela Supabase tem RLS habilitado. Nenhuma exceção.

Políticas default:
- User-owned (`search_sessions`, `pipeline_items`, `feedbacks`): `auth.uid() = user_id`
- Public read-only (`pncp_raw_bids`, `supplier_contracts`): SELECT público, INSERT/UPDATE só service_role
- Admin (`audit_logs`, `/v1/admin/*`): checar `profiles.is_admin OR is_master`

## 4. Anti-Hang Rules (Testing)

Violações causam full-suite freezes.

- **pytest-timeout 30s por test** (`pyproject.toml`)
- **NUNCA `asyncio.get_event_loop().run_until_complete()`** em tests — use `async def` + `@pytest.mark.asyncio`
- **NUNCA `sys.modules["arq"] = MagicMock()`** sem cleanup — conftest `_isolate_arq_module` fixture handles isolation automatically
- **Fire-and-forget**: conftest `_cleanup_pending_async_tasks` cancela lingering `asyncio.create_task()`
- **subprocess in tests**: sempre `timeout=` param em `Popen.communicate()` + `proc.kill()` cleanup
- **timeout_method = "thread"** (Windows compat — signal é Unix-only)

## 5. Migration Policy (STORY-6.3)

- **Source of truth:** `supabase/migrations/YYYYMMDDHHMMSS_description.sql`
- **Pareado sempre:** `YYYYMMDDHHMMSS_description.down.sql` (rollback script)
- **Legacy:** `backend/migrations/` — histórico, NÃO adicionar novas
- **CI (CRIT-050):**
  - PR warning: `migration-gate.yml` bloqueia se down.sql falta
  - Push alert: `migration-check.yml` bloqueia se unapplied
  - Auto-apply: `deploy.yml` roda `supabase db push --include-all` pós-deploy

## 6. Test Mocking Patterns

Violações causam bugs hard-to-debug:

- **Auth:** `app.dependency_overrides[require_auth]` (NUNCA `patch("routes.X.require_auth")`)
- **Cache:** patch `supabase_client.get_supabase` (NUNCA `search_cache.get_supabase`)
- **Config:** `@patch("config.FLAG_NAME", False)` (NUNCA `os.environ`)
- **LLM:** `@patch("llm_arbiter._get_client")` (nível correto)
- **Quota:** tests mockando `/buscar` DEVEM mockar `check_and_increment_quota_atomic` também
- **ARQ:** `sys.modules["arq"]` gerenciado pela fixture autouse `_isolate_arq_module` (não faça manualmente sem cleanup)

## 7. API Type Sync

Toda rota exposta ao frontend DEVE ter `response_model=`. Sem isso o schema não vai pro OpenAPI → frontend fica loosely typed (`{[k: string]: unknown}`).

Regenerar types após mudança:

```bash
cd backend && uvicorn main:app --port 8000 &
npm --prefix frontend run generate:api-types
git add frontend/app/api-types.generated.ts
```

CI gate: `.github/workflows/api-types-check.yml` falha PR se committed drifta.

## 8. Framework Boundary (AIOX L1-L4)

- **L1** Framework Core (`.aiox-core/core/`, `.aiox-core/constitution.md`): **NEVER modify**
- **L2** Framework Templates (`.aiox-core/development/tasks/`, `workflows/`, `agents/`): **extend-only**
- **L3** Project Config (`core-config.yaml`, `agents/*/MEMORY.md`): mutable com cuidado
- **L4** Project Runtime (`docs/stories/`, `packages/`, `squads/`, `tests/`): ALWAYS modify

Deny rules em `.claude/settings.json` reforçam deterministicamente.

## 9. Git Safety

Nunca executar sem autorização explícita do usuário:
- `git push --force` / `--force-with-lease`
- `git reset --hard`
- `git checkout .` / `git restore .`
- `git clean -f`
- `git branch -D`
- `--no-verify`, `--no-gpg-sign`

**Git push + PR creation:** autoridade EXCLUSIVA de `@devops` (ver `.claude/rules/agent-authority.md`).

## 10. Quota + Billing

- **Fail to last known plan:** nunca fall back para `free_trial` em DB errors
- Stripe handles proration automaticamente — NO custom prorata code
- 3-day grace period para subscription gaps
- TODOS Stripe webhook handlers sincronizam `profiles.plan_type`

## Ao adicionar novo invariante

1. Documentar aqui em `invariants.md`
2. Adicionar test em `backend/tests/` OU `.github/workflows/*-check.yml` que falhe se violado
3. Mencionar em CLAUDE.md raiz se for behavior-critical
