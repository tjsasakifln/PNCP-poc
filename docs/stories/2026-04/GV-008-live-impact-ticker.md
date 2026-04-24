# GV-008: Live Impact Ticker — Landing Page Agregado 24h

**Priority:** P2
**Effort:** XS (3 SP, 1-2 dias)
**Squad:** @dev + @ux-design-expert
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 4

---

## Contexto

Landing pages que mostram impacto real-time (Calendly "X meetings scheduled today", Stripe "Y processed today") geram social proof dinâmico + urgência/bandwagon effect.

SmartLic tem dados agregáveis facilmente:
- Análises feitas últimas 24h
- Valor total das oportunidades analisadas (soma `valor_estimado` positivas)
- Contagem users únicos ativos

Ticker: "SmartLic ajudou descobrir **R$ X em oportunidades** nas últimas 24h" — elevator pitch visual.

---

## Acceptance Criteria

### AC1: Endpoint público agregado

- [ ] `backend/routes/public_stats.py` novo:
  - `GET /v1/public/impact-24h` retorna:
    ```json
    {
      "analyses_count": 847,
      "opportunities_value_total_brl": 24750000,
      "unique_users_active": 312,
      "sectors_covered": 15,
      "timestamp": "2026-04-24T14:30:00Z"
    }
    ```
  - Cache Redis 60s
  - Pseudonimização: valor é SOMA agregada (não expõe individual)
  - Rate limit 100 req/min por IP (endpoint público sem auth)

### AC2: Componente `ImpactTicker`

- [ ] `frontend/components/ImpactTicker.tsx`:
  - Banner animado na landing (full-width, ~80px height)
  - Text: "SmartLic ajudou descobrir **R$ {valor_formatado}** em oportunidades nas últimas 24h"
  - Count-up animation ao mount (Framer Motion)
  - Refresh 60s (polling ou Server-Sent Events se leve)
  - Respeita `prefers-reduced-motion` (mostra estático sem animação)
  - Mobile: texto compacto "R$ {valor} em oportunidades • 24h"

### AC3: Integração landing page

- [ ] `frontend/app/page.tsx` adiciona `<ImpactTicker />` acima do hero principal (ou sticky top)
- [ ] Fallback: se endpoint falhar, ticker não renderiza (graceful degradation)

### AC4: Tracking

- [ ] Mixpanel `impact_ticker_viewed` (uma vez por session)

### AC5: Testes

- [ ] Unit `backend/tests/test_public_stats.py`
- [ ] Unit `frontend/__tests__/components/ImpactTicker.test.tsx`
- [ ] E2E Playwright: landing mostra ticker + fallback gracioso

---

## Scope

**IN:**
- Endpoint agregado
- Component animado
- Integração landing

**OUT:**
- Ticker por setor/UF (granular) — v2
- Real-time WebSocket (overkill, 60s polling suficiente) — v2
- Historical graphs/charts — v2

---

## Dependências

- **Nenhuma** — independente

---

## Riscos

- **Contagem baixa desanima (ex: "3 análises últimas 24h"):** fallback para janela 7d se <20 análises/24h; comunicação adaptativa
- **Manipulação via bot:** rate limit 100/min por IP + honeypot anti-bot no endpoint; monitor Sentry se count cresce anomalously

---

## Arquivos Impactados

### Novos
- `frontend/components/ImpactTicker.tsx`
- `backend/routes/public_stats.py`
- `backend/tests/test_public_stats.py`
- `frontend/__tests__/components/ImpactTicker.test.tsx`

### Modificados
- `frontend/app/page.tsx` (adiciona ticker)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — Calendly-style live social proof |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 8/10 — **GO**. Status Draft → Ready. |
