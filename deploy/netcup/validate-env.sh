#!/usr/bin/env bash
set -euo pipefail
ENV_FILE="${1:-/etc/smartlic/smartlic.env}"
required=(NEXT_PUBLIC_SITE_URL BACKEND_URL SAAS_COMMERCE_ENABLED PUBLIC_READ_V1_MODE LEAD_OUTBOX_PATH)
missing=0
# shellcheck disable=SC1090
source "$ENV_FILE"
for key in "${required[@]}"; do
  if [[ -z "${!key:-}" ]]; then
    echo "MISSING $key" >&2
    missing=1
  fi
done
if [[ "${SAAS_COMMERCE_ENABLED}" != "false" ]]; then
  echo "SAAS_COMMERCE_ENABLED must be false in Netcup" >&2
  missing=1
fi
if [[ "${PUBLIC_READ_V1_MODE}" == "on" ]]; then
  echo "PUBLIC_READ_V1_MODE=on is forbidden until the tenders canary gate passes" >&2
  missing=1
fi
if [[ -n "${NEXT_PUBLIC_PUBLIC_READ_V1_DSN:-}" ]]; then
  echo "PUBLIC_READ DSN must never be NEXT_PUBLIC" >&2
  missing=1
fi
if [[ -n "${PUBLIC_READ_V1_DSN:-}" && "${PUBLIC_READ_V1_DSN}" == *browser* ]]; then
  echo "PUBLIC_READ_V1_DSN looks unsafe" >&2
  missing=1
fi
if [[ "${PUBLIC_READ_V1_MODE}" != "off" && -z "${PUBLIC_READ_V1_DSN:-}" ]]; then
  echo "PUBLIC_READ_V1_DSN is required when mode is ${PUBLIC_READ_V1_MODE}" >&2
  missing=1
fi
exit "$missing"
