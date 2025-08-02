#!/bin/bash

# VARIABEL
EXPORTER_VERSION="0.11.0"
EXPORTER_BIN="nginx-prometheus-exporter"
EXPORTER_PORT=9113
SCRAPE_URI="http://localhost/nginx_status"

# Download exporter
curl -L -o /tmp/${EXPORTER_BIN}.tar.gz https://github.com/nginxinc/nginx-prometheus-exporter/releases/download/v${EXPORTER_VERSION}/${EXPORTER_BIN}-${EXPORTER_VERSION}-linux-amd64.tar.gz

# Ekstrak
tar -xzf /tmp/${EXPORTER_BIN}.tar.gz -C /tmp

# Pindahin binary ke /usr/local/bin
sudo mv /tmp/${EXPORTER_BIN}-${EXPORTER_VERSION}-linux-amd64/${EXPORTER_BIN} /usr/local/bin/
sudo chmod +x /usr/local/bin/${EXPORTER_BIN}

# Bikin systemd service
sudo tee /etc/systemd/system/nginx-exporter.service > /dev/null <<EOF
[Unit]
Description=NGINX Prometheus Exporter
After=network.target

[Service]
ExecStart=/usr/local/bin/${EXPORTER_BIN} \\
  -nginx.scrape-uri ${SCRAPE_URI} \\
  -web.listen-address=:${EXPORTER_PORT}

Restart=always
User=nobody

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, enable dan start
sudo systemctl daemon-reload
sudo systemctl enable nginx-exporter
sudo systemctl start nginx-exporter

# Info
echo "🔥 NGINX Exporter running di port ${EXPORTER_PORT}"
echo "➡️  Akses metrics: http://<ip-lo>:${EXPORTER_PORT}/metrics"
