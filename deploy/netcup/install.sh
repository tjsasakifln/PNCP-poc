#!/usr/bin/env bash
# Executable Netcup bootstrap. Run as root on a fresh Debian/Ubuntu box.
set -euo pipefail

APP_USER=smartlic
APP_ROOT=/opt/smartlic
ENV_FILE=/etc/smartlic/smartlic.env

if [[ "$(id -u)" -ne 0 ]]; then
  echo "run as root" >&2
  exit 1
fi

id -u "$APP_USER" >/dev/null 2>&1 || useradd --system --home "$APP_ROOT" --shell /usr/sbin/nologin "$APP_USER"
mkdir -p "$APP_ROOT" /etc/smartlic /var/lib/smartlic /var/log/smartlic
chown -R "$APP_USER:$APP_USER" "$APP_ROOT" /var/lib/smartlic /var/log/smartlic
chmod 0750 /var/lib/smartlic /etc/smartlic

if [[ ! -f "$ENV_FILE" ]]; then
  cp "$(dirname "$0")/smartlic.env.example" "$ENV_FILE"
  chmod 0640 "$ENV_FILE"
  echo "created $ENV_FILE — fill secrets before starting units"
fi

install -m 0644 "$(dirname "$0")/smartlic-web.service" /etc/systemd/system/smartlic-web.service
install -m 0644 "$(dirname "$0")/smartlic-adapter.service" /etc/systemd/system/smartlic-adapter.service
systemctl daemon-reload

echo "units installed. next:"
echo "  1. fill $ENV_FILE"
echo "  2. rsync release to $APP_ROOT"
echo "  3. systemctl enable --now smartlic-adapter smartlic-web caddy"
echo "  4. ./validate-env.sh && ./healthcheck.sh"
