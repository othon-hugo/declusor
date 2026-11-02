#!/bin/bash
# -----------------------------------------------------------------------------
# Identifies available command-line utilities, development toolchains, and
# network binaries.
# -----------------------------------------------------------------------------

(
    for tool in nc netcat ncat telnet socat gcc clang make python3 python perl ruby php node curl wget ssh scp rsync tar gzip base64 openssl jq git nmap tcpdump ftp; do
        if _have "$tool"; then
            printf '%-12s %s\n' "$tool" "$(command -v "$tool" 2>/dev/null)"
        fi
    done
) | label "Available Utilities & Binaries"
