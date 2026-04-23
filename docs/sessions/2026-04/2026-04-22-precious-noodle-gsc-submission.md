# GSC Submission Pack — Pillar Pages (precious-noodle)

**Date:** 2026-04-22
**Trigger:** PR #477 (SEO-008 pillar pages) merged at 15:10 UTC.
**Owner:** User (manual GSC submission required).

## Pre-flight verification

Run before opening GSC:

```bash
for url in licitacoes lei-14133 pncp; do
  echo "=== /guia/$url ==="
  curl -sI "https://smartlic.tech/guia/$url" | head -3
done
```

Wait for HTTP 200 (Railway deploy ~3-5 min after merge). If 404 persists past 10 min, check Railway logs:

```bash
railway logs --service bidiq-frontend --tail 50
```

## URL Inspection + Request Indexing (3 URLs)

For each pillar page, in [Google Search Console](https://search.google.com/search-console):

1. Select property `https://smartlic.tech` (or `sc-domain:smartlic.tech`).
2. Top URL Inspection bar → paste full URL.
3. After inspection completes:
   - Click **Request Indexing**.
   - Wait for confirmation toast ("URL added to priority crawl queue").
4. Repeat for next URL.

URLs to submit (in priority order):

```
https://smartlic.tech/guia/lei-14133
https://smartlic.tech/guia/licitacoes
https://smartlic.tech/guia/pncp
```

Order chosen by expected search volume (Lei 14.133 = highest competitive query in B2G niche).

## Rich Results validation (parallel, 5 min)

After 1 min indexing kicked off, validate JSON-LD via [Rich Results Test](https://search.google.com/test/rich-results):

```
https://search.google.com/test/rich-results?url=https://smartlic.tech/guia/lei-14133
https://search.google.com/test/rich-results?url=https://smartlic.tech/guia/licitacoes
https://search.google.com/test/rich-results?url=https://smartlic.tech/guia/pncp
```

Expected: 4 valid items per page (Article + BreadcrumbList + ItemList + FAQPage). If any item shows warnings, capture screenshot for follow-up — but warnings alone don't block indexing.

## Follow-up monitoring

Re-inspect URLs in GSC after 24-48h:
- Status should change from "URL is not on Google" → "URL is on Google".
- Coverage report → no errors.

If still "Crawled - currently not indexed" after 7 days:
1. Verify internal links in main nav point to /guia (sitemap shard 0 should already include these).
2. Add inbound link from a high-authority existing page (e.g., `/blog/lei-14133-novidades-2026`) if exists.
3. Submit again.

## Why these matter (single-paragraph context)

3 pillars (~11.6k words) in `/guia/` form the topical authority hub for the site's SEO inbound strategy. Each is densely linked to existing `/blog/*` posts (10 internal spokes per pillar) and to authoritative external sources (planalto, pncp, tcu). Indexation acceleration via URL Inspection vs natural crawl shifts time-to-first-impression from ~1-2 weeks to 24-48h. This is the highest-leverage SEO lever in flight.
