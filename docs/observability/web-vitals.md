# Web Vitals — Real User Monitoring (RUM)

**Owner:** `@architect` · **Since:** 2026-04-21 · **Story:** STORY-SEO-006

## What is instrumented

`frontend/app/components/WebVitalsReporter.tsx` hooks into the [`web-vitals` npm package](https://github.com/GoogleChrome/web-vitals) and forwards five Core/adjacent metrics to Google Analytics 4 as custom `web_vitals` events:

| Metric | What it measures | Good | Needs-improvement | Poor |
|--------|------------------|------|-------------------|------|
| **LCP** — Largest Contentful Paint | Time until the biggest above-the-fold element is painted | ≤ 2.5 s | 2.5–4.0 s | > 4.0 s |
| **INP** — Interaction to Next Paint | Overall interaction latency (p75 across page interactions) | ≤ 200 ms | 200–500 ms | > 500 ms |
| **CLS** — Cumulative Layout Shift | Sum of unexpected layout shifts (unitless; reported × 1000) | ≤ 0.1 | 0.1–0.25 | > 0.25 |
| **TTFB** — Time To First Byte | Server responsiveness | ≤ 800 ms | 800–1800 ms | > 1800 ms |
| **FCP** — First Contentful Paint | First painted content on the page | ≤ 1.8 s | 1.8–3.0 s | > 3.0 s |

Thresholds are Google's — align with what Search Console reports in the **Core Web Vitals** section.

## How to see the data

1. Open **GA4** → property for `smartlic.tech`.
2. **Reports → Engagement → Events** — confirm `web_vitals` shows a rising count after deploy (lag ~1 h).
3. **Explore → Free form**:
   - Dimensions: `Event name`, `metric_name` (custom), `Page path`
   - Metrics: `Event count`, **custom metric** `metric_value` with aggregation `Percentile 75`
   - Filter: `Event name = web_vitals`
   - Rows: `Page path`; Columns: `metric_name`
4. Save the exploration as **Web Vitals RUM p75**.

Custom dimension / metric registration (one-time in GA4 Admin):

| Type | Name | Scope | Event param |
|------|------|-------|-------------|
| Custom dimension | `metric_name` | Event | `event_label` |
| Custom metric | `metric_value` | Event | `metric_value` (unit: Standard) |
| Custom dimension | `metric_rating` | Event | `metric_rating` |

## How to react to regression

1. **LCP p75 > 3 s on `/`, `/planos`, or `/buscar` for 3 consecutive days** — open a perf bug. Common culprits: unoptimized hero image, third-party script blocking render, font loading strategy.
2. **INP p75 > 300 ms on any top-traffic page** — investigate long tasks via Chrome DevTools Performance panel; consider `startTransition` or code-splitting.
3. **CLS p75 > 0.15** — find the offending element: `web.dev/debug-layout-shifts`. Usually missing `width`/`height` on images or late-loading ads/embeds.
4. **TTFB p75 > 1 s consistently** — backend/CDN issue, coordinate with `@devops`.

## Complementary signals

- **Lighthouse CI** (runs on PRs) — synthetic lab measurement. Good for catching regressions in PR before merge.
- **Google Search Console → Core Web Vitals** — 28-day rolling aggregate at URL-group level. Lags ~3 weeks behind deploy.
- **Microsoft Clarity** — heatmaps + session recordings, not quantitative CWV.

The `web_vitals` GA4 stream is the **only** real-time, per-URL RUM source in this stack. Trust it over lab data for production decisions.

## Scope & non-goals

- Does not auto-alert on regression. Dashboard is pull-only. If/when needed, a future story can wire a GA4 Alert or a Grafana check over the BigQuery export.
- Sampling: 100% (GA4 default — SmartLic traffic is well below the 10M events/day threshold that triggers sampling).
- No PII in the payload — only metric IDs and ratings.

## Troubleshooting

**"No web_vitals events in GA4"**
- `window.gtag` is missing — check `GoogleAnalytics` component mounted and consent is granted.
- Ad-blocker stripping `gtag` — expected; consented real users will still report.
- DNT (Do Not Track) honored via consent banner → no data for those users.

**"Values look way too high"**
- CLS is multiplied by 1000 when stored as `value` to fit GA4's integer metric aggregation. The raw float is preserved in `metric_value` — use that for accurate analysis.

## Related

- `frontend/app/components/WebVitalsReporter.tsx` — implementation
- `frontend/app/layout.tsx` — mount point
- `frontend/app/components/GoogleAnalytics.tsx` — `gtag` provider (consent-gated)
- STORY-SEO-005 (planned) — `/admin/seo` dashboard integration (pull GA4 Data API → display CWV side-by-side with GSC)
