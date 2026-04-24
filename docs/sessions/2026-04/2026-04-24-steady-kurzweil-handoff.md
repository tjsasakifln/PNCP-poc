# Session steady-kurzweil — 2026-04-24

## Objetivo

Desbloquear funil server-side + restaurar `sitemap/4.xml` + resubmit GSC pra reindex em 48h.

## Entregue

- PR #507 — `fix(seo)(sen-fe-001): align sitemap fetcher cache with page revalidate` — **MERGED** (SHA 6f430147). Fix antipattern ISR + cache:'no-store' em `frontend/app/sitemap.ts`.
- PR #508 — `fix(seo)(sen-fe-001): align fetchContratosStats cache with page revalidate` — **MERGED**. Mesmo antipattern em `/contratos/[setor]/[uf]/page.tsx`, descoberto via grep global.
- PR #510 — `fix(seo): sitemap fetcher fallback para NEXT_PUBLIC_BACKEND_URL em build-time` — **MERGED** (SHA 4f579f7b). Fix `process.env.BACKEND_URL` undefined em build time (Dockerfile só declara `NEXT_PUBLIC_BACKEND_URL` como ARG).
- PR #509 — handoff steady-kurzweil — **MERGED**.

## Impacto em receita — **NÃO REALIZADO nesta sessão**

**REVENUE-ADJACENT (aquisição orgânica).** Shard 4 do sitemap continua retornando **0 URLs** apesar dos 3 PRs mergeados.

Baseline pré-fix: 126 clicks / 9.9k impr 28d (pos 7.1, CTR 1.3%). Esperado pós-fix completo: 10k+ URLs entity programmatic redescobertas em 48-72h. **Bloqueado por root cause adicional** — ver seção "Riscos vivos".

## Descobertas empíricas

**Gaps REVENUE-DIRECT eram falsos alarmes (memory desatualizada):**
- `MIXPANEL_TOKEN` em `bidiq-backend` → **SET** (piped-cray aplicou)
- `RESEND_WEBHOOK_SECRET` → **SET**; webhook id `758ea803` ativo (sparkling-patterson final)
- `checkout_completed` Mixpanel event → já emitido como `subscription_activated` (`backend/webhooks/handlers/checkout.py:122,217`)
- Migration `20260424180000_trial_email_delivery_tracking.sql` → já aplicada em prod
- SEO-013 index `pncp_raw_bids.orgao_cnpj` → deferred (RPCs medidos <3s p95 mesmo sem índice)

