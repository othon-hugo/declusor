#!/bin/bash
set -euo pipefail

ssh-keygen -A >/dev/null 2>&1
exec /usr/sbin/sshd -D -e