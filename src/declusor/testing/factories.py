from typing import Any

from declusor import config, contract, core
from declusor.testing.doubles.connection import DummyConnection
from declusor.testing.doubles.console import DummyConsole
from declusor.testing.doubles.filestore import DummyClientFileStore


def create_test_session(
    connection: contract.IConnection | None = None,
    console: contract.IConsole | None = None,
    files: contract.IClientFileStore | None = None,
) -> contract.SessionContext:
    """Create a SessionContext populated with test doubles by default.

    Args:
        connection: Connection double to inject. Defaults to DummyConnection.
        console: Console double to inject. Defaults to DummyConsole.
        files: File store double to inject. Defaults to DummyClientFileStore.

    Returns:
        A ready-to-use SessionContext instance.
    """

    return contract.SessionContext(
        connection=connection or DummyConnection(),
        console=console or DummyConsole(),
        files=files or DummyClientFileStore(),
    )


def create_dummy_client_config(
    kind: str = "dummy",
    host: str = "127.0.0.1",
    port: int = 9000,
    data_paths: config.DataPaths | None = None,
    options: dict[str, Any] | None = None,
) -> contract.ClientConfig:
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

    return contract.ClientConfig(
        kind=kind,
        host=host,
        port=port,
        data_paths=data_paths if data_paths is not None else config.BasePath.DATA_PATHS,
        options=options if options is not None else {},
    )


def create_dummy_controller_request(text: str = "") -> contract.ControllerRequest:
    """Create a ControllerRequest instance wrapping command text.

    Args:
        text: Raw command string passed to the controller.

    Returns:
        A ControllerRequest instance.
    """

    return contract.ControllerRequest(text)


def create_dummy_options(
    host: str = "127.0.0.1",
    port: int = 9000,
    client: contract.ClientConfig | None = None,
) -> core.DeclusorOptions:
    """Create a fully-formed DeclusorOptions TypedDict for testing.

    Args:
        host: Target host. Defaults to '127.0.0.1'.
        port: Target port. Defaults to 9000.
        client: ClientConfig instance. Defaults to dummy config.

    Returns:
        A valid DeclusorOptions TypedDict mapping.
    """

    return {
        "host": host,
        "port": port,
        "client": client or create_dummy_client_config(host=host, port=port),
    }
