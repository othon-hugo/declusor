#!/bin/bash
# -----------------------------------------------------------------------------
# Extracts wireless network configurations and stored authentication
# credentials.
# -----------------------------------------------------------------------------

# NetworkManager Connections
if [ -d "/etc/NetworkManager/system-connections" ]; then
    grep -rnE '^(ssid|psk|password|key-mgmt)=' /etc/NetworkManager/system-connections 2>/dev/null | label "NetworkManager Wireless Profiles"
fi

# WPA Supplicant
if [ -d "/etc/wpa_supplicant" ] || [ -f "/etc/wpa_supplicant.conf" ]; then
    grep -rnE '(ssid|psk|identity|password)[[:space:]]*=' /etc/wpa_supplicant /etc/wpa_supplicant.conf 2>/dev/null | label "WPA Supplicant Configurations"
fi

# iwd (iNet Wireless Daemon)
if [ -d "/var/lib/iwd" ]; then
    grep -rnE '^(Passphrase|PreSharedKey)=' /var/lib/iwd 2>/dev/null | label "iwd Wireless Credentials"
fi

# Netplan Wireless Definitions
if [ -d "/etc/netplan" ]; then
    grep -rnE '(access-points|password):' /etc/netplan 2>/dev/null | label "Netplan Wireless Definitions"
fi
