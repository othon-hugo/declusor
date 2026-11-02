#!/bin/bash
# -----------------------------------------------------------------------------
# Locates executables with special permission bits (SUID/SGID) for privilege
# escalation.
# -----------------------------------------------------------------------------

GTFO_PATTERN="/(nmap|vim|vi|find|bash|sh|dash|zsh|less|more|cp|mv|awk|gawk|mawk|python[0-9.]*|perl|ruby|lua|php|tar|zip|gzip|bzip2|env|pkexec|systemctl|journalctl|mount|umount|openssl|socat|nc|netcat|curl|wget|gdb|strace|ltrace|docker|lxc|capsh|setarch|time|timeout|stdbuf|watch|xargs)$"

# SUID Binaries
SUID_LIST="$(find / \( -path '/proc/*' -o -path '/sys/*' -o -path '/dev/*' -o -path '/run/*' \) -prune -o -perm -4000 -type f -print 2>/dev/null)"

if [ -n "$SUID_LIST" ]; then
    printf '%s\n' "$SUID_LIST" | format_perms | column -t -s ';' | label "SUID Binaries"
    printf '%s\n' "$SUID_LIST" | grep -E "$GTFO_PATTERN" 2>/dev/null | format_perms | column -t -s ';' | label "High-Risk SUID Binaries (GTFOBins)"
fi

# SGID Binaries
find / \( -path '/proc/*' -o -path '/sys/*' -o -path '/dev/*' -o -path '/run/*' \) -prune -o -perm -2000 -type f -print 2>/dev/null | format_perms | column -t -s ';' | label "SGID Binaries"
