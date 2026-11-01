"""Unit tests for TerminalInputSource presentation component in declusor.presentation.input_source."""

import builtins
from pathlib import Path

import pytest

from declusor import config, contract, presentation, testing


class RecordingReader:
    """Deterministic reader double recording presented prompts and returning configured responses."""

    def __init__(self, responses: list[str] | None = None) -> None:
        self.responses: list[str] = list(responses) if responses is not None else []
        self.prompts: list[str] = []
        self._index: int = 0

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)

        if self._index < len(self.responses):
            response = self.responses[self._index]
            self._index += 1

            return response

        return ""


class TestTerminalInputSourceReading:
    """Tests verifying TerminalInputSource command and raw line reading behavior."""

    def test_terminal_input_source_contract_conformance__implements_iinput_source(self) -> None:
        """TerminalInputSource satisfies the IInputSource contract interface."""

        source = presentation.TerminalInputSource()

        assert isinstance(source, contract.IInputSource)

    def test_terminal_input_source_default_initialization__binds_builtin_input(self) -> None:
        """TerminalInputSource defaults reader to builtins.input when none is injected."""

        source = presentation.TerminalInputSource()

        assert source._reader is builtins.input
        assert source._history_file is None

    def test_terminal_input_source_read_command__strips_surrounding_whitespace(self) -> None:
        """read_command strips leading and trailing whitespace from the injected reader result."""

        reader = RecordingReader(["   execute payload.bin   \n"])
        source = presentation.TerminalInputSource(reader=reader)

        result = source.read_command("[test] ")

        assert result == "execute payload.bin"
        assert reader.prompts == ["[test] "]

    def test_terminal_input_source_read_command_empty_input__returns_empty_string(self) -> None:
        """read_command returns an empty string when the reader produces only whitespace."""

        reader = RecordingReader(["   \t   "])
        source = presentation.TerminalInputSource(reader=reader)

        result = source.read_command("> ")

        assert result == ""
        assert reader.prompts == ["> "]

    def test_terminal_input_source_read_raw__appends_newline_to_output(self) -> None:
        """read_raw appends a trailing newline to the exact output returned by reader."""

        reader = RecordingReader(["raw_command_line"])
        source = presentation.TerminalInputSource(reader=reader)

        result = source.read_raw("prompt> ")

        assert result == "raw_command_line\n"
        assert reader.prompts == ["prompt> "]

    def test_terminal_input_source_read_raw_empty_input__returns_newline_only(self) -> None:
        """read_raw appends a newline even when the reader output is completely empty."""

        reader = RecordingReader([""])
        source = presentation.TerminalInputSource(reader=reader)

        result = source.read_raw("prompt> ")

        assert result == "\n"
        assert reader.prompts == ["prompt> "]

    def test_terminal_input_source_read_raw__preserves_internal_and_leading_whitespace(self) -> None:
        """read_raw does not strip leading or trailing spaces from the underlying response."""

        reader = RecordingReader(["   indented code block   "])
        source = presentation.TerminalInputSource(reader=reader)

        result = source.read_raw("> ")

        assert result == "   indented code block   \n"

    def test_terminal_input_source_read_raw_with_existing_newline__preserves_single_newline(self) -> None:
        """read_raw preserves an existing trailing newline without duplicating it."""

        reader = RecordingReader(["line with newline\n"])
        source = presentation.TerminalInputSource(reader=reader)

        result = source.read_raw("> ")

        assert result == "line with newline\n"

    def test_terminal_input_source_read_command_positional_only__raises_type_error(self) -> None:
        """read_command enforces positional-only argument passing for prompt."""

        source = presentation.TerminalInputSource()

        with pytest.raises(TypeError, match="positional-only"):
            source.read_command(prompt="> ")  # type: ignore[call-arg]

    def test_terminal_input_source_read_raw_positional_only__raises_type_error(self) -> None:
        """read_raw enforces positional-only argument passing for prompt."""

        source = presentation.TerminalInputSource()

        with pytest.raises(TypeError, match="positional-only"):
            source.read_raw(prompt="> ")  # type: ignore[call-arg]


