#!/usr/bin/env bash
# ==============================================================================
# 👑 VOID ARCHIVE AI CEO — 1-CLICK PRODUCTION VPS DEPLOYMENT SCRIPT
# ==============================================================================
set -e

echo "=========================================================="
echo "🚀 Initializing Void Archive AI CEO Studio on Linux VPS..."
echo "=========================================================="

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

echo "📦 Step 1: Installing essential system packages (ffmpeg, sqlite3, python3)..."
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv ffmpeg sqlite3 curl git

echo "🐍 Step 2: Setting up isolated Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "📁 Step 3: Initializing directory tree..."
mkdir -p logs output/thumbnails output/test_thumbnails assets/music assets/sfx config

echo "⚙️ Step 4: Checking environment configuration..."
if [ ! -f "config/.env" ]; then
    echo "⚠️ Warning: config/.env not found! Please ensure config/.env contains your API keys."
else
    echo "✅ config/.env verified."
fi

echo "🛡️ Step 5: Configuring Systemd Service (Auto-Start on Boot + 24/7 Auto-Restart)..."
SERVICE_FILE="/etc/systemd/system/void_archive.service"
CURRENT_USER=$(whoami)

sudo bash -c "cat <<INNER_EOF > $SERVICE_FILE
[Unit]
Description=Void Archive AI CEO Studio 24/7 Autopilot
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python ceo_bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
StandardOutput=append:$APP_DIR/logs/systemd_stdout.log
StandardError=append:$APP_DIR/logs/systemd_stderr.log

[Install]
WantedBy=multi-user.target
INNER_EOF"

sudo systemctl daemon-reload
sudo systemctl enable void_archive.service

echo "=========================================================="
echo "🎉 Void Archive AI CEO Studio is READY on VPS!"
echo "To start now, run:   sudo systemctl start void_archive"
echo "To view status:      sudo systemctl status void_archive"
echo "To view live logs:   tail -f logs/systemd_stdout.log"
echo "=========================================================="
