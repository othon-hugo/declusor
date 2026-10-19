#!/bin/bash
set -euo pipefail

# Ensure SSH host keys are generated
ssh-keygen -A >/dev/null 2>&1

# Start BusyBox cron daemon in background for Vector 3
crond -b -l 8

# Start OpenSSH daemon in foreground
exec /usr/sbin/sshd -D -e