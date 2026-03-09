"""Tests for the ``declusor.cli.console`` module."""

import os
import sys
from io import BytesIO, StringIO
from pathlib import Path

import pytest

from declusor import mock
from declusor.cli import console

# =============================================================================
# Dummies/Mocks
# =============================================================================

class DummyPath:
    """Null-implementation path structure exposing state parameters safely."""
    def __init__(self, target_str: str, exists: bool = True) -> None:
        self._target_str = target_str
        self._exists = exists

    def exists(self) -> bool: return self._exists
    def __str__(self) -> str: return self._target_str

class DummyStdout:
    """Null-implementation stdout structure capturing buffer content streams safely."""
    def __init__(self) -> None:
        self.buffer = BytesIO()

# =============================================================================
# Tests: Console.setup_completer (Tab Completion)
# =============================================================================

def test_console_setup_completer_injects_readline_callbacks() -> None:
    """Setting up the completer must attach standard behavior mappings directly to the readline utility."""

    # ARRANGE: Mock replacement instance
    mock_rl = mock.MockReadline()
    term = console.Console()

    original_readline = console.readline
    console.readline = mock_rl  # type: ignore

    try:
        # ACT: Initialize framework behavior
        term.setup_completer(["execute", "upload", "exit"])

        # ASSERT: Hook function installed successfully
        assert mock_rl.completer is not None
    finally:
        console.readline = original_readline


# =============================================================================
# Tests: Console.enable_history (History management)
# =============================================================================

def test_console_enable_history_reads_existing_file() -> None:
    """Enabling history must attempt to read previous input records natively if the file exists."""

    # ARRANGE: Setup temporary storage validation using stub injection
    mock_rl = mock.MockReadline()
    term = console.Console()

    original_readline = console.readline
    console.readline = mock_rl  # type: ignore

    try:
        # ACT & ASSERT: Target path requested natively from RL wrapper API
        term.enable_history(DummyPath("existing_hist"))  # type: ignore
        assert "existing_hist" in mock_rl.history_read
    finally:
        console.readline = original_readline

def test_console_enable_history_safely_ignores_missing_file() -> None:
    """Enabling history must silently trap FileNotFoundError if readline fails to process the existing file constraint."""

    # ARRANGE: Force failure
    mock_rl = mock.MockReadline()
    term = console.Console()

    original_readline = console.readline
    console.readline = mock_rl  # type: ignore

    try:
        # ACT & ASSERT: Should transparently silence missing file execution contexts
        term.enable_history(DummyPath("missing_hist"))  # type: ignore
        assert len(mock_rl.history_read) == 0
    finally:
        console.readline = original_readline

def test_console_save_history_triggers_write() -> None:
    """Saving history must dispatch a request to readline pointing correctly to the specified persistence target."""

    # ARRANGE: Trigger explicit system exit behavior wrapper tracking
    mock_rl = mock.MockReadline()
    term = console.Console()
    term._history_file = "explicit_hist"  # type: ignore

    original_readline = console.readline
    console.readline = mock_rl  # type: ignore

    try:
        # ACT & ASSERT: Persistence mapping called explicitly without exception output
        term._save_history()
        assert "explicit_hist" in mock_rl.history_written
    finally:
        console.readline = original_readline


# =============================================================================
# Tests: Console I/O methods (Message printing)
# =============================================================================

def test_console_write_message_outputs_to_stdout() -> None:
    """Writing a plain message must emit identical contents trailed by a newline to stdout."""

    # ARRANGE: Influx capture IO mock object
    term = console.Console()
    fake_stdout = StringIO()

    original_stdout = sys.stdout
    sys.stdout = fake_stdout

    try:
        # ACT: Execute IO wrapper logic
        term.write_message("msg")

        # ASSERT: Stream captures fully matched data
        assert fake_stdout.getvalue() == "msg\n"
    finally:
        sys.stdout = original_stdout

def test_console_write_binary_data_outputs_to_stdout_buffer() -> None:
    """Writing raw binary data must bypass unicode processing flushing verbatim values down to stdout.buffer."""

    # ARRANGE: Construct mock structure encompassing binary stream requirements
    term = console.Console()

    fake_stdout = DummyStdout()

    original_stdout = sys.stdout
    sys.stdout = fake_stdout  # type: ignore

    try:
        # ACT: Write byte sequence
        term.write_binary_data(b"binary_payload")

        # ASSERT: Check unencrypted internal extraction values natively
        assert fake_stdout.buffer.getvalue() == b"binary_payload"
    finally:
        sys.stdout = original_stdout

def test_console_write_error_message_outputs_to_stderr() -> None:
    """Writing an error message must prefix string output with standard identifiers directly to stderr."""

    # ARRANGE: stderr string extraction capture frame
    term = console.Console()
    fake_stderr = StringIO()

    original_stderr = sys.stderr
    sys.stderr = fake_stderr

    try:
        # ACT: Issue custom failure
        term.write_error_message("failure data")

        # ASSERT: Validated console prefix spacing configuration
        assert fake_stderr.getvalue() == "error: failure data\n"
    finally:
        sys.stderr = original_stderr

def test_console_write_warning_message_outputs_to_stderr() -> None:
    """Writing a warning message must emit prefixed notifications on standard error."""

    # ARRANGE: Hook into stderr for data gathering
    term = console.Console()
    fake_stderr = StringIO()

    original_stderr = sys.stderr
    sys.stderr = fake_stderr

    try:
        # ACT: Provide generic warning
        term.write_warning_message("watch out")

        # ASSERT: Validate output text and newline injection mapping
        assert fake_stderr.getvalue() == "warning: watch out\n"
    finally:
        sys.stderr = original_stderr
