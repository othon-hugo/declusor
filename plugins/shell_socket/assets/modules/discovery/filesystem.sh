#!/bin/bash
# -----------------------------------------------------------------------------
# Inspects the filesystem to identify interesting paths, permissions, and
# configuration artifacts.
# -----------------------------------------------------------------------------

# Writable Files (excluding current user and pseudo-filesystems)
find / \( -path '/proc/*' -o -path '/sys/*' -o -path '/dev/*' -o -path '/run/*' \) -prune -o -writable ! -user "$(whoami 2>/dev/null || id -un 2>/dev/null)" -type f -print 2>/dev/null | format_perms | column -t -s ';' | label "Writable Files"

# Writable Directories (maxdepth 3, excluding pseudo-filesystems)
find / -maxdepth 3 \( -path '/proc/*' -o -path '/sys/*' -o -path '/dev/*' -o -path '/run/*' \) -prune -o -type d -writable -print 2>/dev/null | format_perms | column -t -s ';' | label "Writable Directories"

# Home Directories
find /home /root -maxdepth 1 2>/dev/null | format_perms | column -t -s ';' | label "Home Directories"

# Current User Crontab
crontab -l 2>/dev/null | grep -vE '^[[:space:]]*(#|$)' | label "User Crontab"

# Key & Credential Files in Home Directories
find /home /root -type f \( -name "authorized_keys" -o -name "*id_dsa*" -o -name "*id_ecdsa*" -o -name "*id_ed25519*" -o -name "*id_rsa*" -o -name "*.key" -o -name "*.pub" -o -name ".env" -o -name ".git-credentials" \) 2>/dev/null | format_perms | column -t -s ';' | label "Key & Credential Artifacts"

# Sensitive Configuration Paths in /etc
find /etc -maxdepth 2 \( -type f -o -type d \) \( -name 'init*' -o -name 'cron*' -o -name 'anacrontab' -o -name 'sudoers*' -o -name 'exports' -o -name 'fstab' \) 2>/dev/null | format_perms | column -t -s ';' | label "System Configuration Paths"

# Scheduled Cron Files
find /var/spool/cron /etc/cron* -type f 2>/dev/null | format_perms | column -t -s ';' | label "Scheduled Cron Files"