class TestTerminalInputSourceHistory:
    """Tests verifying history file enablement, loading, and persistence in TerminalInputSource."""

    def test_terminal_input_source_enable_history__sets_history_file_path(self, tmp_path: Path) -> None:
        """enable_history records the target history file path on the input source."""

        history_file = tmp_path / ".test_history"
        source = presentation.TerminalInputSource()

        source.enable_history(history_file)

        assert source._history_file == history_file

    def test_terminal_input_source_enable_history_when_file_exists__reads_history_via_readline(
        self,
        tmp_path: Path,
    ) -> None:
        """enable_history reads history file into readline when the file already exists on disk."""

        history_file = tmp_path / ".test_history"
        history_file.write_text("cmd1\ncmd2\n")

        dummy_readline = testing.DummyReadlineAdapter()
        source = presentation.TerminalInputSource(readline_adapter=dummy_readline)
        source.enable_history(history_file)

        assert dummy_readline.read_paths == [str(history_file)]

    def test_terminal_input_source_enable_history_when_file_does_not_exist__does_not_call_read(
        self,
        tmp_path: Path,
    ) -> None:
        """enable_history bypasses read_history_file when the history file does not exist."""

        history_file = tmp_path / "nonexistent_history"
        dummy_readline = testing.DummyReadlineAdapter()

        source = presentation.TerminalInputSource(readline_adapter=dummy_readline)
        source.enable_history(history_file)

        assert dummy_readline.read_paths == []

    def test_terminal_input_source_enable_history_suppresses_permission_error(
        self,
        tmp_path: Path,
    ) -> None:
        """enable_history suppresses PermissionError when reading history file."""

        history_file = tmp_path / ".test_history"
        history_file.write_text("cmd\n")

        dummy_readline = testing.DummyReadlineAdapter(read_error=PermissionError("Access denied"))

        source = presentation.TerminalInputSource(readline_adapter=dummy_readline)
        source.enable_history(history_file)

        assert source._history_file == history_file

    def test_terminal_input_source_enable_history_when_readline_is_none__returns_gracefully(
        self,
        tmp_path: Path,
    ) -> None:
        """enable_history returns immediately when readline module is unavailable."""

        dummy_readline = testing.DummyReadlineAdapter(is_available=False)
        history_file = tmp_path / ".test_history"
        source = presentation.TerminalInputSource(readline_adapter=dummy_readline)

        source.enable_history(history_file)

        assert source._history_file is None

    def test_terminal_input_source_save_history__writes_history_file_via_readline(
        self,
        tmp_path: Path,
    ) -> None:
        """_save_history invokes readline.write_history_file with the configured path."""

        history_file = tmp_path / ".saved_history"
        dummy_readline = testing.DummyReadlineAdapter()

        source = presentation.TerminalInputSource(readline_adapter=dummy_readline)
        source.enable_history(history_file)
        source._save_history()

        assert dummy_readline.written_paths == [str(history_file)]

    def test_terminal_input_source_save_history_when_history_file_is_none__does_nothing(self) -> None:
        """_save_history returns cleanly without calling readline when history_file is None."""

        dummy_readline = testing.DummyReadlineAdapter()

        source = presentation.TerminalInputSource(readline_adapter=dummy_readline)
        source._save_history()

        assert dummy_readline.written_paths == []

    def test_terminal_input_source_save_history_suppresses_permission_error(
        self,
        tmp_path: Path,
    ) -> None:
        """_save_history suppresses PermissionError when saving history to disk."""

        history_file = tmp_path / ".test_history"
        dummy_readline = testing.DummyReadlineAdapter(write_error=PermissionError("Disk write protected"))

        source = presentation.TerminalInputSource(readline_adapter=dummy_readline)
        source.enable_history(history_file)
        source._save_history()

        assert source._history_file == history_file

    def test_terminal_input_source_save_history_when_readline_is_none__returns_gracefully(
        self,
        tmp_path: Path,
    ) -> None:
        """_save_history returns cleanly when readline is None."""

        dummy_readline = testing.DummyReadlineAdapter(is_available=False)
        source = presentation.TerminalInputSource(readline_adapter=dummy_readline)
        source.enable_history(tmp_path / "history")

        source._save_history()

    def test_terminal_input_source_enable_history_positional_only__raises_type_error(
        self,
        tmp_path: Path,
    ) -> None:
        """enable_history enforces positional-only argument passing for history_file."""

        source = presentation.TerminalInputSource()

        with pytest.raises(TypeError, match="positional-only"):
            source.enable_history(history_file=tmp_path / ".hist")  # type: ignore[call-arg]

    def test_terminal_input_source_save_history_suppresses_generic_os_error(
        self,
        tmp_path: Path,
    ) -> None:
        """_save_history suppresses generic OSError such as read-only filesystem or device full."""

        history_file = tmp_path / ".test_history"
        dummy_readline = testing.DummyReadlineAdapter(write_error=OSError(30, "Read-only file system"))

        source = presentation.TerminalInputSource(readline_adapter=dummy_readline)
        source.enable_history(history_file)
        source._save_history()

        assert source._history_file == history_file


