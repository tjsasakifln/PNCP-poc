# GV-004: Embed Widget "Análise de Viabilidade" para Sites Terceiros

**Priority:** P1
**Effort:** L (13 SP, 6-8 dias)
**Squad:** @dev + @devops
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 3

---

## Contexto

**Calendly/Loom pattern:** transformar cada customer em distributor. Snippet `<script>` ou `<iframe>` que a empresa cola no próprio site. Widget mostra últimas licitações compatíveis + logo SmartLic + CTA. Cada embed é vector de descoberta passivo — visitors do site do cliente viram visitors do SmartLic.

Adaptação B2G: consultorias e empresas com site próprio (~50% do target) podem embedar "oportunidades em tempo real para seus clientes" — gera valor percebido + lead magnet.

---

## Acceptance Criteria

### AC1: Rota embeddable `/embed/[cnpj]`

- [ ] `frontend/app/embed/[cnpj]/page.tsx`:
  - Query params configuráveis: `?theme=light|dark&limit=5&sectors=saude,educacao&size=compact|full`
  - Renderiza lista de N últimas licitações compatíveis com CNPJ (datalake query)
  - Watermark SmartLic + CTA "Análise completa grátis"
  - Responsive 300-800px width
  - Lazy-load imagens
- [ ] CSP / X-Frame-Options específico para rota `/embed/*`:
  - `frontend/middleware.ts` adiciona `Content-Security-Policy: frame-ancestors *` APENAS para `/embed/*`
  - Resto do site mantém `frame-ancestors 'self'` (segurança preservada)
  - **Revisão @devops obrigatória no PR**

### AC2: Endpoint backend `/v1/embed/{cnpj}`

- [ ] `backend/routes/embed.py` novo:
  - GET `/v1/embed/{cnpj}` retorna JSON com licitações compatíveis
  - Rate limit agressivo: 100 req/min por CNPJ + 1000 req/min por IP origem
  - Cache Redis 30min (embed não precisa real-time)
  - CORS: `Access-Control-Allow-Origin: *` (embed abre em qualquer domínio)
  - Sanitização: só campos públicos do edital (sem dados buscante)
- [ ] Tracking pixel transparente retornado: `<img src="/v1/embed/track?embed_id=X&origin=Y" />`
  - Captura: `origin` (parent domain via Referer), `user_agent`, timestamp

### AC3: Geração do snippet (settings)

- [ ] `frontend/app/settings/embed/page.tsx`:
  - Form: CNPJ (auto-fill da conta), setores, limite, tema
  - Preview live do widget com query params selecionados
  - Código de embed em 2 formatos:
    ```html
    <iframe src="https://smartlic.tech/embed/{cnpj}?theme=light&limit=5" width="100%" height="500" frameborder="0"></iframe>
    ```
    ```html
    <div id="smartlic-widget-{cnpj}"></div>
    <script src="https://smartlic.tech/embed.js" data-cnpj="{cnpj}" data-limit="5"></script>
    ```
  - Botão "Copiar código" com confirmação
- [ ] Gated em plano Pro+ (feature flag `embed_widget_enabled`)

### AC4: Loader JS `/embed.js`

- [ ] `frontend/public/embed.js` (static, cached 1h via Cloudflare):
  - Parse data-attributes do `<script>` tag
  - Injeta iframe responsivo no `<div id="smartlic-widget-{cnpj}">`
  - Adiciona `postMessage` listener para resize dynamic do iframe baseado em conteúdo
  - Minificado (<3KB gzipped)

### AC5: Dashboard de analytics do widget

- [ ] `frontend/app/conta/embed/analytics/page.tsx`:
  - Impressions (daily/weekly)
  - Click-through rate (CTA clicks / impressions)
  - Top referring domains (sites que usam embed)
  - Conversions (signups atribuídos via embed)
- [ ] Backend `GET /v1/user/embed-analytics` agrega dados

### AC6: Attribution

- [ ] CTA "Análise completa grátis" no widget carrega UTM:
  - `utm_source=embed`
  - `utm_medium=widget`
  - `utm_campaign={cnpj}`
  - `utm_content={origin_domain}`
- [ ] Signup carrega esses UTMs → atribuição correta em Mixpanel

### AC7: Testes

- [ ] Unit `backend/tests/test_embed_route.py`
- [ ] E2E Playwright: renderiza widget em página terceira fake (setup Puppeteer cross-origin)
- [ ] Manual: colar snippet em WordPress + validar render
- [ ] Security: XSS attempt via query params — sanitized

---

## Scope

**IN:**
- Rota `/embed/[cnpj]` + endpoint backend
- CSP ajuste rota-específica
- Settings UI + snippet generator
- Loader JS
- Analytics dashboard
- Attribution UTMs

**OUT:**
- Custom branding (remover watermark) — v2 enterprise
- Embed por setor (sem CNPJ) — v2
- React/Vue/Angular components npm packages — v2
- White-label full domain (widget.cliente.com) — v3

---

## Dependências

- **GV-002** (watermark) — embed herda padrão
- Datalake query `search_datalake` RPC
- Plano Pro+ existente

---

## Riscos

- **Clickjacking via embed:** mitigar com CSP `frame-ancestors *` APENAS em rota `/embed/*`. Resto do site SAMEORIGIN. **Revisão segurança @devops obrigatória**.
- **Rate limit exploitation:** CNPJ público = alguém pode criar embed pra CNPJ alheio. Mitigação: somente owner do CNPJ verificado (via plan_data) pode gerar snippet oficial; terceiros podem usar mas atribuição vai pra owner.
- **Performance degradation:** embed em site high-traffic pode saturar. Rate limit + cache 30min; monitoring Prometheus `smartlic_embed_requests_total{cnpj,origin}`.
- **SEO noindex:** rota `/embed/*` deve ter `<meta name="robots" content="noindex">` (não indexar widgets como páginas).

---

## Arquivos Impactados

### Novos
- `frontend/app/embed/[cnpj]/page.tsx`
- `frontend/app/settings/embed/page.tsx`
- `frontend/app/conta/embed/analytics/page.tsx`
- `frontend/public/embed.js`
- `backend/routes/embed.py`
- `backend/tests/test_embed_route.py`
- `frontend/e2e-tests/embed-widget.spec.ts`

### Modificados
- `frontend/middleware.ts` (CSP rota-específica)
- `frontend/app/sitemap.ts` (excluir `/embed/*`)

---

## Testing Strategy

1. **Unit + E2E** AC7
2. **Cross-browser test** iframe render em Chrome/Firefox/Safari + 3 CMSs (WordPress, Webflow, raw HTML)
3. **Security** @devops review CSP + XSS test
4. **Load test** `k6` 1000 req/s no `/v1/embed/{cnpj}` — p95 <200ms com cache hit

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — Calendly/Loom pattern adaptado B2G; gated Pro+ para monetização |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 8/10 — **GO**. CSP complexa docada. Revisão @devops obrigatória no PR. Status Draft → Ready. |
