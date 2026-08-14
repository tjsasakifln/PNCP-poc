#!/usr/bin/env bash
# Rollback to previous release directory. Releases live in /opt/smartlic/releases/<sha>
set -euo pipefail
TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  echo "usage: rollback.sh <sha>" >&2
  exit 1
fi
ln -sfn "/opt/smartlic/releases/$TARGET" /opt/smartlic/current
systemctl restart smartlic-adapter smartlic-web
./healthcheck.sh
