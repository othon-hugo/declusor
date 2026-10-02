from pathlib import Path

from declusor import config, contract


def test_plugin_config_default_mode(tmp_path: Path) -> None:
    """Verify PluginConfig defaults mode to config.DEFAULT_EXECUTION_MODE."""

    fs = contract.PluginFilesystem.from_root(tmp_path)
    plugin_config = contract.PluginConfig(
        kind="dummy",
        host="127.0.0.1",
        port=9000,
        options=contract.ParsedArguments(),
        options_type=contract.ParsedArguments,
        filesystem=fs,
    )

    assert plugin_config.mode == config.ExecutionMode.CLI
    assert plugin_config.mode == config.DEFAULT_EXECUTION_MODE
    assert plugin_config.kind == "dummy"
    assert plugin_config.host == "127.0.0.1"
    assert plugin_config.port == 9000
    assert plugin_config.filesystem == fs


def test_plugin_config_explicit_mode(tmp_path: Path) -> None:
    """Verify PluginConfig accepts explicit execution mode."""

    fs = contract.PluginFilesystem.from_root(tmp_path)
    plugin_config = contract.PluginConfig(
        kind="dummy",
        host="127.0.0.1",
        port=9000,
        options=contract.ParsedArguments(),
        options_type=contract.ParsedArguments,
        filesystem=fs,
        mode=config.ExecutionMode.MCP,
    )

    assert plugin_config.mode == config.ExecutionMode.MCP
