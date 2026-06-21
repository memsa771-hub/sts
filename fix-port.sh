#!/usr/bin/env bash
# Fix port 8000 conflict - run on server: sudo bash fix-port.sh

set -euo pipefail

PORT="${PORT:-8000}"
SERVICE_NAME="${SERVICE_NAME:-sts}"

echo "Stopping ${SERVICE_NAME} service..."
systemctl stop "${SERVICE_NAME}" 2>/dev/null || true
sleep 2

echo "Killing any process on port ${PORT}..."
if command -v fuser >/dev/null 2>&1; then
  fuser -k "${PORT}/tcp" 2>/dev/null || true
else
  pkill -f "gunicorn sitetrack.wsgi" 2>/dev/null || true
fi
sleep 2

echo "Starting ${SERVICE_NAME}..."
systemctl start "${SERVICE_NAME}"
sleep 3

echo
echo "Port status:"
ss -tlnp | grep ":${PORT} " || echo "Nothing listening yet"

echo
echo "Local test:"
curl -s -o /dev/null -w "HTTP %{http_code}\n" --connect-timeout 5 "http://127.0.0.1:${PORT}/" || echo "Failed"

echo
systemctl status "${SERVICE_NAME}" --no-pager -l | head -15

echo
echo "If you see 0.0.0.0:${PORT} above, open http://95.182.86.121:${PORT} in browser"
