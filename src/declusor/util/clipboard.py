"""Clipboard delivery utilities supporting terminal OSC 52 and OS clipboard managers."""

import base64
import os
import subprocess
import sys
from collections.abc import Callable, Mapping
from typing import Protocol, runtime_checkable

from declusor import config


@runtime_checkable
class BinaryWriter(Protocol):
    """Structural protocol for binary stream writers."""

    def write_binary_data(self, data: bytes, /) -> None:
        """Write raw binary payload.

        Args:
            data: Binary payload to write verbatim.
        """

        ...


type CommandRunner = Callable[[list[str], bytes], bool]


def default_command_runner(args: list[str], payload: bytes) -> bool:
    """Execute a system clipboard command passing payload on standard input.

    Args:
        args: Command and arguments to execute.
        payload: Binary payload to pipe to stdin.

    Returns:
        True if command completed successfully (exit code 0), False otherwise.
    """

    try:
        result = subprocess.run(
            args,
            input=payload,
            check=False,
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def get_clipboard_commands(
    platform: str = sys.platform,
    env: Mapping[str, str] | None = None,
) -> list[list[str]]:
    """Determine candidate OS clipboard commands for the given platform and environment.

    Args:
        platform: Platform string (e.g. sys.platform).
        env: Environment variable mapping. Defaults to os.environ if None.

    Returns:
        Ordered list of command argument lists to attempt.
    """

    if env is None:
        env = os.environ

    if platform == "darwin":
        return [["pbcopy"]]

    if platform in ("win32", "cygwin"):
        return [["clip.exe"]]

    if platform.startswith("linux") or "bsd" in platform or platform == "sunos5":
        if env.get("WAYLAND_DISPLAY"):
            return [
                ["wl-copy"],
                ["xclip", "-selection", "clipboard"],
                ["xsel", "-b", "-i"],
            ]

        return [
            ["xclip", "-selection", "clipboard"],
            ["xsel", "-b", "-i"],
            ["wl-copy"],
        ]

    return []


def build_osc52_sequence(payload: bytes) -> bytes:
    """Format binary payload as an OSC 52 terminal clipboard escape sequence.

    Args:
        payload: Binary payload to encode.

    Returns:
        ASCII bytes sequence formatted as '\\x1b]52;c;{base64}\\x07'.
    """

    b64_str = base64.b64encode(payload).decode("ascii")

    return f"\x1b]52;c;{b64_str}\x07".encode("ascii")


def copy_to_clipboard(
    text: str,
    /,
    *,
    view: BinaryWriter | None = None,
    command_runner: CommandRunner | None = None,
    platform: str = sys.platform,
    env: Mapping[str, str] | None = None,
    emit_osc52: bool = True,
) -> None:
    """Copy text to clipboard using OSC 52 terminal sequence and OS-specific clipboard commands.

    Args:
        text: Text to copy to clipboard.
        view: Optional BinaryWriter to receive OSC 52 sequence. If None, writes to sys.stdout.buffer.
        command_runner: Optional command runner callable for dependency injection and testing.
        platform: Target platform identifier (default: sys.platform).
        env: Target environment mapping (default: os.environ).
        emit_osc52: Whether to emit the OSC 52 escape sequence (default: True).

    Raises:
        config.LauncherDeliveryError: If all clipboard delivery mechanisms fail.
    """

    payload = text.encode("utf-8")
    mechanisms_succeeded: int = 0
    failures: list[str] = []

    if emit_osc52:
        osc52_seq = build_osc52_sequence(payload)

        if view is not None:
            try:
                view.write_binary_data(osc52_seq)
                mechanisms_succeeded += 1
            except Exception as error:
                failures.append(f"OSC 52: {type(error).__name__}: {error}")
                pass
        else:
            try:
                sys.stdout.buffer.write(osc52_seq)
                sys.stdout.buffer.flush()
                mechanisms_succeeded += 1
            except (AttributeError, OSError) as error:
                failures.append(f"OSC 52: {type(error).__name__}: {error}")
                pass

    runner = command_runner if command_runner is not None else default_command_runner
    commands = get_clipboard_commands(platform, env)

    for cmd in commands:
        try:
            if runner(cmd, payload):
                mechanisms_succeeded += 1
                break
        except Exception as error:
            failures.append(f"{cmd[0]}: {type(error).__name__}: {error}")
            continue

    if mechanisms_succeeded == 0:
        details = f" Details: {'; '.join(failures)}" if failures else ""
        raise config.LauncherDeliveryError(f"Failed to copy launcher payload to system clipboard: all clipboard mechanisms failed.{details}")
