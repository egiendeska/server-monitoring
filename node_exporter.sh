#!/bin/bash
# Pastikan script dijalankan sebagai root atau pake sudo

# Variabel versi Node Exporter
NODE_EXP_VERSION="1.6.1"

# Update dan install dependensi
apt update && apt install -y wget tar

# Download Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v${NODE_EXP_VERSION}/node_exporter-${NODE_EXP_VERSION}.linux-amd64.tar.gz -O /tmp/node_exporter.tar.gz

# Ekstrak file
tar -xvf /tmp/node_exporter.tar.gz -C /tmp/

# Pindahin binary ke /usr/local/bin
mv /tmp/node_exporter-${NODE_EXP_VERSION}.linux-amd64/node_exporter /usr/local/bin/
chmod +x /usr/local/bin/node_exporter

# Buat user khusus buat Node Exporter
useradd --no-create-home --shell /bin/false node_exporter

# Ubah kepemilikan binary
chown node_exporter:node_exporter /usr/local/bin/node_exporter

# Buat file systemd service
cat <<'EOF' > /etc/systemd/system/node_exporter.service
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, start dan enable Node Exporter
systemctl daemon-reload
systemctl start node_exporter
systemctl enable node_exporter

echo "Node Exporter sudah jalan di port 9100"
