from argparse import Namespace
from socket import socket
from typing import cast

import pytest

from declusor import config, contract, testing, util


def test_dummy_view_write_and_capture() -> None:
    """DummyView captures messages, errors, warnings, info, success, and binary data."""

    view = testing.DummyView()
    view.write_message("msg")
    err = ValueError("err")
    view.write_error(err)
    view.write_warning("warn")
    view.write_info("info")
    view.write_success("success")
    view.write_binary_data(b"data")

    assert view.messages == ["msg"]
    assert view.errors == [err]
    assert view.warnings == ["warn"]
    assert view.info_messages == ["info"]
    assert view.success_messages == ["success"]
    assert view.binary_data == [b"data"]


def test_dummy_input_source_commands_and_prompts() -> None:
    """DummyInputSource feeds inputs, strips for read_command, keeps raw for read_raw, and records prompts."""

    input_source = testing.DummyInputSource(["cmd arg  ", "other\n"])
    assert input_source.read_command("> ") == "cmd arg"
    assert input_source.read_raw("$ ") == "other\n"
    assert input_source.read_command() == ""
    assert input_source.read_raw() == "\n"
    assert input_source.prompts == ["> ", "$ ", "", ""]

    input_source.feed_inputs("  third  ")
    assert input_source.read_command("? ") == "third"


def test_dummy_input_source_exception() -> None:
    """DummyInputSource raises input_exception when configured."""

    input_source = testing.DummyInputSource()
    input_source.input_exception = KeyboardInterrupt("ctrl-c")

    with pytest.raises(KeyboardInterrupt):
        input_source.read_command()

    # Once raised, input_exception resets
    assert input_source.read_command() == ""


def test_dummy_connection_profile() -> None:
    """DummyConnectionProfile exposes properties and formats rendered commands."""

    profile = testing.DummyConnectionProfile(name="test_p", buffer_size=1024, timeout=2.5)
    assert profile.default_buffer_size == 1024
    assert profile.default_timeout == 2.5

    default_rendered = profile.render_operation_command(config.OperationCode.EXEC_FILE, "arg1", "arg2")
    assert default_rendered == f"{config.OperationCode.EXEC_FILE.value} arg1 arg2"

    profile.set_rendered_command(config.OperationCode.STORE_FILE, "custom_store")
    assert profile.render_operation_command(config.OperationCode.STORE_FILE, "arg") == "custom_store"
    assert len(profile.render_calls) == 2


def test_dummy_connection_lifecycle_and_io() -> None:
    """DummyConnection handles initialization, framed read, write, and close."""

    conn = testing.DummyConnection(initial_state=contract.ConnectionState.CREATED)
    state: contract.ConnectionState = conn.state
    assert state == contract.ConnectionState.CREATED
    assert not conn.initialize_called

    conn.initialize()
    state = conn.state
    assert state == contract.ConnectionState.CONNECTED
    assert conn.initialize_called

    conn.write(b"outgoing")
    assert conn.written == [b"outgoing"]

    chunks = list(conn.read())
    assert chunks == [b"chunk1\n", b"chunk2\n"]

    conn.timeout = 10.0
    assert conn.timeout == 10.0

    with conn:
        assert not conn.closed
    assert conn.closed
    state = conn.state
    assert state == contract.ConnectionState.CLOSED


def test_dummy_connection_errors() -> None:
    """DummyConnection raises configured errors on initialize, read, or write."""

    conn = testing.DummyConnection()
    conn.initialize_error = config.ConnectionError("init fail")

    with pytest.raises(config.ConnectionError, match="init fail"):
        conn.initialize()

    conn.write_error = config.ConnectionError("write fail")

    with pytest.raises(config.ConnectionError, match="write fail"):
        conn.write(b"data")

    conn.read_error = config.ConnectionError("read fail")

    with pytest.raises(config.ConnectionError, match="read fail"):
        list(conn.read())

    # Invariant: closed connection rejects initialize and write
    conn.close()

    with pytest.raises(config.ConnectionError, match="Cannot initialize a closed connection"):
        conn.initialize()

    with pytest.raises(config.ConnectionError, match="Connection is not open"):
        conn.write(b"data")


