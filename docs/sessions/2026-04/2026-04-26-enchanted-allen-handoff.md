# Session enchanted-allen — 2026-04-26

## Objetivo

Mover MRR via desbloqueio aquisição orgânica (sitemap/4) + diagnóstico funil + ship 1 contra-medida — pivotado para reativação manual de trials expirados após n=2 invalidar funnel.

## Entregue

- PR #511 — `docs(session): steady-kurzweil final update` — **MERGED** (SHA `8a1edaaa`).
- Bloco A: `NODE_OPTIONS=--dns-result-order=ipv4first` setado em Railway `bidiq-frontend` (hardening preventivo). **Achado:** `sitemap/4.xml` já estava servindo 7368 URLs (vs 0 reportado em steady-kurzweil — ISR regenerou organicamente em ~30h após #510). Total sitemap atual: 42 + 60 + 1792 + 348 + 7368 = **9610 URLs servindo**.
- Bloco B.1: query Supabase mostrou **4 profiles totais; 2 reais** (paulo.souza@adeque-t.com.br, dslicitacoesthe@gmail.com). 1 admin (eu), 1 system-cache-warmer (obsoleto). Ambos trials reais expiraram <7d. Funnel Mixpanel **abaixo noise floor**.
- 2 emails reativação enviados via Resend (Resend IDs `92e691a0` paulo, `36dbfada` ds licitações). From `tiago@smartlic.tech`, reply-to `tiago.sasaki@gmail.com`. Drafts personalizados (não template) baseados em uso real (282 licitações R$1.27B, 4 buscas em 12d). Drafts log: `docs/sessions/2026-04/2026-04-26-enchanted-allen-reactivation-emails.md`.
- GSC `sitemap.xml` re-submetido via Playwright MCP. Status: Processado, `Enviado: 26/abr` (de 21/abr). GSC vai re-crawl e descobrir 9610 URLs em 24-72h. Screenshot: `gsc-sitemap-resubmitted-2026-04-26.png`.
- Commit `a9b9f03d` — `feat(landing): badge trial "14 dias grátis · sem cartão" above-the-fold no hero`. 18/18 testes HeroSection PASS.
- Commit `5c16fb24` — `feat(analytics): capture landing_page + external referrer no signup_completed`. `captureLandingContext` + `getAcquisitionProperties` (additive). 27/27 testes analytics PASS.

## Impacto em receita

**Direto manual:** 2 emails reativação tocam 100% dos trials reais expirados <7d. Conversão depende de resposta (você).

**Aquisição orgânica:** sitemap GSC re-submetido. Descoberta de shards 2 (1792 URLs) e 4 (7368 URLs) em 24-72h. Trafego incremental esperado em 7-30d (escala depende de qualidade do conteúdo programmatic + autoridade da home).

**Conversão LP:** badge `14 dias grátis · sem cartão` agora visível above-the-fold na home (antes só aparecia no footer-CTA com `text-sm text-white/50`). Lift esperado: 5-15% em conversion landing → /signup.

**Atribuição futura:** `signup_completed` agora carrega `landing_page` + `landing_referrer` (não-interno). Quando GSC trouxer tráfego, vou poder cruzar **qual página converteu** vs apenas UTM. Mensurável via Mixpanel breakdown.

## Pendente (dono + prazo)

- [ ] **@devops:** push `session/2026-04-26-enchanted-allen` (renomeada de `fix/sen-fe-001-sitemap-shard-4-networking`) + criar PR — segunda 28/abr.
- [ ] **Você:** receber respostas dos 2 emails. Se responderem, escutar 1min antes de vender. Se aceitarem extensão, rodar SQL: `update profiles set trial_expires_at = now() + interval '14 days', subscription_status = 'trial' where email in (...)`. — qualquer hora.
- [ ] **Você:** GSC `Páginas` view em 48-72h, filtro `Origem: Sitemap` — confirmar shards 2 + 4 reportando "Descobertas" (URLs em /contratos/[setor]/[uf], /contratos/orgao/[cnpj], etc.). — quarta-feira 29/abr.
- [ ] Cleanup `system-cache-warmer@internal.smartlic.tech` profile (obsoleto pós cache-warming-deprecation 2026-04-18) — backlog ENG-DEBT, 5min.
- [ ] **4 fixes LP/conversion descobertos no audit (Task #7)** — backlog REVENUE-ADJACENT:
  - Form `/signup` reduzir 4→3 campos (mover phone para onboarding) — 2-3h, lift 5-10%
  - Hero LP adicionar prova social numérica (X editais analisados, Y consultorias) — 30min
  - Pricing page hero adicionar badge trial junto ao preço — 15min
  - Tracking do botão "Ver como funciona" (qual % desce vs clica primary) — 15min
- [ ] Resend webhook HMAC verify gap em `routes/trial_emails.py::resend_webhook` — defer (security debt, baixa prioridade até volume).

## Riscos vivos

- **Médio: respostas dos 2 emails.** Se não responderem em 48h, considere segundo follow-up curto (1 frase). Personalize baseado no que o primeiro email disse.
- **Baixo: Railway `NODE_OPTIONS=ipv4first` ainda não testado em deploy real.** Aplica no próximo build natural. Sem rollback necessário se quebrar (env var trivial).
- **Baixo: GSC pode retornar "Não foi possível ler" se sitemap tiver schema error não detectado.** Re-checar 48h.

## KPIs da sessão

| Métrica | Alvo | Observado | Status |
|---|---|---|---|
| Shipped to prod (caminho receita) | ≥1 | 2 commits em branch (Hero badge + signup_source); 2 emails reativação enviados; GSC resubmetido | ✅ (deploy via @devops push pendente) |
| Incidentes novos | 0 | 0 | ✅ |
| Tempo em docs | <15% | ~12% (handoff + email drafts) | ✅ |
| Instrumentação adicionada | ≥1 evento funil | `landing_page` + `landing_referrer` em `signup_completed` | ✅ |
| Funil B diagnostico | Documentado | n=2 invalidou; pivot para reativação manual | ✅ |

## Memory updates

- `feedback_n2_below_noise_eng_theater.md` — NEW: n<5 reais = abaixo noise floor pra automação. Personal email > template/cron. Reason: SmartLic 2026-04-26 (4 profiles totais, 2 reais; advisor flagged). How to apply: antes de desenhar email-lifecycle cron / funnel diag, rodar `select count(*) from profiles where is_admin=false` + filtrar system users. Se <5, defer automação, foque manual.
- `reference_resend_personal_tone_send.md` — NEW: Resend pode enviar email pessoal usando domain verified (`smartlic.tech`). From: `Tiago Sasaki <tiago@smartlic.tech>`, reply-to: `tiago.sasaki@gmail.com`. Plain text body (não HTML template) para vibe pessoal. Resend prod key em Railway `bidiq-backend`.
- `reference_gsc_playwright_resubmit.md` — NEW: GSC sitemap resubmit via Playwright funciona se host browser tem session Google ativa. Propriedade `sc-domain:` exige URL completa (não path relativo) — submit `sitemap.xml` retorna "Endereço inválido"; submit `https://smartlic.tech/sitemap.xml` é aceito. ISR caches podem reportar `0 páginas encontradas` por horas após resubmit (re-crawl assíncrono GSC).
- `feedback_handoff_stale_30h.md` — NEW: Handoff de sessão anterior pode estar stale 24-30h por regen orgânico (ISR, cache, async cron). Reason: enchanted-allen 2026-04-26 — `sitemap/4=0` virou `7368` em ~30h após steady-kurzweil. How to apply: discriminador empírico antes de planejar (5min) — se memória/handoff afirma estado X em código que tem TTL ou regen async, validar X com curl/grep antes de comprometer plano.
