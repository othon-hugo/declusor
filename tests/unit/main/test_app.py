from unittest.mock import MagicMock, patch

from declusor import contract, core
from declusor.main.app import Application, create_application


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
    mock_plugin = MagicMock(spec=contract.IClientPlugin)
    mock_plugin.name = "mock_client"

    mock_runtime = MagicMock(spec=contract.IClientRuntime)
    mock_runtime.client_script = "#!/bin/sh"
    mock_connection = MagicMock(spec=contract.IConnection)
    mock_runtime.create_connection.return_value = mock_connection

    mock_plugin.build_runtime.return_value = mock_runtime

    registry = core.ClientRegistry()
    registry.register(mock_plugin)

    app = Application(registry)

    mock_client_config = MagicMock(spec=contract.ClientConfig)
    mock_client_config.kind = "mock_client"
    mock_client_config.host = "127.0.0.1"
    mock_client_config.port = 9000
    mock_client_config.data_paths = MagicMock()
    mock_client_config.data_paths.clients.exists.return_value = False
    mock_client_config.data_paths.modules.exists.return_value = False
    mock_client_config.data_paths.library.exists.return_value = False

    options: core.DeclusorOptions = {
        "host": "127.0.0.1",
        "port": 9000,
        "client": mock_client_config,
    }

    with (
        patch("declusor.util.await_connection") as mock_await,
        patch("declusor.presentation.PromptCLI.run") as mock_prompt_run,
    ):
        mock_socket = MagicMock()
        mock_await.return_value.__enter__.return_value = mock_socket
        mock_connection.__enter__.return_value = mock_connection

        app.run(options)

        mock_await.assert_called_once_with("127.0.0.1", 9000)
        mock_connection.initialize.assert_called_once()
        mock_prompt_run.assert_called_once()
