from pathlib import Path
from socket import socket
from typing import cast

import declusor_shell_socket as shell_socket

from declusor import config, contract, testing


def test_shell_socket_plugin_metadata() -> None:
    """Verify shell_socket.ShellSocketPlugin metadata properties (name, description, version)."""

    assert shell_socket.ShellSocketPlugin.name == "shell_socket"
    assert shell_socket.ShellSocketPlugin.description != ""
    assert shell_socket.ShellSocketPlugin.version == "1.0.0"


def test_build_config_uses_bundled_assets_when_data_paths_is_none() -> None:
    """When data_paths is None, plugin must cleanly resolve bundled ASSETS_DIR."""

    args = contract.PluginNamespace(host="127.0.0.1", port=9000)
    cfg = shell_socket.ShellSocketPlugin.build_config(args, None)

    assert cfg.options["launcher_path"] == shell_socket.plugin.ASSETS_DIR / "launchers" / "shell_socket_client.sh"
    assert cfg.options["helpers_dir"] == shell_socket.plugin.ASSETS_DIR / "helpers"
    assert cfg.options["modules_dir"] == shell_socket.plugin.ASSETS_DIR / "modules"
    assert cfg.data_paths is None

    shell_socket.ShellSocketPlugin.validate(cfg)


def test_build_config_resolves_custom_data_paths_when_provided(tmp_path: Path) -> None:
    """When custom data_paths is provided, plugin resolves against client namespace."""

    custom_launcher = tmp_path / "shell_socket" / "launchers" / "shell_socket_client.sh"
    custom_launcher.parent.mkdir(parents=True)
    custom_launcher.write_text("# custom launcher", encoding="utf-8")

    data_paths = config.DataPaths.from_root(tmp_path)
    args = contract.PluginNamespace(host="127.0.0.1", port=9000)
    cfg = shell_socket.ShellSocketPlugin.build_config(args, data_paths)

    assert cfg.options["launcher_path"] == custom_launcher
    assert cfg.data_paths == data_paths

    shell_socket.ShellSocketPlugin.validate(cfg)


def test_build_runtime_renders_configured_client_script(tmp_path: Path) -> None:
    """Verify shell_socket.ShellSocketPlugin.build_runtime renders client script with substituted parameters."""

    client_path = tmp_path / "client.sh"
    client_path.write_text("connect $DECLUSOR_HOST:$DECLUSOR_PORT ack=$DECLUSOR_ACKNOWLEDGE", encoding="utf-8")
    plugin_config = contract.PluginConfig(
        kind=shell_socket.ShellSocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={
            "launcher_path": client_path,
            "helpers_dir": tmp_path / "helpers",
            "modules_dir": tmp_path / "modules",
        },
    )

    runtime = shell_socket.ShellSocketPlugin.build_runtime(plugin_config)
    assert runtime.client_script.startswith("connect 127.0.0.1:9000 ack=\\x")


def test_build_runtime_renders_bundled_launcher_with_declusor_prefix() -> None:
    """Verify default bundled shell_socket_client.sh renders with substituted values."""

    args = contract.PluginNamespace(host="192.168.1.50", port=5555)
    cfg = shell_socket.ShellSocketPlugin.build_config(args, None)
    runtime = shell_socket.ShellSocketPlugin.build_runtime(cfg)

    script = runtime.client_script
    assert "/dev/tcp/192.168.1.50/5555" in script
    assert "$DECLUSOR_HOST" not in script
    assert "$DECLUSOR_PORT" not in script
    assert "$DECLUSOR_ACKNOWLEDGE" not in script
    assert "$data" in script  # Runtime bash variable is preserved


def test_build_runtime_creates_shell_socket_connection(tmp_path: Path) -> None:
    """Verify runtime creates a valid shell_socket.ShellSocketConnection instance."""

    client_path = tmp_path / "client.sh"
    client_path.write_text("$DECLUSOR_HOST:$DECLUSOR_PORT", encoding="utf-8")

    plugin_config = contract.PluginConfig(
        kind=shell_socket.ShellSocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={
            "launcher_path": client_path,
            "helpers_dir": tmp_path / "helpers",
            "modules_dir": tmp_path / "modules",
        },
    )

    dummy_sock = testing.DummySocket(peer_name=("127.0.0.1", 9000))

    runtime = shell_socket.ShellSocketPlugin.build_runtime(plugin_config)
    client_connection = runtime.create_connection(cast(socket, dummy_sock))

    assert isinstance(client_connection, shell_socket.ShellSocketConnection)
