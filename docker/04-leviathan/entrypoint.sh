#!/bin/bash
set -euo pipefail

ssh-keygen -A >/dev/null 2>&1

# Ensure capability persists across overlay filesystems on container startup
TAR_BIN="$(command -v tar 2>/dev/null || echo '/bin/tar')"
TAR_REAL="$(readlink -f "$TAR_BIN" || echo "$TAR_BIN")"
setcap cap_dac_read_search+ep "$TAR_REAL" 2>/dev/null || setcap cap_dac_read_search+ep "$TAR_BIN" 2>/dev/null || true

exec /usr/sbin/sshd -D -e