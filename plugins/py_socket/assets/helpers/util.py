"""Helper library: output formatting utilities for the py_socket client agent.

This module is transmitted to the remote Python agent during session
initialization and executed in the persistent session scope. It provides
presentation helpers mirroring the Declusor shell_socket utility conventions,
ensuring consistent output formatting across discovery modules.
"""

import platform
import sys


def print_with_label(title: str, content: str = "") -> None:
    """Print a labelled section to stdout.

    Formats the output consistent with the shell_socket ``print_with_label``
    convention: an uppercase title followed by a separator line of equal
    length, then the body text.

    Args:
        title: Section heading displayed in uppercase.
        content: Body text to display beneath the heading. When empty,
            the function only prints the heading and separator.
    """

    heading = title.upper()
    separator = "-" * len(heading)

    print(f"\n{heading}\n{separator}")

    if content:
        print(content)


def format_table(headers: list, rows: list) -> str:
    """Format tabular data as an aligned plain-text table.

    Computes the maximum width of each column across headers and all rows,
    then produces a fixed-width, space-separated text table. No external
    dependencies are required.

    Args:
        headers: Column header labels.
        rows: Sequence of rows, each a sequence of string cell values.

    Returns:
        Formatted table string with aligned columns.
    """

    all_rows = [headers] + [list(row) for row in rows]
    col_widths = [max(len(str(row[i])) for row in all_rows if i < len(row)) for i in range(len(headers))]

    lines = []

    for row in all_rows:
        cells = (str(row[i]).ljust(col_widths[i]) if i < len(row) else "".ljust(col_widths[i]) for i in range(len(headers)))
        lines.append("  ".join(cells).rstrip())

    return "\n".join(lines)


def get_system_summary() -> dict:
    """Collect basic platform and process metadata.

    Returns:
        Dictionary with keys: ``platform``, ``architecture``, ``release``,
        ``python_version``, ``username``, and ``pid``.
    """

    import os

    return {
        "platform": platform.system(),
        "architecture": platform.machine(),
        "release": platform.release(),
        "python_version": sys.version.split()[0],
        "username": os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
        "pid": os.getpid(),
    }
