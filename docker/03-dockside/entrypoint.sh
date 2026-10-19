#!/bin/bash
set -euo pipefail

ssh-keygen -A >/dev/null 2>&1

# Dynamically map host docker.sock GID to player group inside container
if [ -S /var/run/docker.sock ]; then
    SOCK_GID=$(stat -c '%g' /var/run/docker.sock)
    EXISTING_GRP=$(getent group "$SOCK_GID" | cut -d: -f1 || true)

    if [ -n "$EXISTING_GRP" ]; then
        addgroup player "$EXISTING_GRP" 2>/dev/null || true
    else
        addgroup -g "$SOCK_GID" dockerhost 2>/dev/null || true
        addgroup player dockerhost 2>/dev/null || true
    fi
fi

exec /usr/sbin/sshd -D -e