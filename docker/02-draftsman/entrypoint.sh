#!/bin/bash
set -euo pipefail

ssh-keygen -A >/dev/null 2>&1

# 1. Start local Redis and seed in-memory credentials/sessions
redis-server --bind 127.0.0.1 --port 6379 --daemonize yes
sleep 1
redis-cli SET "config:svc_telemetry:user" "svc_telemetry" >/dev/null
redis-cli SET "config:svc_telemetry:pass" "TelemetrySvc_2026!" >/dev/null
redis-cli SET "session:admin:jwt" "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.draftsman_payload" >/dev/null
redis-cli SAVE >/dev/null

# 2. Start Telemetry Daemon as svc_telemetry with leaked secrets in /proc/<PID>/environ & cmdline
su -s /bin/bash svc_telemetry -c \
    "SVC_USER=svc_telemetry SVC_PASS='TelemetrySvc_2026!' INTERNAL_API_KEY='dkl_live_draftsman_8821' \
    python3 /opt/telemetry/telemetry_daemon.py --auth-secret=TelemetrySvc_2026! &"

exec /usr/sbin/sshd -D -e