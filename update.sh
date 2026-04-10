#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/red/current"
VENV_PATH="$APP_DIR/.venv"
SERVICE_NAME="red"

cd "$APP_DIR"

echo "[1/5] Pull latest code..."
git pull

echo "[2/5] Activate virtualenv..."
source "$VENV_PATH/bin/activate"

echo "[3/5] Install dependencies..."
pip install -r requirements.txt

echo "[4/5] Restart service..."
systemctl restart "$SERVICE_NAME"

echo "[5/5] Check service status..."
systemctl status "$SERVICE_NAME" --no-pager

echo "Update completed."
