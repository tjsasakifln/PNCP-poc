# Performance Testing Guide

**Version:** 1.0
**Date:** 2026-01-31
**Issues:** #110, #115, #126

---

## Overview

BidIQ now has comprehensive performance testing infrastructure covering:

1. **Image Optimization** - next/image with priority loading
2. **Backend Benchmarks** - pytest-benchmark for regression tracking
3. **Frontend Performance** - Lighthouse CI for Core Web Vitals
4. **Load Testing** - Locust for scalability validation

---

## 1. Image Optimization (Issue #110)

### What Changed

✅ **Before:** `<img>` tag with no optimization (slow LCP)
✅ **After:** `next/image` with priority loading and remote pattern configuration

### Configuration

**File:** `frontend/next.config.js`

```javascript
images: {
  remotePatterns: [
    {
      protocol: 'https',
      hostname: 'static.wixstatic.com',
      pathname: '/media/**',
    },
  ],
}
```

### Benefits

- **Automatic optimization:** WebP/AVIF conversion
- **Lazy loading:** Off-screen images load on demand
- **Priority loading:** Above-the-fold logo loads immediately
- **Responsive images:** Correct size served per device
- **Better LCP:** Largest Contentful Paint < 2.5s (Core Web Vital)

### Verification

```bash
cd frontend
npm run build
npm run lighthouse

# Check for:
# ✅ unsized-images: Pass
# ✅ LCP < 2500ms
# ✅ modern-image-formats: Pass
```

---

## 2. Backend Performance Benchmarks (Issue #115 - Part 1)

### Overview

pytest-benchmark tracks performance of critical backend functions to catch regressions.

### Benchmark Suites

#### test_benchmark_filter.py (19 benchmarks)

**Tests:**
- Text normalization (short, long, special chars)
- Individual filters (UF, valor, keywords)
- Full filter pipeline
- Throughput (1000 licitações)
- Edge cases (empty, very long)

**Performance Targets:**
- `normalizar_texto` (short): < 10 μs
- `filtrar_por_uf`: < 5 μs
- `filtrar_por_valor`: < 5 μs
- `filtrar_por_keywords`: < 50 μs
- `filtrar_licitacao` (full): < 100 μs
- Throughput (1000 items): < 100 ms

#### test_benchmark_pncp_client.py (11 benchmarks)

**Tests:**
- Request building
- Response parsing
- Pagination logic
- Data processing (100, 500 items)
- URL construction

**Performance Targets:**
- `build_params`: < 5 μs
- `parse_response`: < 20 μs
- `process_500_items`: < 500 μs

### Running Benchmarks

```bash
cd backend

# Run all benchmarks
pytest tests/test_benchmark_*.py --benchmark-only -v

# Save baseline
pytest --benchmark-only --benchmark-save=baseline

# Compare with baseline
pytest --benchmark-only --benchmark-compare=baseline

# Auto-save to .benchmarks/
pytest --benchmark-only --benchmark-autosave

# Generate histogram
pytest --benchmark-only --benchmark-histogram=histogram
```

### Output Example

```
---------------------------- benchmark: filter_uf_match ----------------------------
Name (time in us)          Min      Max     Mean  StdDev  Median     IQR  Outliers
---------------------------------------------------------------------------------
test_benchmark_...       3.20    15.40     3.45    0.82    3.30    0.40     12;15
---------------------------------------------------------------------------------
```

### CI Integration

Benchmarks run in CI but don't fail builds (informational only). Add `--benchmark-compare` to fail on regressions:

```yaml
- name: Run benchmarks
  run: |
    cd backend
    pytest --benchmark-only --benchmark-compare=baseline || true
```

---

## 3. Frontend Performance Audits (Issue #115 - Part 2)

### Lighthouse CI

**Configuration:** `frontend/lighthouserc.js`

Runs automated performance audits on every PR and push to main.

### Performance Budgets

**Core Web Vitals:**
- First Contentful Paint (FCP): < 2.0s
- Largest Contentful Paint (LCP): < 2.5s
- Cumulative Layout Shift (CLS): < 0.1
- Total Blocking Time (TBT): < 300ms
- Speed Index (SI): < 3.4s
- Time to Interactive (TTI): < 3.8s

