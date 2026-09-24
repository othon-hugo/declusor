from pathlib import Path

import pytest

from declusor import config, core, testing


def test_declusor_parser_initialization_with_manager() -> None:
    """Verify parser binds a ClientPluginManager directly."""

    manager = core.PluginManager()
    manager.register(testing.DummyClientPlugin)

    parser = core.DeclusorParser(manager, name="test_app")
    assert parser.manager is manager
    assert parser.prog == "test_app"


def test_declusor_parser_parse_success(tmp_path: Path) -> None:
    """Verify parser parses argv and builds validated PluginConfig."""

    testing.DummyClientPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyClientPlugin)

    parser = core.DeclusorParser(manager, name="test_app")
    options = parser.parse(["127.0.0.1", "9000", "-c", testing.DummyClientPlugin.name, "--data-root", str(tmp_path)])

    assert options["host"] == "127.0.0.1"
    assert options["port"] == 9000
    assert options["plugin"].kind == testing.DummyClientPlugin.name
    assert options["plugin"].data_paths is not None
    assert options["plugin"].data_paths.root == tmp_path
    assert parser in testing.DummyClientPlugin.configured_parsers


def test_declusor_parser_parse_defaults_data_paths_to_none() -> None:
    """When --data-root is omitted, client config data_paths must be None."""

    testing.DummyClientPlugin.reset()
    manager = core.PluginManager()
    manager.register(testing.DummyClientPlugin)

    parser = core.DeclusorParser(manager, name="test_app")
    options = parser.parse(["127.0.0.1", "9000", "-c", testing.DummyClientPlugin.name])

    assert options["plugin"].data_paths is None


def test_declusor_parser_parse_missing_positional_raises() -> None:
    """Verify parser raises ParserError when required positional args are missing."""

    manager = core.PluginManager()
    parser = core.DeclusorParser(manager, name="test_app")

    with pytest.raises(config.ParserError):
        parser.parse(["127.0.0.1"])  # missing port
