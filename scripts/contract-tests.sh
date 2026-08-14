#!/usr/bin/env bash
# =============================================================================
# Contract Tests — OpenAPI schema compliance para backend<>frontend
#
# Issue #1970: Valida que respostas reais do backend estao em conformidade com
# o schema OpenAPI, evitando que mudancas no backend quebrem o frontend
# silenciosamente.
#
# Usage:
#   ./scripts/contract-tests.sh                          # TestClient local
#   BACKEND_URL=http://127.0.0.1:8000 ./scripts/contract-tests.sh # local explicit target
#   ./scripts/contract-tests.sh --specs                  # mostra schemas expected
#   ./scripts/contract-tests.sh --help                   # show help
#
# Requer:
#   - Python 3.12+ com FastAPI, jsonschema, httpx
#   - (para modo remoto) curl somente
#
# Dependencias Python (instaladas automaticamente se faltar):
#   pip install jsonschema httpx
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SPECS_FILE="$SCRIPT_DIR/contract-specs/expected-schemas.json"
PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

# ── Help & modes ──────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--help" ]]; then
  sed -n '2,18p' "$0"
  echo ""
  echo "Modes:"
  echo "  --specs        List all endpoint schemas"
  echo "  --list-only    List endpoints without running tests"
  echo "  --help         This message"
  exit 0
fi

if [[ "${1:-}" == "--specs" || "${1:-}" == "--list-only" ]]; then
  if command -v python3 &>/dev/null; then
    python3 -c "
import json
with open('$SPECS_FILE') as f:
    specs = json.load(f)
