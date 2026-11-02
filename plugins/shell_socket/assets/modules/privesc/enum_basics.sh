#!/bin/bash
# -----------------------------------------------------------------------------
# Audits the host for common privilege escalation vectors and security
# misconfigurations.
# -----------------------------------------------------------------------------

(
    printf 'Kernel Version: %s\n' "$(uname -r 2>/dev/null)"

    [ -w "/etc/passwd" ] && printf '[!] CRITICAL: /etc/passwd is writable\n'
    [ -w "/etc/shadow" ] && printf '[!] CRITICAL: /etc/shadow is writable\n'
    [ -w "/etc/sudoers" ] && printf '[!] CRITICAL: /etc/sudoers is writable\n'
    [ -w "/var/run/docker.sock" ] && printf '[!] CRITICAL: Docker socket (/var/run/docker.sock) is writable\n'

    # Check for writable directories in PATH
    IFS=':'
    for pdir in $PATH; do
        if [ -n "$pdir" ] && [ -d "$pdir" ] && [ -w "$pdir" ]; then
            printf '[!] Writable PATH directory: %s\n' "$pdir"
        fi
    done
    unset IFS

    # Check high-risk group memberships
    id_out="$(id 2>/dev/null)"
    for grp in docker lxd lxc disk shadow adm wheel sudo; do
        if printf '%s' "$id_out" | grep -qw "$grp"; then
            printf '[!] Member of privileged group: %s\n' "$grp"
        fi
    done

    # Check NFS no_root_squash
    if [ -r "/etc/exports" ]; then
        grep -vE '^[[:space:]]*(#|$)' /etc/exports 2>/dev/null | grep "no_root_squash" | while IFS= read -r line; do
            printf '[!] NFS no_root_squash export: %s\n' "$line"
        done
    fi

    # Non-interactive sudo privileges
    if _have sudo; then
        sudo -n -l 2>/dev/null
    fi
) | label "Privilege Escalation Vectors"
