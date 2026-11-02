#!/bin/bash
# -----------------------------------------------------------------------------
# Enumerates local user accounts, active sessions, and privilege group
# memberships.
# -----------------------------------------------------------------------------

# Current User Identity
(
    printf 'User: %s\n' "$(whoami 2>/dev/null || id -un 2>/dev/null)"
    id 2>/dev/null
) | label "Current User Identity"

# Last Logged In Users
( lastlog 2>/dev/null | grep -vE '\*\*.*\*\*' | tail -n +2 | column -t ) | label "Last Logged In Users"

# Currently Active Sessions
( w -hs 2>/dev/null || who 2>/dev/null || users 2>/dev/null ) | label "Active User Sessions"

# Accounts with Interactive Login Shells
awk -F: '$7 !~ /(nologin|false|sync|halt|shutdown)$/ && $7 != "" {print $1 ";" $3 ";" $6 ";" $7}' /etc/passwd 2>/dev/null | column -t -s ';' | label "Interactive User Accounts"

# Privileged Group Memberships
awk -F: '/^(sudo|wheel|root|adm|docker|lxd|disk|shadow):/ && $4 != "" {print $1 ": " $4}' /etc/group 2>/dev/null | label "Privileged Group Members"
