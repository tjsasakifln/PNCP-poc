/**
 * STORY-3.3 (EPIC-TD-2026Q2): k6 load test — GET /analytics?endpoint=summary
 *
 * Profile:
 *   - Ramp-up   : 1 min (0 -> 100 RPS)
 *   - Sustain   : 4 min at 100 RPS
 *   - Ramp-down : 30 s
 *
 * Thresholds:
 *   - http_req_duration p(95) < 500 ms
 *   - http_req_failed   rate  < 1%
 *
 * Run:
 *   k6 run tests/load/dashboard.k6.js \
 *     --env BACKEND_URL=https://smartlic-backend-staging.up.railway.app
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { SharedArray } from 'k6/data';
import { Rate, Trend } from 'k6/metrics';

const BACKEND_URL = __ENV.BACKEND_URL || 'http://localhost:8000';
const JWTS_PATH = __ENV.JWTS_PATH || './fixtures/jwts.json';
const SMOKE = __ENV.SMOKE === '1' || __ENV.SMOKE === 'true';

const dashErrors = new Rate('dashboard_errors');
const dashLatency = new Trend('dashboard_latency_ms', true);

const jwts = new SharedArray('jwts', function () {
  try {
    // eslint-disable-next-line no-undef
    const raw = open(JWTS_PATH);
    const parsed = JSON.parse(raw);
    const tokens = Array.isArray(parsed.tokens) ? parsed.tokens : [];
    if (tokens.length === 0) throw new Error('no tokens in fixture');
    return tokens;
  } catch (err) {
    if (!SMOKE) {
      throw new Error(
        `Failed to load JWTs from ${JWTS_PATH}: ${err.message}. ` +
          `See tests/load/README.md.`
      );
    }
    return ['smoke-placeholder-jwt'];
  }
});

export const options = SMOKE
  ? {
      vus: 1,
      duration: '10s',
      thresholds: { http_req_failed: ['rate<0.5'] },
    }
  : {
      scenarios: {
        dashboard: {
          executor: 'ramping-arrival-rate',
          startRate: 0,
          timeUnit: '1s',
          preAllocatedVUs: 100,
          maxVUs: 300,
          stages: [
            { target: 100, duration: '1m' },
            { target: 100, duration: '4m' },
            { target: 0, duration: '30s' },
          ],
        },
      },
      thresholds: {
        http_req_duration: ['p(95)<500'],
        http_req_failed: ['rate<0.01'],
        dashboard_errors: ['rate<0.01'],
      },
    };

function pickToken() {
  return jwts[Math.floor(Math.random() * jwts.length)];
}

export default function () {
  const token = pickToken();
  const url = `${BACKEND_URL}/analytics?endpoint=summary`;
  const params = {
    headers: { Authorization: `Bearer ${token}` },
    tags: { endpoint: 'analytics_summary' },
    timeout: '10s',
  };

  const res = http.get(url, params);
  dashLatency.add(res.timings.duration);
  const ok = check(res, {
    'status is 200': (r) => r.status === 200,
    'has body': (r) => r.body && r.body.length > 0,
  });
  dashErrors.add(!ok);

  if (SMOKE) sleep(1);
}
