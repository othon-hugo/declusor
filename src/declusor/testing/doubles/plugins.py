from collections.abc import Mapping
from pathlib import Path
from socket import socket

from declusor import config, contract
from declusor.testing.doubles.connection import DummyConnection
from declusor.testing.doubles.filestore import DummyPluginFileStore


class DummyConfig(contract.ParsedArguments, total=False):
    """Configuration options for DummyPlugin."""


class DummyPluginRuntime(contract.IPluginRuntime):
    """Fully-typed client runtime producing configured connections and scripts."""

    def __init__(
        self,
        file_store: contract.IPluginProcessor | None = None,
        client_script: str = "#!/bin/sh\necho dummy",
        connection_to_return: contract.IConnection | None = None,
    ) -> None:
        self._file_store: contract.IPluginProcessor = file_store or DummyPluginFileStore()
        self._client_script: str = client_script
        self.connection_to_return: contract.IConnection | None = connection_to_return
        self.created_connections: list[contract.IConnection] = []

    @property
    def processor(self) -> contract.IPluginProcessor:
        return self._file_store

    @property
    def launcher(self) -> str:
        return self._client_script

    def create_connection(self, connection: socket, /) -> contract.IConnection:
        """Return configured connection or new DummyConnection instance."""

        conn = self.connection_to_return or DummyConnection()
        self.created_connections.append(conn)

        return conn


class DummyPlugin(contract.IPluginExtension[DummyConfig]):
    """Fully-typed plugin implementing the IPluginExtension extension point."""

    name: str = "dummy"
    description: str = "Dummy client plugin for unit tests"
    version: str = "1.0.0"
    author: str = "Test Suite"
    options_type = DummyConfig

    configured_parsers: list[contract.IArgumentParser] = []
    runtime_instance: contract.IPluginRuntime | None = None
    validation_error: BaseException | None = None

    @classmethod
    def reset(cls) -> None:
        """Reset static test tracking state."""

        cls.configured_parsers.clear()
        cls.runtime_instance = None
        cls.validation_error = None

    @classmethod
    def configure_parser(cls, parser: contract.IArgumentParser, /) -> None:
        cls.configured_parsers.append(parser)

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> DummyConfig:
        return DummyConfig()

    @classmethod
    def build_config(
        cls,
        host: str,
        port: int,
        options: DummyConfig,
        /,
        filesystem: contract.PluginFilesystem | None = None,
        mode: config.ExecutionMode = config.Settings.DEFAULT_EXECUTION_MODE,
    ) -> contract.PluginConfig[DummyConfig]:
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
        if cls.validation_error is not None:
            raise cls.validation_error

    @classmethod
    def build_runtime(cls, plugin_config: contract.PluginConfig[DummyConfig], /) -> contract.IPluginRuntime:
        return cls.runtime_instance or DummyPluginRuntime()
