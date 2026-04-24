# Session piped-cray — 2026-04-24

**Branch base:** `feat/trial-conversion-smooth-island` (sessão anterior) → `main` (atual)
**Plan:** `~/.claude/plans/mission-empresa-morrendo-piped-cray.md`
**Mission:** empresa-morrendo (MRR única métrica)
**Classe:** REVENUE-DIRECT (#501 fix + merge) + UPTIME-CRITICAL (Mixpanel backend token) + REVENUE-ADJACENT (#502 retention)

## Objetivo

Fechar loop trial-conversion (merge #501), validar telemetria Mixpanel backend firing em prod (precondition para medição), shipar retention datalake 400d + SEO guards (#502).

## Entregue

| PR | Commit | Escopo |
|----|--------|--------|
| **#501 MERGED** | `152c8202` | `feat(trial-conversion): coupon badge + paywall_hit + plan_selected Mixpanel events` |
| **#502 MERGED** | `69252fff` | `fix(datalake): extend pncp_raw_bids retention 30→400d to unbreak SEO pages` |
| Railway vars | — | `MIXPANEL_TOKEN` setado em `bidiq-backend` (reuse project token frontend, 32 chars). Era AUSENTE — backend funnel events (`paywall_hit` x3, `trial_started`) silenciavam em prod |

## Audit GATE / Discriminador (Fase 1)

Advisor (pre-execução) flagou risco handoff smooth-island: "Mixpanel token pode não estar configurado em prod". Discriminador empírico <5min:

```bash
railway variables --service bidiq-backend --kv | awk -F= '{print $1}' | grep -i mixpanel
# → vazio (gap confirmado)
railway variables --service bidiq-frontend --kv | awk -F= '{print $1}' | grep -i mixpanel
# → NEXT_PUBLIC_MIXPANEL_TOKEN (frontend OK)
```

Gap confirmado: `backend/analytics_events.py:26` `os.getenv("MIXPANEL_TOKEN", "")` retornava vazio → silent-fail, zero dados enviados. User aprovou fix via @devops — set atomic reutilizando frontend project token.

## Impacto em receita

| Mudança | Estado | Como medir (24h soak) |
|---------|--------|----------------------|
| `MIXPANEL_TOKEN` setado backend | DONE prod | Mixpanel Live View 30min pós-deploy — esperar eventos `paywall_hit` por `reason={trial_expired, plan_expired, dunning_blocked, dunning_grace_period}` |
| Coupon badge emerald `/planos?coupon=TRIAL_COMEBACK_20` | DONE prod (merge #501) | Browser smoke: banner renderiza + preços riscados |
| `paywall_hit` event (backend) | DONE prod | Mixpanel count 24h — pré-fix MIXPANEL_TOKEN era 0 |
| `plan_selected` event (frontend) | DONE prod | Mixpanel funnel rate vs `checkout_initiated` |
| DataLake retention 400d + SEO zero-data guards | DONE merge #502 | `/observatorio` 200; migration `20260424133500_extend_pncp_retention_400d.sql` aplicada via deploy.yml auto-apply |

Hipótese Day 16 conversão (herdada smooth-island): user chega em `/planos?coupon=` vê preço cheio, não percebe desconto → baixa conversão. Fix: banner emerald + preços riscados torna desconto acionável.

**Gap anterior:** sem `MIXPANEL_TOKEN` backend, `paywall_hit` dark — toda decisão conversion pós-smooth-island era especulativa. Agora mensurável.

## Pendente (dono + prazo)

- [ ] **24h soak Mixpanel verify** — próxima sessão (2026-04-25+) — queries em handoff smooth-island, acrescentar `paywall_hit` por `reason`
- [ ] **Delete script ad-hoc** `backend/scripts/audit_trial_email_log_smooth_island.py` — DONE fase 4 (untracked file)
- [ ] **Fix permanente teste flaky** `test_decrypt_raises_error_on_tampered_ciphertext` — backlog ENG-DEBT, memory `feedback_jwt_base64url_flaky_test.md` — single-char flip base64url tem 6.25% false-pass; fix: full-replacement ou re-sign. NÃO em caminho receita.

## Riscos vivos

| Risco | Severidade | Prazo virar incidente |
|-------|-----------|----------------------|
| Deploy Railway backend pós-merge #501 pode tomar 3-5min — smoke window 30min ainda não completo ao encerrar sessão | LOW | Próxima sessão confirma via Mixpanel Live View |
| `delivery_status` NULL em `trial_email_log` (herdado) | MED | Auditar Resend dashboard se conversion <esperado em 48h |
| Teste oauth flaky 6.25% false-pass base64url tamper | LOW | ENG-DEBT, não em revenue path |

## Memory updates

| File | Razão |
|------|-------|
| `reference_mixpanel_backend_token_gap_2026_04_24.md` | Prod state não-derivable: backend estava sem MIXPANEL_TOKEN até piped-cray fix. Próxima sessão que adicionar event server-side deve verificar com `railway variables --service bidiq-backend --kv \| grep MIXPANEL_TOKEN` |

## KPIs da sessão

| Métrica | Alvo | Realizado |
|---------|------|-----------|
| Shipped to prod | ≥1 mudança caminho receita | #501 merged + `MIXPANEL_TOKEN` backend fix + #502 merged (3 shipped) |
| Incidentes novos | 0 | 0 |
| Tempo em docs | <15% | ~10% (handoff + memory) |
| Tempo em fix não-prod | <25% | ~5% (só investigação flaky test — não fixado) |
| Instrumentação adicionada | ≥1 evento funil | `MIXPANEL_TOKEN` fix ativa **6 eventos backend já instrumentados** (`paywall_hit` x3 choke points + `trial_started` + outros) que estavam dark |

## Próxima ação prioritária

**Próxima sessão 2026-04-25+: verificar 24h soak Mixpanel — queries em handoff smooth-island (paywall_hit count por reason, plan_selected por has_coupon, funnel paywall→plan→checkout→paid). Se conversion <hipótese, iterar com dados.**
