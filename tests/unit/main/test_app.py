"""Unit tests for Application lifecycle and route wiring using typed test doubles."""

from unittest.mock import patch

from declusor import core
from declusor.main.app import Application, create_application
from declusor.testing import (
    DummyClientPlugin,
    DummyClientRuntime,
    DummyConnection,
    DummySocket,
    create_dummy_client_config,
)


def test_create_application_initializes_plugins() -> None:
    """Verify create_application loads built-in plugins into registry."""
    app = create_application()
    assert isinstance(app, Application)
    assert "shell_socket" in app._registry.names()
    assert "py_socket" in app._registry.names()


def test_application_connect_routes() -> None:
    """Verify application registers core routes on its router."""
    registry = core.ClientRegistry()
    app = Application(registry)
    app._connect_routes()

    expected_routes = {"help", "execute", "load", "shell", "upload", "command", "exit"}
    assert expected_routes.issubset(set(app._router.routes))


def test_application_run_lifecycle() -> None:
    """Verify Application.run lifecycle from validation to prompt execution."""
    dummy_conn = DummyConnection()
    dummy_runtime = DummyClientRuntime(connection_to_return=dummy_conn)
    DummyClientPlugin.reset()
    DummyClientPlugin.runtime_instance = dummy_runtime

    registry = core.ClientRegistry()
    registry.register(DummyClientPlugin)

    app = Application(registry)

    client_config = create_dummy_client_config(kind=DummyClientPlugin.name)
    options: core.DeclusorOptions = {
        "host": "127.0.0.1",
        "port": 9000,
        "client": client_config,
    }

    dummy_sock = DummySocket()
    with (
        patch("declusor.util.await_connection", return_value=dummy_sock) as mock_await,
        patch("declusor.presentation.PromptCLI.run") as mock_prompt_run,
    ):
        app.run(options)

        mock_await.assert_called_once_with("127.0.0.1", 9000)
        assert dummy_conn.initialize_called
        mock_prompt_run.assert_called_once()
