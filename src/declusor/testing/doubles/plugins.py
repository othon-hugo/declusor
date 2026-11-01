"""Dummy plugin implementation conforming to IPluginExtension."""

from collections.abc import Mapping
from pathlib import Path
from typing import Final

from declusor import config, contract, core

from .connection import DummyConnection
from .filestore import DummyPluginFileStore


class DummyConfig(contract.ParsedArguments, total=False):
    """Configuration options for DummyPlugin."""


class DummyPluginRuntime(contract.IPluginRuntime):
    """Fully-typed client runtime producing configured connections and scripts."""

    def __init__(
        self,
        file_store: contract.IPluginProcessor | None = None,
        client_script: str = "#!/bin/sh\necho dummy",
        connection_to_return: contract.IConnection | None = None,
        launcher_delivery: contract.LauncherDelivery | None = None,
        launcher_kind: config.LauncherKind = config.DEFAULT_LAUNCHER_KIND,
    ) -> None:
        """Initialize plugin runtime double with mock processor and launcher delivery."""

        self._file_store: contract.IPluginProcessor = file_store or DummyPluginFileStore()
        script_bytes = client_script.encode("utf-8")
        self._launcher_delivery = launcher_delivery or contract.LauncherDelivery(script=script_bytes, kind=launcher_kind)
        self.connection_to_return: contract.IConnection | None = connection_to_return
        self.created_connections: list[contract.IConnection] = []
        self.received_transports: list[contract.ITransport] = []

    @property
    def processor(self) -> contract.IPluginProcessor:
        """Return the plugin processor double."""

        return self._file_store

    @property
    def launcher(self) -> contract.LauncherDelivery:
        """Return the launcher delivery double."""

        return self._launcher_delivery

    def create_connection(self, transport: contract.ITransport, /) -> contract.IConnection:
        """Return configured connection or new DummyConnection instance."""

        self.received_transports.append(transport)
        conn = self.connection_to_return or DummyConnection(transport=transport)
        self.created_connections.append(conn)

        return conn


class DummyPlugin(contract.IPluginExtension[DummyConfig]):
    """Fully-typed plugin implementing the IPluginExtension extension point."""

    name: str = "dummy"
    """Unique test plugin identifier."""

    description: str = "Dummy client plugin for unit tests"
    """Human-readable description string."""

    version: str = "1.0.0"
    """SemVer version string."""

    author: str = "Test Suite"
    """Author name string."""

    options_type = DummyConfig
    """Parsed options schema type."""

    routes = core.OFFICIAL_ROUTES
    """Registered route mappings."""

    supported_launcher_kinds: frozenset[config.LauncherKind] = frozenset({config.LauncherKind.STAGED, config.LauncherKind.STAGELESS})
    """Set of supported launcher kinds."""

    DEFAULT_SUPPORTED_TRANSPORT_LAYERS: Final[frozenset[config.TransportLayer | str]] = frozenset(
        {
            config.TransportLayer.XOR,
            "custom",
            "dummy_layer",
            "app_layer",
        }
    )
    """Default supported transport layers for test double."""

    supported_transport_layers: frozenset[config.TransportLayer | str] = DEFAULT_SUPPORTED_TRANSPORT_LAYERS
    """Set of supported transport layer kinds."""

    configured_parsers: list[contract.IArgumentParser] = []
    """Record of parsers passed to configure_parser."""

    runtime_instance: contract.IPluginRuntime | None = None
    """Configured runtime instance returned by build_runtime."""

    validation_error: BaseException | None = None
    """Configured exception raised by validate."""

    @classmethod
    def reset(cls) -> None:
        """Reset static test tracking state."""

        cls.configured_parsers.clear()
        cls.runtime_instance = None
        cls.validation_error = None
        cls.supported_transport_layers = cls.DEFAULT_SUPPORTED_TRANSPORT_LAYERS

    @classmethod
    def configure_parser(cls, parser: contract.IArgumentParser, /) -> None:
        """Record parser configuration call."""

        cls.configured_parsers.append(parser)

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> DummyConfig:
        """Return dummy options instance."""

        return DummyConfig()

    @classmethod
    def build_config(
        cls,
        host: str,
        port: int,
        options: DummyConfig,
        /,
        filesystem: contract.PluginFilesystem | None = None,
        mode: config.ExecutionMode = config.DEFAULT_EXECUTION_MODE,
    ) -> contract.PluginConfig[DummyConfig]:
        """Build plugin configuration instance."""

        dummy_fs = contract.PluginFilesystem(
            root=Path("."),
            assets=Path("."),
            launchers=Path("."),
            modules=Path("."),
            helpers=Path("."),
        )

        return contract.PluginConfig(
            kind=cls.name,
            host=host,
            port=port,
            options=options,
            options_type=cls.options_type,
            filesystem=filesystem or dummy_fs,
            mode=mode,
        )

    @classmethod
    def validate(cls, plugin_config: contract.PluginConfig[DummyConfig], /) -> None:
        """Execute validation barrier, raising configured error if set."""

        if cls.validation_error is not None:
            raise cls.validation_error

    @classmethod
    def build_runtime(cls, plugin_config: contract.PluginConfig[DummyConfig], /) -> contract.IPluginRuntime:
        """Build configured runtime instance double."""

        return cls.runtime_instance or DummyPluginRuntime(launcher_kind=plugin_config.launcher_kind)
