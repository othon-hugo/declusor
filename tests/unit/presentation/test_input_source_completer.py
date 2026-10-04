"""Unit tests for TerminalInputSource tab completion and file discovery in declusor.presentation.input_source."""

import glob
import readline
from collections.abc import Callable
from pathlib import Path

import pytest

from declusor import presentation


def _get_configured_completer(
    source: presentation.TerminalInputSource,
    routes: list[str],
    assets_dir: Path | None = None,
) -> Callable[[str, int], str | None]:
    """Helper to configure completer and retrieve the bound readline completer function."""

    source.setup_completer(routes, assets_dir)
    completer = readline.get_completer()
    assert completer is not None
    return completer


class TestTerminalInputSourceCompleterSetup:
    """Tests verifying setup_completer configuration on the readline module."""

    def test_terminal_input_source_setup_completer__configures_delims_and_completer(self) -> None:
        """setup_completer binds the line completion function and sets word delimiters."""

        source = presentation.TerminalInputSource()

        source.setup_completer(["help", "exit"])

        completer = readline.get_completer()
        assert callable(completer)
        delims = readline.get_completer_delims()
        assert " " in delims
        assert "\t" in delims
        assert ";" in delims

    def test_terminal_input_source_setup_completer_when_readline_is_none__returns_gracefully(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """setup_completer returns cleanly when readline is None."""

        monkeypatch.setattr(presentation.input_source, "readline", None)

        source = presentation.TerminalInputSource()
        source.setup_completer(["help", "exit"])

    def test_terminal_input_source_setup_completer_positional_only__raises_type_error(self) -> None:
        """setup_completer enforces positional-only argument passing for command_routes."""

        source = presentation.TerminalInputSource()

        with pytest.raises(TypeError, match="positional-only"):
            source.setup_completer(command_routes=["help", "exit"])  # type: ignore[call-arg]

    def test_terminal_input_source_setup_completer_assets_dir_keyword__raises_type_error(self) -> None:
        """setup_completer enforces positional-only argument passing for assets_dir."""

        source = presentation.TerminalInputSource()

        with pytest.raises(TypeError, match="positional-only"):
            source.setup_completer(["help", "exit"], assets_dir=Path("."))  # type: ignore[call-arg]


class TestTerminalInputSourceCommandCompletion:
    """Tests verifying command route prefix matching in TerminalInputSource completer."""

    def test_terminal_input_source_complete_command__returns_matching_routes_in_order(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Command completion returns matching routes in sequence and None at end."""

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["help", "exit", "execute", "eval"])

        monkeypatch.setattr(readline, "get_line_buffer", lambda: "ex")

        assert completer("ex", 0) == "exit"
        assert completer("ex", 1) == "execute"
        assert completer("ex", 2) is None

    def test_terminal_input_source_complete_command_empty_prefix__returns_all_routes(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Command completion with empty prefix returns all registered routes."""

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["exit", "help"])

        monkeypatch.setattr(readline, "get_line_buffer", lambda: "")

        assert completer("", 0) == "exit"
        assert completer("", 1) == "help"
        assert completer("", 2) is None

    def test_terminal_input_source_complete_command_no_matches__returns_none(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Command completion returns None immediately when no routes match the prefix."""

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["help", "exit"])

        monkeypatch.setattr(readline, "get_line_buffer", lambda: "zz")

        assert completer("zz", 0) is None

    def test_terminal_input_source_complete_command_state_beyond_bounds__returns_none(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Command completion returns None when state exceeds total matching routes."""

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["exit"])

        monkeypatch.setattr(readline, "get_line_buffer", lambda: "ex")

        assert completer("ex", 99) is None

    def test_terminal_input_source_complete_get_line_buffer_exception__returns_none(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Completer catches exceptions from readline.get_line_buffer and returns None."""

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["exit"])

        def broken_get_line_buffer() -> str:
            raise RuntimeError("buffer unavailable")

        monkeypatch.setattr(readline, "get_line_buffer", broken_get_line_buffer)

        assert completer("ex", 0) is None

    def test_terminal_input_source_complete_command_with_leading_whitespace__returns_matching_routes(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Command completion ignores leading whitespace in line buffer and matches prefix."""

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["exit", "execute"])

        monkeypatch.setattr(readline, "get_line_buffer", lambda: "   ex")

        assert completer("ex", 0) == "exit"
        assert completer("ex", 1) == "execute"
        assert completer("ex", 2) is None

    def test_terminal_input_source_complete_command_whitespace_only_buffer__returns_all_routes(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Command completion with whitespace-only line buffer and empty text yields all routes."""

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["alpha", "beta"])

        monkeypatch.setattr(readline, "get_line_buffer", lambda: "    ")

        assert completer("", 0) == "alpha"
        assert completer("", 1) == "beta"
        assert completer("", 2) is None


class TestTerminalInputSourceFileCompletion:
    """Tests verifying file path autocomplete and directory navigation in TerminalInputSource."""

    def test_terminal_input_source_complete_file__matches_files_in_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """File completion discovers matching files when the leading command is registered."""

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["upload", "exit"])

        target_file = tmp_path / "payload.bin"
        target_file.write_bytes(b"data")
        prefix = str(tmp_path / "pay")

        monkeypatch.setattr(readline, "get_line_buffer", lambda: f"upload {prefix}")

        match = completer(prefix, 0)
        assert match == str(target_file)
        assert completer(prefix, 1) is None

    def test_terminal_input_source_complete_file__appends_trailing_slash_to_directories(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """File completion appends trailing path separator to matching directory names."""

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["upload"])

        sub_dir = tmp_path / "subfolder"
        sub_dir.mkdir()
        prefix = str(tmp_path / "sub")

        monkeypatch.setattr(readline, "get_line_buffer", lambda: f"upload {prefix}")

        match = completer(prefix, 0)
        assert match == f"{sub_dir}/"
        assert completer(prefix, 1) is None

    def test_terminal_input_source_complete_file_state_beyond_bounds__returns_none(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """File completion returns None without IndexError when state exceeds matches."""

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["upload"])

        target_file = tmp_path / "data.bin"
        target_file.write_bytes(b"123")
        prefix = str(tmp_path / "dat")

        monkeypatch.setattr(readline, "get_line_buffer", lambda: f"upload {prefix}")

        assert completer(prefix, 0) == str(target_file)
        assert completer(prefix, 1) is None
        assert completer(prefix, 5) is None

    def test_terminal_input_source_complete_file_when_command_not_in_routes__returns_none(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """File completion is rejected when the leading command is not in registered routes."""

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["upload"])

        prefix = str(tmp_path / "some_file")
        monkeypatch.setattr(readline, "get_line_buffer", lambda: f"unregistered_cmd {prefix}")

        assert completer(prefix, 0) is None

    def test_terminal_input_source_complete_file_os_error_during_search__returns_none(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """File completion gracefully suppresses OSError raised during directory search."""

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["upload"])

        def broken_glob(*args: object, **kwargs: object) -> list[str]:
            raise OSError("I/O error during directory read")

        monkeypatch.setattr(glob, "glob", broken_glob)
        monkeypatch.setattr(readline, "get_line_buffer", lambda: "upload /invalid/path")

        assert completer("/invalid/path", 0) is None

    def test_terminal_input_source_complete_file_with_leading_whitespace_in_line_buffer__discovers_matches(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """File completion succeeds when line buffer has leading spaces before the command."""

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["upload"])

        target_file = tmp_path / "archive.tar"
        target_file.write_bytes(b"content")
        prefix = str(tmp_path / "arch")

        monkeypatch.setattr(readline, "get_line_buffer", lambda: f"   upload   {prefix}")

        assert completer(prefix, 0) == str(target_file)
        assert completer(prefix, 1) is None

    def test_terminal_input_source_complete_file_multiple_matches_sorted__returns_alphabetical_sequence(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """File completion yields multiple matches in deterministic lexicographical order."""

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["upload"])

        file_z = tmp_path / "file_z.bin"
        file_a = tmp_path / "file_a.bin"
        file_m = tmp_path / "file_m.bin"
        file_z.write_bytes(b"z")
        file_a.write_bytes(b"a")
        file_m.write_bytes(b"m")

        prefix = str(tmp_path / "file_")
        monkeypatch.setattr(readline, "get_line_buffer", lambda: f"upload {prefix}")

        assert completer(prefix, 0) == str(file_a)
        assert completer(prefix, 1) == str(file_m)
        assert completer(prefix, 2) == str(file_z)
        assert completer(prefix, 3) is None

    def test_terminal_input_source_complete_file_with_glob_special_characters__escapes_literal_filename(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """File completion treats glob special characters like brackets in search term as literals."""

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["upload"])

        special_file = tmp_path / "[payload].bin"
        special_file.write_bytes(b"data")

        prefix = str(tmp_path / "[pay")
        monkeypatch.setattr(readline, "get_line_buffer", lambda: f"upload {prefix}")

        assert completer(prefix, 0) == str(special_file)
        assert completer(prefix, 1) is None

    def test_terminal_input_source_complete_file_empty_search_term__lists_current_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """File completion with empty search term lists files in the current working directory."""

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["upload"])

        file1 = tmp_path / "alpha.txt"
        file1.write_bytes(b"1")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(readline, "get_line_buffer", lambda: "upload ")

        assert completer("", 0) == "alpha.txt"
        assert completer("", 1) is None


class TestTerminalInputSourceAssetCompletion:
    """Tests verifying asset directory autocompletion and command-aware scoping in TerminalInputSource."""

    def test_terminal_input_source_complete_load__with_assets_modules__completes_from_modules_dir(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """load command autocompletes payload modules from the plugin's assets/modules directory."""

        assets_dir = tmp_path / "assets"
        modules_dir = assets_dir / "modules" / "discovery"
        modules_dir.mkdir(parents=True)
        (modules_dir / "system_info.py").write_bytes(b"")
        (modules_dir / "dev_tools.py").write_bytes(b"")
        (assets_dir / "helpers").mkdir()

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["load", "upload"], assets_dir=assets_dir)

        monkeypatch.setattr(readline, "get_line_buffer", lambda: "load ")
        assert completer("", 0) == "discovery/"
        assert completer("", 1) is None

        monkeypatch.setattr(readline, "get_line_buffer", lambda: "load discovery/")
        assert completer("discovery/", 0) == "discovery/dev_tools.py"
        assert completer("discovery/", 1) == "discovery/system_info.py"
        assert completer("discovery/", 2) is None

    def test_terminal_input_source_complete_load__with_assets_without_modules__completes_from_assets_root(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """load command falls back to assets directory root when modules subdirectory is absent."""

        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        (assets_dir / "payload.py").write_bytes(b"")

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["load"], assets_dir=assets_dir)

        monkeypatch.setattr(readline, "get_line_buffer", lambda: "load ")
        assert completer("", 0) == "payload.py"
        assert completer("", 1) is None

    def test_terminal_input_source_complete_load__with_explicit_host_prefix__completes_from_host_filesystem(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """load command respects explicit ./ prefix to complete from the operator host directory."""

        assets_dir = tmp_path / "assets"
        (assets_dir / "modules").mkdir(parents=True)
        (assets_dir / "modules" / "asset_mod.py").write_bytes(b"")

        host_dir = tmp_path / "host"
        host_dir.mkdir()
        (host_dir / "local_script.py").write_bytes(b"")

        monkeypatch.chdir(host_dir)
        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["load"], assets_dir=assets_dir)

        monkeypatch.setattr(readline, "get_line_buffer", lambda: "load ./loc")
        assert completer("./loc", 0) == "./local_script.py"
        assert completer("./loc", 1) is None

    def test_terminal_input_source_complete_upload__with_assets_dir__defaults_to_host_filesystem(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """upload command completes from the host working directory even when assets_dir is configured."""

        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        (assets_dir / "asset_file.bin").write_bytes(b"")

        host_dir = tmp_path / "host"
        host_dir.mkdir()
        (host_dir / "upload_target.bin").write_bytes(b"")

        monkeypatch.chdir(host_dir)
        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["upload", "load"], assets_dir=assets_dir)

        monkeypatch.setattr(readline, "get_line_buffer", lambda: "upload ")
        assert completer("", 0) == "upload_target.bin"
        assert completer("", 1) is None

    def test_terminal_input_source_complete_execute__with_assets_dir__defaults_to_host_filesystem(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """execute command completes from the host working directory even when assets_dir is configured."""

        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        (assets_dir / "asset_script.sh").write_bytes(b"")

        host_dir = tmp_path / "host"
        host_dir.mkdir()
        (host_dir / "run_me.sh").write_bytes(b"")

        monkeypatch.chdir(host_dir)
        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["execute"], assets_dir=assets_dir)

        monkeypatch.setattr(readline, "get_line_buffer", lambda: "execute ")
        assert completer("", 0) == "run_me.sh"
        assert completer("", 1) is None


class TestTerminalInputSourceBlocklistFiltering:
    """Tests verifying default and custom blocklist filtering during tab completion."""

    def test_terminal_input_source_complete_file__skips_blocked_directories_and_files(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """File completion omits standard cache/environment directories and metadata files."""

        (tmp_path / "valid.txt").write_bytes(b"data")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / ".git").mkdir()
        (tmp_path / ".venv").mkdir()
        (tmp_path / "venv").mkdir()
        (tmp_path / ".DS_Store").write_bytes(b"")
        (tmp_path / "subfolder").mkdir()

        monkeypatch.chdir(tmp_path)
        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["upload"])

        monkeypatch.setattr(readline, "get_line_buffer", lambda: "upload ")

        assert completer("", 0) == "subfolder/"
        assert completer("", 1) == "valid.txt"
        assert completer("", 2) is None

    def test_terminal_input_source_complete_file__skips_blocked_extensions(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """File completion omits files with compiled bytecode, swap, or backup extensions."""

        (tmp_path / "script.py").write_bytes(b"print(1)")
        (tmp_path / "script.pyc").write_bytes(b"")
        (tmp_path / "script.pyo").write_bytes(b"")
        (tmp_path / "editor.swp").write_bytes(b"")
        (tmp_path / "backup.bak").write_bytes(b"")
        (tmp_path / "readme~").write_bytes(b"")

        monkeypatch.chdir(tmp_path)
        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["upload"])

        monkeypatch.setattr(readline, "get_line_buffer", lambda: "upload ")

        assert completer("", 0) == "script.py"
        assert completer("", 1) is None

    def test_terminal_input_source_complete_file__when_inside_blocked_directory__returns_empty(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """File completion immediately returns empty when searching within a blocked directory."""

        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "target.pyc").write_bytes(b"")

        monkeypatch.chdir(tmp_path)
        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["upload"])

        monkeypatch.setattr(readline, "get_line_buffer", lambda: "upload __pycache__/")
        assert completer("__pycache__/", 0) is None

        abs_prefix = str(cache_dir / "tar")
        monkeypatch.setattr(readline, "get_line_buffer", lambda: f"upload {abs_prefix}")
        assert completer(abs_prefix, 0) is None

    def test_terminal_input_source_complete_file__setup_completer_keyword_override(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """setup_completer keyword arguments override default blocked names and extensions."""

        (tmp_path / "keep.txt").write_bytes(b"data")
        (tmp_path / "custom_blocked.txt").write_bytes(b"")
        (tmp_path / "bytecode.pyc").write_bytes(b"")

        monkeypatch.chdir(tmp_path)
        source = presentation.TerminalInputSource()
        completer = readline.get_completer()

        source.setup_completer(
            ["upload"],
            blocked_names=["custom_blocked.txt"],
            blocked_extensions=[],
        )
        completer = readline.get_completer()
        assert completer is not None

        monkeypatch.setattr(readline, "get_line_buffer", lambda: "upload ")

        assert completer("", 0) == "bytecode.pyc"
        assert completer("", 1) == "keep.txt"
        assert completer("", 2) is None

    def test_terminal_input_source_complete_asset__skips_blocked_names_and_extensions(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Asset module completion filters out blocked cache directories and bytecode files."""

        assets_dir = tmp_path / "assets"
        modules_dir = assets_dir / "modules"
        modules_dir.mkdir(parents=True)
        (modules_dir / "discovery.py").write_bytes(b"")
        (modules_dir / "discovery.pyc").write_bytes(b"")
        (modules_dir / "__pycache__").mkdir()

        source = presentation.TerminalInputSource()
        completer = _get_configured_completer(source, ["load"], assets_dir=assets_dir)

        monkeypatch.setattr(readline, "get_line_buffer", lambda: "load ")

        assert completer("", 0) == "discovery.py"
        assert completer("", 1) is None
