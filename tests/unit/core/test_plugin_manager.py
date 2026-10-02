from pathlib import Path
from unittest.mock import patch

import pytest

from declusor import config, contract, core, testing


class DummyValidConfig(contract.ParsedArguments, total=False):
    pass


class DummyValidPlugin(contract.IPluginExtension[DummyValidConfig]):
    """Compliant test plugin implementing all required IPlugin methods."""

    name = "dummy_test"
    description = "A dummy plugin for unit tests"
    version = "1.0.0"
    options_type = DummyValidConfig

    @classmethod
    def configure_parser(cls, parser: contract.IArgumentParser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: object, /) -> DummyValidConfig:
        return DummyValidConfig()

    @classmethod
    def build_config(
        cls,
        host: str,
        port: int,
        options: DummyValidConfig,
        /,
        filesystem: contract.PluginFilesystem | None = None,
        mode: config.ExecutionMode = config.DEFAULT_EXECUTION_MODE,
    ) -> contract.PluginConfig[DummyValidConfig]:
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
    def validate(cls, plugin_config: contract.PluginConfig[DummyValidConfig], /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config: contract.PluginConfig[DummyValidConfig], /) -> contract.IPluginRuntime:
        return testing.DummyPluginRuntime()


class NotAPlugin:
    """Class that does not inherit from IPlugin."""

    name = "not_a_plugin"


class MissingAbstractMethods(contract.IPluginExtension[contract.ParsedArguments]):
    """Plugin subclass missing required abstract method implementations."""

    name = "missing_methods"


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------


def test_validation_accepts_valid_plugin() -> None:
    """Verify that a compliant IPlugin subclass passes contract validation."""

    manager = core.PluginManager()
    manager.validate_plugin(DummyValidPlugin)


def test_validation_rejects_non_class() -> None:
    """Verify that validating a non-class object raises PluginValidationError."""

    manager = core.PluginManager()

    with pytest.raises(config.PluginValidationError, match="must be a class"):
        manager.validate_plugin("not_a_class")  # type: ignore[arg-type]


def test_validation_rejects_non_subclass() -> None:
    """Verify that classes not inheriting from IPlugin are rejected."""

    manager = core.PluginManager()

    with pytest.raises(config.PluginValidationError, match="must implement 'IPlugin'"):
        manager.validate_plugin(NotAPlugin)


def test_validation_rejects_unimplemented_abstract_methods() -> None:
    """Verify that plugins with unimplemented abstract methods raise PluginValidationError."""

    manager = core.PluginManager()

    with pytest.raises(config.PluginValidationError, match="unimplemented abstract methods"):
        manager.validate_plugin(MissingAbstractMethods)


def test_validation_rejects_empty_name() -> None:
    """Verify that plugins with missing or blank names are rejected."""

    class EmptyNamePlugin(DummyValidPlugin):
        name = "   "

    manager = core.PluginManager()

    with pytest.raises(config.PluginValidationError, match="must define a non-empty string 'name'"):
        manager.validate_plugin(EmptyNamePlugin)


# ---------------------------------------------------------------------------
# Registration & Precedence Tests
# ---------------------------------------------------------------------------


def test_register_and_get() -> None:
    """Verify registering a valid plugin and retrieving it by name."""

    manager = core.PluginManager()
    manager.register(DummyValidPlugin)

    assert manager.get("dummy_test") is DummyValidPlugin
    assert "dummy_test" in manager.names()


def test_register_duplicate_without_override_raises() -> None:
    """Verify that registering a duplicate plugin without allow_override raises ValueError."""

    manager = core.PluginManager()
    manager.register(DummyValidPlugin, source="first")

    with pytest.raises(ValueError, match="already registered"):
        manager.register(DummyValidPlugin, source="second", allow_override=False)


def test_register_duplicate_with_override_replaces() -> None:
    """Verify that registering a duplicate plugin with allow_override replaces the previous one."""

    class ReplacementPlugin(DummyValidPlugin):
        description = "Replaced version"

    manager = core.PluginManager()
    manager.register(DummyValidPlugin, source="original")
    manager.register(ReplacementPlugin, source="override", allow_override=True)

    assert manager.get("dummy_test") is ReplacementPlugin
    assert manager.get_source("dummy_test") == "override"


