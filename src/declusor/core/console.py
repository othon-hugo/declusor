import atexit
import glob
import os
import readline
import sys
from pathlib import Path
from typing import Optional, Sequence

from declusor import interface


class Console(interface.IConsole):
    """Console implementation using readline for input and output."""

    def __init__(self) -> None:
        self._history_file: Optional[Path] = None

    def setup_completer(self, command_routes: Sequence[str], /) -> None:
        """Set up the readline completer for command line input.

        Args:
            command_routes: Sequence of available commands.
        """

        if not readline:
            return

        def _search_file(search_term: str) -> list[str]:
            """Search for files and directories matching the search term."""

            files: list[str] = []

            if not search_term:
                search_term = ""

            searching_dir = os.path.dirname(search_term)
            searching_file = os.path.basename(search_term)

            target_dir = searching_dir if searching_dir else "."

            try:
                for filename in glob.glob(searching_file + "*", root_dir=target_dir):
                    filepath = os.path.join(target_dir, filename)

                    match_string = os.path.join(searching_dir, filename)

                    if os.path.isdir(filepath):
                        files.append(os.path.join(match_string, ""))
                    elif os.path.isfile(filepath):
                        files.append(match_string)
            except OSError:
                pass

            return files

        def _complete_line(text: str, state: int) -> str | None:
            def _find_file(text: str, state: int) -> str | None:
                matches = _search_file(text)

                return (matches + [None])[state]

            def _find_command(text: str, state: int) -> str | None:
                matches = [line for line in command_routes if line.startswith(text)]

                if state < len(matches):
                    return matches[state]

                return None

            try:
                line_buffer = readline.get_line_buffer()
                commands = line_buffer.split(" ", 1)
            except Exception:
                return None

            match len(commands):
                case 0 | 1:
                    return _find_command(text, state)
                case 2:
                    if commands[0] in command_routes:
                        return _find_file(text, state)
                case _:
                    return None

            return None

        readline.set_completer_delims(" \t\n;")
        readline.set_completer(_complete_line)
        readline.parse_and_bind("tab: complete")

    def enable_history(self, history_file: Path, /) -> None:
        """Enable history saving and loading.

        Args:
            history_file: Path to the history file.
        """

        if not readline:
            return

        self._history_file = history_file

        if self._history_file.exists():
            try:
                readline.read_history_file(str(self._history_file))
            except (FileNotFoundError, PermissionError):
                pass

        atexit.register(self._save_history)

    def read_line(self, prompt: str = "", /) -> str:
        """Read a line from standard input with readline support.

        Note:
            Uses input() to preserve readline functionality (autocomplete, history).
            This is a blocking call.
        """

        return input(prompt) + "\n"

    def read_stripped_line(self, prompt: str = "", /) -> str:
        """Read a line from standard input and strip whitespace."""

        return self.read_line(prompt).strip()

    def write_message(self, message: str, /) -> None:
        """Write a message to standard output."""

        sys.stdout.write(message + "\n")
        sys.stdout.flush()

    def write_binary_data(self, message: bytes, /) -> None:
        """Write binary data to standard output."""

        sys.stdout.buffer.write(message)
        sys.stdout.buffer.flush()

    def write_error_message(self, message: str | BaseException, /) -> None:
        """Write an error message to standard error."""

        sys.stderr.write(f"error: {message}\n")
        sys.stderr.flush()

    def write_warning_message(self, message: str | BaseException, /) -> None:
        """Write a warning message to standard error."""

        sys.stderr.write(f"warning: {message}\n")
        sys.stderr.flush()

    def _save_history(self) -> None:
        """Save history to file."""

        if readline and self._history_file:
            try:
                readline.write_history_file(str(self._history_file))
            except (FileNotFoundError, PermissionError):
                pass
