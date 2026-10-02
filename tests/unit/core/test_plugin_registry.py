from declusor import core, testing


def test_registries_are_isolated() -> None:
    """Registering a plugin must not affect another registry instance."""

    first = core.PluginRegistry()
    second = core.PluginRegistry()

    first.register(testing.DummyPlugin)

    assert first.names() == (testing.DummyPlugin.name,)
    assert second.names() == ()


def test_parser_uses_injected_manager() -> None:
    """The parser must resolve plugins only from its injected manager."""

    manager = core.PluginManager()
    manager.register(testing.DummyPlugin)

    plugin_config = core.DeclusorParser(name="declusor").parse(
        manager,
        ["127.0.0.1", "9000", "--plugin", testing.DummyPlugin.name],
    )

    assert plugin_config.kind == testing.DummyPlugin.name
