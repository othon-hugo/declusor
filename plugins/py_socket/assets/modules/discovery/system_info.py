import os
import platform
import sys

label: type

try:
    import subprocess

    result = subprocess.run(
        ["ps", "-axo", "pid,user,stat,comm"],
        capture_output=True,
        text=True,
    )

    label("Running Processes", result.stdout.strip())
except Exception as e:
    label("Running Processes", e)

try:
    info = [
        f"OS: {platform.system()} {platform.release()} ({platform.version()})",
        f"Architecture: {platform.machine()} ({platform.processor()})",
        f"Hostname: {platform.node()}",
        f"Python: {sys.version}",
        f"PID: {os.getpid()}",
        f"User: {os.environ.get('USER') or os.environ.get('USERNAME') or 'unknown'}",
        f"Working directory: {os.getcwd()}",
    ]

    label("System Information", "\n".join(info))
except Exception as e:
    label("System Information", e)


try:
    env_lines = [f"{k}={v}" for k, v in sorted(os.environ.items())]
    label("Environment Variables", "\n".join(env_lines))
except Exception as e:
    label("Environment Variables", e)
