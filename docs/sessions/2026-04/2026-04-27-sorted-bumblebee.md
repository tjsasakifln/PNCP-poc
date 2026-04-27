# Session sorted-bumblebee — 2026-04-27

## Objetivo

Fechar recovery flap (perfil-b2g + sitemap 20-67% fail) — escalou para P0 backend wedged ativo, depois Stage 3 (healthcheck path bug bloqueando promotion).

## Entregue

- **PR #529** (`hotfix(incident): perfil-b2g + fornecedor budget + negative cache (P0)`) — 3 commits em `session/2026-04-27-api-recovery`:
  1. `11b368cc` — code fix: `asyncio.wait_for(_, 30s)` + negative cache 5min em `/v1/empresa/{cnpj}/perfil-b2g` e `/v1/fornecedores/{cnpj}/profile` + replace sync `.execute()` → `await sb_execute()` (event loop unblock)
  2. `901092ae` — OpenAPI snapshot regen (docstring 1-line update)
  3. `fc31ce2f` — `railway.toml`: `healthcheckPath /health → /health/live` (Stage 3 critical)
- **Railway env var:** `PYTHONASYNCIODEBUG=0` (era `1`) em `bidiq-backend` via MCP. Triggered redeploy 14:15 (que falhou healthcheck — Stage 3).
- **Railway redeploy 14:00 UTC** drenou workers Stage 2 (transient recovery 30s).
- **Memory updates:** `project_backend_outage_2026_04_27.md` (multi-stage final), nova `feedback_audit_env_vars_after_incident.md`.

## Impacto em receita

- Backend prod **NÃO estabilizado ao final desta sessão** — fixes em PR aguardando merge.
- Após user mergear PR #529 → Railway auto-deploy → `/health/live` healthcheck passa → novo container promovido com fix de código → wedge resolvido.
- **Trial signup path desbloqueia ao deploy.** Pré-revenue n=2: cada minuto down = signup zero.

## Multi-Stage Causal Chain (final)

| Stage | Causa | Resolução |
|-------|-------|-----------|
| 1 (ontem) | `service_role.statement_timeout=null` + WEB_CONCURRENCY=1 | ALTER ROLE 60s + WEB_CONCURRENCY=4 (já live) |
| 2 (hoje 14:00) | Hotfix #515 incompleto: perfil-b2g + fornecedor sem budget/cache + sync `.execute()` bloqueia event loop | PR #529 commits 1-2 |
| 3 (hoje 14:00-14:21) | `healthcheckPath=/health` sonda 5 APIs externas (PNCP/Portal/Licitar/BLL/BNC × 10s) — falha 11/11 attempts sob load → Railway nunca promove novos containers, mantém zombies wedged | PR #529 commit 3 |

## Pendente (dono + prazo)

- [ ] **Mergear PR #529 quando CI green** — @user — quando Backend+Frontend Tests COMPLETED+SUCCESS (ETA ~5-10min do encerramento desta sessão)
- [ ] **Soak 30min pós-deploy em prod** — @user — após merge
- [ ] **Validar `/health/live` <500ms via Railway healthcheck retry** — automatic
- [ ] **Composite index review `pncp_supplier_contracts(is_active, ni_fornecedor)`** — @data-engineer — esta semana
- [ ] **Negative cache em `/contratos/orgao/{cnpj}/stats`** — @dev — baixa prio (não no crawl path atual)
- [ ] **Story SEN-BE-008 (slow core endpoints cache)** — @sm/dev — Ready há 4d
- [ ] **Cron monitor `/health/live` a cada 5min com Sentry alert** — @devops — para detectar wedge

## Riscos vivos

| Risco | Severidade | Prazo |
|-------|------------|-------|
| Backend wedge cíclico até PR #529 merge + deploy | ALTO | resolve em <10min após user merge |
| CI re-run em fc31ce2f não passar | MÉDIO | local tests 25/25 OK; risco residual |
| Recidiva próxima Googlebot wave (24-48h) | MÉDIO | observar `slow_request` counter por 48h |
| Stage 4 latente: `/contratos/orgao/{cnpj}/stats` mesmo padrão | BAIXO | não está no crawl path atual |

## Memory updates

- `project_backend_outage_2026_04_27.md` — multi-stage final
- `feedback_audit_env_vars_after_incident.md` — novo (PYTHONASYNCIODEBUG lição)
- `MEMORY.md` — index atualizado

## Bootstrap empírico (gravado pra futuras sessões)

| Probe | Pré-fix | Pós redeploy 14:04 | Pós-PR-merge (esperado) |
|-------|---------|--------------------|-----|
| `/health/live` | 0 bytes 10s+ | 200 0.5-1.2s (transient) | 200 <0.5s soak 100% |
| Soak 30× | n/a | 6/30 PASS = 80% fail (cíclico) | 30/30 esperado |

## Discriminadores chave (memory-worthy)

1. **`/health/live` 10s timeout = workers stuck OR healthcheck wrong path.** Ambas hipóteses descartam cold-start.
2. **`'1/1 replicas never became healthy!'` em Railway logs = healthcheck path probably wrong** (sonda IO sob load).
3. **Sync `.execute()` dentro de async handler bloqueia event loop completo** — single slow query saturates entire process.

## Próxima ação prioritária de receita

Após merge PR #529 + soak OK → próxima sessão: validar GSC indexing pós-recovery (rota inbound trial gratuito, n=2 baseline). Charter Opção 2 do plano original.
