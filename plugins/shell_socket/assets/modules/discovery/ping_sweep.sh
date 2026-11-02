#!/bin/bash
# -----------------------------------------------------------------------------
# Probes network ranges to discover reachable hosts on adjacent segments.
# -----------------------------------------------------------------------------

subnet="$(get_local_subnet)"
[ -n "$subnet" ] || exit 0

(
    for i in $(seq 1 254 2>/dev/null || echo {1..254}); do
        ( ping -c 1 -W 1 "$subnet.$i" >/dev/null 2>&1 && printf '%s.%s is reachable\n' "$subnet" "$i" ) &
    done
    wait
) | sort -V | label "Reachable Subnet Hosts ($subnet.0/24)"