**Category Scores (0-100):**
- Performance: 85+
- Accessibility: 90+
- Best Practices: 90+
- SEO: 90+

### Running Locally

```bash
cd frontend

# Build first
npm run build

# Run Lighthouse CI
npm run lighthouse

# Or step-by-step:
npm run lighthouse:collect  # Collect data
npm run lighthouse:assert   # Check thresholds
```

### CI Integration

**Workflow:** `.github/workflows/lighthouse.yml`

**Triggers:**
- Pull requests (frontend changes)
- Push to main (frontend changes)

**Output:**
- PR comment with scores and Core Web Vitals
- Artifacts with full Lighthouse reports
- Build fails if Performance < 85

**Example PR Comment:**

```
🚦 Lighthouse Performance Report

Category Scores
Performance: 🟢 92
Accessibility: 🟢 95
Best Practices: 🟢 91
SEO: 🟢 100

Core Web Vitals
FCP: 1200ms (< 2000ms) ✅
LCP: 1800ms (< 2500ms) ✅
CLS: 0.05 (< 0.1) ✅
TBT: 150ms (< 300ms) ✅

Performance Budget
✅ Performance score meets threshold (85+)
✅ LCP within budget (< 2.5s)
✅ CLS within budget (< 0.1)
```

---

## 4. Load Testing (Issue #126)

### Overview

Locust load testing validates backend scalability under concurrent user load.

**File:** `backend/locustfile.py`

### Test Scenarios

#### 1. Smoke Test (5 users, 30s)

Quick validation that endpoints work under minimal load.

```bash
cd backend
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 5 \
  --spawn-rate 1 \
  --run-time 30s \
  --headless \
  --only-summary
```

#### 2. Load Test (50 users, 2min)

Realistic concurrent user load.

```bash
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 120s \
  --headless \
  --csv=results/load-test
```

#### 3. Stress Test (100 users, 5min)

Maximum parameters (5 UFs, 30 day range) to test breaking points.

```bash
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 300s \
  --headless \
  --user-class StressTestUser
```

#### 4. Endurance Test (20 users, 30min)

Long-running test to detect memory leaks and resource exhaustion.

```bash
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 20 \
  --spawn-rate 2 \
  --run-time 1800s \
  --headless
```

### User Behaviors

**BidIQUser (default):**
- Health check (1x weight)
- Search uniformes (10x weight)
- Download Excel (3x weight)
- Wait 1-3s between requests (realistic think time)

**StressTestUser:**
- Aggressive search only
- Always uses max parameters (5 UFs, 30 days)
- Minimal wait time (0-1s)

### Running Interactively

```bash
cd backend
locust -f locustfile.py --host=http://localhost:8000

# Open browser to http://localhost:8089
# Configure users and spawn rate
# Watch real-time charts
```

### CI Integration

**Workflow:** `.github/workflows/load-test.yml`

**Triggers:**
- Weekly (Sunday 2 AM UTC)
- Manual dispatch (configurable users/duration)
- Pull requests (backend changes)

**Quality Gates:**
- Failure rate < 5%
- P95 response time < 10s
- Throughput > 1 req/s

**Manual Trigger:**

```bash
# Via GitHub UI: Actions → Load Testing → Run workflow
# Or via CLI:
gh workflow run load-test.yml \
  -f users=100 \
  -f duration=300s
```

### Output Artifacts

**CSV Files:**
- `load-test_stats.csv` - Per-endpoint statistics
- `load-test_failures.csv` - Failure details
- `load-test_exceptions.csv` - Exception traces

**HTML Report:**
- `load-test-report.html` - Interactive charts and graphs

**Custom Metrics:**

```
CUSTOM PERFORMANCE METRICS
📊 Search Endpoint (/api/buscar):
   Requests: 234
   Avg: 3200ms
   Min: 1200ms
   Max: 8900ms
   P95: 5600ms

📦 Download Endpoint (/api/download):
   Requests: 45
   Avg: 450ms
   Min: 200ms
   Max: 1200ms
```

