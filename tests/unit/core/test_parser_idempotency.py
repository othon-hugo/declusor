from pathlib import Path

from declusor import core, testing


def test_parser_parse_is_idempotent(tmp_path: Path) -> None:
    """Calling parse() multiple times on the same DeclusorParser must not error."""

    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    argv = ["127.0.0.1", "8080", "--plugin", testing.DummyPlugin.name, "--assets-dir", str(tmp_path)]

    parser = core.DeclusorParser(manager, name="test_app", description="test description")
    config1 = parser.parse(argv)
    assert config1.host == "127.0.0.1"
    assert config1.port == 8080

    # Second parse on the exact same parser instance
    config2 = parser.parse(argv)
    assert config2.host == "127.0.0.1"
    assert config2.port == 8080
