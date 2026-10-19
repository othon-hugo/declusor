#!/bin/bash
set -euo pipefail

# 1. Create telemetry service account and group
addgroup telemetry
adduser -D -s /bin/bash -G telemetry svc_telemetry
echo "svc_telemetry:TelemetrySvc_2026!" | chpasswd

# 2. Create SQLite Database with vessel data and user password hashes
mkdir -p /var/lib/draftsman /opt/telemetry
sqlite3 /var/lib/draftsman/vessels.db << 'EOF'
CREATE TABLE vessels (id INT PRIMARY KEY, name TEXT, status TEXT, last_ping TEXT);
INSERT INTO vessels VALUES (101, 'SS Declusor Horizon', 'ACTIVE', '2026-10-18 20:15:00');
INSERT INTO vessels VALUES (102, 'MV Northern Star', 'DOCKED', '2026-10-18 19:50:12');

CREATE TABLE service_accounts (username TEXT, role TEXT, password_hint TEXT, api_token TEXT);
INSERT INTO service_accounts VALUES (
    'svc_telemetry',
    'telemetry-operator',
    'Password passed to telemetry_daemon.py via ENV and cached in local Redis',
    'tok_live_99a8b7c6d5e4f3g2h1'
);
EOF
chmod 644 /var/lib/draftsman/vessels.db

# 3. Create Database Client Authentication Helpers (.pgpass and .my.cnf)
cat << 'EOF' > /home/svc_telemetry/.pgpass
pg-cluster.declusor.local:5432:vessel_telemetry:svc_telemetry:TelemetrySvc_2026!
EOF

cat << 'EOF' > /home/svc_telemetry/.my.cnf
[client]
user=svc_telemetry
password="TelemetrySvc_2026!"
host=mysql.declusor.local
EOF

chown svc_telemetry:telemetry /home/svc_telemetry/.pgpass /home/svc_telemetry/.my.cnf
chmod 600 /home/svc_telemetry/.pgpass /home/svc_telemetry/.my.cnf

# 4. Create Python Telemetry HTTP Server (exposes /proc/<PID>/environ and cmdline when running)
cat << 'EOF' > /opt/telemetry/telemetry_daemon.py
import http.server
import socketserver
import json
import os

PORT = 8082

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        response = {
            "service": "draftsman-telemetry-daemon",
            "status": "healthy",
            "redis_cache": "127.0.0.1:6379",
            "sqlite_db": "/var/lib/draftsman/vessels.db",
            "healthcheck_binary": "/usr/local/bin/healthcheck (restricted to group: telemetry)"
        }
        self.wfile.write(json.dumps(response, indent=2).encode())

    def log_message(self, format, *args):
        pass

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
EOF
chmod 755 /opt/telemetry/telemetry_daemon.py