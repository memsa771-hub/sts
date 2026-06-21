#!/usr/bin/env bash
# Quick diagnostics for STS deployment
# Run on server: sudo bash diagnose.sh

PORT="${PORT:-8000}"
SERVICE_NAME="${SERVICE_NAME:-sts}"

echo "============================================"
echo " STS Connection Diagnostics"
echo "============================================"

echo
echo "[1] Service status"
systemctl status "${SERVICE_NAME}" --no-pager -l || true

echo
echo "[2] Is port ${PORT} listening?"
if command -v ss >/dev/null 2>&1; then
  PORT_INFO=$(ss -tlnp | grep ":${PORT} " || true)
  if [[ -n "${PORT_INFO}" ]]; then
    echo "${PORT_INFO}"
    if echo "${PORT_INFO}" | grep -q "127.0.0.1:${PORT}"; then
      if ! echo "${PORT_INFO}" | grep -qE "0\.0\.0\.0:${PORT}|\[::\]:${PORT}|\*:${PORT}"; then
        echo
        echo "PROBLEM: Port ${PORT} is only on 127.0.0.1 (localhost)."
        echo "External browsers cannot connect. Fix with:"
        echo "  sudo systemctl stop ${SERVICE_NAME}"
        echo "  sudo fuser -k ${PORT}/tcp"
        echo "  sudo systemctl start ${SERVICE_NAME}"
      fi
    fi
  else
    echo "NOT LISTENING on port ${PORT}"
  fi
else
  netstat -tlnp 2>/dev/null | grep ":${PORT} " || echo "NOT LISTENING on port ${PORT}"
fi

echo
echo "[3] Local HTTP test (127.0.0.1:${PORT})"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "http://127.0.0.1:${PORT}/" || echo "000")
if [[ "${HTTP_CODE}" == "200" || "${HTTP_CODE}" == "302" || "${HTTP_CODE}" == "301" ]]; then
  echo "OK - app responds locally (HTTP ${HTTP_CODE})"
else
  echo "FAILED - HTTP code: ${HTTP_CODE}"
  echo "If not 200/302, check logs below."
fi

echo
echo "[4] Recent service logs"
journalctl -u "${SERVICE_NAME}" -n 40 --no-pager || true

echo
echo "[5] Firewall (UFW)"
if command -v ufw >/dev/null 2>&1; then
  ufw status || true
else
  echo "UFW not installed"
fi

echo
echo "[6] Environment file"
APP_DIR="$(systemctl show "${SERVICE_NAME}" -p WorkingDirectory --value 2>/dev/null || echo /home/root/sts)"
if [[ -f "${APP_DIR}/.env" ]]; then
  grep -E '^DJANGO_' "${APP_DIR}/.env" | sed 's/SECRET_KEY=.*/SECRET_KEY=***hidden***/'
else
  echo "No .env found at ${APP_DIR}/.env"
fi

echo
echo "============================================"
echo " If [3] OK but browser still fails:"
echo "  -> Open port ${PORT} in your VPS/cloud panel"
echo "     (Hetzner, Contabo, AWS, etc.)"
echo "  -> UFW alone is not enough on most VPS"
echo "============================================"
