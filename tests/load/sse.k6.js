/**
 * STORY-3.3 (EPIC-TD-2026Q2): k6 load test — SSE /buscar-progress/{search_id}
 *
 * Profile: 50 concurrent connections, each held for ~60s.
 *
 * NOTE: k6 has no native SSE module. SSE is just HTTP with
 * `text/event-stream`; we open a long-lived `http.get()` with a 65s
 * timeout. The connection holds open until the server closes it
 * (search complete) or the timeout fires.
 *
 * Thresholds:
 *   - http_req_connecting p(95) < 2000 ms (connect time)
 *   - http_req_failed     rate  < 5%      (premature disconnects)
 *
 * search_id sourcing: by default uses a placeholder UUID. For more
 * realistic runs, each VU can POST /buscar first to get a real
 * search_id (set REALISTIC=1). Placeholder is fine for connect-time
 * baseline.
 *
 * Run:
 *   k6 run tests/load/sse.k6.js \
 *     --env BACKEND_URL=https://smartlic-backend-staging.up.railway.app
 */

import http from 'k6/http';
import { check } from 'k6';
import { SharedArray } from 'k6/data';
import { Rate, Trend } from 'k6/metrics';

const BACKEND_URL = __ENV.BACKEND_URL || 'http://localhost:8000';
const JWTS_PATH = __ENV.JWTS_PATH || './fixtures/jwts.json';
const SMOKE = __ENV.SMOKE === '1' || __ENV.SMOKE === 'true';
const REALISTIC = __ENV.REALISTIC === '1';
const PLACEHOLDER_SEARCH_ID =
  __ENV.SSE_SEARCH_ID || '00000000-0000-0000-0000-000000000001';

const sseConnectTime = new Trend('sse_connect_ms', true);
const sseHoldTime = new Trend('sse_hold_ms', true);
const sseDisconnectErr = new Rate('sse_premature_disconnects');

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
      duration: '15s',
      thresholds: { http_req_failed: ['rate<0.5'] },
    }
  : {
      scenarios: {
        sse: {
          executor: 'constant-vus',
          vus: 50,
          duration: '5m',
          gracefulStop: '70s',
        },
      },
      thresholds: {
        http_req_connecting: ['p(95)<2000'],
        http_req_failed: ['rate<0.05'],
        sse_premature_disconnects: ['rate<0.05'],
      },
    };

function pickToken() {
  return jwts[Math.floor(Math.random() * jwts.length)];
}

function getSearchId(token) {
  if (!REALISTIC) return PLACEHOLDER_SEARCH_ID;
  // Realistic mode: POST /buscar to spawn a search and capture search_id
  const today = new Date();
  const end = today.toISOString().slice(0, 10);
  const start = new Date(today.getTime() - 10 * 24 * 60 * 60 * 1000)
    .toISOString()
    .slice(0, 10);
  const res = http.post(
    `${BACKEND_URL}/buscar`,
    JSON.stringify({
      ufs: ['SP'],
      data_inicial: start,
      data_final: end,
      setor_id: 'construcao_civil',
    }),
    {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      timeout: '10s',
    }
  );
  try {
    const body = JSON.parse(res.body);
    return body.search_id || PLACEHOLDER_SEARCH_ID;
  } catch (_e) {
    return PLACEHOLDER_SEARCH_ID;
  }
}

export default function () {
  const token = pickToken();
  const searchId = getSearchId(token);
  const url = `${BACKEND_URL}/buscar-progress/${searchId}`;
  const params = {
    headers: {
      Accept: 'text/event-stream',
      Authorization: `Bearer ${token}`,
      'Cache-Control': 'no-cache',
    },
    tags: { endpoint: 'sse_progress' },
    timeout: '65s',
  };

  const start = Date.now();
  const res = http.get(url, params);
  const elapsed = Date.now() - start;

  sseConnectTime.add(res.timings.connecting);
  sseHoldTime.add(elapsed);

  // Premature disconnect: connection closed in <5s without SSE data.
  // SSE responses always start with HTTP 200 even if connection drops
  // early; we look at body length + elapsed time as a heuristic.
  const isPremature = elapsed < 5000 && (!res.body || res.body.length < 50);
  sseDisconnectErr.add(isPremature);

  check(res, {
    'sse status is 200': (r) => r.status === 200,
    'sse held >= 5s OR completed': (r) => elapsed >= 5000 || r.body.includes('"status":"completed"'),
    'has event-stream content-type': (r) => {
      const ct = r.headers['Content-Type'] || r.headers['content-type'] || '';
      return ct.includes('text/event-stream');
    },
  });
}
