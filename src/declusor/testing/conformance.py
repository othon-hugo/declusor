import inspect
from pathlib import Path
from typing import Any

import pytest

from declusor import config, contract, util
from declusor.testing.doubles.socket import DummySocket


def assert_conforms_to_client_plugin(
    plugin_cls: type[contract.IClientPlugin],
    *,
    sample_options: dict[str, Any] | None = None,
    tmp_path: Path | None = None,
) -> None:
    """Verify that a class satisfies the structural and behavioral invariants of IClientPlugin.

    Args:
        plugin_cls: The plugin class to test.
        sample_options: Optional custom CLI option mapping.
        tmp_path: Optional temporary directory for asset file validation.
    """

    assert inspect.isclass(plugin_cls), f"{plugin_cls!r} must be a class."
    assert issubclass(plugin_cls, contract.IClientPlugin), f"{plugin_cls!r} must subclass contract.IClientPlugin."

    # Invariant 1: Metadata presence
    assert isinstance(plugin_cls.name, str) and plugin_cls.name.strip(), "plugin.name must be a non-empty string."
    assert isinstance(plugin_cls.description, str), "plugin.description must be a string."
    assert isinstance(plugin_cls.version, str), "plugin.version must be a string."

    # Invariant 2: Parser configuration
    parser = util.Parser(prog="test")
    plugin_cls.configure_parser(parser)

    # Invariant 3: Config construction
    args = util.Namespace(host="127.0.0.1", port=9000, **(sample_options or {}))

    if tmp_path is not None:
        data_paths = config.DataPaths.from_root(tmp_path)
        client_data = data_paths.for_client(plugin_cls.name)
        client_data.launcher.mkdir(parents=True, exist_ok=True)
        (client_data.launcher / f"{plugin_cls.name}_client.py").write_text("# client")
        (client_data.launcher / f"{plugin_cls.name}_client.sh").write_text("# client")
        client_config = plugin_cls.build_config(args, data_paths)
    else:
        client_config = plugin_cls.build_config(args, config.BasePath.DATA_PATHS)

    assert isinstance(client_config, contract.ClientConfig), f"build_config must return ClientConfig, got {type(client_config)}."
    assert client_config.kind == plugin_cls.name, f"client_config.kind ({client_config.kind}) must match plugin.name ({plugin_cls.name})."
    assert client_config.host == "127.0.0.1"
    assert client_config.port == 9000

    # Invariant 4: Validation
    plugin_cls.validate(client_config)

    # Invariant 5: Runtime creation
    runtime = plugin_cls.build_runtime(client_config)
    assert isinstance(runtime, contract.IClientRuntime), f"build_runtime must return IClientRuntime, got {type(runtime)}."
    assert isinstance(runtime.client_script, str), "runtime.client_script must return a bootstrap string."
    assert isinstance(runtime.client_files, contract.IClientFileStore), "runtime.client_files must implement IClientFileStore."

    # Invariant 6: Connection instantiation
    dummy_sock = DummySocket(incoming_bytes=b"")
    # Cast to socket to satisfy interface
    from socket import socket
    from typing import cast

    sock = cast(socket, dummy_sock)
    connection = runtime.create_connection(sock)
    assert isinstance(connection, contract.IConnection), f"create_connection must return IConnection, got {type(connection)}."
    assert connection.state in (contract.ConnectionState.CREATED, contract.ConnectionState.CONNECTED), (
        f"Initial state must be CREATED or CONNECTED, got {connection.state}."
    )


class PluginConformanceTestSuite:
    """Base pytest test suite for verifying full contract conformance of a client plugin.

    Plugin authors can simply subclass this in their test suite and define the
    ``plugin_class`` fixture.

    Example::

        class TestMyPluginConformance(PluginConformanceTestSuite):
            @pytest.fixture
            def plugin_class(self) -> type[contract.IClientPlugin]:
                return MyPlugin
    """

    @pytest.fixture
    def plugin_class(self) -> type[contract.IClientPlugin]:
        """Subclasses must override this to provide the plugin class under test."""

        raise NotImplementedError

    @pytest.fixture
    def sample_options(self) -> dict[str, Any]:
        """Optional custom option mapping for the plugin."""

        return {}

    def test_plugin_metadata(self, plugin_class: type[contract.IClientPlugin]) -> None:
        """Verify plugin defines valid name, description, and version."""

        assert isinstance(plugin_class.name, str) and plugin_class.name.strip()
        assert isinstance(plugin_class.description, str)
        assert isinstance(plugin_class.version, str)

    def test_configure_parser_callable(self, plugin_class: type[contract.IClientPlugin]) -> None:
        """Verify configure_parser accepts a Parser without error."""

        parser = util.Parser(prog="conformance")
        plugin_class.configure_parser(parser)

    def test_build_config_contract(
        self,
        plugin_class: type[contract.IClientPlugin],
        sample_options: dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """Verify build_config returns an immutable ClientConfig instance matching the plugin."""

        args = util.Namespace(host="10.0.0.1", port=4444, **sample_options)
        data_paths = config.DataPaths.from_root(tmp_path)
        client_config = plugin_class.build_config(args, data_paths)
        assert isinstance(client_config, contract.ClientConfig)
        assert client_config.kind == plugin_class.name
        assert client_config.host == "10.0.0.1"
        assert client_config.port == 4444

    def test_full_conformance(
        self,
        plugin_class: type[contract.IClientPlugin],
        sample_options: dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """Run full contract invariant suite."""

        assert_conforms_to_client_plugin(
            plugin_class,
            sample_options=sample_options,
            tmp_path=tmp_path,
        )
