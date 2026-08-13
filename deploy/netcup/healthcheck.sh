#!/usr/bin/env bash
set -euo pipefail
fail=0
for url in http://127.0.0.1:8000/health/live http://127.0.0.1:3000/; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" || echo 000)
  echo "$url -> $code"
  if [[ "$code" != "200" && "$code" != "301" && "$code" != "308" ]]; then
    fail=1
  fi
done
curl -s --max-time 5 http://127.0.0.1:8000/v1/public-read/health || fail=1
exit "$fail"
