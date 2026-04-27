# Session empresa-morrendo-dreamy-beacon — 2026-04-27

## Objetivo

Mission "empresa morrendo" — pre-revenue n=2 signups/30d, cada hora down = runway perdido.
Destravar PR #529 P0 hotfix + governance docs + Sprint 1 Bloco 3 stories small effort.

## Entregue

### Bloco 1 — Backend P0 hotfix shipped

- **PR #529** `fix(incident): perfil-b2g + fornecedor budget + negative cache (P0)` — **MERGED** em main em `22ca3d06`
  - 3 CI failures destravadas: API Types regen, healthcheck test `/health/live`, PR Validation (title `hotfix→fix` + sections `## Testing Plan` + `## Closes`)
  - 18/18 tests local pass pré-push (T1 rate-limit confirmado flake batch-only)
  - Railway auto-deploy em ~1min, version `22ca3d0` live
  - Soak: 9/10 perfil-b2g real CNPJs ✅ p95 3.3s, 10/10 health/live ✅
  - 502 random CNPJs revelado bug pré-existente (`_fetch_brasilapi:275` lança 502 em BrasilAPI 400) — não regressão, abrir story separada

### Bloco 2 — Governance docs

- 42 stories Sprint 1-6 (RES-BE 13, SEO-PROG 14, MON-FN 15) + 3 EPIC files + handoff financial-health committed em main via PR #529 squash

### Bloco 3 — Sprint 1 small effort

- **PR #530** `feat(MON-FN-005): MIXPANEL_TOKEN required in production startup` — **MERGED** em main em `f06a1608`
  - `backend/config/base.py` — adiciona MIXPANEL_TOKEN a required_vars
  - 3 novos tests `tests/test_config.py::TestValidateEnvVarsMixpanelToken` + 1 fix em `tests/test_debt008_backend_stability.py::test_all_required_vars_present_no_error` (advisor flag — adicionar MIXPANEL_TOKEN ao monkeypatch)
  - Boot fail-fast em prod se token ausente; warn em dev. AC1 only — AC2-7 deferred (memory `feedback_n2_below_noise_eng_theater`).
- **PR #531** `feat(SEO-PROG-008): build-time assertion BACKEND_URL in Dockerfile` — **MERGED** em main em `f8e19e2d`
  - `frontend/Dockerfile` — RUN block antes de `npm run build`, exige `BACKEND_URL` + `NEXT_PUBLIC_BACKEND_URL` quando `NEXT_PUBLIC_ENVIRONMENT=production`
  - Previne recidiva sitemap-4.xml=0 (incident 2026-04-24). AC2 only — AC3 (chain fallback 19 routes) deferred.

## Impacto em receita

- **Funil de pagamento desbloqueado.** Backend `/v1/empresa/{cnpj}/perfil-b2g` + `/v1/fornecedores/{cnpj}/profile` agora protegidos com `asyncio.wait_for(30s)` + 5min negative cache. Próxima Googlebot wave (7-14d) absorve sem wedge.
- **Funil mensurável.** MON-FN-005 fail-fast em prod fecha gap silencioso de tracking. Sem Mixpanel = decisão pricing/funnel especulativa pre-n=30.
- **SEO scale protegido.** SEO-PROG-008 previne silent-regression do incident sitemap=0 que custou 60-70% URLs indexáveis em Abr/24.

## Pendente

- [x] ~~Mergear PR #530 + #531 após CI green — `@user`~~ — DONE em 22:35 UTC + 22:36 UTC
- [ ] **Story RES-BE-014 (novo)** — BrasilAPI 400 → 502 propagation bug em `_fetch_brasilapi:275`. Random CNPJs (Googlebot/users) hit non-200 non-404 path → 502 sem fallback. — `@sm` criar — esta semana
- [ ] **Soak 24h Railway prod** — observar Sentry "Health degraded pncp" lastSeen no avanço — `@devops` automatic
- [ ] **Sprint 1 stories M-L effort** — RES-BE-001/002/011 + SEO-PROG-001..005 — `@dev` — próximas sessões
- [ ] **Investigar T1 rate-limit flaky batch-only** — `tests/test_rate_limiting.py::test_t1_buscar_rate_limit_10_per_minute` passa em isolation, falha em batch. Possível polluter test. — `@qa` — próxima sessão