def test_dummy_client_file_store() -> None:
    """DummyPluginFileStore renders scripts, returns library payloads, and tracks module loading."""

    store = testing.DummyPluginFileStore()
    rendered = store.render_client_script("10.0.0.1", 4444, b"\xaa\xbb")

    assert "10.0.0.1" in rendered
    assert "4444" in rendered
    assert "aabb" in rendered
    assert len(store.render_calls) == 1

    lib = store.load_library()
    assert lib == b"dummy_library_payload"
    assert store.load_library_calls == 1

    assert store.load_module("default_mod") == b"module_bytes:default_mod"
    store.set_module("custom_mod", b"custom_content")
    assert store.load_module("custom_mod") == b"custom_content"
    assert store.load_module_calls == ["default_mod", "custom_mod"]

    # Error simulation
    store.load_library_error = config.ConnectionError("library load fail")
    with pytest.raises(config.ConnectionError, match="library load fail"):
        store.load_library()

    store.load_module_error = config.InvalidOperation("module load fail")
    with pytest.raises(config.InvalidOperation, match="module load fail"):
        store.load_module("bad_mod")

    store.render_error = config.InvalidOperation("render fail")
    with pytest.raises(config.InvalidOperation, match="render fail"):
        store.render_client_script("1.1.1.1", 1234, b"ack")


def test_dummy_client_runtime() -> None:
    """DummyPluginRuntime exposes client script and creates dummy connections."""

    conn = testing.DummyConnection()
    runtime = testing.DummyPluginRuntime(client_script="echo test", connection_to_return=conn)

    assert isinstance(runtime.client_files, contract.IClientFileStore)
    assert runtime.client_script == "echo test"

    dummy_socket = testing.DummySocket()
    created = runtime.create_connection(cast(socket, dummy_socket))
    assert created is conn
    assert runtime.created_connections == [conn]


def test_dummy_client_plugin() -> None:
    """DummyPlugin implements the IPlugin contract with reset support."""

    testing.DummyPlugin.reset()
    assert testing.DummyPlugin.name == "dummy"

    parser = util.Parser()
    testing.DummyPlugin.configure_parser(parser)
    assert testing.DummyPlugin.configured_parsers == [parser]

    ns = contract.PluginNamespace(host="10.0.0.2", port=8000)
    assert isinstance(ns, contract.PluginArguments)
    cfg = testing.DummyPlugin.build_config(ns, None)
    assert cfg.kind == "dummy"
    assert cfg.host == "10.0.0.2"
    assert cfg.port == 8000

    # Also verify compatibility with standard argparse.Namespace
    legacy_ns = Namespace(host="10.0.0.2", port=8000, extra_val=42)
    assert isinstance(legacy_ns, contract.PluginArguments)
    from_ns = contract.PluginNamespace.from_namespace(legacy_ns)
    assert from_ns.host == "10.0.0.2"
    assert from_ns.port == 8000
    assert from_ns.extra_val == 42
    assert from_ns.get("extra_val") == 42
    assert from_ns.get("missing", "default") == "default"
    assert "extra_val" in from_ns
    assert "missing" not in from_ns
    assert "PluginNamespace(" in repr(from_ns)
    assert from_ns == contract.PluginNamespace(host="10.0.0.2", port=8000, extra_val=42)
    assert from_ns.to_dict()["extra_val"] == 42
    assert isinstance(from_ns, contract.PluginArguments)
    cfg_legacy = testing.DummyPlugin.build_config(legacy_ns, None)
    assert cfg_legacy.host == "10.0.0.2"

    testing.DummyPlugin.validate(cfg)

    testing.DummyPlugin.validation_error = config.ParserError("bad config")

    with pytest.raises(config.ParserError, match="bad config"):
        testing.DummyPlugin.validate(cfg)

    runtime = testing.DummyPlugin.build_runtime(cfg)
    assert isinstance(runtime, contract.IPluginRuntime)

    testing.DummyPlugin.reset()
    assert len(testing.DummyPlugin.configured_parsers) == 0
    assert testing.DummyPlugin.validation_error is None


def test_dummy_router() -> None:
    """DummyRouter connects routes, dispatches, handles usage, and raises RouterError on unknown."""

    router = testing.DummyRouter()

    def sample_controller(
        session: contract.SessionContext,
        req: contract.ControllerRequest,
    ) -> contract.ControllerResult:
        """Sample usage line.
        Extended explanation.
        """

        return contract.ControllerResult()

    router.connect("sample", sample_controller)
    assert "sample" in router.routes
    assert router.locate("sample") is sample_controller
    assert router.locate_calls == ["sample"]
    assert router.get_route_usage("sample") == "Sample usage line."

    router.set_route_usage("sample", "Overridden usage")
    assert router.get_route_usage("sample") == "Overridden usage"

    with pytest.raises(ValueError, match="route already exists"):
        router.connect("sample", sample_controller)

    with pytest.raises(config.RouterError):
        router.locate("nonexistent")


