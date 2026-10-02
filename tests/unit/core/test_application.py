from pathlib import Path

from declusor import config, contract, core, presentation, testing


def test_application_connect_routes() -> None:
    """Verify application registers core routes on its router."""

    manager = core.PluginManager()
    router = core.Router()
    view = presentation.TerminalView()
    input_source = presentation.TerminalInputSource()
    runner = testing.DummySessionRunner()

    declusor_app = core.Application(
        router,
        view,
        plugin_manager=manager,
        session_runner=runner,
        input_source=input_source,
    )

    expected_routes = {"help", "execute", "load", "shell", "upload", "command", "code", "eval", "exit"}
    assert expected_routes.issubset(set(declusor_app._router.routes))


def test_application_register_plugin_at_runtime() -> None:
    """Verify application allows registering client plugins at runtime."""

    manager = core.PluginManager()
    router = core.Router()
    view = presentation.TerminalView()
    input_source = presentation.TerminalInputSource()
    runner = testing.DummySessionRunner()

    declusor_app = core.Application(
        router,
        view,
        plugin_manager=manager,
        session_runner=runner,
        input_source=input_source,
    )

    testing.DummyPlugin.reset()
    declusor_app.register_plugin(testing.DummyPlugin)

    assert testing.DummyPlugin.name in declusor_app.plugin_manager.names()


def test_application_run_lifecycle(tmp_path: Path) -> None:
    """Verify Application.run coordinates connection, handshake, launcher output, and session runner."""

    dummy_conn = testing.DummyConnection()
    dummy_runtime = testing.DummyPluginRuntime(
        client_script="launcher_script_payload",
        connection_to_return=dummy_conn,
    )
    testing.DummyPlugin.reset()
    testing.DummyPlugin.runtime_instance = dummy_runtime

    manager = core.PluginManager()
    router = core.Router()
    view = testing.DummyView()
    input_source = testing.DummyInputSource()
    runner = testing.DummySessionRunner()

    manager.register(testing.DummyPlugin)

    listener = testing.MemoryTransportListener()
    _ = listener.create_client()

    declusor_app = core.Application(
        router,
        view,
        plugin_manager=manager,
        session_runner=runner,
        input_source=input_source,
        listener_factory=lambda host, port: listener,
    )

    fs = contract.PluginFilesystem.from_root(tmp_path)
    plugin_config = contract.PluginConfig(
        kind=testing.DummyPlugin.name,
        host="127.0.0.1",
        port=9000,
        options=contract.ParsedArguments(),
        options_type=contract.ParsedArguments,
        filesystem=fs,
    )

    declusor_app.run(plugin_config)

    assert dummy_conn.initialize_called
    assert "launcher_script_payload" in view.messages
    assert len(runner.run_calls) == 1

    active_session, active_router = runner.run_calls[0]
    assert active_router is router
    assert active_session.connection is dummy_conn
    assert active_session.view is view


def test_application_run_silent_launcher_output(tmp_path: Path) -> None:
    """Verify Application.run suppresses launcher message when launcher_output_mode is SILENT."""

    dummy_conn = testing.DummyConnection()
    dummy_runtime = testing.DummyPluginRuntime(
        client_script="secret_launcher",
        connection_to_return=dummy_conn,
    )
    testing.DummyPlugin.reset()
    testing.DummyPlugin.runtime_instance = dummy_runtime

    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    router = core.Router()
    view = testing.DummyView()
    runner = testing.DummySessionRunner()
    listener = testing.MemoryTransportListener()
    _ = listener.create_client()

    declusor_app = core.Application(
        router,
        view,
        plugin_manager=manager,
        session_runner=runner,
        listener_factory=lambda host, port: listener,
    )

    fs = contract.PluginFilesystem.from_root(tmp_path)
    plugin_config = contract.PluginConfig(
        kind=testing.DummyPlugin.name,
        host="127.0.0.1",
        port=9000,
        options=contract.ParsedArguments(),
        options_type=contract.ParsedArguments,
        filesystem=fs,
        launcher_output_mode=config.LauncherOutputMode.SILENT,
    )

    declusor_app.run(plugin_config)

    assert len(view.messages) == 0


