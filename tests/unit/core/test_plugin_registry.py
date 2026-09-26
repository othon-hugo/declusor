import pytest

from declusor import core, testing


def test_registries_are_isolated() -> None:
    """Registering a plugin must not affect another registry instance."""

    first = core.PluginRegistry()
    second = core.PluginRegistry()

    first.register(testing.DummyPlugin)

    assert first.names() == (testing.DummyPlugin.name,)
    assert second.names() == ()


def test_parser_uses_injected_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    """The parser must resolve plugins only from its injected manager."""

    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)
    monkeypatch.setattr(
        "sys.argv",
        ["declusor", "127.0.0.1", "9000", "--plugin", testing.DummyPlugin.name],
    )

    plugin_config = core.DeclusorParser(manager, name="declusor").parse()

    assert plugin_config.kind == testing.DummyPlugin.name
