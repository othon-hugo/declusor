# -----------------------------------------------------------------------------
# Gathers general host reconnaissance data and operating environment
# characteristics.
# -----------------------------------------------------------------------------

import os
import platform
import shutil
import sys
from contextlib import suppress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from std import format_table, get_system_summary, label, run_command

# System Overview
with suppress(Exception):
    summary = get_system_summary()
    rows: list[list[str]] = [
        ["OS", f"{summary['platform']} {summary['release']} ({platform.version()})"],
        ["Architecture", f"{summary['architecture']} ({platform.processor() or 'generic'})"],
        ["Hostname", platform.node()],
        ["Python", sys.version.split()[0]],
        ["PID", str(summary["pid"])],
        ["User", str(summary["username"])],
        ["Working Directory", os.getcwd()],
    ]

    if hasattr(os, "getuid"):
        rows.append(["UID / GID", f"uid={os.getuid()} gid={os.getgid()} groups={os.getgroups()}"])

    with suppress(OSError):
        usage = shutil.disk_usage("/")
        total_gb = usage.total // (1024**3)
        free_gb = usage.free // (1024**3)
        rows.append(["Root Disk", f"{free_gb} GiB free / {total_gb} GiB total"])

    if os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"):
        rows.append(["Environment", "Containerized"])

    label("System Information", format_table(["Property", "Value"], rows))

# Running Processes
with suppress(Exception):
    proc_out = ""

    for cmd in (["ps", "-eo", "pid,user,stime,args"], ["ps", "-axo", "pid,user,stat,comm"], ["tasklist"]):
        proc_out = run_command(cmd)
        if proc_out:
            break

    if proc_out:
        lines = proc_out.splitlines()[:50]
        label("Running Processes", "\n".join(lines))

# Environment Variables
with suppress(Exception):
    env_rows = [[k, v] for k, v in sorted(os.environ.items())]

    if env_rows:
        label("Environment Variables", format_table(["Variable", "Value"], env_rows))
