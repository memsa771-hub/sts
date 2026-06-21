#!/usr/bin/env bash
# Site Tracking System - Ubuntu deploy script
# Usage on server:
#   curl -fsSL https://raw.githubusercontent.com/memsa771-hub/sts/main/deploy.sh -o deploy.sh
#   sudo bash deploy.sh
#
# Or after cloning:
#   cd sts && sudo bash deploy.sh

set -euo pipefail

SERVER_IP="${SERVER_IP:-95.182.86.121}"
PORT="${PORT:-8000}"
REPO_URL="${REPO_URL:-https://github.com/memsa771-hub/sts.git}"
BRANCH="${BRANCH:-main}"
SERVICE_NAME="${SERVICE_NAME:-sts}"
DEPLOY_USER="${DEPLOY_USER:-${SUDO_USER:-ubuntu}}"
APP_DIR="${APP_DIR:-/home/${DEPLOY_USER}/sts}"
VENV_DIR="${APP_DIR}/venv"
ENV_FILE="${APP_DIR}/.env"

echo "============================================"
echo " STS Deploy"
echo " Server : ${SERVER_IP}:${PORT}"
echo " App dir: ${APP_DIR}"
echo " User   : ${DEPLOY_USER}"
echo "============================================"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root: sudo bash deploy.sh"
  exit 1
fi

if ! id "${DEPLOY_USER}" &>/dev/null; then
  echo "Creating user ${DEPLOY_USER}..."
  useradd -m -s /bin/bash "${DEPLOY_USER}"
fi

echo "[1/8] Installing system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
  python3 \
  python3-venv \
  python3-pip \
  python3-dev \
  git \
  curl \
  libjpeg-dev \
  zlib1g-dev \
  libpng-dev

echo "[2/8] Getting application code..."
if [[ ! -d "${APP_DIR}/.git" ]]; then
  sudo -u "${DEPLOY_USER}" git clone --branch "${BRANCH}" "${REPO_URL}" "${APP_DIR}"
else
  sudo -u "${DEPLOY_USER}" git -C "${APP_DIR}" fetch origin "${BRANCH}"
  sudo -u "${DEPLOY_USER}" git -C "${APP_DIR}" checkout "${BRANCH}"
  sudo -u "${DEPLOY_USER}" git -C "${APP_DIR}" pull origin "${BRANCH}"
fi

echo "[3/8] Creating Python virtual environment..."
if [[ ! -d "${VENV_DIR}" ]]; then
  sudo -u "${DEPLOY_USER}" python3 -m venv "${VENV_DIR}"
fi
sudo -u "${DEPLOY_USER}" "${VENV_DIR}/bin/pip" install --upgrade pip
sudo -u "${DEPLOY_USER}" "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt"

echo "[4/8] Creating environment file..."
if [[ ! -f "${ENV_FILE}" ]]; then
  SECRET_KEY="$("${VENV_DIR}/bin/python" -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
  cat > "${ENV_FILE}" <<EOF
DJANGO_SECRET_KEY=${SECRET_KEY}
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=${SERVER_IP},localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=http://${SERVER_IP}:${PORT}
EOF
  chown "${DEPLOY_USER}:${DEPLOY_USER}" "${ENV_FILE}"
  chmod 600 "${ENV_FILE}"
  echo "Created ${ENV_FILE}"
else
  echo "Using existing ${ENV_FILE}"
fi

mkdir -p "${APP_DIR}/media" "${APP_DIR}/staticfiles"
chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "${APP_DIR}"

echo "[5/8] Running migrations and collecting static files..."
sudo -u "${DEPLOY_USER}" bash -c "
  set -a
  source '${ENV_FILE}'
  set +a
  cd '${APP_DIR}'
  '${VENV_DIR}/bin/python' manage.py migrate --noinput
  '${VENV_DIR}/bin/python' manage.py collectstatic --noinput
"

echo "[6/8] Installing systemd service..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=Site Tracking System (Django)
After=network.target

[Service]
User=${DEPLOY_USER}
Group=${DEPLOY_USER}
WorkingDirectory=${APP_DIR}
EnvironmentFile=${ENV_FILE}
ExecStart=${VENV_DIR}/bin/gunicorn sitetrack.wsgi:application \\
    --bind 0.0.0.0:${PORT} \\
    --workers 3 \\
    --timeout 120 \\
    --access-logfile - \\
    --error-logfile -
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "[7/8] Starting service..."
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  echo "Opening firewall port ${PORT}..."
  ufw allow "${PORT}/tcp" || true
fi

echo "[8/8] Checking service status..."
sleep 2
if systemctl is-active --quiet "${SERVICE_NAME}"; then
  echo
  echo "============================================"
  echo " DEPLOY SUCCESS"
  echo " Open: http://${SERVER_IP}:${PORT}"
  echo "============================================"
  echo
  echo "Useful commands:"
  echo "  sudo systemctl status ${SERVICE_NAME}"
  echo "  sudo systemctl restart ${SERVICE_NAME}"
  echo "  sudo journalctl -u ${SERVICE_NAME} -f"
  echo
  echo "Create admin user (first time only):"
  echo "  cd ${APP_DIR} && source .env && source venv/bin/activate"
  echo "  set -a && source .env && set +a && python manage.py createsuperuser"
else
  echo "Service failed to start. Logs:"
  journalctl -u "${SERVICE_NAME}" -n 30 --no-pager
  exit 1
fi
