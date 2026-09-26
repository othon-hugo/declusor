from unittest.mock import patch

from declusor import contract, core, main, presentation, testing


def test_create_application_initializes_plugins() -> None:
    """Verify create_application loads built-in plugins into manager."""

    app = main.create_application()
    assert isinstance(app, main.Application)
    assert isinstance(app, main.TerminalApplication)
    assert app.manager is not None
    assert "shell_socket" in app.manager.names()
    assert "py_socket" in app.manager.names()
    assert isinstance(app.runner, presentation.PromptLoop)


def test_application_connect_routes() -> None:
    """Verify application registers core routes on its router."""

    manager = core.PluginManager()
    router = core.Router()
    view = presentation.TerminalView()
    input_source = presentation.TerminalInputSource()
    runner = testing.DummySessionRunner()
    app = main.Application(manager, router, view, runner, input_source)

    expected_routes = {"help", "execute", "load", "shell", "upload", "command", "exit"}
    assert expected_routes.issubset(set(app._router.routes))


def test_application_register_plugin_at_runtime() -> None:
    """Verify application allows registering client plugins at runtime."""

    manager = core.PluginManager()
    router = core.Router()
    view = presentation.TerminalView()
    input_source = presentation.TerminalInputSource()
    runner = testing.DummySessionRunner()
    app = main.Application(manager, router, view, runner, input_source)

    testing.DummyPlugin.reset()

    app.register_plugin(testing.DummyPlugin)
    assert testing.DummyPlugin.name in app.manager.names()


def test_application_runner_property_and_setter() -> None:
    """Verify Application.runner can be inspected and replaced at runtime."""

    manager = core.PluginManager()
    router = core.Router()
    view = presentation.TerminalView()
    runner1 = testing.DummySessionRunner()
    runner2 = testing.DummySessionRunner()

    app = main.Application(manager, router, view, runner1)
    assert app.runner is runner1

    app.runner = runner2
    assert app.runner is runner2


def test_application_run_lifecycle_with_no_data_paths() -> None:
    """Verify Application.run succeeds with data_paths=None without host filesystem checks."""

    dummy_conn = testing.DummyConnection()
    dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
    testing.DummyPlugin.reset()
    testing.DummyPlugin.runtime_instance = dummy_runtime

    manager = core.PluginManager()
    router = core.Router()
    view = presentation.TerminalView()
    input_source = presentation.TerminalInputSource()
    runner = testing.DummySessionRunner()

    manager.register(testing.DummyPlugin)

    app = main.Application(manager, router, view, runner, input_source)

    plugin_config = contract.PluginConfig(
        kind=testing.DummyPlugin.name,
        host="127.0.0.1",
        port=9000,
        data_paths=None,
    )

    dummy_sock = testing.DummySocket()

    with patch("declusor.util.await_connection", return_value=dummy_sock) as mock_await:
        app.run(plugin_config)

        mock_await.assert_called_once_with("127.0.0.1", 9000)
        assert dummy_conn.initialize_called

        assert len(runner.run_calls) == 1
        _, active_router = runner.run_calls[0]
        assert active_router is router
        assert not hasattr(app, "_validate_directories")


def test_application_run_with_custom_runner_override() -> None:
    """Verify passing a runner override to run() uses the override instead of default."""

    dummy_conn = testing.DummyConnection()
    dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
    testing.DummyPlugin.reset()
    testing.DummyPlugin.runtime_instance = dummy_runtime

    manager = core.PluginManager()
    router = core.Router()
    view = presentation.TerminalView()
    default_runner = testing.DummySessionRunner()
    override_runner = testing.DummySessionRunner()

    manager.register(testing.DummyPlugin)
    app = main.Application(manager, router, view, default_runner)

    plugin_config = contract.PluginConfig(
        kind=testing.DummyPlugin.name,
        host="127.0.0.1",
        port=9000,
        data_paths=None,
    )

    dummy_sock = testing.DummySocket()

    with patch("declusor.util.await_connection", return_value=dummy_sock):
        app.run(plugin_config, runner=override_runner)

        assert len(default_runner.run_calls) == 0
        assert len(override_runner.run_calls) == 1
        _, active_router = override_runner.run_calls[0]
        assert active_router is router


def test_terminal_application_default_runner() -> None:
    """Verify TerminalApplication initializes with a PromptLoop runner."""

    manager = core.PluginManager()
    router = core.Router()
    view = presentation.TerminalView()
    input_source = presentation.TerminalInputSource()

    app = main.TerminalApplication(manager, router, view, input_source)
    assert isinstance(app.runner, presentation.PromptLoop)
