# Story SEO-019: Crawler Protection — robots.txt Crawl-delay + Rate Limit Googlebot

**Epic:** EPIC-SEO-RECOVERY-2026-Q2
**Priority:** 🟡 P2
**Story Points:** 3 SP
**Owner:** @dev
**Status:** Ready
**Depends on:** SEO-015

---

## Problem

Logs Railway backend 2026-04-24 mostram padrão típico de crawl burst:
```
GET /v1/empresa/{cnpj}/perfil-b2g (várias/seg)
GET /v1/fornecedores/{cnpj}/profile
GET /v1/contratos/orgao/{cnpj}/stats
GET /v1/orgao/{cnpj}/stats -> 404 (443s)
GET /v1/observatorio/relatorio/*
GET /v1/blog/stats/contratos/*
```

São IPs Railway internos (`100.64.0.x`) — frontend SSR/ISR + crawlers externos indiretos via frontend.

Com `WEB_CONCURRENCY=2`, até mesmo após SEO-013 fixar latência média, **bursts de crawler** (Googlebot pode abrir 10+ conexões paralelas a descobrir entity pages) podem saturar workers.

### Camadas de defesa

1. **robots.txt `Crawl-delay`** — pede a crawlers polidos (Bingbot, Yandex) 1s entre requests. Googlebot ignora Crawl-delay mas respeita GSC "crawl rate" setting.
2. **Rate limit por User-Agent no backend** — 429 após N req/min por bot, mantém user traffic privilegiado. Precisa ser generoso para não prejudicar indexação.
3. **Pricing/burst capacity** — se SEO-015 CDN absorve bem, rate limit pode ser menos crítico.

---

## Acceptance Criteria

- [ ] **AC1** — Verificar `frontend/public/robots.txt` existe e inclui:
  ```
  User-agent: *
  Allow: /
  Sitemap: https://smartlic.tech/sitemap.xml

  User-agent: Bingbot
  Crawl-delay: 1

  User-agent: YandexBot
  Crawl-delay: 2

  User-agent: GPTBot
  Disallow: /

  User-agent: CCBot
  Disallow: /
  ```
  (Bloquear GPTBot/CCBot é decisão de negócio — documentar na story.)
- [ ] **AC2** — Adicionar middleware backend rate limit por User-Agent:
  - `backend/middleware/crawler_rate_limit.py` — limits: Googlebot/Bingbot max 100 req/min, outros bots detectados (heurística UA string) 60 req/min.
  - Retornar 429 + `Retry-After: 60` em burst excedido.
  - Excluir rotas `/v1/sitemap/*` (servidas por CDN pós SEO-015) e `/health`.
  - Usar Redis pipeline para contador (já disponível no projeto).
- [ ] **AC3** — GSC Crawl Stats verificar após 7 dias: total crawl requests não deve cair >10% (queremos reduzir burst spikes, não reduzir crawl total). Documentar via GSC → Settings → Crawl stats.
- [ ] **AC4** — Prometheus `smartlic_crawler_rate_limit_429_total{user_agent}` deve ser >0 mas <1% do tráfego total — indicador que rate limit está ativo mas não agressivo.
- [ ] **AC5** — GSC Coverage não deve regredir: se Coverage "Valid" cair em 14d, rate limit foi agressivo demais. Rollback via feature flag `CRAWLER_RATE_LIMIT_ENABLED=false`.
- [ ] **AC6** — Teste de integração `backend/tests/test_crawler_rate_limit.py`:
  - Simula 200 requests Googlebot em 60s → primeiras 100 passam, resto 429
  - Rotas `/v1/sitemap/*` não rate-limited (crítico para indexação)
  - User-Agent Chrome normal não rate-limited

---

## Scope IN

- robots.txt com Crawl-delay para bots secundários
- Middleware rate limit backend por User-Agent
- Feature flag para disable emergency
- Observabilidade (Prometheus + GSC Crawl Stats monitoring)

## Scope OUT

- Block completo de crawlers (exceto GPTBot/CCBot se decisão business)
- Fingerprinting avançado (browser fingerprint, etc.)
- WAF-level rate limit (fica para Cloudflare se SEO-015 Opção A)
- Rate limit por IP (user rate limit é outro tipo — fora escopo)

---

## Implementation Notes

### robots.txt

```bash
# Verificar estado atual
curl -s https://smartlic.tech/robots.txt
cat /mnt/d/pncp-poc/frontend/public/robots.txt

# Editar se necessário
```

### Middleware rate limit

```python
# backend/middleware/crawler_rate_limit.py (NOVO)
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import re

BOT_LIMITS = {
    'googlebot': 100,
    'bingbot': 100,
    'yandexbot': 60,
    'applebot': 60,
    'facebookexternalhit': 30,
    # fallback genérico para *bot*
    '_default_bot': 60,
}
BOT_REGEX = re.compile(r'(Googlebot|Bingbot|YandexBot|AppleBot|facebookexternalhit|DuckDuckBot|baiduspider|bot|crawler|spider)', re.IGNORECASE)

EXEMPT_PATHS = ('/v1/sitemap/', '/health', '/metrics')

class CrawlerRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(p) for p in EXEMPT_PATHS):
            return await call_next(request)

        ua = request.headers.get('user-agent', '')
        match = BOT_REGEX.search(ua)
        if not match:
            return await call_next(request)

        bot_key = match.group(1).lower()
        limit = BOT_LIMITS.get(bot_key, BOT_LIMITS['_default_bot'])

        # Redis sliding window counter
        redis = get_redis()
        key = f"crawler_rate:{bot_key}:{int(time.time() // 60)}"  # per-minute bucket
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, 120)

        if current > limit:
            record_metric('smartlic_crawler_rate_limit_429_total', {'user_agent': bot_key})
            return Response(status_code=429, headers={'Retry-After': '60'})

        return await call_next(request)
```

Register em `backend/startup/middleware_setup.py` atrás de config flag `CRAWLER_RATE_LIMIT_ENABLED`.

### Feature flag

```python
# backend/config.py
CRAWLER_RATE_LIMIT_ENABLED: bool = os.getenv('CRAWLER_RATE_LIMIT_ENABLED', 'false').lower() == 'true'
```

Deploy inicialmente com flag OFF. Ativar após 7d de baseline GSC Crawl Stats + monitoring.

### Decisão GPTBot/CCBot

Disallow = user-controlled opt-out de LLM training. Justificativas:
- PRO disallow: dados B2G são competitive advantage; não queremos LLMs usando dados do SmartLic para responder queries de usuários que poderiam pagar
- CON disallow: SEO futuro pode migrar para "AI search" (Perplexity, ChatGPT com citações) — bloquear GPTBot pode excluir SmartLic dessas vitrines

**Recomendação:** disallow por ora, reavaliar em Q3 quando Perplexity/ChatGPT traffic medível.

---

## Dependencies

- **Pre:** SEO-015 (CDN absorve maior parte do crawler load — rate limit é safety net)
- **Unlocks:** Backend estabilidade sob carga sustentada

---

## Change Log

| Date | Agent | Action |
|------|-------|--------|
| 2026-04-24 | @sm (River) | Story criada. Feature flag-gated para rollout seguro — 7d baseline antes de ativar. |
| 2026-04-24 | @po (Pax) | *validate-story-draft 10/10 → GO. Status Draft → Ready. FF rollback + GPTBot decisão documentada. Pronta para @dev após SEO-015. |
