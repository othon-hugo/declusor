#!/bin/bash
# -----------------------------------------------------------------------------
# Gathers general host reconnaissance data and operating environment
# characteristics.
# -----------------------------------------------------------------------------

# Host Overview
(
    printf 'Hostname: %s\n' "$(hostname 2>/dev/null || cat /etc/hostname 2>/dev/null)"
    printf 'Kernel:   %s\n' "$(uname -a 2>/dev/null)"
    release="$(grep -E '^(PRETTY_NAME|NAME)=' /etc/*release 2>/dev/null | head -n 1 | cut -d= -f2- | tr -d '"')"
    [ -n "$release" ] && printf 'OS:       %s\n' "$release"
    printf 'Uptime:   %s\n' "$(uptime -p 2>/dev/null || uptime 2>/dev/null)"
    if [ -f "/.dockerenv" ] || [ -f "/run/.containerenv" ] || grep -qE '(docker|kubepods|lxc|containerd)' /proc/1/cgroup 2>/dev/null; then
        printf 'Context:  Containerized Environment\n'
    fi
) | label "System Overview"

# Hardware & Memory Summary
(
    awk -F: '/model name/ {gsub(/^[ \t]+/, "", $2); print "CPU:      " $2; exit}' /proc/cpuinfo 2>/dev/null
    free -h 2>/dev/null || head -n 5 /proc/meminfo 2>/dev/null
) | label "Hardware & Memory"

# Environment Variables
env 2>/dev/null | sort | label "Environment Variables"

# Running Processes (Top 50)
list_processes | head -n 50 | label "Running Processes (Sample)"

# PCI Devices
lspci 2>/dev/null | label "PCI Buses & Devices"

# Mounted Filesystems
mount 2>/dev/null | grep -vE "tmpfs|proc|sysfs|cgroup|devpts|mqueue|hugetlbfs|securityfs|debugfs" | label "Mounted Filesystems"

# Disk Usage
df -h 2>/dev/null | label "Disk Usage"
