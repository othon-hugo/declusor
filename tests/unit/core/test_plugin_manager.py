from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from declusor import config, contract
from declusor.config import PluginValidationError
from declusor.core import PluginManager


class DummyValidPlugin(contract.IClientPlugin):
    name = "dummy_test"
    description = "A dummy plugin for unit tests"

    @classmethod
    def configure_parser(cls, parser, /) -> None:
        pass

    @classmethod
    def build_config(cls, args, data_paths=None, /):
        return MagicMock()

    @classmethod
    def validate(cls, client_config, /) -> None:
        pass

    @classmethod
    def build_runtime(cls, client_config, /):
        return MagicMock()


class NotAPlugin:
    name = "not_a_plugin"


class MissingAbstractMethods(contract.IClientPlugin):
    name = "missing_methods"
    # Unimplemented abstract methods


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------


def test_validation_accepts_valid_plugin() -> None:
    manager = PluginManager()
    manager.validate_plugin(DummyValidPlugin)


def test_validation_rejects_non_class() -> None:
    manager = PluginManager()
    with pytest.raises(PluginValidationError, match="must be a class"):
        manager.validate_plugin("not_a_class")  # type: ignore[arg-type]


def test_validation_rejects_non_subclass() -> None:
    manager = PluginManager()
    with pytest.raises(PluginValidationError, match="must implement 'IClientPlugin'"):
        manager.validate_plugin(NotAPlugin)


def test_validation_rejects_unimplemented_abstract_methods() -> None:
    manager = PluginManager()
    with pytest.raises(PluginValidationError, match="unimplemented abstract methods"):
        manager.validate_plugin(MissingAbstractMethods)


def test_validation_rejects_empty_name() -> None:
    class EmptyNamePlugin(DummyValidPlugin):
        name = "   "

    manager = PluginManager()
    with pytest.raises(PluginValidationError, match="must define a non-empty string 'name'"):
        manager.validate_plugin(EmptyNamePlugin)


# ---------------------------------------------------------------------------
# Registration & Precedence Tests
# ---------------------------------------------------------------------------


def test_register_and_get() -> None:
    manager = PluginManager()
    manager.register(DummyValidPlugin)

    assert manager.get("dummy_test") is DummyValidPlugin
    assert "dummy_test" in manager.names()


def test_register_duplicate_without_override_raises() -> None:
    manager = PluginManager()
    manager.register(DummyValidPlugin, source="first")

    with pytest.raises(ValueError, match="already registered"):
        manager.register(DummyValidPlugin, source="second", allow_override=False)


def test_register_duplicate_with_override_replaces() -> None:
    class ReplacementPlugin(DummyValidPlugin):
        description = "Replaced version"

    manager = PluginManager()
    manager.register(DummyValidPlugin, source="original")
    manager.register(ReplacementPlugin, source="override", allow_override=True)

    assert manager.get("dummy_test") is ReplacementPlugin
    assert manager.get_source("dummy_test") == "override"


def test_get_unknown_plugin_raises_parser_error() -> None:
    manager = PluginManager()
    with pytest.raises(config.ParserError, match="Unknown client 'unknown'"):
        manager.get("unknown")


# ---------------------------------------------------------------------------
# Discovery Tests
# ---------------------------------------------------------------------------


def test_discover_builtins() -> None:
    manager = PluginManager()
    manager.discover(enable_entry_points=False)

    available = manager.names()
    assert "shell_socket" in available
    assert "py_socket" in available


def test_discover_from_directory(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "custom_agent"
    plugin_dir.mkdir()

    plugin_code = """
from declusor import contract

class CustomAgentPlugin(contract.IClientPlugin):
    name = "custom_agent"
    description = "Drop-in test agent"

    @classmethod
    def configure_parser(cls, parser, /) -> None:
        pass

    @classmethod
    def build_config(cls, args, data_paths=None, /):
        return None

    @classmethod
    def validate(cls, client_config, /) -> None:
        pass

    @classmethod
    def build_runtime(cls, client_config, /):
        return None
"""
    (plugin_dir / "plugin.py").write_text(plugin_code, encoding="utf-8")

    manager = PluginManager()
    loaded = manager.load_from_directory(tmp_path)

    assert "custom_agent" in loaded
    assert manager.get("custom_agent").name == "custom_agent"


def test_discover_from_entry_points() -> None:
    mock_ep = MagicMock()
    mock_ep.name = "mock_plugin"
    mock_ep.load.return_value = DummyValidPlugin

    with patch("importlib.metadata.entry_points", return_value=[mock_ep]):
        manager = PluginManager()
        loaded = manager.load_from_entry_points()

        assert "dummy_test" in loaded
        assert manager.get("dummy_test") is DummyValidPlugin
