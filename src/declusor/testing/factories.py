from pathlib import Path
from typing import overload

from declusor import config, contract
from declusor.testing.doubles.connection import DummyConnection
from declusor.testing.doubles.filestore import DummyPluginFileStore
from declusor.testing.doubles.input_source import DummyInputSource
from declusor.testing.doubles.plugins import DummyConfig
from declusor.testing.doubles.view import DummyView


def create_test_session(
    connection: contract.IConnection | None = None,
    view: contract.IView | None = None,
    input_source: contract.IInputSource | None = None,
    files: contract.IPluginProcessor | None = None,
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
        input_source=input_source or DummyInputSource(),
        plugin_processor=files or DummyPluginFileStore(),
    )


def create_dummy_plugin_config(
    kind: str = "dummy",
    host: str = "127.0.0.1",
    port: int = 9000,
    filesystem: contract.PluginFilesystem | None = None,
    options: DummyConfig | None = None,
    mode: config.ExecutionMode = config.DEFAULT_EXECUTION_MODE,
    *,
    timeout: float | None = None,
    launcher_output_mode: config.LauncherOutputMode = config.DEFAULT_LAUNCHER_OUTPUT_MODE,
    launcher_output_path: Path | None = None,
    launcher_wrapper: str | None = None,
    transport_layers: tuple[str, ...] = (),
) -> contract.PluginConfig[DummyConfig]:
    """Create a PluginConfig instance for testing.

    Args:
        kind: Client implementation identifier. Defaults to "dummy".
        host: Host address. Defaults to "127.0.0.1".
        port: Port number. Defaults to 9000.
        filesystem: Optional PluginFilesystem instance. Defaults to None.
        options: Plugin options dictionary. Defaults to empty DummyConfig.
        mode: Application execution mode.
        timeout: Default network socket operation timeout in seconds.
        launcher_output_mode: Delivery mode for the generated client launcher.
        launcher_output_path: Destination file path when launcher_output_mode is FILE.
        launcher_wrapper: Optional shell invocation wrapper template.
        transport_layers: Ordered sequence of transport layer names.

    Returns:
        An immutable PluginConfig dataclass instance.
    """

    dummy_fs = contract.PluginFilesystem(
        root=Path("."),
        assets=Path("."),
        launchers=Path("."),
        modules=Path("."),
        helpers=Path("."),
    )

    return contract.PluginConfig(
        kind=kind,
        host=host,
        port=port,
        options=options if options is not None else DummyConfig(),
        options_type=DummyConfig,
        filesystem=filesystem or dummy_fs,
        mode=mode,
        timeout=timeout,
        launcher_output_mode=launcher_output_mode,
        launcher_output_path=launcher_output_path,
        launcher_wrapper=launcher_wrapper,
        transport_layers=transport_layers,
    )


@overload
def create_dummy_controller_request(
    text: str = "",
    argument_type: None = None,
) -> contract.IControllerRequest[contract.ControllerArguments]: ...


@overload
def create_dummy_controller_request[T: contract.ControllerArguments](
    text: str = "",
    argument_type: type[T] = ...,
) -> contract.IControllerRequest[T]: ...


def create_dummy_controller_request[T: contract.ControllerArguments](
    text: str = "",
    argument_type: type[T] | None = None,
) -> contract.IControllerRequest[T] | contract.IControllerRequest[contract.ControllerArguments]:
    """Create a ControllerRequest instance wrapping command text.

    Args:
        text: Raw command string passed to the controller.
        argument_type: Optional expected ControllerArguments TypedDict type.

    Returns:
        An IControllerRequest instance.
    """

    from declusor.presentation.request import ControllerRequest

    if argument_type is not None:
        return ControllerRequest[T](text)

    return ControllerRequest[contract.ControllerArguments](text)


def create_dummy_options(
    host: str = "127.0.0.1",
    port: int = 9000,
    client: contract.PluginConfig[DummyConfig] | None = None,
) -> contract.PluginConfig[DummyConfig]:
    """Create a fully-formed PluginConfig for testing.

    Args:
        host: Target host. Defaults to '127.0.0.1'.
        port: Target port. Defaults to 9000.
        client: PluginConfig instance. Defaults to dummy config.

    Returns:
        A valid PluginConfig instance.
    """

    return client or create_dummy_plugin_config(host=host, port=port)
