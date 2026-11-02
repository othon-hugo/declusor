#!/bin/bash
# -----------------------------------------------------------------------------
# Scans network targets to discover exposed HTTP/HTTPS web services.
# -----------------------------------------------------------------------------

subnet="$(get_local_subnet)"
[ -n "$subnet" ] || exit 0

PORTS="80 443 8000 8080 8443"

(
    for i in $(seq 1 254 2>/dev/null || echo {1..254}); do
        target="$subnet.$i"
        for port in $PORTS; do
            ( probe_tcp "$target" "$port" 1 && printf 'http://%s:%s OPEN\n' "$target" "$port" ) &
        done
    done
    wait
) | sort -V | label "Discovered Web Services ($subnet.0/24)"
