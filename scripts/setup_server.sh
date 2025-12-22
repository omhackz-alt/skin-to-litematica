#!/bin/bash
# Server Setup Script for Skin to Litematica
# Run this on your Ubuntu server as root

set -e

echo "=== Updating system ==="
apt update && apt upgrade -y

echo "=== Installing dependencies ==="
apt install -y python3 python3-pip python3-venv nginx git

echo "=== Creating app directory ==="
mkdir -p /var/www/skin-to-litematica
cd /var/www/skin-to-litematica

echo "=== Cloning repository ==="
git clone https://github.com/ponpon77/skin-to-litematica.git .

echo "=== Setting up Python virtual environment ==="
python3 -m venv venv
source venv/bin/activate

echo "=== Installing Python dependencies ==="
pip install --upgrade pip
pip install -r web/requirements.txt

echo "=== Creating upload directories ==="
mkdir -p web/static/uploads web/static/output
chmod 755 web/static/uploads web/static/output

echo "=== Setup complete! ==="
echo "Next steps:"
echo "1. Run: bash scripts/setup_nginx.sh"
echo "2. Run: bash scripts/setup_gunicorn.sh"
