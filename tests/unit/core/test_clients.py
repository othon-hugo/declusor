import pytest

from declusor import core, testing


def test_registries_are_isolated() -> None:
    """Registering a plugin must not affect another registry instance."""

    first = core.PluginRegistry()
    second = core.PluginRegistry()

    first.register(testing.DummyClientPlugin)

    assert first.names() == (testing.DummyClientPlugin.name,)
    assert second.names() == ()


def test_parser_uses_injected_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    """The parser must resolve clients only from its injected manager."""

    manager = core.PluginManager()
    manager.register(testing.DummyClientPlugin)
    monkeypatch.setattr(
        "sys.argv",
        ["declusor", "127.0.0.1", "9000", "--client", testing.DummyClientPlugin.name],
    )

    options = core.DeclusorParser(manager, name="declusor").parse()

    assert options["plugin"].kind == testing.DummyClientPlugin.name
