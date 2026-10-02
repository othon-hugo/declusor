from pathlib import Path

import declusor_shell_socket as shell_socket

from declusor import contract, testing


def test_build_config_uses_default_assets_when_filesystem_is_none() -> None:
    """When filesystem is None, plugin builds default PluginFilesystem from bundled assets."""

    options = shell_socket.ShellSocketPlugin.extract_options({})
    cfg = shell_socket.ShellSocketPlugin.build_config("127.0.0.1", 9000, options)

    assert cfg.kind == "shell_socket"
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 9000
    assert cfg.filesystem is not None
    shell_socket.ShellSocketPlugin.validate(cfg)


def test_build_config_uses_custom_filesystem_when_provided(tmp_path: Path) -> None:
    """When custom filesystem is provided, plugin resolves against that filesystem."""

    launchers = tmp_path / "launchers"
    launchers.mkdir()
    (launchers / "shell_socket_client.sh").write_text("#!/bin/sh", encoding="utf-8")

    fs = contract.PluginFilesystem.from_root(tmp_path)
    options = shell_socket.ShellSocketPlugin.extract_options({})
    cfg = shell_socket.ShellSocketPlugin.build_config("127.0.0.1", 9000, options, filesystem=fs)

    assert cfg.filesystem == fs
    shell_socket.ShellSocketPlugin.validate(cfg)


def test_build_runtime_renders_bundled_launcher_with_parameters() -> None:
    """Verify default bundled shell_socket_client.sh renders with substituted values."""

    options = shell_socket.ShellSocketPlugin.extract_options({})
    cfg = shell_socket.ShellSocketPlugin.build_config("192.168.1.50", 5555, options)
    runtime = shell_socket.ShellSocketPlugin.build_runtime(cfg)

    delivery = runtime.launcher
    assert isinstance(delivery, contract.LauncherDelivery)
    script = delivery.text
    assert "/dev/tcp/192.168.1.50/5555" in script
    assert "$DECLUSOR_HOST" not in script
    assert "$DECLUSOR_PORT" not in script
    assert "$DECLUSOR_ACKNOWLEDGE" not in script
    assert "$data" in script  # Runtime bash variable is preserved


def test_build_runtime_creates_shell_socket_connection() -> None:
    """Verify runtime creates a valid shell_socket.ShellSocketConnection instance."""

    options = shell_socket.ShellSocketPlugin.extract_options({})
    cfg = shell_socket.ShellSocketPlugin.build_config("127.0.0.1", 9000, options)
    dummy_trans = testing.DummyTransport(peer_address="127.0.0.1:9000")

    runtime = shell_socket.ShellSocketPlugin.build_runtime(cfg)
    client_connection = runtime.create_connection(dummy_trans)

    assert isinstance(client_connection, shell_socket.ShellSocketConnection)
