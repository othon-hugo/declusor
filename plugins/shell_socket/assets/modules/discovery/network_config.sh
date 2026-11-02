#!/bin/bash
# -----------------------------------------------------------------------------
# Enumerates host network topology, interfaces, routing, and active socket
# states.
# -----------------------------------------------------------------------------

# Network Interfaces & Addresses
(
    if _have ip; then
        ip -br addr 2>/dev/null || ip addr 2>/dev/null | awk '/^[0-9]+:/ {iface=$2} /inet6? / {print iface, $1, $2}'
    elif _have ifconfig; then
        ifconfig -a 2>/dev/null
    fi
) | label "Network Interfaces & Addresses"

# DNS Resolvers
grep -E '^[^#;]' /etc/resolv.conf 2>/dev/null | grep nameserver | label "DNS Nameservers"

# Local Host Mappings
grep -vE '^[[:space:]]*(#|$)' /etc/hosts 2>/dev/null | label "Host Mappings (/etc/hosts)"

# Neighbor / ARP Cache
( ip neighbour 2>/dev/null || arp -a 2>/dev/null ) | label "ARP & Neighbor Cache"

# Routing Table
( ip route 2>/dev/null || route -n 2>/dev/null || netstat -rn 2>/dev/null ) | label "Routing Table"

# Listening Sockets
list_sockets listening | column -t | label "Listening Services"

# Active Established Connections
list_sockets established | column -t | label "Active Connections"