def test_dummy_socket() -> None:
    """DummySocket simulates network I/O, byte buffers, peer names, chunks, and context manager."""

    sock = testing.DummySocket(incoming_bytes=b"hello world", peer_name=("1.2.3.4", 8080), fileno_val=99)
    assert sock.getpeername() == ("1.2.3.4", 8080)
    assert sock.fileno() == 99

    sock.settimeout(3.0)
    assert sock.timeout == 3.0
    assert sock.settimeout_calls == [3.0]

    chunk = sock.recv(5)
    assert chunk == b"hello"
    assert sock.recv(10) == b" world"
    assert sock.recv_calls == [5, 10]

    sock.feed_bytes(b"more")
    assert sock.recv(10) == b"more"

    # Discrete chunk streaming
    sock.feed_recv_chunks(b"frame1", b"frame2")
    assert sock.recv(100) == b"frame1"
    assert sock.recv(100) == b"frame2"

    sent_len = sock.send(b"sent1")
    assert sent_len == 5
    assert sock.send_calls == [b"sent1"]
    sock.sendall(b"sent2")
    assert sock.sendall_calls == [b"sent2"]
    assert sock.sent_bytes == b"sent1sent2"

    with sock:
        assert not sock.closed
    assert sock.closed
    assert sock.close_calls == 1

    # Error simulation
    sock.sendall_error = OSError("sendall fail")
    with pytest.raises(OSError, match="sendall fail"):
        sock.sendall(b"fail")

    sock.send_error = OSError("send fail")
    with pytest.raises(OSError, match="send fail"):
        sock.send(b"fail")

    sock.recv_error = TimeoutError("recv timeout")
    with pytest.raises(TimeoutError, match="recv timeout"):
        sock.recv(10)


def test_dummy_application() -> None:
    """DummyApplication records run calls, provides manager, and propagates configured errors."""

    cfg = testing.create_dummy_options()
    app = testing.DummyApplication()
    assert isinstance(app.manager, core.PluginManager)

    app.register_plugin(testing.DummyPlugin)
    assert testing.DummyPlugin.name in app.manager.names()

    app.run(cfg)
    assert app.run_calls == [cfg]

    app.run_error = config.ConnectionError("run fail")
    with pytest.raises(config.ConnectionError, match="run fail"):
        app.run(cfg)


def test_dummy_command_and_errors(test_session: contract.SessionContext) -> None:
    """DummyCommand executes sequence and propagates configured errors."""

    cmd = testing.DummyCommand()
    test_session.execute(cmd)
    assert cmd.call_sequence == ["send_request", "read_response"]

    err_cmd = testing.DummyCommand(send_request_error=config.CommandError("send failed"))
    with pytest.raises(config.CommandError, match="send failed"):
        test_session.execute(err_cmd)

    read_err_cmd = testing.DummyCommand(read_response_error=config.CommandError("read failed"))
    with pytest.raises(config.CommandError, match="read failed"):
        test_session.execute(read_err_cmd)


def test_factories() -> None:
    """create_test_session, create_dummy_plugin_config, create_dummy_controller_request produce typed objects."""

    session = testing.create_test_session()
    assert isinstance(session.connection, testing.DummyConnection)
    assert isinstance(session.view, testing.DummyView)
    assert isinstance(session.input, testing.DummyInputSource)
    assert isinstance(session.files, testing.DummyPluginFileStore)

    cfg = testing.create_dummy_plugin_config(kind="custom", host="192.168.1.1", port=1234, options={"opt": "val"})
    assert cfg.kind == "custom"
    assert cfg.host == "192.168.1.1"
    assert cfg.port == 1234
    assert cfg.options == {"opt": "val"}

    req = testing.create_dummy_controller_request("hello world")
    assert req.request_line == "hello world"
    assert isinstance(req, contract.ControllerRequest)

    args = testing.create_dummy_plugin_arguments(host="10.10.10.10", port=7777, extra_flag=True)
    assert args.host == "10.10.10.10"
    assert args.port == 7777
    assert args.extra_flag is True
    assert isinstance(args, contract.PluginArguments)


def test_dummy_session_runner(
    test_session: contract.SessionContext,
    dummy_router: testing.DummyRouter,
) -> None:
    """DummySessionRunner records invocations and raises configured error."""

    runner = testing.DummySessionRunner()
    runner.run(test_session, dummy_router)

    assert len(runner.run_calls) == 1
    assert runner.run_calls[0] == (test_session, dummy_router)

    error_runner = testing.DummySessionRunner(run_error=config.DeclusorException("runner failed"))
    with pytest.raises(config.DeclusorException, match="runner failed"):
        error_runner.run(test_session, dummy_router)