**Root causes sitemap/4 (progressivos):**
1. **Antipattern SEN-FE-001** (fixado #507 + #508): `cache:'no-store'` em fetcher + `revalidate=N` em page-level abortava ISR regen. Resolvido via `next:{revalidate:N}` alinhado.
2. **Dockerfile ARG gap** (fixado #510): `frontend/Dockerfile` declara apenas `NEXT_PUBLIC_BACKEND_URL` como ARG. `process.env.BACKEND_URL` fica undefined em build → fallback `http://localhost:8000` → connection refused. Resolvido via chain fallback `BACKEND_URL || NEXT_PUBLIC_BACKEND_URL || localhost`.
3. **Container → public URL networking** (vivo): build logs de PR #510 mostram fetches para `api.smartlic.tech` timeout **determinísticos** durante `next build`, mesmo com BACKEND_URL resolvido corretamente. `[HEALTH] WARNING: BACKEND_URL 'https://api.smartlic.tech' unreachable — latency_ms=5002` também em runtime intermitente. Hipótese: IPv6 preference (Node 20+) sobre Cloudflare IPv6 flaky no Railway container network.

## Estado final sitemap

```bash
curl -s "https://smartlic.tech/sitemap/4.xml" | grep -c "<url>"
# Atual: 0 (cache persisting empty build-time artifact; TTL 3600s)
# Cache fresh até ~20:53 UTC de 2026-04-24; ISR regen tenta runtime fetch após.
```

Shards 0-3 continuam funcionando (42+60+810+327 = 1239 URLs servidas). Apenas shard 4 (entity programmatic) afetado.

## Pendente (dono + prazo)

- [ ] **Próxima sessão (crítico)**: resolver root cause #3 (Railway container → public URL networking). Opções ranqueadas:
  1. `railway variables --service bidiq-frontend --set NODE_OPTIONS=--dns-result-order=ipv4first` + redeploy — contorna IPv6 flakiness. Low-risk, reversível.
  2. Trocar `BACKEND_URL` para URL interna Railway: `http://bidiq-uniformes.railway.internal:<port>`. Maior robustez, requer ARG Dockerfile + descobrir port backend.
  3. Adicionar `ARG BACKEND_URL` + `ENV BACKEND_URL=$BACKEND_URL` no `frontend/Dockerfile` + passar em `deploy.yml` build args — resolve issue build-time sem tocar runtime.
- [ ] Validar `curl sitemap/4.xml | grep -c "<url>"` >5000 após fix #3
- [ ] **User**: resubmit `https://smartlic.tech/sitemap.xml` no Google Search Console após shard 4 populado (instruções abaixo)
- [ ] Resend webhook HMAC verify — gap security vivo em `routes/trial_emails.py::resend_webhook` — defer até volume escalar

## GSC Resubmit — Passos (user, pós-fix#3)

1. Validar shard 4 servindo URLs:
   ```bash
   curl -s "https://smartlic.tech/sitemap/4.xml" | grep -c "<url>"
   # Esperado: >100 (preferível >5000)
   ```
2. Ir para Google Search Console → propriedade `smartlic.tech` → menu **Sitemaps**.
3. Se `https://smartlic.tech/sitemap.xml` já listado, clicar 3-pontos → **Remover sitemap** → re-adicionar.
4. Alternativa: digitar `sitemap.xml` + **Enviar** — GSC redescobre shards.
5. Status esperado: `Sucesso`, última leitura <5min.
6. 48-72h observar: GSC → **Páginas** → filtrar `Origem: Sitemap` → shard 4 reporta URLs "Descobertas". Impressões em `/contratos/orgao/{cnpj}`, `/cnpj/{cnpj}`, `/orgaos/{cnpj}`, `/fornecedores/{cnpj}`, `/municipios/{slug}`, `/itens/{catmat}` aumentam em 7-14 dias.

## Riscos vivos

- **Alta: sitemap/4 continua vazio.** Build-time fetches falhando determinísticos; runtime regen pode falhar também. Fix requer confirm user (env var Railway OU mudança Dockerfile).
- **Baixa: ISR cache empty até 3600s pós-deploy.** Se runtime fetches funcionarem após TTL, regen popula sozinho (check pós-20:53 UTC).

## KPIs da sessão

| Métrica | Alvo | Observado | Status |
|---|---|---|---|
| Shipped to prod | ≥1 mudança em caminho receita | 3 PRs merged (#507 #508 #510) | ✅ |
| Incidentes novos | 0 | 0 | ✅ |
| Tempo em docs | <15% | ~10% | ✅ |
| Instrumentação adicionada | ≥1 evento funil | 0 (gaps revenue-direct eram no-ops) | ⚠️ |
| sitemap/4 populated | >5000 URLs | 0 | ❌ |

## Memory updates

- `feedback_sen_fe_001_recidiva_sitemap.md` — NEW: após fix SEN-FE-001, grep global por outros call sites é mandatório. Recorrência 2026-04-24.
- `reference_frontend_dockerfile_backend_url_gap.md` — NEW: Dockerfile frontend declara apenas `NEXT_PUBLIC_*` como ARG; `BACKEND_URL` puro undefined em build. Fix via chain fallback OU adicionar ARG.
- `MEMORY.md` — index atualizado (trial_email_log, SEN-FE-001 recidiva, Dockerfile BACKEND_URL gap).

## Objetivo cumprido?

**Parcial.** 3 root causes de sitemap/4=0 encontrados e fixados (SEN-FE-001 + SEN-FE-001 recidiva + Dockerfile ARG gap). **4º root cause descoberto vivo**: Railway container → public URL networking. Fix requer ação com confirmação user (env var ou Dockerfile change). GSC resubmit pendente até shard 4 populado.

## Próxima ação prioritária

1. User autoriza opção 1/2/3 acima (Railway networking fix).
2. Deploy + validate sitemap/4 >100 URLs.
3. User GSC resubmit.

Custo alternativo: aguardar 3600s cache TTL + 1 probe ISR — se runtime networking funciona, regen popula. Baixo esforço, baixa certeza.
