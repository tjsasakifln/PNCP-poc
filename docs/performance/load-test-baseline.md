# SmartLic Load Test Baseline

**Owner:** @qa + @devops
**Story:** STORY-3.3 (EPIC-TD-2026Q2)
**Last updated:** 2026-04-14

This document defines the methodology, thresholds, and interpretation
guidance for the k6-based load test baseline. The baseline gives us
objective evidence that performance-oriented stories
(TD-SYS-014 LLM async, TD-SYS-003 Railway timeout, etc.) actually moved
the numbers.

## Methodology

1. **Tool:** k6 v0.50+ (open-source CLI). Parallel suite to the legacy
   Locust runner; both are kept until k6 has 4 weeks of stable history.
2. **Target:** `smartlic-backend-staging.up.railway.app` (Railway tier
   identical to production: same plan, same resources, same env vars
   except `OPENAI_API_KEY=sk-test`).
3. **Scripts:** `tests/load/{buscar,dashboard,sse}.k6.js` — see
   `tests/load/README.md`.
4. **Cadence:** Weekly automated run (Mon 03:00 UTC) via
   `.github/workflows/k6-load-test.yml`. Manual `workflow_dispatch` for
   ad-hoc baselining (e.g. before/after a perf story merge).
5. **Auth:** Pre-minted Supabase JWTs for 3-5 test users with active
   `smartlic_pro` plan. JWTs stored in repo secret `LOAD_TEST_JWTS`
   (multi-line) and written to `tests/load/fixtures/jwts.json` at run
   time.

## Thresholds

| Endpoint                              | RPS / VU | Duration | p95 SLO  | Error SLO | Rationale |
|---------------------------------------|----------|----------|----------|-----------|-----------|
| `POST /buscar`                        | 50 RPS   | 5 min    | < 3000ms | < 2%      | Search is the hot path; users abandon at >3s. Async-first since CRIT-072 returns 202 in <2s, so 3s p95 leaves headroom for SSE setup. |
| `GET /analytics?endpoint=summary`     | 100 RPS  | 5 min    | < 500ms  | < 1%      | Read-only summary, served from materialized view. Anything over 500ms p95 means the dashboard renders late. |
| `GET /buscar-progress/{id}` (SSE)     | 50 conns | 60 s     | connect < 2s; disconnect rate < 5% | n/a | Long-lived stream. Connect time = handshake + Railway proxy + first byte. Premature disconnect (<5s) indicates Railway 60s idle / undici BodyTimeout regression. |

Threshold breach in CI fails the build (workflow exits non-zero).

## Interpreting k6 output

A k6 run prints a summary like:

```
http_req_duration..............: avg=420ms min=80ms med=380ms max=2.4s p(90)=890ms p(95)=1.2s p(99)=2.1s
http_req_failed................: 0.43% ✓ 12 ✗ 2788
http_reqs......................: 2800 9.32/s
iterations.....................: 2800 9.32/s
vus............................: 50   min=0 max=50
```

Key fields:

- **`http_req_duration` p(95) / p(99)** — the latency tail. p(95) is
  the SLO field; p(99) tells you how bad the worst 1% is (often LLM
  cold-start or Railway proxy hiccups).
- **`http_req_failed` rate** — share of requests that returned 4xx /
  5xx or timed out. Compare to the per-endpoint error SLO above.
- **`http_reqs` per second** — actual achieved RPS. If this is well
  below the targeted RPS, the executor was VU-bound or the backend was
  rejecting connections.
- **Custom metrics** — each script defines a `Trend` and a `Rate` with
  a script-specific name (e.g. `buscar_latency_ms`,
  `sse_premature_disconnects`). These map 1:1 to Grafana panels.

## Snapshotting a baseline

```bash
# Run with summary export
k6 run tests/load/buscar.k6.js \
  --env BACKEND_URL=https://smartlic-backend-staging.up.railway.app \
  --summary-export=docs/performance/baseline-$(date +%F)-buscar.json

# Repeat for dashboard and sse, then aggregate into a single JSON:
node tests/load/scripts/aggregate-baseline.js \
  --buscar baseline-2026-04-14-buscar.json \
  --dashboard baseline-2026-04-14-dashboard.json \
  --sse baseline-2026-04-14-sse.json \
  --out docs/performance/baseline-2026-04-14.json
```

The aggregated file follows the schema in
`docs/performance/baseline-2026-04-14.json` and is the file the CI
comparison step reads.

## Comparing runs

The CI workflow does this automatically. Manually:

```bash
# Pull current baseline + the run you want to compare
NEW=docs/performance/baseline-2026-05-01.json
OLD=docs/performance/baseline-2026-04-14.json

python3 - <<'PY'
import json, sys
new = json.load(open("$NEW"))
old = json.load(open("$OLD"))
for endpoint in new["endpoints"]:
    o = old["endpoints"][endpoint]
    n = new["endpoints"][endpoint]
    if o["p95_ms"] is None or n["p95_ms"] is None:
        continue
    delta = (n["p95_ms"] - o["p95_ms"]) / o["p95_ms"] * 100
    flag = "FAIL" if delta > 20 else "OK"
    print(f"{endpoint}: p95 {o['p95_ms']}ms -> {n['p95_ms']}ms ({delta:+.1f}%) {flag}")
PY
```

Rule of thumb: **>20% p95 degradation on any endpoint blocks merge**.
Improvements of any size are welcome and become the new baseline once
verified for 2 consecutive runs.

## Grafana dashboard

Public placeholder (will be wired once Grafana Cloud account is set up):

- Dashboard: `https://grafana.smartlic.tech/d/k6-baseline`
- Source: k6 Cloud streaming integration (token in repo secret
  `K6_CLOUD_TOKEN`, opt-in via `--out cloud` flag)

Until the Grafana panel is live, the GitHub Actions artifact (summary
JSON + run log) is the source of truth. Each run is retained for
30 days.

## Risks and follow-ups

- **R1 — Staging != prod:** Railway plan parity is enforced manually.
  Capture `railway service info` output as part of each baseline run
  to detect drift.
- **R2 — JWT expiry:** Supabase access tokens default to 1h. The
  weekly job re-fetches from `LOAD_TEST_JWTS` secret each run; rotate
  the secret monthly.
- **R3 — Cost:** Running k6 in CI costs ~3 minutes of GitHub Actions
  per week. SSE script is the most expensive (5 min wall clock). Total
  monthly cost: ~1h of `ubuntu-latest`, well within free tier.
- **R4 — k6 SSE limitation:** k6 has no native SSE module; we use
  long-poll HTTP with 65s timeout as a proxy. This measures connect
  time and connection persistence accurately, but does NOT verify SSE
  event payloads. Functional SSE coverage stays in Playwright
  (`frontend/e2e-tests/`).
