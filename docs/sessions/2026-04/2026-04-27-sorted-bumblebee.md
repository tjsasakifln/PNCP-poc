# Session sorted-bumblebee — 2026-04-27

## Objetivo

Fechar recovery flap (perfil-b2g + sitemap 20-67% fail) — escalou para P0 backend wedged ativo.

## Entregue

- **PR #529** (`hotfix(incident): perfil-b2g + fornecedor budget + negative cache`) — commit `11b368cc` em `session/2026-04-27-api-recovery`. CI rodando.
- **Railway env var:** `PYTHONASYNCIODEBUG=0` (era `1`) em `bidiq-backend` via MCP. Triggered redeploy `71e27195` 14:15 UTC.
- **Railway redeploy** 14:00 UTC drenou workers wedged Stage 1.
- **Memory updates:** `project_backend_outage_2026_04_27.md` (multi-stage), nova `feedback_audit_env_vars_after_incident.md`.

## Impacto em receita

- Backend prod restaurado (transient flap pós-fixes — esperado estabilizar com PR #529 deploy).
- Trial signup path desbloqueado (estava 100% fail durante wedge).
- Googlebot crawl não mais derruba backend cyclically (após PR merge).
- **Hipótese a testar próxima sessão:** GSC indexing acelera com backend estável + on-page SEO recente.

## Pendente (dono + prazo)

- [ ] **Monitor PR #529 → merge → soak 30min em prod** — @user — hoje (CI green expected ~5-10min)
- [ ] **Composite index review `pncp_supplier_contracts(is_active, ni_fornecedor)`** — @data-engineer — esta semana
- [ ] **Negative cache pattern em `/contratos/orgao/{cnpj}/stats`** — @dev — baixa prio (não no crawl path atual)
- [ ] **Story SEN-BE-008 (slow core endpoints cache)** — @sm/dev — Ready há 4d
- [ ] **Cron monitor /health/live a cada 5min com Sentry alert** — @devops — para detectar wedge antes do user

## Riscos vivos

- **Wedge cíclico até PR #529 deploy ativo** — ALTO — janela ~20-30min até PR mergeado + redeploy
- **Recidiva em próxima Googlebot wave (24-48h)** — MÉDIO — observar /v1/empresa/* e /v1/fornecedores/* slow_request counter
- **Stage 3 latente:** `/contratos/orgao/{cnpj}/stats` mesmo padrão — pode wedge se Googlebot encontrar route via sitemap

## Memory updates

- `project_backend_outage_2026_04_27.md` — multi-stage final (Stage 1 yesterday + Stage 2 hoje)
- `feedback_audit_env_vars_after_incident.md` — novo (PYTHONASYNCIODEBUG lição)
- `MEMORY.md` — index atualizado

## Bootstrap empírico (gravado pra futuras sessões)

| Probe | Pré-fix | Pós-redeploy 14:04 | Pós PYTHONASYNCIODEBUG=0 |
|-------|---------|---------------------|--------------------------|
| `/health/live` | 0 bytes 10s+ | 200 0.5-1.2s | (deploy 14:15 in-progress) |
| Soak 30× | n/a | 6/30 PASS = 80% fail (cíclico) | TBD |

**Discriminador chave:** `/health/live` (pure-async, zero IO) timeout = workers blocked. Não cold-start.

## Próxima ação prioritária de receita

Após merge PR #529 + deploy soak OK → próxima sessão: validar GSC indexing pós-recovery (rota inbound trial gratuito, n=2 baseline). Charter Opção 2 do plano original.
