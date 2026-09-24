import pytest

from declusor import core, testing


def test_registries_are_isolated() -> None:
    """Registering a plugin must not affect another registry instance."""

    first = core.ClientPluginRegistry()
    second = core.ClientPluginRegistry()

    first.register(testing.DummyClientPlugin)

    assert first.names() == (testing.DummyClientPlugin.name,)
    assert second.names() == ()


def test_parser_uses_injected_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """The parser must resolve clients only from its injected registry."""

    registry = core.ClientPluginRegistry()
    registry.register(testing.DummyClientPlugin)
    monkeypatch.setattr(
        "sys.argv",
        ["declusor", "127.0.0.1", "9000", "--client", testing.DummyClientPlugin.name],
    )

    options = core.DeclusorParser(registry, name="declusor").parse()

    assert options["client"].kind == testing.DummyClientPlugin.name
