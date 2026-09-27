from pathlib import Path

import declusor_py_socket as py_socket
import pytest

from declusor import config, contract, testing


def test_py_socket_plugin_metadata() -> None:
    """Verify py_socket.PySocketPlugin metadata properties (name, description, version)."""

    assert py_socket.PySocketPlugin.name == "py_socket"
    assert py_socket.PySocketPlugin.description != ""
    assert py_socket.PySocketPlugin.version == "1.0.0"


def test_extract_options_returns_typed_dict() -> None:
    """Verify extract_options returns a PySocketConfig instance."""

    raw: dict[str, object] = {}
    options = py_socket.PySocketPlugin.extract_options(raw)

    assert isinstance(options, dict)


def test_build_config_uses_default_assets_when_filesystem_is_none() -> None:
    """When filesystem is None, plugin builds default PluginFilesystem from bundled assets."""

    options = py_socket.PySocketPlugin.extract_options({})
    cfg = py_socket.PySocketPlugin.build_config("127.0.0.1", 9000, options)

    assert cfg.kind == "py_socket"
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 9000
    assert cfg.filesystem is not None
    py_socket.PySocketPlugin.validate(cfg)


def test_build_config_uses_custom_filesystem_when_provided(tmp_path: Path) -> None:
    """When custom filesystem is provided, plugin resolves against that filesystem."""

    launchers = tmp_path / "launchers"
    launchers.mkdir()
    (launchers / "py_socket_client.py").write_text("#!/usr/bin/env python3", encoding="utf-8")

    fs = contract.PluginFilesystem.from_root(tmp_path)
    options = py_socket.PySocketPlugin.extract_options({})
    cfg = py_socket.PySocketPlugin.build_config("127.0.0.1", 9000, options, filesystem=fs)

    assert cfg.filesystem == fs
    py_socket.PySocketPlugin.validate(cfg)


def test_validate_raises_when_launcher_missing(tmp_path: Path) -> None:
    """Verify plugin configuration validation raises ParserError when launcher file is missing."""

    fs = contract.PluginFilesystem.from_root(tmp_path)
    options = py_socket.PySocketPlugin.extract_options({})
    cfg = py_socket.PySocketPlugin.build_config("127.0.0.1", 9000, options, filesystem=fs)

    with pytest.raises(config.ParserError, match="Client launcher file does not exist"):
        py_socket.PySocketPlugin.validate(cfg)


def test_build_runtime_renders_bundled_launcher_with_parameters() -> None:
    """Verify default bundled py_socket_client.py renders with substituted values."""

    options = py_socket.PySocketPlugin.extract_options({})
    cfg = py_socket.PySocketPlugin.build_config("192.168.1.50", 5555, options)
    runtime = py_socket.PySocketPlugin.build_runtime(cfg)

    script = runtime.launcher
    assert "192.168.1.50" in script
    assert "5555" in script
    assert "$HOST" not in script
    assert "$PORT" not in script
    assert "$ACKNOWLEDGE" not in script


def test_build_runtime_creates_py_socket_connection() -> None:
    """Verify runtime creates a valid py_socket.PySocketConnection instance."""

    options = py_socket.PySocketPlugin.extract_options({})
    cfg = py_socket.PySocketPlugin.build_config("127.0.0.1", 9000, options)
    dummy_trans = testing.DummyTransport(peer_address="127.0.0.1:9000")

    runtime = py_socket.PySocketPlugin.build_runtime(cfg)
    client_connection = runtime.create_connection(dummy_trans)

    assert isinstance(client_connection, py_socket.PySocketConnection)