class TestTerminalInputSourceConfiguration:
    """Tests verifying configuration and blocklist properties of TerminalInputSource."""

    def test_terminal_input_source_default_blocklists__match_config_defaults(self) -> None:
        """TerminalInputSource defaults blocked_names and blocked_extensions to config constants."""

        source = presentation.TerminalInputSource()

        assert source.blocked_names == config.DEFAULT_COMPLETION_BLOCKED_NAMES
        assert source.blocked_extensions == config.DEFAULT_COMPLETION_BLOCKED_EXTENSIONS

    def test_terminal_input_source_custom_blocklists__stored_as_frozenset(self) -> None:
        """TerminalInputSource converts custom blocked collections to immutable frozensets."""

        custom_names = ["node_modules", "dist"]
        custom_exts = [".tmp"]

        source = presentation.TerminalInputSource(
            blocked_names=custom_names,
            blocked_extensions=custom_exts,
        )

        assert source.blocked_names == frozenset(custom_names)
        assert source.blocked_extensions == frozenset(custom_exts)


class TestSystemReadlineAdapter:
    """Tests verifying behavior of SystemReadlineAdapter backed by stdlib readline."""

    def test_system_readline_adapter_availability(self) -> None:
        """SystemReadlineAdapter is available on standard Linux Python runtimes."""

        adapter = presentation.SystemReadlineAdapter()

        assert adapter.is_available is True

    def test_system_readline_adapter_line_buffer_and_delims(self) -> None:
        """SystemReadlineAdapter returns string line buffer and delimiter set."""

        adapter = presentation.SystemReadlineAdapter()

        assert isinstance(adapter.get_line_buffer(), str)
        assert isinstance(adapter.get_completer_delims(), str)

    def test_system_readline_adapter_completer_roundtrip(self) -> None:
        """SystemReadlineAdapter allows registering and clearing completer callable."""

        adapter = presentation.SystemReadlineAdapter()

        def stub_completer(text: str, state: int) -> str | None:
            return None

        adapter.set_completer(stub_completer)
        assert adapter.get_completer() is stub_completer

        adapter.set_completer(None)
        assert adapter.get_completer() is None

    def test_system_readline_adapter_delims_and_bindings(self) -> None:
        """SystemReadlineAdapter allows setting delimiters and parse_and_bind initialization."""

        adapter = presentation.SystemReadlineAdapter()
        original_delims = adapter.get_completer_delims()

        try:
            adapter.set_completer_delims(" \t\n;")
            assert adapter.get_completer_delims() == " \t\n;"
            adapter.parse_and_bind("tab: complete")
        finally:
            adapter.set_completer_delims(original_delims)

    def test_system_readline_adapter_history_file(self, tmp_path: Path) -> None:
        """SystemReadlineAdapter can read and write history files."""

        adapter = presentation.SystemReadlineAdapter()
        history_file = tmp_path / "system_history.txt"
        history_file.write_text("cmd1\ncmd2\n")

        adapter.read_history_file(str(history_file))
        adapter.write_history_file(str(history_file))
        assert history_file.exists()
