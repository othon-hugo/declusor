"""Tests for the ``declusor.connection.shell_socket`` module."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from declusor import config, mock
from declusor.connection import shell_socket



# =============================================================================
# Tests: ShellSocketProfile
# =============================================================================

def test_shellsocketprofile_post_init_validates_buffer_size() -> None:
    """Initializing a profile with a negative or zero buffer size must raise a ``ConnectionFailure``."""
    # ARRANGE & ACT & ASSERT: Attempt construction with invalid constraint logic mapping
    with pytest.raises(config.ConnectionFailure, match="buffer_size must be > 0"):
        shell_socket.ShellSocketProfile(
            name="test",
            client_path=Path("dummy"),
            ack_server_raw=b"S",
            ack_client_raw=b"C",
            allowed_payload_extensions=(),
            allowed_library_extensions=(),
            _default_buffer_size=0
        )

def test_shellsocketprofile_post_init_validates_timeout() -> None:
    """Initializing a profile with a negative timeout must raise a ``ConnectionFailure``."""
    with pytest.raises(config.ConnectionFailure, match="connection_timeout must be >= 0 or None"):
        shell_socket.ShellSocketProfile(
            name="test",
            client_path=Path("dummy"),
            ack_server_raw=b"S",
            ack_client_raw=b"C",
            allowed_payload_extensions=(),
            allowed_library_extensions=(),
            _default_timeout=-1.0
        )

def test_shellsocketprofile_properties_return_values() -> None:
    """Properties must expose exactly the configuration supplied at instance construction."""
    profile = shell_socket.ShellSocketProfile(
        name="test",
        client_path=Path("dummy"),
        ack_server_raw=b"S",
        ack_client_raw=b"C",
        allowed_payload_extensions=(),
        allowed_library_extensions=(),
        _default_buffer_size=1024,
        _default_timeout=5.0
    )

    assert profile.default_buffer_size == 1024
    assert profile.default_timeout == 5.0

def test_shellsocketprofile_render_operation_command_success() -> None:
    """Rendering a supported operation code must format arguments via shlex and append them."""
    profile = shell_socket.ShellSocketProfile(
        name="test",
        client_path=Path("dummy"),
        ack_server_raw=b"S",
        ack_client_raw=b"C",
        allowed_payload_extensions=(),
        allowed_library_extensions=(),
        _supported_functions={config.OperationCode.STORE_FILE: "store"}
    )

    cmd = profile.render_operation_command(config.OperationCode.STORE_FILE, "arg1", "arg space")

    assert cmd == "store arg1 'arg space'"

def test_shellsocketprofile_render_operation_command_returns_none_if_unsupported() -> None:
    """Rendering an unsupported operation code must return None."""
    profile = shell_socket.ShellSocketProfile(
        name="test",
        client_path=Path("dummy"),
        ack_server_raw=b"S",
        ack_client_raw=b"C",
        allowed_payload_extensions=(),
        allowed_library_extensions=(),
        _supported_functions={}
    )

    cmd = profile.render_operation_command(config.OperationCode.STORE_FILE, "arg1")

    assert cmd is None

def test_shellsocketprofile_iter_library_paths_yields_valid_files() -> None:
    """Iterating library directories must yield correctly extending files exclusively."""
    with TemporaryDirectory() as td:
        root = Path(td)
        (root / "valid.sh").touch()
        (root / "invalid.txt").touch()
        (root / "dir.sh").mkdir()

        profile = shell_socket.ShellSocketProfile(
            name="test",
            client_path=Path("dummy"),
            ack_server_raw=b"S",
            ack_client_raw=b"C",
            allowed_payload_extensions=(".sh",),
            allowed_library_extensions=(".sh",),
            _library_root_directory=root
        )

        paths = list(profile.iter_library_paths())

        assert len(paths) == 1
        assert paths[0].name == "valid.sh"

def test_shellsocketprofile_resolve_module_path_succeeds() -> None:
    """Resolving a safe path within constraints must yield resolving Path structures."""
    with TemporaryDirectory() as td:
        root = Path(td)
        profile = shell_socket.ShellSocketProfile(
            name="test",
            client_path=Path("dummy"),
            ack_server_raw=b"S",
            ack_client_raw=b"C",
            allowed_payload_extensions=(),
            allowed_library_extensions=(),
            _module_root_directory=root
        )

        resolved = profile.resolve_module_path("module.py")
        assert root in resolved.parents

def test_shellsocketprofile_resolve_module_path_raises_on_traversal() -> None:
    """Resolving an unsafe traversal path must throw config.InvalidOperation exceptions aggressively."""
    with TemporaryDirectory() as td:
        root = Path(td)
        profile = shell_socket.ShellSocketProfile(
            name="test",
            client_path=Path("dummy"),
            ack_server_raw=b"S",
            ack_client_raw=b"C",
            allowed_payload_extensions=(),
            allowed_library_extensions=(),
            _module_root_directory=root
        )

        with pytest.raises(config.InvalidOperation, match="is not relative to the module root directory"):
            profile.resolve_module_path("../outside.py")

def test_shellsocketprofile_render_client_script_substitutes() -> None:
    """Rendering script correctly replaces standard variable tags via template structure format overrides."""
    profile = shell_socket.ShellSocketProfile(
        name="test",
        client_path=mock.MockPath(read_data="CONNECT $HOST $PORT ACK $ACKNOWLEDGE"),  # type: ignore
        ack_server_raw=b"S",
        ack_client_raw=b"ACK",
        allowed_payload_extensions=(),
        allowed_library_extensions=()
    )

    script = profile.render_client_script("127.0.0.1", 80)
    assert script == "CONNECT 127.0.0.1 80 ACK \\x41\\x43\\x4b"

def test_shellsocketprofile_render_client_script_raises_on_oserror() -> None:
    """Failure to read client target templates should bubble mapping appropriately via ConnectionFailure hooks."""
    profile = shell_socket.ShellSocketProfile(
        name="test",
        client_path=mock.MockPath(error=OSError("denied")),  # type: ignore
        ack_server_raw=b"S",
        ack_client_raw=b"ACK",
        allowed_payload_extensions=(),
        allowed_library_extensions=()
    )

    with pytest.raises(config.ConnectionFailure, match="Failed to read client script"):
        profile.render_client_script("127.0.0.1", 80)


# =============================================================================
# Tests: ShellSocketConnection
# =============================================================================

def test_shellsocketconnection_initializes_and_renders_script() -> None:
    """Initializing a connection maps peer attributes and timeouts prior to client logic staging."""
    profile = shell_socket.ShellSocketProfile(
        name="test",
        client_path=mock.MockPath(read_data="HELLO $HOST"),  # type: ignore
        ack_server_raw=b"S",
        ack_client_raw=b"C",
        allowed_payload_extensions=(),
        allowed_library_extensions=(),
        _default_timeout=1.5
    )
    mock_socket = mock.MockSocket()
    mock_socket.peer_name = ("1.2.3.4", 99)

    conn = shell_socket.ShellSocketConnection(mock_socket, profile)  # type: ignore

    assert mock_socket.timeout == 1.5
    assert conn.client_script == "HELLO 1.2.3.4"
    assert conn.client is profile
    assert conn.timeout == 1.5

def test_shellsocketconnection_timeout_setter() -> None:
    """Updating timeout via property safely cascades configuration into underlying OS wrapper bounds."""
    profile = shell_socket.ShellSocketProfile(
        name="test",
        client_path=mock.MockPath(read_data=""),  # type: ignore
        ack_server_raw=b"S",
        ack_client_raw=b"C",
        allowed_payload_extensions=(),
        allowed_library_extensions=(),
        _default_timeout=None
    )
    mock_socket = mock.MockSocket()
    mock_socket.peer_name = ("1.2.3.4", 99)
    conn = shell_socket.ShellSocketConnection(mock_socket, profile)  # type: ignore

    conn.timeout = 2.0
    assert mock_socket.timeout == 2.0
    assert conn.timeout == 2.0

def test_shellsocketconnection_initialize_handshake_succeeds() -> None:
    """Handshakes strictly check return sentinel payloads for precise byte validation logic matching config structure parameters."""
    profile = shell_socket.ShellSocketProfile(
        name="test",
        client_path=mock.MockPath(read_data=""),  # type: ignore
        ack_server_raw=b"S",
        ack_client_raw=b"ACK",
        allowed_payload_extensions=(),
        allowed_library_extensions=()
    )
    mock_socket = mock.MockSocket()
    mock_socket.peer_name = ("1.2.3.4", 99)
    mock_socket.recv_data = [b"ACK"]
    conn = shell_socket.ShellSocketConnection(mock_socket, profile)  # type: ignore

    conn.initialize()
    # If no exception logic branches out sequence processing worked flawlessly

def test_shellsocketconnection_initialize_handshake_fails_on_bad_ack() -> None:
    """Validating unknown or wrong ACKs fails handshake securely terminating mapping process logic cascades."""
    profile = shell_socket.ShellSocketProfile(
        name="test",
        client_path=mock.MockPath(read_data=""),  # type: ignore
        ack_server_raw=b"S",
        ack_client_raw=b"ACK",
        allowed_payload_extensions=(),
        allowed_library_extensions=()
    )
    mock_socket = mock.MockSocket()
    mock_socket.peer_name = ("1.2.3.4", 99)
    mock_socket.recv_data = [b"BAD"]
    conn = shell_socket.ShellSocketConnection(mock_socket, profile)  # type: ignore

    with pytest.raises(config.ConnectionFailure, match="invalid client ACK during session initialization"):
        conn.initialize()

def test_shellsocketconnection_initialize_handshake_fails_on_timeout() -> None:
    """Validating IO timeouts raises failure wrapper."""
    profile = shell_socket.ShellSocketProfile(
        name="test",
        client_path=mock.MockPath(read_data=""),  # type: ignore
        ack_server_raw=b"S",
        ack_client_raw=b"ACK",
        allowed_payload_extensions=(),
        allowed_library_extensions=()
    )
    mock_socket = mock.MockSocket()
    mock_socket.peer_name = ("1.2.3.4", 99)
    mock_socket.recv_exception = TimeoutError()
    conn = shell_socket.ShellSocketConnection(mock_socket, profile)  # type: ignore

    with pytest.raises(config.ConnectionFailure, match="timeout waiting for client ACK"):
        conn.initialize()

def test_shellsocketconnection_read_yields_framed_payloads() -> None:
    """Reading chunks via socket should strip ACK padding effectively wrapping data seamlessly via frame borders correctly yielding arrays mapped to iteration constraints safely."""
    profile = shell_socket.ShellSocketProfile(
        name="test",
        client_path=mock.MockPath(read_data=""),  # type: ignore
        ack_server_raw=b"S",
        ack_client_raw=b"ACK",
        allowed_payload_extensions=(),
        allowed_library_extensions=(),
        _default_buffer_size=10
    )
    # Payload "data" joined with "ACK" and more sequence bytes
    mock_socket = mock.MockSocket()
    mock_socket.peer_name = ("1.2.3.4", 99)
    # The ACK has length 3. b"d" length = 1 (hits len(combined) < ack_len).
    mock_socket.recv_data = [b"d", b"ataR", b"EAL", b"ACK"]
    conn = shell_socket.ShellSocketConnection(mock_socket, profile)  # type: ignore

    chunks = list(conn.read())
    assert b"".join(chunks) == b"dataREAL"

def test_shellsocketconnection_read_handles_connection_reset() -> None:
    """Missing buffer return triggers reset exceptions."""
    profile = shell_socket.ShellSocketProfile(
        name="test",
        client_path=mock.MockPath(read_data=""),  # type: ignore
        ack_server_raw=b"S",
        ack_client_raw=b"ACK",
        allowed_payload_extensions=(),
        allowed_library_extensions=()
    )
    mock_socket = mock.MockSocket()
    mock_socket.peer_name = ("1.2.3.4", 99)
    mock_socket.recv_data = [b"partial", b""]
    conn = shell_socket.ShellSocketConnection(mock_socket, profile)  # type: ignore

    with pytest.raises(config.ConnectionFailure, match="Failed to read from connection: Connection closed by peer"):
        list(conn.read())

def test_shellsocketconnection_read_handles_timeout() -> None:
    """Exception timeouts wrap safely to Connection failures natively protecting internal constraints directly mapped inside abstraction bindings securely without cascading OS faults explicitly upwards unchecked mapping paths cleanly."""
    profile = shell_socket.ShellSocketProfile(
        name="test",
        client_path=mock.MockPath(read_data=""),  # type: ignore
        ack_server_raw=b"S",
        ack_client_raw=b"ACK",
        allowed_payload_extensions=(),
        allowed_library_extensions=()
    )
    mock_socket = mock.MockSocket()
    mock_socket.peer_name = ("1.2.3.4", 99)
    mock_socket.recv_exception = TimeoutError()
    conn = shell_socket.ShellSocketConnection(mock_socket, profile)  # type: ignore

    with pytest.raises(config.ConnectionFailure, match="Timeout while reading from connection"):
        list(conn.read())

def test_shellsocketconnection_write_succeeds() -> None:
    """Writing sends payload and ACK sentinel bytes exclusively mapping directly on OS interface buffers."""
    profile = shell_socket.ShellSocketProfile(
        name="test",
        client_path=mock.MockPath(read_data=""),  # type: ignore
        ack_server_raw=b"SERVERACK",
        ack_client_raw=b"ACK",
        allowed_payload_extensions=(),
        allowed_library_extensions=()
    )
    mock_socket = mock.MockSocket()
    mock_socket.peer_name = ("1.2.3.4", 99)
    conn = shell_socket.ShellSocketConnection(mock_socket, profile)  # type: ignore

    conn.write(b"payload")

    # Assert sequence checks out successfully
    assert mock_socket.sent_data == [b"payload", b"SERVERACK"]

def test_shellsocketconnection_write_handles_errors() -> None:
    """Socket level timeouts translate transparently raising exceptions checking mapping correctly securely guarding against raw native propagation logic leaks."""
    profile = shell_socket.ShellSocketProfile(
        name="test",
        client_path=mock.MockPath(read_data=""),  # type: ignore
        ack_server_raw=b"SERVERACK",
        ack_client_raw=b"ACK",
        allowed_payload_extensions=(),
        allowed_library_extensions=()
    )

    mock_socket = mock.MockSocket()
    mock_socket.peer_name = ("1.2.3.4", 99)
    conn = shell_socket.ShellSocketConnection(mock_socket, profile)  # type: ignore

    mock_socket.send_exception = TimeoutError()
    with pytest.raises(config.ConnectionFailure, match="Timeout while writing"):
        conn.write(b"data")

    mock_socket.send_exception = OSError("broken pipe")
    with pytest.raises(config.ConnectionFailure, match="Failed to write to connection: broken pipe"):
        conn.write(b"data")

def test_shellsocketconnection_close_terminates_socket() -> None:
    """Close triggers raw protocol hook mapped underneath wrapping effectively resolving constraints cleanly releasing buffer constraints system logic structures completely destroying bindings successfully passing parameters mapped exclusively over underlying instances tightly safely."""
    profile = shell_socket.ShellSocketProfile(
        name="test",
        client_path=mock.MockPath(read_data=""),  # type: ignore
        ack_server_raw=b"S",
        ack_client_raw=b"ACK",
        allowed_payload_extensions=(),
        allowed_library_extensions=()
    )
    mock_socket = mock.MockSocket()
    mock_socket.peer_name = ("1.2.3.4", 99)
    conn = shell_socket.ShellSocketConnection(mock_socket, profile)  # type: ignore

    conn.close()
    assert mock_socket.closed is True

def test_shellsocketconnection_load_payload_raises_on_oserror() -> None:
    """Payload resolution failing file IO mapping handles exception logic throwing custom bindings seamlessly integrating correctly."""
    profile = shell_socket.ShellSocketProfile(
        name="test",
        client_path=mock.MockPath(read_data=""),  # type: ignore
        ack_server_raw=b"S",
        ack_client_raw=b"ACK",
        allowed_payload_extensions=(),
        allowed_library_extensions=()
    )
    mock_socket = mock.MockSocket()
    mock_socket.peer_name = ("1.2.3.4", 99)
    conn = shell_socket.ShellSocketConnection(mock_socket, profile)  # type: ignore

    # Simulate valid resolution path to mock yielding an IO error upon reads handling check
    class TrappingProfile(shell_socket.ShellSocketProfile):
        def resolve_module_path(self, m):
            return mock.MockPath(error=OSError("permissions denied"))  # type: ignore

    conn._profile = TrappingProfile(name="", client_path=Path(""), ack_server_raw=b"", ack_client_raw=b"", allowed_payload_extensions=(), allowed_library_extensions=())

    with pytest.raises(config.ConnectionFailure, match="Failed to read payload script"):
        conn._load_payload("dummy.sh")

def test_shellsocketconnection_load_library_success() -> None:
    """Loading libraries must append files configured sequentially mapping effectively mapping."""
    with TemporaryDirectory() as td:
        root = Path(td)
        (root / "valid.sh").write_text("echo valid")

        profile = shell_socket.ShellSocketProfile(
            name="test",
            client_path=mock.MockPath(read_data=""),  # type: ignore
            ack_server_raw=b"S",
            ack_client_raw=b"C",
            allowed_payload_extensions=(".sh",),
            allowed_library_extensions=(".sh",),
            _library_root_directory=root
        )
        mock_socket = mock.MockSocket()
        mock_socket.peer_name = ("1.2.3.4", 99)
        conn = shell_socket.ShellSocketConnection(mock_socket, profile)  # type: ignore

        libs = conn._load_library()
        assert libs == b"echo valid"

def test_shellsocketconnection_load_payload_success() -> None:
    """Loading payloads mapping correctly mapped OS parameters explicitly securely directly yields payloads correctly."""
    with TemporaryDirectory() as td:
        root = Path(td)
        (root / "payload.sh").write_text("echo payload")

        profile = shell_socket.ShellSocketProfile(
            name="test",
            client_path=mock.MockPath(read_data=""),  # type: ignore
            ack_server_raw=b"S",
            ack_client_raw=b"C",
            allowed_payload_extensions=(".sh",),
            allowed_library_extensions=(".sh",),
            _module_root_directory=root
        )
        mock_socket = mock.MockSocket()
        mock_socket.peer_name = ("1.2.3.4", 99)
        conn = shell_socket.ShellSocketConnection(mock_socket, profile)  # type: ignore

        payload = conn._load_payload("payload.sh")
        assert payload == b"echo payload"
