import argparse

from declusor import config, contract


def test_plugin_config_default_mode() -> None:
    """Verify PluginConfig defaults mode to Settings.DEFAULT_EXECUTION_MODE."""

    plugin_config = contract.PluginConfig(kind="dummy", host="127.0.0.1", port=9000)
    assert plugin_config.mode == config.ExecutionMode.CLI
    assert plugin_config.mode == config.Settings.DEFAULT_EXECUTION_MODE


def test_plugin_config_explicit_mode() -> None:
    """Verify PluginConfig accepts explicit execution mode."""

    plugin_config = contract.PluginConfig(
        kind="dummy",
        host="127.0.0.1",
        port=9000,
        mode=config.ExecutionMode.MCP,
    )
    assert plugin_config.mode == config.ExecutionMode.MCP


def test_plugin_namespace_default_mode() -> None:
    """Verify PluginNamespace defaults mode to Settings.DEFAULT_EXECUTION_MODE."""

    ns = contract.PluginNamespace(host="127.0.0.1", port=9000)
    assert ns.mode == config.ExecutionMode.CLI


def test_plugin_namespace_from_argparse_namespace() -> None:
    """Verify PluginNamespace.from_namespace maps mode correctly."""

    raw_ns = argparse.Namespace(host="127.0.0.1", port=9000, mode=config.ExecutionMode.HTTP)
    ns = contract.PluginNamespace.from_namespace(raw_ns)
    assert ns.mode == config.ExecutionMode.HTTP
