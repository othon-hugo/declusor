from os import urandom
from pathlib import Path

import pytest

from declusor import mock


# =============================================================================
# Fixtures -- Mock objects
# =============================================================================


@pytest.fixture
def mock_profile() -> mock.MockConnectionProfile:
    """Return a ``MockConnectionProfile`` satisfying the ``IConnectionProfile`` interface."""

    return mock.MockConnectionProfile()


@pytest.fixture
def mock_connection(mock_profile: mock.MockConnectionProfile) -> mock.MockConnection:
    """Return a ``MockConnection`` satisfying the ``IConnection`` interface."""

    return mock.MockConnection(mock_profile)


@pytest.fixture
def mock_console() -> mock.MockConsole:
    """Return a ``MockConsole`` satisfying the ``IConsole`` interface."""

    return mock.MockConsole()


@pytest.fixture
def mock_router() -> mock.MockRouter:
    """Return a ``MockRouter`` satisfying the ``IRouter`` interface."""

    return mock.MockRouter()


@pytest.fixture
def mock_socket() -> mock.MockSocket:
    """Return a ``MockSocket`` mimicking a ``socket.socket``."""

    return mock.MockSocket()


@pytest.fixture
def mock_readline() -> mock.MockReadline:
    """Return a mocked readline instance."""

    return mock.MockReadline()


# =============================================================================
# Fixtures -- Temporary files
# =============================================================================


TEMP_SCRIPT_CONTENT = "TEMP_SCRIPT_CONTENT"


@pytest.fixture
def temp_script_file(tmp_path: Path) -> Path:
    """Create a temporary shell script with known content."""

    script_filepath = tmp_path / "script.sh"
    script_filepath.touch()

    with script_filepath.open("w") as f:
        f.write(TEMP_SCRIPT_CONTENT)

    return script_filepath


TEMP_BINARY_FILE_CONTENT = urandom(128)


@pytest.fixture
def temp_binary_file(tmp_path: Path) -> Path:
    """Create a temporary file containing non-UTF-8 binary bytes."""

    binary_filepath = tmp_path / "binary.bin"
    binary_filepath.touch()

    with binary_filepath.open("wb") as f:
        f.write(TEMP_BINARY_FILE_CONTENT)

    return binary_filepath


TEMP_PAYLOAD_CONTENT = "echo 'hello world'\n"


@pytest.fixture
def temp_payload(tmp_path: Path) -> Path:
    """Create a temporary payload file with known content."""

    payload_filepath = tmp_path / "payload.sh"

    with payload_filepath.open("w") as f:
        f.write(TEMP_PAYLOAD_CONTENT)

    return payload_filepath


@pytest.fixture
def temp_script(tmp_path: Path) -> Path:
    """Create a temporary script file for controller execute tests."""

    script_filepath = tmp_path / "execute_script.sh"

    with script_filepath.open("w") as f:
        f.write(TEMP_SCRIPT_CONTENT)

    return script_filepath


@pytest.fixture
def temp_file(tmp_path: Path) -> Path:
    """Create a temporary file with known content."""

    filepath = tmp_path / "testfile.txt"

    with filepath.open("w") as f:
        f.write("file content for testing")

    return filepath


@pytest.fixture
def temp_history_file(tmp_path: Path) -> Path:
    """Create a temporary history file path."""

    return tmp_path / "history"
