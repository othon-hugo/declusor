import inspect
from collections.abc import Mapping
from pathlib import Path
from socket import socket
from typing import cast

import pytest

from declusor import contract, util
from declusor.testing.doubles.socket import DummySocket


def assert_conforms_to_client_plugin(
    plugin_cls: type[contract.IPluginExtension[contract.ParsedArguments]],
    *,
    sample_options: Mapping[str, object] | None = None,
    tmp_path: Path | None = None,
) -> None:
    """Verify that a class satisfies the structural and behavioral invariants of IPluginExtension.

    Args:
        plugin_cls: The plugin class to test.
        sample_options: Optional custom CLI option mapping.
        tmp_path: Optional temporary directory for asset file validation.
    """

    assert inspect.isclass(plugin_cls), f"{plugin_cls!r} must be a class."
    assert issubclass(plugin_cls, contract.IPluginExtension), f"{plugin_cls!r} must subclass contract.IPluginExtension."

    # Invariant 1: Metadata presence
    assert isinstance(plugin_cls.name, str) and plugin_cls.name.strip(), "plugin.name must be a non-empty string."
    assert isinstance(plugin_cls.description, str), "plugin.description must be a string."
    assert isinstance(plugin_cls.version, str), "plugin.version must be a string."
    assert plugin_cls.options_type is not None, "plugin.options_type must be defined."

    # Invariant 2: Parser configuration
    parser = util.Parser(prog="test")
    plugin_cls.configure_parser(parser)

    # Invariant 3: Config construction via extract_options and build_config
    options = plugin_cls.extract_options(sample_options or {})

    if tmp_path is not None:
        filesystem = contract.PluginFilesystem.from_root(tmp_path)
        filesystem.launchers.mkdir(parents=True, exist_ok=True)
        filesystem.helpers.mkdir(parents=True, exist_ok=True)
        filesystem.modules.mkdir(parents=True, exist_ok=True)
        (filesystem.launchers / f"{plugin_cls.name}_client.py").write_text("# client")
        (filesystem.launchers / f"{plugin_cls.name}_client.sh").write_text("# client")
        plugin_config = plugin_cls.build_config("127.0.0.1", 9000, options, filesystem=filesystem)
    else:
        plugin_config = plugin_cls.build_config("127.0.0.1", 9000, options)

    assert isinstance(plugin_config, contract.PluginConfig), f"build_config must return PluginConfig, got {type(plugin_config)}."
    assert plugin_config.kind == plugin_cls.name, f"plugin_config.kind ({plugin_config.kind}) must match plugin.name ({plugin_cls.name})."
    assert plugin_config.host == "127.0.0.1"
    assert plugin_config.port == 9000
    assert plugin_config.options_type == plugin_cls.options_type

    # Invariant 4: Validation
    plugin_cls.validate(plugin_config)

    # Invariant 5: Runtime creation
    runtime = plugin_cls.build_runtime(plugin_config)
    assert isinstance(runtime, contract.IPluginRuntime), f"build_runtime must return IPluginRuntime, got {type(runtime)}."
    assert isinstance(runtime.launcher, str), "runtime.launcher must return a bootstrap string."
    assert isinstance(runtime.processor, contract.IPluginProcessor), "runtime.processor must implement IPluginProcessor."

    # Invariant 6: Connection instantiation
    dummy_sock = DummySocket(incoming_bytes=b"")
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
            def plugin_class(self) -> type[contract.IPluginExtension[contract.ParsedArguments]]:
                return MyPlugin
    """

    @pytest.fixture
    def plugin_class(self) -> type[contract.IPluginExtension[contract.ParsedArguments]]:
        """Subclasses must override this to provide the plugin class under test."""

        raise NotImplementedError

    @pytest.fixture
    def sample_options(self) -> Mapping[str, object]:
        """Optional custom option mapping for the plugin."""

        return {}

    def test_plugin_metadata(self, plugin_class: type[contract.IPluginExtension[contract.ParsedArguments]]) -> None:
        """Verify plugin defines valid name, description, and version."""

        assert isinstance(plugin_class.name, str) and plugin_class.name.strip()
        assert isinstance(plugin_class.description, str)
        assert isinstance(plugin_class.version, str)
        assert plugin_class.options_type is not None

    def test_configure_parser_callable(self, plugin_class: type[contract.IPluginExtension[contract.ParsedArguments]]) -> None:
        """Verify configure_parser accepts a Parser without error."""

        parser = util.Parser(prog="conformance")
        plugin_class.configure_parser(parser)

    def test_build_config_contract(
        self,
        plugin_class: type[contract.IPluginExtension[contract.ParsedArguments]],
        sample_options: Mapping[str, object],
        tmp_path: Path,
    ) -> None:
        """Verify build_config returns an immutable PluginConfig instance matching the plugin."""

        filesystem = contract.PluginFilesystem.from_root(tmp_path)
        options = plugin_class.extract_options(sample_options)
        plugin_config = plugin_class.build_config("10.0.0.1", 4444, options, filesystem=filesystem)

        assert isinstance(plugin_config, contract.PluginConfig)
        assert plugin_config.kind == plugin_class.name
        assert plugin_config.host == "10.0.0.1"
        assert plugin_config.port == 4444

    def test_full_conformance(
        self,
        plugin_class: type[contract.IPluginExtension[contract.ParsedArguments]],
        sample_options: Mapping[str, object],
        tmp_path: Path,
    ) -> None:
        """Run full contract invariant suite."""

        assert_conforms_to_client_plugin(
            plugin_class,
            sample_options=sample_options,
            tmp_path=tmp_path,
        )


assert_conforms_to_plugin = assert_conforms_to_client_plugin
