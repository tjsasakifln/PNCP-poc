/**
 * STORY-3.3 (EPIC-TD-2026Q2): k6 load test — POST /buscar
 *
 * Profile:
 *   - Ramp-up   : 1 min (0 -> target VUs)
 *   - Sustain   : 4 min at 50 RPS
 *   - Ramp-down : 30 s (target -> 0)
 *
 * Thresholds:
 *   - http_req_duration p(95) < 3000 ms
 *   - http_req_failed   rate  < 2%
 *
 * Auth: JWTs loaded from tests/load/fixtures/jwts.json (path overridable
 *       via JWTS_PATH env var).
 *
 * Run local:
 *   k6 run tests/load/buscar.k6.js \
 *     --env BACKEND_URL=https://smartlic-backend-staging.up.railway.app
 *
 * Smoke:
 *   k6 run tests/load/buscar.k6.js --env SMOKE=1 --vus 1 --duration 10s
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { SharedArray } from 'k6/data';
import { Rate, Trend } from 'k6/metrics';

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const BACKEND_URL = __ENV.BACKEND_URL || 'http://localhost:8000';
const JWTS_PATH = __ENV.JWTS_PATH || './fixtures/jwts.json';
const SMOKE = __ENV.SMOKE === '1' || __ENV.SMOKE === 'true';

// Custom metrics for easier dashboard wiring
const searchErrors = new Rate('buscar_errors');
const searchLatency = new Trend('buscar_latency_ms', true);

// ---------------------------------------------------------------------------
// JWT fixture loading (SharedArray keeps it out of per-VU memory)
// ---------------------------------------------------------------------------

const jwts = new SharedArray('jwts', function () {
  try {
    // eslint-disable-next-line no-undef
    const raw = open(JWTS_PATH);
    const parsed = JSON.parse(raw);
    const tokens = Array.isArray(parsed.tokens) ? parsed.tokens : [];
    if (tokens.length === 0) {
      throw new Error('no tokens in fixture');
    }
    return tokens;
  } catch (err) {
    // Fail fast in non-smoke mode — running without JWTs hits auth 401
    // and produces a meaningless baseline.
    if (!SMOKE) {
      throw new Error(
        `Failed to load JWTs from ${JWTS_PATH}: ${err.message}. ` +
          `See tests/load/README.md for how to generate the fixture.`
      );
    }
    return ['smoke-placeholder-jwt'];
  }
});

// ---------------------------------------------------------------------------
// Options
// ---------------------------------------------------------------------------

export const options = SMOKE
  ? {
      vus: 1,
      duration: '10s',
      thresholds: {
        http_req_failed: ['rate<0.5'], // smoke is permissive
      },
    }
  : {
      // 50 RPS sustained requires ~50 * avg_latency_s VUs; we use stages
      // with per-stage VU count tuned for ~50 RPS at 1s avg duration.
      scenarios: {
        buscar: {
          executor: 'ramping-arrival-rate',
          startRate: 0,
          timeUnit: '1s',
          preAllocatedVUs: 100,
          maxVUs: 200,
          stages: [
            { target: 50, duration: '1m' }, // ramp-up
            { target: 50, duration: '4m' }, // sustain 50 RPS
            { target: 0, duration: '30s' }, // ramp-down
          ],
        },
      },
      thresholds: {
        http_req_duration: ['p(95)<3000'],
        http_req_failed: ['rate<0.02'],
        buscar_errors: ['rate<0.02'],
      },
    };

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Returns a 10-day window ending today in YYYY-MM-DD (UTC-safe).
 * Dynamic so scripts don't rot.
 */
function recentDateRange() {
  const today = new Date();
  const end = today.toISOString().slice(0, 10);
  const start = new Date(today.getTime() - 10 * 24 * 60 * 60 * 1000)
    .toISOString()
    .slice(0, 10);
  return { data_inicial: start, data_final: end };
}

function buildPayload() {
  const { data_inicial, data_final } = recentDateRange();
  return JSON.stringify({
    ufs: ['SP', 'RJ'],
    data_inicial,
    data_final,
    setor_id: 'construcao_civil',
    modo_busca: 'abertas',
    pagina: 1,
    itens_por_pagina: 20,
  });
}

function pickToken() {
  return jwts[Math.floor(Math.random() * jwts.length)];
}

// ---------------------------------------------------------------------------
// Default VU function
// ---------------------------------------------------------------------------

export default function () {
  const token = pickToken();
  const url = `${BACKEND_URL}/buscar`;
  const payload = buildPayload();
  const params = {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    tags: { endpoint: 'buscar' },
    timeout: '30s',
  };

  const res = http.post(url, payload, params);

  searchLatency.add(res.timings.duration);
  const ok = check(res, {
    'status is 200 or 202': (r) => r.status === 200 || r.status === 202,
    'has response body': (r) => r.body && r.body.length > 0,
  });

  searchErrors.add(!ok);

  // Arrival-rate executor controls pacing; sleep kept small for smoke mode.
  if (SMOKE) {
    sleep(1);
  }
}
