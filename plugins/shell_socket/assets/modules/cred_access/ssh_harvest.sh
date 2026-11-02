#!/bin/bash
# -----------------------------------------------------------------------------
# Discovers and harvests SSH credentials, keys, configurations, and active
# session material.
# -----------------------------------------------------------------------------

# Private Keys & Certificates
find / \( -path '/proc/*' -o -path '/sys/*' -o -path '/dev/*' -o -path '/run/*' \) -prune -o -type f \( -name "id_rsa" -o -name "id_dsa" -o -name "id_ecdsa*" -o -name "id_ed25519*" -o -name "*.pem" -o -name "authorized_keys" \) -print 2>/dev/null | label "SSH Keys & Authorized Keys"

# SSH Configurations
(
    find /home /root /etc/ssh -maxdepth 4 -type f \( -name "ssh_config" -o -name "config" \) 2>/dev/null | while IFS= read -r cfg; do
        [ -r "$cfg" ] || continue
        matches="$(grep -E "^[[:space:]]*(Host |HostName|User|IdentityFile|Port|ProxyJump)" "$cfg" 2>/dev/null)"
        if [ -n "$matches" ]; then
            printf '[%s]\n%s\n' "$cfg" "$matches"
        fi
    done
) | label "SSH Client Configurations"

# Known Hosts
(
    find /home /root /etc/ssh -maxdepth 4 -type f -name "known_hosts" 2>/dev/null | while IFS= read -r kh; do
        [ -r "$kh" ] || continue
        hosts="$(awk '{print $1}' "$kh" 2>/dev/null | cut -d, -f1 | sort -u)"
        if [ -n "$hosts" ]; then
            printf '[%s]\n%s\n' "$kh" "$hosts"
        fi
    done
) | label "SSH Known Hosts"

# Active SSH Agent Sockets
if [ -n "${SSH_AUTH_SOCK:-}" ] && [ -S "${SSH_AUTH_SOCK:-}" ]; then
    (
        printf 'Socket: %s\n' "$SSH_AUTH_SOCK"
        ssh-add -l 2>/dev/null
    ) | label "Active SSH Agent"
fi
