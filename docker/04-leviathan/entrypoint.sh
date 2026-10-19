#!/bin/bash
set -euo pipefail

ssh-keygen -A >/dev/null 2>&1

# Ensure capability persists across overlay filesystems on container startup
setcap cap_dac_read_search+ep /usr/bin/tar 2>/dev/null || true

exec /usr/sbin/sshd -D -e