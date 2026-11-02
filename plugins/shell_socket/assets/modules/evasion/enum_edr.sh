#!/bin/bash
# -----------------------------------------------------------------------------
# Detects security monitoring agents, endpoint protection software, and
# defensive telemetry.
# -----------------------------------------------------------------------------

EDR_KEYWORDS="carbon|crowdstrike|cylance|sentinel|defender|symantec|mcafee|kaspersky|sophos|trendmicro|eset|bitdefender|fireeye|tanium|cb-defense|falcon|elastic|auditd|sysmon|falco|ossec|wazuh"

# Active Security Processes
# shellcheck disable=SC2009
( list_processes | grep -iE "$EDR_KEYWORDS" | grep -v grep ) | label "Active Security & Monitoring Processes"

# Loaded Kernel Modules
( lsmod 2>/dev/null | grep -iE "$EDR_KEYWORDS" ) | label "Security Kernel Modules"

# Security Agent Directories & Configurations
( find /etc /opt /usr/local /var/ossec -maxdepth 2 \( -name "*agent*" -o -name "*sensor*" -o -name "*falcon*" -o -name "*defender*" -o -name "*audit*" \) 2>/dev/null | grep -iE "$EDR_KEYWORDS" ) | label "Security Configuration Artifacts"

# Mandatory Access Control & Auditing Status
(
    if _have getenforce; then
        printf 'SELinux:  %s\n' "$(getenforce 2>/dev/null)"
    elif [ -f "/sys/fs/selinux/enforce" ]; then
        printf 'SELinux:  enforce=%s\n' "$(cat /sys/fs/selinux/enforce 2>/dev/null)"
    fi
    if _have aa-status; then
        aa-status --enabled 2>/dev/null && printf 'AppArmor: enabled\n'
    elif [ -f "/sys/module/apparmor/parameters/enabled" ]; then
        printf 'AppArmor: %s\n' "$(cat /sys/module/apparmor/parameters/enabled 2>/dev/null)"
    fi
) | label "Mandatory Access Control Status"