for ep in specs['endpoints']:
    print(f\"  {ep['method']:6s} {ep['path']:40s} ({ep['id']})\")
    print(f\"         Status: {ep.get('expected_status', 'any')}\")
    print()
"
  else
    echo "Python3 required to list specs"
    exit 1
  fi
  exit 0
fi

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${CYAN}====================================================${NC}"
echo -e "${CYAN}  Contract Tests — OpenAPI Schema Compliance${NC}"
echo -e "${CYAN}====================================================${NC}"
echo ""

# ── Check specs file ──────────────────────────────────────────────────────────
if [[ ! -f "$SPECS_FILE" ]]; then
  echo -e "${RED}ERRO: Specs file not found: $SPECS_FILE${NC}"
  exit 1
fi

# ── Mode: TestClient (local) or remote ────────────────────────────────────────
REMOTE_MODE=false
BACKEND_URL="${BACKEND_URL:-}"

if [[ -n "$BACKEND_URL" ]]; then
  REMOTE_MODE=true
  echo -e "${YELLOW}Mode: remote — ${BACKEND_URL}${NC}"
else
  echo -e "${GREEN}Mode: local — FastAPI TestClient${NC}"
fi

echo ""

# ── Check Python deps ─────────────────────────────────────────────────────────
_missing_deps=false
python3 -c "import jsonschema" 2>/dev/null || _missing_deps=true

if ! $REMOTE_MODE; then
  python3 -c "import httpx" 2>/dev/null || _missing_deps=true
fi

if $_missing_deps; then
  echo -e "${YELLOW}Installing Python dependencies...${NC}"
  if $REMOTE_MODE; then
    pip install jsonschema -q 2>&1 | tail -1 || {
      echo -e "${RED}Failed to install jsonschema. Try: pip install jsonschema${NC}"
      exit 1
    }
  else
    pip install jsonschema httpx -q 2>&1 | tail -1 || {
      echo -e "${RED}Failed to install dependencies. Try: pip install jsonschema httpx${NC}"
      exit 1
    }
  fi
fi

# ── Run tests ─────────────────────────────────────────────────────────────────
run_tests_local() {
  cd "$PROJECT_DIR/backend"

  python3 -c "
import json, sys, os
from pathlib import Path

# Load specs
with open('$SPECS_FILE') as f:
    specs = json.load(f)

endpoints = specs['endpoints']

# Import FastAPI app
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test-service-role-key'
os.environ['OPENAI_API_KEY'] = 'sk-test-key'
os.environ['ENCRYPTION_KEY'] = 'bzc732A921Puw9JN4lrzMo1nw0EjlcUdAyR6Z6N7Sqc='
os.environ['ENVIRONMENT'] = 'test'
os.environ['SENTRY_DSN'] = ''
os.environ['REDIS_URL'] = ''
os.environ['LOG_LEVEL'] = 'WARNING'

sys.path.insert(0, '.')

from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Track results
results = []
total = 0
passed = 0
failed = 0

for ep in endpoints:
    total += 1
    ep_id = ep['id']
    method = ep['method'].lower()
    path = ep['path']
    params = ep.get('params', {})
    headers = ep.get('headers', {})
    expected_status = ep.get('expected_status', 200)
    schema = ep.get('response_schema', {})
    desc = ep.get('description', '')

    # Normalize expected_status to list
    if isinstance(expected_status, int):
        expected_list = [expected_status]
    else:
        expected_list = expected_status

    try:
        if method == 'get':
            resp = client.get(path, params=params, headers=headers)
        elif method == 'post':
            resp = client.post(path, json=params or {}, headers=headers)
        else:
            results.append((ep_id, 'FAIL', 'Unsupported method'))
            failed += 1
            continue

        status = resp.status_code
        try:
            body = resp.json()
        except Exception:
            body = None

        # Check status code
        status_ok = status in expected_list
        if not status_ok:
            results.append((ep_id, 'FAIL',
                f'Expected status {expected_list}, got {status}. Body: {str(body)[:200]}'))
            failed += 1
            continue

        # Validate response body against expected schema
        if body is not None and schema:
            from jsonschema import validate, ValidationError
            try:
                validate(instance=body, schema=schema)
                results.append((ep_id, 'PASS', f'HTTP {status} — schema OK'))
                passed += 1
            except ValidationError as e:
                results.append((ep_id, 'FAIL',
                    f'HTTP {status} — schema mismatch: {e.message}'))
                failed += 1
        else:
            results.append((ep_id, 'PASS', f'HTTP {status} (no body to validate)'))
            passed += 1

    except Exception as e:
        results.append((ep_id, 'FAIL', f'Exception: {type(e).__name__}: {e}'))
        failed += 1

# Output results
print('')
for ep_id, verdict, msg in results:
    if verdict == 'PASS':
        print(f'  [PASS] {ep_id}: {msg}')
    else:
        print(f'  [FAIL] {ep_id}: {msg}')

print('')
print(f'Results: {passed}/{total} passed, {failed}/{total} failed')
sys.exit(0 if failed == 0 else 1)
" 2>&1
}

run_tests_remote() {
  local url="$BACKEND_URL"

  cd "$PROJECT_DIR"

  python3 -c "
import json, sys, urllib.request, urllib.error, urllib.parse

with open('$SPECS_FILE') as f:
    specs = json.load(f)

endpoints = specs['endpoints']
url_base = '$url'.rstrip('/')

total = 0
passed = 0
failed = 0

for ep in endpoints:
    total += 1
    ep_id = ep['id']
    method = ep['method'].lower()
    path = ep['path']
    params = ep.get('params', {})
    headers = ep.get('headers', {})
    expected_status = ep.get('expected_status', 200)
    schema = ep.get('response_schema', {})
    desc = ep.get('description', '')

    if isinstance(expected_status, int):
        expected_list = [expected_status]
    else:
        expected_list = expected_status

    full_url = url_base + path
    if method == 'get' and params:
        qs = '&'.join(f'{k}={urllib.parse.quote(str(v))}' for k, v in params.items())
        full_url += '?' + qs

    try:
        req = urllib.request.Request(full_url, method=method.upper())
        for k, v in headers.items():
            req.add_header(k, v)

        if method == 'post' and params:
            data = json.dumps(params).encode('utf-8')
            req.data = data
            req.add_header('Content-Type', 'application/json')

        try:
            resp = urllib.request.urlopen(req, timeout=15)
            body = json.loads(resp.read().decode('utf-8'))
            status = resp.status
        except urllib.error.HTTPError as e:
            status = e.code
            try:
                body = json.loads(e.read().decode('utf-8'))
            except Exception:
                body = None

        # Check status
        status_ok = status in expected_list
        if not status_ok:
            print(f'  [FAIL] {ep_id}: Expected status {expected_list}, got {status}')
            failed += 1
            continue

        # Validate schema
        if body and schema:
            from jsonschema import validate, ValidationError
            try:
                validate(instance=body, schema=schema)
                print(f'  [PASS] {ep_id}: HTTP {status} — schema OK')
                passed += 1
            except ValidationError as e:
                print(f'  [FAIL] {ep_id}: schema mismatch: {e.message}')
                failed += 1
        else:
            print(f'  [PASS] {ep_id}: HTTP {status} (no body to validate)')
            passed += 1

    except Exception as e:
        print(f'  [FAIL] {ep_id}: {type(e).__name__}: {e}')
        failed += 1

print('')
print(f'Results: {passed}/{total} passed, {failed}/{total} failed')
sys.exit(0 if failed == 0 else 1)
" 2>&1
}

# ── Execute ───────────────────────────────────────────────────────────────────
if $REMOTE_MODE; then
  run_tests_remote "$BACKEND_URL"
  EXIT_CODE=$?
else
  run_tests_local
  EXIT_CODE=$?
fi

echo ""
if [ "$EXIT_CODE" -eq 0 ]; then
  echo -e "${GREEN}All contract tests passed.${NC}"
else
  echo -e "${RED}Some contract tests failed. Check output above.${NC}"
fi

exit $EXIT_CODE
