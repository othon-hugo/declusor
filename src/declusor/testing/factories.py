from typing import Any

from declusor import config, contract, core
from declusor.testing.doubles.connection import DummyConnection
from declusor.testing.doubles.filestore import DummyPluginFileStore
from declusor.testing.doubles.input_source import DummyInputSource
from declusor.testing.doubles.view import DummyView


def create_test_session(
    connection: contract.IConnection | None = None,
    view: contract.IView | None = None,
    input_source: contract.IInputSource | None = None,
    files: contract.IClientFileStore | None = None,
) -> contract.SessionContext:
    """Create a SessionContext populated with test doubles by default.

    Args:
        connection: Connection double to inject. Defaults to DummyConnection.
        view: View double to inject. Defaults to DummyView.
        input_source: Input source double to inject. Defaults to DummyInputSource.
        files: File store double to inject. Defaults to DummyPluginFileStore.

    Returns:
        A ready-to-use SessionContext instance.
    """

    return contract.SessionContext(
        connection=connection or DummyConnection(),
        view=view or DummyView(),
        input=input_source or DummyInputSource(),
        files=files or DummyPluginFileStore(),
    )


def create_dummy_plugin_config(
    kind: str = "dummy",
    host: str = "127.0.0.1",
    port: int = 9000,
    data_paths: config.DataPaths | None = None,
    options: dict[str, Any] | None = None,
) -> contract.PluginConfig:
    """Create a PluginConfig instance for testing.

    Args:
        kind: Client implementation identifier. Defaults to "dummy".
        host: Host address. Defaults to "127.0.0.1".
        port: Port number. Defaults to 9000.
        data_paths: Optional DataPaths instance. Defaults to None.
        options: Plugin options dictionary. Defaults to empty dict.

    Returns:
        An immutable PluginConfig dataclass instance.
    """

    return contract.PluginConfig(
        kind=kind,
        host=host,
        port=port,
        data_paths=data_paths,
        options=options if options is not None else {},
    )


def create_dummy_plugin_arguments(
    host: str = "127.0.0.1",
    port: int = 9000,
    **extra: Any,
) -> contract.PluginNamespace:
    """Create a PluginNamespace instance for testing.

    Args:
        host: Target host. Defaults to '127.0.0.1'.
        port: Target port. Defaults to 9000.
        **extra: Additional plugin-specific arguments.

    Returns:
        A pre-configured PluginNamespace instance satisfying PluginArguments.
    """

    return contract.PluginNamespace(host=host, port=port, **extra)


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
    client: contract.PluginConfig | None = None,
) -> core.DeclusorOptions:
    """Create a fully-formed DeclusorOptions TypedDict for testing.

    Args:
        host: Target host. Defaults to '127.0.0.1'.
        port: Target port. Defaults to 9000.
        client: PluginConfig instance. Defaults to dummy config.

    Returns:
        A valid DeclusorOptions TypedDict mapping.
    """

    return {
        "host": host,
        "port": port,
        "plugin": client or create_dummy_plugin_config(host=host, port=port),
    }
