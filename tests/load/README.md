# SmartLic Load Tests (k6)

STORY-3.3 (EPIC-TD-2026Q2) — k6 baseline scripts for the production
backend hot paths. The legacy Locust suite (`backend/locustfile.py` +
`.github/workflows/load-test.yml`) remains in place; k6 runs alongside
it for finer-grained latency thresholds and CI baseline comparisons.

## Scripts

| Script              | Endpoint                              | Profile                  | p95 SLO  | Error SLO |
|---------------------|---------------------------------------|--------------------------|----------|-----------|
| `buscar.k6.js`      | `POST /buscar`                        | 50 RPS for 5 min         | < 3000ms | < 2%      |
| `dashboard.k6.js`   | `GET /analytics?endpoint=summary`     | 100 RPS for 5 min        | < 500ms  | < 1%      |
| `sse.k6.js`         | `GET /buscar-progress/{search_id}`    | 50 concurrent x ~60s     | connect < 2s | disconnect < 5% |

## Install k6

```bash
# macOS
brew install k6

# Ubuntu / Debian
sudo gpg -k && \
  sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
    --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69 && \
  echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" \
    | sudo tee /etc/apt/sources.list.d/k6.list && \
  sudo apt update && sudo apt install -y k6

# Windows (Chocolatey)
choco install k6

# Verify
k6 version
```

## Generate JWT fixtures

The scripts authenticate via `Authorization: Bearer <jwt>`. Pre-mint a
small pool of JWTs for test users and write them to
`tests/load/fixtures/jwts.json` (gitignored).

```bash
# Option A: Supabase admin CLI (recommended)
supabase auth admin generate-link \
  --project-ref fqqyovlzdzimiwfofdjk \
  --type magiclink \
  --email loadtest1@smartlic.tech
# then exchange the magic link for a session token via the SDK.

# Option B: gotrue REST (service-role key required)
curl -X POST "https://fqqyovlzdzimiwfofdjk.supabase.co/auth/v1/token?grant_type=password" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"loadtest1@smartlic.tech","password":"<test-password>"}' \
  | jq -r '.access_token'

# Then assemble the fixture:
cp tests/load/fixtures/jwts.json.example tests/load/fixtures/jwts.json
$EDITOR tests/load/fixtures/jwts.json   # paste 3-5 access tokens
```

WARNING: `jwts.json` is gitignored. Never commit real tokens.

## Run locally

```bash
# Smoke test (1 VU, 10s) — sanity-check script syntax and connectivity
k6 run tests/load/buscar.k6.js \
  --env SMOKE=1 \
  --env BACKEND_URL=http://localhost:8000

# Full baseline against staging
k6 run tests/load/buscar.k6.js \
  --env BACKEND_URL=https://smartlic-backend-staging.up.railway.app

k6 run tests/load/dashboard.k6.js \
  --env BACKEND_URL=https://smartlic-backend-staging.up.railway.app

k6 run tests/load/sse.k6.js \
  --env BACKEND_URL=https://smartlic-backend-staging.up.railway.app

# Custom JWT fixture path
k6 run tests/load/buscar.k6.js --env JWTS_PATH=/secure/jwts.json
```

## Export results

```bash
# JSON summary (machine-readable, used by CI baseline comparison)
k6 run tests/load/buscar.k6.js \
  --summary-export=baseline-buscar-$(date +%F).json

# Streaming JSON (one event per line, full granularity)
k6 run tests/load/buscar.k6.js --out json=buscar-stream.json
```

## k6 Cloud (optional)

```bash
# Login (one-time)
k6 cloud login --token "$K6_CLOUD_TOKEN"

# Run in cloud (50 VU free tier)
k6 cloud tests/load/buscar.k6.js \
  --env BACKEND_URL=https://smartlic-backend-staging.up.railway.app
```

## Targeting

- **DO NOT** run full load against production during business hours.
- Default target: `https://smartlic-backend-staging.up.railway.app`
- Production: only after coordination + during low-traffic windows.

## CI

Automated weekly runs against staging are wired in
`.github/workflows/k6-load-test.yml` (Mon 03:00 UTC + manual dispatch).
The workflow publishes the summary JSON as an artifact and compares
p95 against `docs/performance/baseline-2026-04-14.json`; >20% degradation
fails the build.

## Related

- `docs/performance/load-test-baseline.md` — methodology + interpretation
- `docs/performance/baseline-2026-04-14.json` — current baseline snapshot
- `.github/workflows/load-test.yml` — legacy Locust suite (kept)
