#!/bin/bash
set -euo pipefail

ssh-keygen -A >/dev/null 2>&1

# Start Cron daemon and Nginx web server
crond -b -l 8
nginx

exec /usr/sbin/sshd -D -e