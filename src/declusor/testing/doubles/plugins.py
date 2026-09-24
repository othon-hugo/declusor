from socket import socket

from declusor import config, contract, util
from declusor.testing.doubles.connection import DummyConnection
from declusor.testing.doubles.filestore import DummyClientFileStore


class DummyClientRuntime(contract.IPluginRuntime):
    """Fully-typed client runtime producing configured connections and scripts."""

    def __init__(
        self,
        file_store: contract.IPluginFileStore | None = None,
        client_script: str = "#!/bin/sh\necho dummy",
        connection_to_return: contract.IConnection | None = None,
    ) -> None:
        self._file_store: contract.IPluginFileStore = file_store or DummyClientFileStore()
        self._client_script: str = client_script
        self.connection_to_return: contract.IConnection | None = connection_to_return
        self.created_connections: list[contract.IConnection] = []

    @property
    def client_files(self) -> contract.IPluginFileStore:
        return self._file_store

    @property
    def client_script(self) -> str:
        return self._client_script

    def create_connection(self, connection: socket, /) -> contract.IConnection:
        """Return configured connection or new DummyConnection instance."""

        conn = self.connection_to_return or DummyConnection()
        self.created_connections.append(conn)

        return conn


class DummyClientPlugin(contract.IPlugin):
    """Fully-typed plugin implementing the IPlugin extension point."""

    name: str = "dummy"
    description: str = "Dummy client plugin for unit tests"
    version: str = "1.0.0"
    author: str = "Test Suite"

    configured_parsers: list[util.Parser] = []
    runtime_instance: contract.IPluginRuntime | None = None
    validation_error: BaseException | None = None

    @classmethod
    def reset(cls) -> None:
        """Reset static test tracking state."""

        cls.configured_parsers.clear()
        cls.runtime_instance = None
        cls.validation_error = None

    @classmethod
    def configure_parser(cls, parser: util.Parser, /) -> None:
        cls.configured_parsers.append(parser)

    @classmethod
    def build_config(cls, args: util.Namespace, data_paths: config.DataPaths | None = None, /) -> contract.PluginConfig:
        return contract.PluginConfig(
            kind=cls.name,
            host=getattr(args, "host", "127.0.0.1"),
            port=getattr(args, "port", 9000),
            data_paths=data_paths,
        )

    @classmethod
    def validate(cls, client_config: contract.PluginConfig, /) -> None:
        if cls.validation_error is not None:
            raise cls.validation_error

    @classmethod
    def build_runtime(cls, client_config: contract.PluginConfig, /) -> contract.IPluginRuntime:
        return cls.runtime_instance or DummyClientRuntime()


DummyPlugin = DummyClientPlugin
DummyPluginRuntime = DummyClientRuntime
