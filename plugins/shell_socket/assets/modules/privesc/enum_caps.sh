#!/bin/bash
# -----------------------------------------------------------------------------
# Identifies binaries granted elevated kernel capabilities.
# -----------------------------------------------------------------------------

if _have getcap; then
    getcap -r / 2>/dev/null | label "Elevated File Capabilities"
fi