def test_get_unknown_plugin_raises_plugin_not_found_error() -> None:
    """Verify that retrieving an unregistered plugin name raises PluginNotFoundError."""

    manager = core.PluginManager()

    with pytest.raises(config.PluginNotFoundError, match="Unknown client 'unknown'"):
        manager.get("unknown")


# ---------------------------------------------------------------------------
# Discovery Tests
# ---------------------------------------------------------------------------


def test_discover_builtins() -> None:
    """Verify automatic discovery of built-in plugins (shell_socket and py_socket)."""

    manager = core.PluginManager()
    manager.discover(enable_entry_points=False)

    available = manager.names()
    assert "shell_socket" in available
    assert "py_socket" in available


def test_discover_from_directory(tmp_path: Path) -> None:
    """Verify dynamic plugin discovery from a filesystem directory."""

    plugin_dir = tmp_path / "custom_agent"
    plugin_dir.mkdir()

    plugin_code = """
from collections.abc import Mapping
from declusor import contract

class CustomAgentConfig(contract.ParsedArguments, total=False):
    pass

class CustomAgentPlugin(contract.IPluginExtension[CustomAgentConfig]):
    name = "custom_agent"
    description = "Drop-in test agent"
    options_type = CustomAgentConfig

    @classmethod
    def configure_parser(cls, parser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> CustomAgentConfig:
        return CustomAgentConfig()

    @classmethod
    def build_config(cls, host, port, options, /, filesystem=None, mode=None):
        return None

    @classmethod
    def validate(cls, plugin_config, /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config, /):
        return None
"""
    (plugin_dir / "plugin.py").write_text(plugin_code, encoding="utf-8")

    manager = core.PluginManager()
    loaded = manager.load_from_directory(tmp_path)

    assert "custom_agent" in loaded
    assert manager.get("custom_agent").name == "custom_agent"


def test_discover_from_directory_src_layout(tmp_path: Path) -> None:
    """Verify plugin discovery from an autonomous package using src/<plugin_name>/ layout."""

    plugin_root = tmp_path / "custom_src_agent"
    src_pkg = plugin_root / "src" / "custom_src_agent"
    src_pkg.mkdir(parents=True)

    plugin_code = """
from collections.abc import Mapping
from declusor import contract

class CustomSrcAgentConfig(contract.ParsedArguments, total=False):
    pass

class CustomSrcAgentPlugin(contract.IPluginExtension[CustomSrcAgentConfig]):
    name = "custom_src_agent"
    description = "Drop-in test agent using src layout"
    options_type = CustomSrcAgentConfig

    @classmethod
    def configure_parser(cls, parser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> CustomSrcAgentConfig:
        return CustomSrcAgentConfig()

    @classmethod
    def build_config(cls, host, port, options, /, filesystem=None, mode=None):
        return None

    @classmethod
    def validate(cls, plugin_config, /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config, /):
        return None
"""
    (src_pkg / "__init__.py").write_text(plugin_code, encoding="utf-8")

    manager = core.PluginManager()
    loaded = manager.load_from_directory(tmp_path)

    assert "custom_src_agent" in loaded
    assert manager.get("custom_src_agent").name == "custom_src_agent"


def test_discover_from_entry_points() -> None:
    """Verify plugin discovery via Python entry points ('declusor.plugins')."""

    class DummyEntryPoint:
        def __init__(self, name: str, plugin_cls: type[DummyValidPlugin]) -> None:
            self.name = name
            self._plugin_cls = plugin_cls

        def load(self) -> type[DummyValidPlugin]:
            return self._plugin_cls

    ep = DummyEntryPoint(name="mock_plugin", plugin_cls=DummyValidPlugin)

    with patch("importlib.metadata.entry_points", return_value=[ep]):
        manager = core.PluginManager()
        loaded = manager.load_from_entry_points()

        assert "dummy_test" in loaded
        assert manager.get("dummy_test") is DummyValidPlugin