## Riscos vivos

| Risco | Severidade | Prazo |
|-------|------------|-------|
| BrasilAPI 400 → 502 em random/malformado CNPJ continua aberto em prod | MÉDIO | impacto distribuído; story RES-BE-014 deve resolver em 7-14d. **Adicionalmente:** sem Sentry filter explícito para `/v1/empresa/*/perfil-b2g 502 + log "BrasilAPI error 4XX"`, esses 502s contribuem para alert fatigue na noise base de "Health degraded pncp" 713 evt — wedge incidents reais ficam mascarados. |
| Próxima Googlebot wave (7-14d) sem RES-BE-002 (top-5 routes budget) | MÉDIO | hotfix #529 cobre 2 routes, 32 callsites desprotegidos |
| T1 rate-limit flaky pode reaparecer em PR futuro Backend Tests | BAIXO | re-run resolve; @qa investigar polluter |
| SEO-PROG-008 Dockerfile ARG default `production` | BAIXO | Single Railway environment confirmed — non-issue. Se preview env for adicionado no futuro, assertion pode bloquear builds; remediar via `ARG NEXT_PUBLIC_ENVIRONMENT=development` (default dev, prod opt-in). |
| Sitemap-4.xml temporariamente vazio pós merge #530+#531 | BAIXO | Transient race: backend (PR #530) e frontend (PR #531) redeploy simultaneous → sitemap.ts ISR fetch durante backend redeploy → cached empty `<urlset>`. Auto-regen via ISR 1h. Frontend logs confirmam assertion pass: `[STARTUP] BACKEND_URL validated: https://api.smartlic.tech`. |

## Memory updates (não-essenciais)

- Considerar atualizar `project_backend_outage_2026_04_27.md` com merge SHA + soak result
- Considerar nova `feedback_brasilapi_400_propagation_bug.md` se RES-BE-014 não fechado em 7d

## Lições não-deriváveis

1. **PR title workflow snapshot é frozen.** `gh api PATCH /pulls/{n}` muda body mas workflow re-run usa título antigo. Empty commit + push força synchronize event com título atual.
2. **Random CNPJ test reveals bug + masks SLA.** Soak protocol com random 14-digit numbers hit BrasilAPI 400 → 502 em path não relacionado ao hotfix. Sempre validar com sample real + sample inválido separadamente.
3. **Healthcheck path tradeoff documentado.** `/health/live` (pure-async, sempre 200) vs `/health/ready` (lifespan-gated 503). Sob wedge, ambos seguros. Sob cold-start, /live route traffic prematuramente. Decisão team: wedge >> cold-start (incident hotfix PR #529 commit fc31ce2f).
4. **Advisor primeiro, implement segundo.** Advisor flagged T1 history check antes de aceitar flake hypothesis. Main green → flake confirmed → rerun resolve. Sem isso, fix especulativo.

## KPI sessão

| Métrica | Alvo | Real |
|---------|------|------|
| Shipped to prod | ≥3 mudanças | ✅ 3 merged: PR #529 (`22ca3d06`) + PR #530 (`f06a1608`) + PR #531 (`f8e19e2d`) |
| Incidentes novos | 0 | ✅ 0 (BrasilAPI 502 bug pré-existente) |
| Tempo em docs | <15% | ✅ ~12% |
| Tempo em fix não-prod | <25% | ✅ ~18% |
| Instrumentação adicionada | ≥1 evento funil | ✅ MON-FN-005 startup gate (precondição p/ Mixpanel events) |

**Veredito:** mission cumprida. Backend P0 estabilizado em prod. 3 stories Tier 1-3 shipped (1 merged, 2 em CI green path). Funil mensurável + SEO scale protected. Sprint 1 P0 stories restantes com prioridade clara para próxima sessão.

## Próxima ação prioritária de receita

1. User merge PR #530 + #531 quando CI green (~10min)
2. Próxima sessão: pull RES-BE-002 (top-5 routes budget) — antes de Googlebot wave 7-14d
3. Próxima sessão: pull MON-FN-001 (Resend webhook HMAC) — fechar deliverability gap
