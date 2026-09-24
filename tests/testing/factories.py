"""Factory functions and builders for setting up Declusor test fixtures."""

from typing import Any

from declusor import config
from declusor.config import DataPaths
from declusor.contract import (
    ClientConfig,
    ControllerRequest,
    IClientFileStore,
    IConnection,
    IConsole,
    SessionContext,
)
from tests.testing.doubles import DummyClientFileStore, DummyConnection, DummyConsole


def create_test_session(
    connection: IConnection | None = None,
    console: IConsole | None = None,
    files: IClientFileStore | None = None,
) -> SessionContext:
    """Create a SessionContext populated with test doubles by default.

    Args:
        connection: Connection double to inject. Defaults to DummyConnection.
        console: Console double to inject. Defaults to DummyConsole.
        files: File store double to inject. Defaults to DummyClientFileStore.

    Returns:
        A ready-to-use SessionContext instance.
    """
    return SessionContext(
        connection=connection or DummyConnection(),
        console=console or DummyConsole(),
        files=files or DummyClientFileStore(),
    )


def create_dummy_client_config(
    kind: str = "dummy",
    host: str = "127.0.0.1",
    port: int = 9000,
    data_paths: DataPaths | None = None,
    options: dict[str, Any] | None = None,
) -> ClientConfig:
    """Create a ClientConfig instance for testing.

    Args:
        kind: Client implementation identifier. Defaults to "dummy".
        host: Host address. Defaults to "127.0.0.1".
        port: Port number. Defaults to 9000.
        data_paths: DataPaths instance. Defaults to config.BasePath.DATA_PATHS.
        options: Plugin options dictionary. Defaults to empty dict.

    Returns:
        An immutable ClientConfig dataclass instance.
    """
    return ClientConfig(
        kind=kind,
        host=host,
        port=port,
        data_paths=data_paths if data_paths is not None else config.BasePath.DATA_PATHS,
        options=options if options is not None else {},
    )


def create_dummy_controller_request(text: str = "") -> ControllerRequest:
    """Create a ControllerRequest instance wrapping command text.

    Args:
        text: Raw command string passed to the controller.

    Returns:
        A ControllerRequest instance.
    """
    return ControllerRequest(text)
