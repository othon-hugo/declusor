from pathlib import Path

import pytest

from declusor import config, core
from declusor.testing import DummyClientPlugin


def test_declusor_parser_initialization_with_registry() -> None:
    """Verify parser configures common arguments based on registry plugins."""
    registry = core.ClientRegistry()
    registry.register(DummyClientPlugin)

    parser = core.DeclusorParser(registry, name="test_app")
    assert parser.prog == "test_app"


def test_declusor_parser_parse_success(tmp_path: Path) -> None:
    """Verify parser parses argv and builds validated ClientConfig."""
    DummyClientPlugin.reset()
    registry = core.ClientRegistry()
    registry.register(DummyClientPlugin)

    parser = core.DeclusorParser(registry, name="test_app")
    options = parser.parse(["127.0.0.1", "9000", "-c", DummyClientPlugin.name, "--data-root", str(tmp_path)])

    assert options["host"] == "127.0.0.1"
    assert options["port"] == 9000
    assert options["client"].kind == DummyClientPlugin.name
    assert options["client"].data_paths.root == tmp_path
    assert parser in DummyClientPlugin.configured_parsers


def test_declusor_parser_parse_missing_positional_raises() -> None:
    """Verify parser raises ParserError when required positional args are missing."""
    registry = core.ClientRegistry()
    parser = core.DeclusorParser(registry, name="test_app")

    with pytest.raises(config.ParserError):
        parser.parse(["127.0.0.1"])  # missing port
