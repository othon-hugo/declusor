from unittest.mock import patch

from declusor import contract, core, main, testing


def test_create_application_initializes_plugins() -> None:
    """Verify create_application loads built-in plugins into manager."""

    app = main.create_application()
    assert isinstance(app, main.Application)
    assert app.manager is not None
    assert "shell_socket" in app.manager.names()
    assert "py_socket" in app.manager.names()


def test_application_connect_routes() -> None:
    """Verify application registers core routes on its router."""

    manager = core.PluginManager()
    app = main.Application(manager)
    app._connect_routes()

    expected_routes = {"help", "execute", "load", "shell", "upload", "command", "exit"}
    assert expected_routes.issubset(set(app._router.routes))


def test_application_register_plugin_at_runtime() -> None:
    """Verify application allows registering client plugins at runtime."""

    manager = core.PluginManager()
    app = main.Application(manager)
    testing.DummyClientPlugin.reset()

    app.register_plugin(testing.DummyClientPlugin)
    assert testing.DummyClientPlugin.name in app.manager.names()


def test_application_run_lifecycle_with_no_data_paths() -> None:
    """Verify Application.run succeeds with data_paths=None without host filesystem checks."""

    dummy_conn = testing.DummyConnection()
    dummy_runtime = testing.DummyClientRuntime(connection_to_return=dummy_conn)
    testing.DummyClientPlugin.reset()
    testing.DummyClientPlugin.runtime_instance = dummy_runtime

    manager = core.PluginManager()
    manager.register(testing.DummyClientPlugin)

    app = main.Application(manager)

    client_config = contract.PluginConfig(
        kind=testing.DummyClientPlugin.name,
        host="127.0.0.1",
        port=9000,
        data_paths=None,
    )
    options: core.DeclusorOptions = {
        "host": "127.0.0.1",
        "port": 9000,
        "plugin": client_config,
    }

    dummy_sock = testing.DummySocket()

    with (
        patch("declusor.util.await_connection", return_value=dummy_sock) as mock_await,
        patch("declusor.presentation.PromptCLI.run") as mock_prompt_run,
    ):
        app.run(options)

        mock_await.assert_called_once_with("127.0.0.1", 9000)
        assert dummy_conn.initialize_called
        mock_prompt_run.assert_called_once()
        assert not hasattr(app, "_validate_directories")
