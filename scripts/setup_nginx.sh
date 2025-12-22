#!/bin/bash
# Nginx Configuration Script

cat > /etc/nginx/sites-available/skin-to-litematica << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /static/ {
        alias /var/www/skin-to-litematica/web/static/;
    }

    client_max_body_size 16M;
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/skin-to-litematica /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and restart nginx
nginx -t && systemctl restart nginx

echo "Nginx configured! Site will be available at http://YOUR_SERVER_IP"
