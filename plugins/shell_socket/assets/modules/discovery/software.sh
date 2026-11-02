#!/bin/bash
# -----------------------------------------------------------------------------
# Inventories installed software packages, runtimes, and system utilities.
# -----------------------------------------------------------------------------

# Compilers & Language Runtimes
(
    for tool in gcc g++ clang make cmake python python3 perl ruby php java go rustc node npm; do
        _have "$tool" && command -v "$tool" 2>/dev/null
    done
) | label "Compilers & Language Runtimes"

# Security & Diagnostic Utilities
(
    for tool in nmap nc netcat ncat socat tcpdump wireshark tshark gdb strace ltrace openssl; do
        _have "$tool" && command -v "$tool" 2>/dev/null
    done
) | label "Security & Diagnostic Utilities"

# Container & Virtualization Tooling
(
    for tool in docker podman kubectl crictl ctr lxc virsh systemd-detect-virt; do
        _have "$tool" && command -v "$tool" 2>/dev/null
    done
) | label "Container & Virtualization Tooling"

# Installed Packages (Debian/Ubuntu)
if _have dpkg; then
    dpkg -l 2>/dev/null | awk '/^ii/ {print $2, $3}' | head -n 25 | column -t | label "Installed Packages (dpkg sample)"
fi

# Installed Packages (RHEL/CentOS/Fedora)
if _have rpm; then
    rpm -qa 2>/dev/null | head -n 25 | label "Installed Packages (rpm sample)"
fi

# Installed Packages (Alpine)
if _have apk; then
    apk info -v 2>/dev/null | head -n 25 | label "Installed Packages (apk sample)"
fi

# Installed Packages (Arch)
if _have pacman; then
    pacman -Q 2>/dev/null | head -n 25 | label "Installed Packages (pacman sample)"
fi
