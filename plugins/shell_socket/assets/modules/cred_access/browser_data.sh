#!/bin/bash
# -----------------------------------------------------------------------------
# Locates web browser artifacts and profile data for credential extraction and
# analysis.
# -----------------------------------------------------------------------------

# Mozilla-based Browsers
find /home /root "${HOME:-/root}" -maxdepth 5 \( -name "logins.json" -o -name "key4.db" -o -name "cert9.db" -o -name "places.sqlite" -o -name "cookies.sqlite" \) 2>/dev/null | sort -u | label "Mozilla Profile Artifacts"

# Chromium-based Browsers
find /home /root "${HOME:-/root}" -maxdepth 5 \( -path "*/google-chrome/*" -o -path "*/chromium/*" -o -path "*/BraveSoftware/*" -o -path "*/microsoft-edge/*" -o -path "*/vivaldi/*" \) \( -name "Login Data" -o -name "History" -o -name "Cookies" -o -name "Local State" \) 2>/dev/null | sort -u | label "Chromium Profile Artifacts"
