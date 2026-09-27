from pathlib import Path

import pytest

from declusor import config, core, testing


def test_declusor_parser_initialization() -> None:
    """Verify parser initializes with name and description without requiring a manager."""

    parser = core.DeclusorParser(name="test_app", description="test description")
    assert parser.prog == "test_app"
    assert parser.description == "test description"


def test_declusor_parser_parse_success(tmp_path: Path) -> None:
    """Verify parser parses argv and builds validated PluginConfig."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")
    plugin_config = parser.parse(
        manager,
        ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "--assets-dir", str(tmp_path)],
    )

    assert plugin_config.host == "127.0.0.1"
    assert plugin_config.port == 9000
    assert plugin_config.kind == testing.DummyPlugin.name
    assert plugin_config.filesystem is not None
    assert plugin_config.filesystem.root == tmp_path.resolve()
    assert parser in testing.DummyPlugin.configured_parsers


def test_declusor_parser_parse_defaults_filesystem_to_plugin_default() -> None:
    """When --assets-dir is omitted, plugin builds its default filesystem."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")
    plugin_config = parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name])

    assert plugin_config.filesystem is not None


def test_parser_parse_is_idempotent(tmp_path: Path) -> None:
    """Calling parse() multiple times on the same DeclusorParser must not error."""

    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    argv = ["127.0.0.1", "8080", "--plugin", testing.DummyPlugin.name, "--assets-dir", str(tmp_path)]

    parser = core.DeclusorParser(name="test_app", description="test description")
    config1 = parser.parse(manager, argv)
    assert config1.host == "127.0.0.1"
    assert config1.port == 8080

    # Second parse on the exact same parser instance
    config2 = parser.parse(manager, argv)
    assert config2.host == "127.0.0.1"
    assert config2.port == 8080


def test_declusor_parser_parse_missing_positional_raises() -> None:
    """Verify parser raises ParserError when required positional args are missing."""

    manager = core.PluginManager()
    parser = core.DeclusorParser(name="test_app")

    with pytest.raises(config.ParserError):
        parser.parse(manager, ["127.0.0.1"])  # missing port


def test_declusor_parser_parse_invalid_plugin_raises() -> None:
    """Verify parser raises ParserError when selected plugin is not registered."""

    manager = core.PluginManager()
    parser = core.DeclusorParser(name="test_app")

    with pytest.raises(config.ParserError, match="invalid choice"):
        parser.parse(manager, ["127.0.0.1", "9000", "-p", "nonexistent"])


def test_declusor_parser_mode_defaults_to_cli() -> None:
    """Verify parser defaults execution mode to ExecutionMode.CLI."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")
    plugin_config = parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name])

    assert plugin_config.mode == config.ExecutionMode.CLI


def test_declusor_parser_explicit_mode() -> None:
    """Verify parser accepts explicit --mode and -m arguments."""

    testing.DummyPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    parser = core.DeclusorParser(name="test_app")
    plugin_config = parser.parse(
        manager,
        ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "--mode", "http"],
    )
    assert plugin_config.mode == config.ExecutionMode.HTTP

    plugin_config_short = parser.parse(
        manager,
        ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "-m", "mcp"],
    )
    assert plugin_config_short.mode == config.ExecutionMode.MCP


def test_declusor_parser_invalid_mode_raises() -> None:
    """Verify parser raises ParserError when invalid execution mode is provided."""

    manager = core.PluginManager()
    parser = core.DeclusorParser(name="test_app")

    with pytest.raises(config.ParserError):
        parser.parse(manager, ["127.0.0.1", "9000", "--mode", "invalid_mode"])
