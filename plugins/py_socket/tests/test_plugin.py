from pathlib import Path
from socket import socket
from typing import cast

import declusor_py_socket as py_socket
import pytest

from declusor import config, contract, testing, util


def test_build_config_uses_bundled_assets_when_data_paths_is_none() -> None:
    """When data_paths is None, plugin must cleanly resolve bundled ASSETS_DIR."""

    args = util.Namespace(host="127.0.0.1", port=9000)
    cfg = py_socket.PySocketPlugin.build_config(args, None)

    assert cfg.options["launcher_path"] == py_socket.plugin.ASSETS_DIR / "launchers" / "py_socket_client.py"
    assert cfg.options["helpers_dir"] == py_socket.plugin.ASSETS_DIR / "helpers"
    assert cfg.options["modules_dir"] == py_socket.plugin.ASSETS_DIR / "modules"
    assert cfg.data_paths is None
    py_socket.PySocketPlugin.validate(cfg)


def test_build_config_resolves_custom_data_paths_when_provided(tmp_path: Path) -> None:
    """When custom data_paths is provided, plugin resolves against client namespace."""

    custom_launcher = tmp_path / "py_socket" / "launchers" / "py_socket_client.py"
    custom_launcher.parent.mkdir(parents=True)
    custom_launcher.write_text("# custom launcher", encoding="utf-8")

    data_paths = config.DataPaths.from_root(tmp_path)
    args = util.Namespace(host="127.0.0.1", port=9000)
    cfg = py_socket.PySocketPlugin.build_config(args, data_paths)

    assert cfg.options["launcher_path"] == custom_launcher
    assert cfg.data_paths == data_paths
    py_socket.PySocketPlugin.validate(cfg)


def test_build_runtime_renders_configured_client_script(tmp_path: Path) -> None:
    """Verify PySocketPlugin.build_runtime renders launcher script with host, port, and ACK."""

    launcher = tmp_path / "py_socket_client.py"
    launcher.write_text("HOST = '$HOST'\nPORT = int('$PORT')\nACK = bytes.fromhex('$ACKNOWLEDGE')")

    plugin_config = contract.PluginConfig(
        kind=py_socket.PySocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={
            "launcher_path": launcher,
            "helpers_dir": tmp_path / "helpers",
            "modules_dir": tmp_path / "modules",
        },
    )

    runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)
    assert "127.0.0.1" in runtime.client_script
    assert "9000" in runtime.client_script


def test_build_runtime_creates_py_socket_connection(tmp_path: Path) -> None:
    """Verify runtime creates a valid PySocketConnection instance for connected sockets."""

    launcher = tmp_path / "py_socket_client.py"
    launcher.write_text("HOST = '$HOST'\nPORT = int('$PORT')\nACK = bytes.fromhex('$ACKNOWLEDGE')")

    plugin_config = contract.PluginConfig(
        kind=py_socket.PySocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={
            "launcher_path": launcher,
            "helpers_dir": tmp_path / "helpers",
            "modules_dir": tmp_path / "modules",
        },
    )

    runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)
    dummy_sock = testing.DummySocket()
    conn = runtime.create_connection(cast(socket, dummy_sock))
    assert isinstance(conn, py_socket.PySocketConnection)


def test_validate_passes_when_launcher_exists(tmp_path: Path) -> None:
    """Verify plugin configuration validation succeeds when launcher file exists."""

    launcher = tmp_path / "py_socket_client.py"
    launcher.write_text("# launcher")

    plugin_config = contract.PluginConfig(
        kind=py_socket.PySocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={"launcher_path": launcher},
    )

    py_socket.PySocketPlugin.validate(plugin_config)


def test_validate_raises_when_launcher_missing(tmp_path: Path) -> None:
    """Verify plugin configuration validation raises ParserError when launcher file is missing."""

    plugin_config = contract.PluginConfig(
        kind=py_socket.PySocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={"launcher_path": tmp_path / "nonexistent.py"},
    )

    with pytest.raises(config.ParserError, match="Client launcher file does not exist"):
        py_socket.PySocketPlugin.validate(plugin_config)
