"""STORY-SEO-015: Cache-Control headers compartilhados para endpoints /v1/sitemap/*.

Habilita CDN/proxy intermediarios (Cloudflare, browsers, crawlers) a cachear
respostas por 6h fresh + 12h stale-while-revalidate + 24h stale-if-error.

Reduz carga no backend (WEB_CONCURRENCY=2) durante crawler bursts (Googlebot
parallelism pode atingir 10+ conexoes simultaneas em endpoint sitemap).

Defer (story SEO-015.1): Redis L2 cache layer + purge pos-ingestion.
TTL natural 6h ja cobre 90% do problema com zero codigo extra alem de headers.

Uso em handler:

    from fastapi import Response
    from routes._sitemap_cache_headers import SITEMAP_CACHE_HEADERS

    @router.get("/sitemap/foo", ...)
    async def sitemap_foo(response: Response):
        response.headers.update(SITEMAP_CACHE_HEADERS)
        ...
"""

# 6h fresh (max-age=21600) + 12h stale-while-revalidate + 24h stale-if-error.
# Tradeoffs:
#   - 6h fresh: ingestion daily 2am BRT; sitemap muda <=1x/dia. 6h evita over-stale
#     entre ingestion (max 1 ciclo perdido).
#   - stale-while-revalidate=43200 (12h): CDN serve stale + dispara refresh em
#     background. Crawler nunca ve timeout enquanto backend gera nova versao.
#   - stale-if-error=86400 (24h): se backend 5xx, CDN serve stale por ate 24h.
#     Crawler nao detecta erros transientes.
SITEMAP_CACHE_HEADERS = {
    "Cache-Control": "public, max-age=21600, stale-while-revalidate=43200, stale-if-error=86400",
    "Vary": "Accept-Encoding",
}
