from pathlib import Path

from declusor import core, testing


def test_parser_parse_is_idempotent(tmp_path: Path) -> None:
    """Calling parse() multiple times on the same DeclusorParser must not error."""

    registry = core.ClientPluginRegistry()
    registry.register(testing.DummyClientPlugin)

    argv = ["127.0.0.1", "8080", "--client", testing.DummyClientPlugin.name, "--data-root", str(tmp_path)]

    parser = core.DeclusorParser(registry, name="test_app", description="test description")
    options1 = parser.parse(argv)
    assert options1["host"] == "127.0.0.1"
    assert options1["port"] == 8080

    # Second parse on the exact same parser instance
    options2 = parser.parse(argv)
    assert options2["host"] == "127.0.0.1"
    assert options2["port"] == 8080
