import atexit
import glob
import os
import readline
from collections.abc import Callable, Collection, Mapping, Sequence
from contextlib import suppress
from pathlib import Path

from declusor import config, contract


class TerminalInputSource(contract.IInputSource):
    """Terminal input source implementation using readline for input, history, and autocomplete."""

    def __init__(
        self,
        reader: Callable[[str], str] | None = None,
        *,
        blocked_names: Collection[str] | None = None,
        blocked_extensions: Collection[str] | None = None,
    ) -> None:
        self._reader: Callable[[str], str] = reader if reader is not None else input
        self._history_file: Path | None = None
        self._blocked_names: frozenset[str] = frozenset(blocked_names) if blocked_names is not None else config.DEFAULT_COMPLETION_BLOCKED_NAMES
        self._blocked_extensions: frozenset[str] = (
            frozenset(blocked_extensions) if blocked_extensions is not None else config.DEFAULT_COMPLETION_BLOCKED_EXTENSIONS
        )

    @property
    def blocked_names(self) -> frozenset[str]:
        """Names of files and directories excluded from autocompletion."""

        return self._blocked_names

    @property
    def blocked_extensions(self) -> frozenset[str]:
        """File extensions excluded from autocompletion."""

        return self._blocked_extensions

    def read_command(self, prompt: str = "", /) -> str:
        """Read a stripped command string from standard input.

        Args:
            prompt: Text prompt displayed to the operator.

        Returns:
            The input string with leading and trailing whitespace stripped.
        """

        return self._reader(prompt).strip()

    def read_raw(self, prompt: str = "", /) -> str:
        """Read a raw line from standard input with newline appended.

        Args:
            prompt: Text prompt displayed to the operator.

        Returns:
            The raw input string including trailing newline.
        """

        raw_line = self._reader(prompt)

        return raw_line if raw_line.endswith("\n") else f"{raw_line}\n"

    def setup_completer(
        self,
        command_routes: Sequence[str],
        assets_dir: Path | None = None,
        route_completions: Mapping[str, config.RouteCompletionMode] | None = None,
        /,
        *,
        blocked_names: Collection[str] | None = None,
        blocked_extensions: Collection[str] | None = None,
    ) -> None:
        """Set up the readline completer for command line input.

        Args:
            command_routes: Sequence of available commands.
            assets_dir: Optional base directory for client plugin assets.
            route_completions: Optional mapping of route identifiers to their completion mode.
            blocked_names: Optional override of file and directory names to exclude.
            blocked_extensions: Optional override of file extensions to exclude.
        """

        if not readline:
            return

        active_blocked_names = frozenset(blocked_names) if blocked_names is not None else self._blocked_names
        active_blocked_extensions = frozenset(blocked_extensions) if blocked_extensions is not None else self._blocked_extensions

        def _is_blocked(filename: str) -> bool:
            """Check if a candidate file or directory name is in the block list."""

            if filename in active_blocked_names:
                return True

            return any(filename.endswith(ext) for ext in active_blocked_extensions)

        def _search_file(search_term: str, base_dir: Path | None = None) -> list[str]:
            """Search for files and directories matching the search term."""

            files: list[str] = []

            if not search_term:
                search_term = ""

            searching_dir = os.path.dirname(search_term)
            searching_file = os.path.basename(search_term)

            if any(part in active_blocked_names for part in Path(searching_dir).parts):
                return []

            is_explicit_host_path = search_term.startswith(("./", "../")) or os.path.isabs(search_term)

            if is_explicit_host_path or base_dir is None:
                target_dir = searching_dir if searching_dir else "."
            else:
                target_dir = os.path.join(base_dir, searching_dir) if searching_dir else str(base_dir)

            try:
                pattern = glob.escape(searching_file) + "*"

                for filename in glob.glob(pattern, root_dir=target_dir):
                    if _is_blocked(filename):
                        continue

                    filepath = os.path.join(target_dir, filename)

                    match_string = os.path.join(searching_dir, filename)

                    if os.path.isdir(filepath):
                        files.append(os.path.join(match_string, ""))
                    elif os.path.isfile(filepath):
                        files.append(match_string)
            except OSError:
                pass

            files.sort()

            return files

        def _complete_line(text: str, state: int) -> str | None:
            def _find_file(text: str, state: int, base_dir: Path | None = None) -> str | None:
                matches = _search_file(text, base_dir=base_dir)

                if state < len(matches):
                    return matches[state]

                return None

            def _find_command(text: str, state: int) -> str | None:
                matches = [line for line in command_routes if line.startswith(text)]

                if state < len(matches):
                    return matches[state]

                return None

            try:
                line_buffer = readline.get_line_buffer()
                commands = line_buffer.lstrip().split(" ", 1)
            except Exception:
                return None

            match len(commands):
                case 0 | 1:
                    return _find_command(text, state)
                case 2:
                    leading_cmd = commands[0]
                    if leading_cmd in command_routes:
                        if route_completions is not None:
                            mode = route_completions.get(leading_cmd, config.RouteCompletionMode.NONE)
                        elif assets_dir is None:
                            mode = config.RouteCompletionMode.HOST_PATH
                        elif leading_cmd == config.OfficialRoute.LOAD.value:
                            mode = config.RouteCompletionMode.MODULE_PATH
                        elif leading_cmd in (config.OfficialRoute.UPLOAD.value, config.OfficialRoute.EXECUTE.value):
                            mode = config.RouteCompletionMode.HOST_PATH
                        else:
                            mode = config.RouteCompletionMode.ASSET_PATH

                        match mode:
                            case config.RouteCompletionMode.HOST_PATH:
                                return _find_file(text, state, base_dir=None)
                            case config.RouteCompletionMode.MODULE_PATH:
                                modules_dir = assets_dir / "modules" if assets_dir is not None else None
                                base = modules_dir if modules_dir is not None and modules_dir.is_dir() else assets_dir
                                return _find_file(text, state, base_dir=base)
                            case config.RouteCompletionMode.ASSET_PATH:
                                return _find_file(text, state, base_dir=assets_dir)
                            case config.RouteCompletionMode.NONE:
                                return None
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
            with suppress(OSError):
                readline.read_history_file(str(self._history_file))

        atexit.register(self._save_history)

    def _save_history(self) -> None:
        """Save history to file."""

        if readline and self._history_file:
            with suppress(OSError):
                readline.write_history_file(str(self._history_file))
