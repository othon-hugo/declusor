# -----------------------------------------------------------------------------
# Identifies available command-line utilities, development toolchains, and
# network binaries.
# -----------------------------------------------------------------------------

import shutil
from contextlib import suppress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from std import format_table, label

tools = [
    ("Runtime", "Python 3", "python3"),
    ("Runtime", "Python 2", "python"),
    ("Runtime", "Ruby", "ruby"),
    ("Runtime", "Node.js", "node"),
    ("Runtime", "PHP", "php"),
    ("Runtime", "Perl", "perl"),
    ("Runtime", "Java", "java"),
    ("Runtime", "Go", "go"),
    ("Build", "GCC", "gcc"),
    ("Build", "Clang", "clang"),
    ("Build", "Make", "make"),
    ("Build", "CMake", "cmake"),
    ("Build", "Git", "git"),
    ("Container", "Docker", "docker"),
    ("Container", "Podman", "podman"),
    ("Container", "Kubectl", "kubectl"),
    ("Network", "curl", "curl"),
    ("Network", "wget", "wget"),
    ("Network", "nc / ncat", "nc"),
    ("Network", "socat", "socat"),
    ("Network", "ssh", "ssh"),
    ("Archive/Crypto", "tar", "tar"),
    ("Archive/Crypto", "gzip", "gzip"),
    ("Archive/Crypto", "openssl", "openssl"),
]

with suppress(Exception):
    results: list[list[str]] = []

    for category, name, binary in tools:
        path = shutil.which(binary)

        if path:
            results.append([category, name, binary, path])

    if results:
        headers = ["Category", "Tool", "Binary", "Path"]
        label("Available Utilities & Toolchains", format_table(headers, results))
