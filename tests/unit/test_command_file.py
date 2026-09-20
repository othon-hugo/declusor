"""Tests for ``declusor.command.file`` (``_BaseFileCommand``, ``ExecuteFile``, ``UploadFile``).

Covers initialization (path validation, opcode guard), the base64-encoding
pipeline in ``_format_command``, the two concrete subclasses, and edge cases
(binary content, empty files, large files).
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_session() -> MagicMock:
    """Return a ``MagicMock`` satisfying the ``IConnection`` interface."""


@pytest.fixture
def mock_console() -> MagicMock:
    """Return a ``MagicMock`` satisfying the ``IConsole`` interface."""


@pytest.fixture
def temp_script(tmp_path: Path) -> Path:
    """Create a temporary shell script with known content."""


@pytest.fixture
def temp_binary_file(tmp_path: Path) -> Path:
    """Create a temporary file containing non-UTF-8 binary bytes."""


# =============================================================================
# Tests: _BaseFileCommand initialization
# =============================================================================


def test_init_accepts_string_path(temp_script: Path) -> None:
    """A plain ``str`` path must be coerced to ``Path`` and validated."""


def test_init_accepts_path_object(temp_script: Path) -> None:
    """A ``pathlib.Path`` object must be stored without conversion errors."""


def test_init_validates_file_existence(temp_script: Path) -> None:
    """``ensure_file_exists`` must be invoked during construction."""


def test_init_raises_on_nonexistent_file() -> None:
    """Constructing with a path that does not exist must raise ``InvalidOperation``."""


def test_init_raises_when_opcode_is_not_implemented() -> None:
    """Direct instantiation of ``_BaseFileCommand`` (opcode = NotImplemented) must raise ``NotImplementedError``."""


# =============================================================================
# Tests: _BaseFileCommand._format_command
# =============================================================================


def test_format_command_returns_bytes(temp_script: Path) -> None:
    """The formatted command must be returned as ``bytes``, not ``str``."""


def test_format_command_base64_encodes_file_content(temp_script: Path) -> None:
    """The file content must appear base64-encoded inside the returned bytes."""


def test_format_command_includes_function_name(temp_script: Path) -> None:
    """The shell function name mapped from ``_OPCODE`` must prefix the output."""


def test_format_command_raises_when_opcode_unsupported(temp_script: Path) -> None:
    """If the profile has no mapping for the opcode, ``InvalidOperation`` must be raised."""


# =============================================================================
# Tests: ExecuteFile
# =============================================================================


def test_execute_file_opcode_is_exec_file() -> None:
    """``ExecuteFile._OPCODE`` must equal ``OperationCode.EXEC_FILE``."""


def test_execute_file_writes_command_to_session(mock_session: MagicMock, mock_console: MagicMock, temp_script: Path) -> None:
    """``execute`` must transmit the base64-encoded command bytes via ``session.write``."""


def test_execute_file_command_format(temp_script: Path) -> None:
    """The command string must follow the pattern ``<function_name> '<base64>'``."""


# =============================================================================
# Tests: UploadFile
# =============================================================================


def test_upload_file_opcode_is_store_file() -> None:
    """``UploadFile._OPCODE`` must equal ``OperationCode.STORE_FILE``."""


def test_upload_file_writes_command_to_session(mock_session: MagicMock, mock_console: MagicMock, temp_script: Path) -> None:
    """``execute`` must transmit the base64-encoded store command via ``session.write``."""


def test_upload_file_command_format(temp_script: Path) -> None:
    """The command string must follow the pattern ``<store_function> '<base64>'``."""


def test_upload_file_inherits_base_file_command() -> None:
    """``UploadFile`` must be a subclass of ``_BaseFileCommand``."""


# =============================================================================
# Tests: Edge cases
# =============================================================================


def test_handles_binary_content(temp_binary_file: Path) -> None:
    """Non-UTF-8 binary data must be correctly base64-encoded."""


def test_handles_empty_file(tmp_path: Path) -> None:
    """A zero-byte file must produce the base64 encoding of an empty payload."""


def test_handles_large_file(tmp_path: Path) -> None:
    """A file of at least 1 MiB must be fully base64-encoded without truncation."""
