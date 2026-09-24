"""Unit tests for Application lifecycle and route wiring using typed test doubles."""

from unittest.mock import patch

from declusor import core, main, testing


def test_create_application_initializes_plugins() -> None:
    """Verify create_application loads built-in plugins into registry."""

    app = main.create_application()
    assert isinstance(app, main.Application)
    assert "shell_socket" in app._registry.names()
    assert "py_socket" in app._registry.names()


def test_application_connect_routes() -> None:
    """Verify application registers core routes on its router."""

    registry = core.ClientPluginRegistry()
    app = main.Application(registry)
    app._connect_routes()

    expected_routes = {"help", "execute", "load", "shell", "upload", "command", "exit"}
    assert expected_routes.issubset(set(app._router.routes))


def test_application_run_lifecycle() -> None:
    """Verify Application.run lifecycle from validation to prompt execution."""

    dummy_conn = testing.DummyConnection()
    dummy_runtime = testing.DummyClientRuntime(connection_to_return=dummy_conn)
    testing.DummyClientPlugin.reset()
    testing.DummyClientPlugin.runtime_instance = dummy_runtime

    registry = core.ClientPluginRegistry()
    registry.register(testing.DummyClientPlugin)

    app = main.Application(registry)

    client_config = testing.create_dummy_client_config(kind=testing.DummyClientPlugin.name)
    options: core.DeclusorOptions = {
        "host": "127.0.0.1",
        "port": 9000,
        "client": client_config,
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
