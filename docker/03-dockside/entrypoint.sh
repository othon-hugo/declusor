#!/bin/bash
set -euo pipefail

ssh-keygen -A >/dev/null 2>&1

# Map host docker.sock GID exclusively to 'devops' (NOT 'player')
if [ -S /var/run/docker.sock ]; then
    SOCK_GID=$(stat -c '%g' /var/run/docker.sock)
    EXISTING_GRP=$(getent group "$SOCK_GID" | cut -d: -f1 || true)

    if [ -n "$EXISTING_GRP" ]; then
        addgroup devops "$EXISTING_GRP" 2>/dev/null || true
    else
        addgroup -g "$SOCK_GID" dockerhost 2>/dev/null || true
        addgroup devops dockerhost 2>/dev/null || true
    fi
fi

exec /usr/sbin/sshd -D -e