def test_application_run_file_launcher_output(tmp_path: Path) -> None:
    """Verify Application.run writes launcher to file when launcher_output_mode is FILE."""

    dummy_conn = testing.DummyConnection()
    dummy_runtime = testing.DummyPluginRuntime(
        client_script="file_launcher_payload",
        connection_to_return=dummy_conn,
    )
    testing.DummyPlugin.reset()
    testing.DummyPlugin.runtime_instance = dummy_runtime

    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    router = core.Router()
    view = testing.DummyView()
    runner = testing.DummySessionRunner()
    listener = testing.MemoryTransportListener()
    _ = listener.create_client()

    declusor_app = core.Application(
        router,
        view,
        plugin_manager=manager,
        session_runner=runner,
        listener_factory=lambda host, port: listener,
    )

    output_file = tmp_path / "out" / "launcher.sh"
    fs = contract.PluginFilesystem.from_root(tmp_path)
    plugin_config = contract.PluginConfig(
        kind=testing.DummyPlugin.name,
        host="127.0.0.1",
        port=9000,
        options=contract.ParsedArguments(),
        options_type=contract.ParsedArguments,
        filesystem=fs,
        launcher_output_mode=config.LauncherOutputMode.FILE,
        launcher_output_path=output_file,
    )

    declusor_app.run(plugin_config)

    assert output_file.is_file()
    assert output_file.read_text(encoding="utf-8") == "file_launcher_payload"
    assert len(view.messages) == 0


def test_application_run_wrapped_launcher_output(tmp_path: Path) -> None:
    """Verify Application.run wraps launcher with launcher_wrapper template."""

    dummy_conn = testing.DummyConnection()
    dummy_runtime = testing.DummyPluginRuntime(
        client_script="raw_script",
        connection_to_return=dummy_conn,
    )
    testing.DummyPlugin.reset()
    testing.DummyPlugin.runtime_instance = dummy_runtime

    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    router = core.Router()
    view = testing.DummyView()
    runner = testing.DummySessionRunner()
    listener = testing.MemoryTransportListener()
    _ = listener.create_client()

    declusor_app = core.Application(
        router,
        view,
        plugin_manager=manager,
        session_runner=runner,
        listener_factory=lambda host, port: listener,
    )

    fs = contract.PluginFilesystem.from_root(tmp_path)
    plugin_config = contract.PluginConfig(
        kind=testing.DummyPlugin.name,
        host="127.0.0.1",
        port=9000,
        options=contract.ParsedArguments(),
        options_type=contract.ParsedArguments,
        filesystem=fs,
        launcher_wrapper="python3 -c '$DECLUSOR_SCRIPT'",
    )

    declusor_app.run(plugin_config)

    assert "python3 -c 'raw_script'" in view.messages


def test_application_run_wraps_transport_with_single_layer(tmp_path: Path) -> None:
    """Verify Application.run wraps the accepted transport with configured transport layers."""

    dummy_conn = testing.DummyConnection()
    dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
    testing.DummyPlugin.reset()
    testing.DummyPlugin.runtime_instance = dummy_runtime

    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    router = core.Router()
    view = testing.DummyView()
    runner = testing.DummySessionRunner()
    listener = testing.MemoryTransportListener()
    _ = listener.create_client()

    declusor_app = core.Application(
        router,
        view,
        plugin_manager=manager,
        session_runner=runner,
        listener_factory=lambda host, port: listener,
    )

    fs = contract.PluginFilesystem.from_root(tmp_path)
    plugin_config = contract.PluginConfig(
        kind=testing.DummyPlugin.name,
        host="127.0.0.1",
        port=9000,
        options=contract.ParsedArguments(),
        options_type=contract.ParsedArguments,
        filesystem=fs,
        transport_layers=("xor",),
    )

    declusor_app.run(plugin_config)

    assert len(dummy_runtime.received_transports) == 1
    received = dummy_runtime.received_transports[0]
    assert isinstance(received, contract.ITransportLayer)
    # The inner wrapped transport should be the accepted memory transport from the listener
    assert isinstance(received.underlying, testing.MemoryTransport)


def test_application_run_wraps_transport_with_stacked_layers(tmp_path: Path) -> None:
    """Verify Application.run stacks multiple transport layers in order."""

    dummy_conn = testing.DummyConnection()
    dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
    testing.DummyPlugin.reset()
    testing.DummyPlugin.runtime_instance = dummy_runtime

    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    router = core.Router()
    view = testing.DummyView()
    runner = testing.DummySessionRunner()
    listener = testing.MemoryTransportListener()
    _ = listener.create_client()

    declusor_app = core.Application(
        router,
        view,
        plugin_manager=manager,
        session_runner=runner,
        listener_factory=lambda host, port: listener,
    )

    fs = contract.PluginFilesystem.from_root(tmp_path)
    plugin_config = contract.PluginConfig(
        kind=testing.DummyPlugin.name,
        host="127.0.0.1",
        port=9000,
        options=contract.ParsedArguments(),
        options_type=contract.ParsedArguments,
        filesystem=fs,
        transport_layers=("xor", "xor"),
    )

    declusor_app.run(plugin_config)

    assert len(dummy_runtime.received_transports) == 1
    outer = dummy_runtime.received_transports[0]
    assert isinstance(outer, contract.ITransportLayer)
    inner = outer.underlying
    assert isinstance(inner, contract.ITransportLayer)
    assert isinstance(inner.underlying, testing.MemoryTransport)
