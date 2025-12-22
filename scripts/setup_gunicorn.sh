#!/bin/bash
# Gunicorn systemd service setup

cat > /etc/systemd/system/skin-to-litematica.service << 'EOF'
[Unit]
Description=Skin to Litematica Web Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/skin-to-litematica/web
Environment="PATH=/var/www/skin-to-litematica/venv/bin"
ExecStart=/var/www/skin-to-litematica/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
chown -R www-data:www-data /var/www/skin-to-litematica

# Enable and start the service
systemctl daemon-reload
systemctl enable skin-to-litematica
systemctl start skin-to-litematica

echo "Gunicorn service started!"
echo "Check status: systemctl status skin-to-litematica"