---

## Performance Monitoring in CI/CD

### GitHub Actions Summary

| Workflow | Trigger | Runs | Quality Gate |
|----------|---------|------|--------------|
| `tests.yml` | Push, PR | All tests + coverage | Coverage 70%+ (backend), 60%+ (frontend) |
| `lighthouse.yml` | Push, PR (frontend) | Lighthouse CI | Performance 85+ |
| `load-test.yml` | Weekly, Manual, PR (backend) | Locust load test | Failure rate < 5% |

### PR Checks

Every PR automatically runs:
1. ✅ Unit tests (backend + frontend)
2. ✅ E2E tests (Playwright)
3. ✅ Lighthouse audit (if frontend changes)
4. ✅ Load test (if backend changes)

### Viewing Results

**In PR:**
- Automated comments with scores/metrics
- Check details for full logs

**In Actions:**
- Artifacts with detailed reports
- CSV data for trending analysis

---

## Best Practices

### 1. Run Locally Before Pushing

```bash
# Backend
cd backend
pytest --benchmark-only  # Quick check
pytest --cov             # Full tests

# Frontend
cd frontend
npm run build
npm run lighthouse
```

### 2. Establish Baselines

```bash
# Save baseline after optimization
pytest --benchmark-save=after-optimization

# Compare future runs
pytest --benchmark-compare=after-optimization
```

### 3. Monitor Trends

- Save benchmark CSVs to repository (`.benchmarks/`)
- Use `pytest-benchmark compare` to track regressions
- Review Lighthouse trends in CI artifacts

### 4. Load Test Staging

Before production deploy:

```bash
# Against staging environment
locust -f locustfile.py \
  --host=https://staging.bidiq.com \
  --users 100 \
  --spawn-rate 10 \
  --run-time 300s \
  --headless
```

---

## Troubleshooting

### Lighthouse Fails with "Missing Images"

**Issue:** next/image requires remote patterns configured.

**Fix:** Add hostname to `next.config.js` → `images.remotePatterns`

### Benchmarks Show Regressions

**Issue:** Code change slowed down critical path.

**Fix:**
1. Run `pytest --benchmark-compare=baseline --benchmark-histogram=perf`
2. Identify slow function
3. Profile with `cProfile` or `line_profiler`
4. Optimize and re-benchmark

### Load Test Fails with High Failure Rate

**Issue:** Backend can't handle load.

**Fix:**
1. Check backend logs for errors
2. Monitor CPU/memory during test
3. Identify bottleneck (PNCP API, LLM, Excel generation)
4. Add caching, optimize queries, or scale horizontally

### Lighthouse Performance Score Drops

**Issue:** New code increased bundle size or blocking time.

**Fix:**
1. Check bundle size: `npm run build`
2. Analyze: `npx @next/bundle-analyzer`
3. Code split heavy components
4. Lazy load non-critical features

---

## Next Steps

### Recommended Enhancements

1. **Backend:**
   - Add database query benchmarks
   - Profile LLM calls with different models
   - Cache PNCP responses in Redis

2. **Frontend:**
   - Set up Lighthouse Server for historical tracking
   - Add Real User Monitoring (RUM)
   - Bundle size budgets in CI

3. **Load Testing:**
   - Test with distributed Locust (master/worker)
   - Add APM (Application Performance Monitoring)
   - Chaos engineering (simulate PNCP API failures)

---

## References

- **pytest-benchmark:** https://pytest-benchmark.readthedocs.io/
- **Lighthouse CI:** https://github.com/GoogleChrome/lighthouse-ci
- **Locust:** https://docs.locust.io/
- **Core Web Vitals:** https://web.dev/vitals/
- **Next.js Image Optimization:** https://nextjs.org/docs/app/building-your-application/optimizing/images

---

**Related Issues:**
- #110: Images use `<img>` instead of next/image (slow LCP) ✅
- #115: No performance benchmarks (regressions untracked) ✅
- #126: No load testing (backend scalability unknown) ✅
