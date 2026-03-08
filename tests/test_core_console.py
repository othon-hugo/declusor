"""Tests for ``declusor.core.console.Console``.

Covers initialization, ``read_line`` / ``read_stripped_line`` input methods,
``write_message`` / ``write_binary_data`` / ``write_error_message`` /
``write_warning_message`` output methods, readline tab-completion setup, and
history file persistence.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def console():
    """Return a fresh ``Console`` instance."""


@pytest.fixture
def mock_readline(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock the ``readline`` module for completer tests."""


@pytest.fixture
def temp_history_file(tmp_path: Path) -> Path:
    """Return a temporary history file path."""


# =============================================================================
# Tests: Console initialization
# =============================================================================


def test_init_history_file_is_none() -> None:
    """``_history_file`` must default to ``None``."""


# =============================================================================
# Tests: Console.read_line
# =============================================================================


def test_read_line_returns_user_input() -> None:
    """``read_line()`` must return the raw string typed by the user."""


def test_read_line_displays_custom_prompt() -> None:
    """``read_line(prompt=">> ")`` must display ``">> "`` before input."""


# =============================================================================
# Tests: Console.read_stripped_line
# =============================================================================


def test_read_stripped_line_removes_whitespace() -> None:
    """Leading and trailing whitespace must be stripped."""


def test_read_stripped_line_returns_empty_for_blank_input() -> None:
    """A whitespace-only input must produce an empty string."""


# =============================================================================
# Tests: Console.write_message
# =============================================================================


def test_write_message_outputs_to_stdout(capsys) -> None:
    """The message must appear on ``stdout`` followed by a newline."""


def test_write_message_appends_newline(capsys) -> None:
    """A newline must be automatically appended by ``write_message``."""


def test_write_message_flushes_stdout() -> None:
    """``stdout`` must be flushed immediately after writing."""


# =============================================================================
# Tests: Console.write_binary_data
# =============================================================================


def test_write_binary_data_outputs_bytes(capsys) -> None:
    """Raw bytes must be written to ``stdout.buffer``."""


def test_write_binary_data_no_trailing_newline() -> None:
    """No automatic newline must be appended by ``write_binary_data``."""


def test_write_binary_data_flushes_buffer() -> None:
    """``stdout.buffer`` must be flushed immediately."""


# =============================================================================
# Tests: Console.write_error_message
# =============================================================================


def test_write_error_message_outputs_to_stderr(capsys) -> None:
    """The message must appear on ``stderr`` prefixed with ``"error: "``."""


def test_write_error_message_accepts_exception_object() -> None:
    """Passing an ``Exception`` instance must include its message in the output."""


def test_write_error_message_prefix() -> None:
    """The output must always start with ``"error: "``."""


# =============================================================================
# Tests: Console.write_warning_message
# =============================================================================


def test_write_warning_message_outputs_to_stderr(capsys) -> None:
    """The message must appear on ``stderr`` prefixed with ``"warning: "``."""


def test_write_warning_message_accepts_exception_object() -> None:
    """Passing a ``RuntimeError`` instance must include its message in the output."""


# =============================================================================
# Tests: Console.setup_completer
# =============================================================================


def test_setup_completer_sets_delimiters(mock_readline: MagicMock) -> None:
    """``set_completer_delims`` must be called with the correct delimiter string."""


def test_setup_completer_registers_function(mock_readline: MagicMock) -> None:
    """``set_completer`` must be called with the internal completer callable."""


def test_setup_completer_binds_tab(mock_readline: MagicMock) -> None:
    """``parse_and_bind("tab: complete")`` must be invoked."""


def test_setup_completer_suggests_route_names() -> None:
    """Typing a partial route name and pressing TAB must suggest matching routes."""


def test_setup_completer_suggests_file_paths() -> None:
    """After a complete route name, TAB must suggest file paths."""


def test_setup_completer_handles_no_readline() -> None:
    """If ``readline`` is ``None`` (unavailable), ``setup_completer`` must return without error."""


# =============================================================================
# Tests: Console.enable_history
# =============================================================================


def test_enable_history_sets_history_file_path(temp_history_file: Path) -> None:
    """``_history_file`` must be set to the given path."""


def test_enable_history_reads_existing_file(temp_history_file: Path) -> None:
    """``read_history_file`` must be called when the file already exists."""


def test_enable_history_handles_missing_file(temp_history_file: Path) -> None:
    """A missing file must not raise (``FileNotFoundError`` is caught)."""


def test_enable_history_registers_atexit(temp_history_file: Path) -> None:
    """``atexit.register`` must be called with ``_save_history``."""


def test_save_history_writes_file(temp_history_file: Path) -> None:
    """``write_history_file`` must be called with the stored history path."""
