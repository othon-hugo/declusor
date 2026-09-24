"""Unit tests for ClientRegistry isolation and DeclusorParser client selection."""

import pytest

from declusor import core
from declusor.testing import DummyClientPlugin


def test_registries_are_isolated() -> None:
    """Registering a plugin must not affect another registry instance."""
    first = core.ClientRegistry()
    second = core.ClientRegistry()

    first.register(DummyClientPlugin)

    assert first.names() == (DummyClientPlugin.name,)
    assert second.names() == ()


def test_parser_uses_injected_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """The parser must resolve clients only from its injected registry."""
    registry = core.ClientRegistry()
    registry.register(DummyClientPlugin)
    monkeypatch.setattr(
        "sys.argv",
        ["declusor", "127.0.0.1", "9000", "--client", DummyClientPlugin.name],
    )

    options = core.DeclusorParser(registry, name="declusor").parse()

    assert options["client"].kind == DummyClientPlugin.name
