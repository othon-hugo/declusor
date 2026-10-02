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


def test_plugin_config_launcher_defaults(tmp_path: Path) -> None:
    """Verify PluginConfig defaults launcher delivery options."""

    fs = contract.PluginFilesystem.from_root(tmp_path)
    plugin_config = contract.PluginConfig(
        kind="dummy",
        host="127.0.0.1",
        port=9000,
        options=contract.ParsedArguments(),
        options_type=contract.ParsedArguments,
        filesystem=fs,
    )

    assert plugin_config.launcher_output_mode == config.LauncherOutputMode.TERMINAL
    assert plugin_config.launcher_output_mode == config.DEFAULT_LAUNCHER_OUTPUT_MODE
    assert plugin_config.launcher_output_path is None
    assert plugin_config.launcher_wrapper is None


def test_launcher_delivery_defaults() -> None:
    """Verify LauncherDelivery default attributes."""

    delivery = contract.LauncherDelivery(script=b"echo hello")

    assert delivery.script == b"echo hello"
    assert delivery.output_mode == config.LauncherOutputMode.TERMINAL
    assert delivery.output_path is None
    assert delivery.wrapper_template is None
    assert delivery.text == "echo hello"
    assert str(delivery) == "echo hello"


def test_launcher_delivery_file_mode_with_path(tmp_path: Path) -> None:
    """Verify LauncherDelivery allows FILE mode when output_path is provided."""

    target_file = tmp_path / "launcher.sh"
    delivery = contract.LauncherDelivery(
        script=b"echo hello",
        output_mode=config.LauncherOutputMode.FILE,
        output_path=target_file,
    )

    assert delivery.output_mode == config.LauncherOutputMode.FILE
    assert delivery.output_path == target_file


def test_launcher_delivery_file_mode_without_path_raises() -> None:
    """Verify LauncherDelivery rejects FILE mode when output_path is None."""

    import pytest

    with pytest.raises(config.DeclusorException, match="output_path must be set when output_mode is FILE"):
        contract.LauncherDelivery(
            script=b"echo hello",
            output_mode=config.LauncherOutputMode.FILE,
            output_path=None,
        )


def test_launcher_delivery_non_file_mode_with_path_raises(tmp_path: Path) -> None:
    """Verify LauncherDelivery rejects output_path when output_mode is not FILE."""

    import pytest

    with pytest.raises(config.DeclusorException, match="output_path is only valid when output_mode is FILE"):
        contract.LauncherDelivery(
            script=b"echo hello",
            output_mode=config.LauncherOutputMode.TERMINAL,
            output_path=tmp_path / "out.sh",
        )
