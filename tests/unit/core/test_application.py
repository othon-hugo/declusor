from pathlib import Path
from unittest.mock import patch

from declusor import contract, core, presentation, testing


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

    expected_routes = {"help", "execute", "load", "shell", "upload", "command", "exit"}
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

    declusor_app = core.Application(
        router,
        view,
        plugin_manager=manager,
        session_runner=runner,
        input_source=input_source,
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

    dummy_sock = testing.DummySocket()

    with patch("declusor.util.await_connection", return_value=dummy_sock) as mock_await:
        declusor_app.run(plugin_config)

        mock_await.assert_called_once_with("127.0.0.1", 9000)
        assert dummy_conn.initialize_called
        assert "launcher_script_payload" in view.messages
        assert len(runner.run_calls) == 1

        active_session, active_router = runner.run_calls[0]
        assert active_router is router
        assert active_session.connection is dummy_conn
        assert active_session.view is view
