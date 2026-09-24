"""Module: system information discovery for the py_socket client agent.

Loaded on demand via the ``load`` command. Uses helpers available in the
persistent session scope (loaded during initialization). Falls back to
standard library methods if helpers are not present.
"""
import os
import platform
import sys

# --- Running Processes ---
try:
    import subprocess
    result = subprocess.run(
        ["ps", "-axo", "pid,user,stat,comm"],
        capture_output=True,
        text=True,
    )
    print_with_label("Running Processes", result.stdout.strip())
except Exception:
    print_with_label("Running Processes", "(ps not available)")

# --- System Information ---
info = [
    f"OS: {platform.system()} {platform.release()} ({platform.version()})",
    f"Architecture: {platform.machine()} ({platform.processor()})",
    f"Hostname: {platform.node()}",
    f"Python: {sys.version}",
    f"PID: {os.getpid()}",
    f"User: {os.environ.get('USER') or os.environ.get('USERNAME') or 'unknown'}",
    f"Working directory: {os.getcwd()}",
]
print_with_label("System Information", "\n".join(info))

# --- Environment Variables ---
env_lines = [f"{k}={v}" for k, v in sorted(os.environ.items())]
print_with_label("Environment Variables", "\n".join(env_lines))
