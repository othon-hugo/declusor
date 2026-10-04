from pathlib import Path

import declusor_py_socket as py_socket
import pytest

from declusor import config, contract, testing


class TestPySocketPluginConfig:
    """Verify PySocketPlugin configuration extraction, creation, and validation."""

    def test_build_config__default_assets__uses_bundled_assets(self) -> None:
        """When filesystem is None, plugin builds default PluginFilesystem from bundled assets."""

        options = py_socket.PySocketPlugin.extract_options({})
        cfg = py_socket.PySocketPlugin.build_config("127.0.0.1", 9000, options)

        assert cfg.kind == "py_socket"
        assert cfg.host == "127.0.0.1"
        assert cfg.port == 9000
        assert cfg.filesystem is not None
        py_socket.PySocketPlugin.validate(cfg)

    def test_build_config__custom_filesystem__resolves_against_custom_filesystem(self, tmp_path: Path) -> None:
        """When custom filesystem is provided, plugin resolves against that filesystem."""

        launchers = tmp_path / "launchers"
        launchers.mkdir()
        (launchers / "py_socket_client.py").write_text("#!/usr/bin/env python3", encoding="utf-8")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        options = py_socket.PySocketPlugin.extract_options({})
        cfg = py_socket.PySocketPlugin.build_config("127.0.0.1", 9000, options, filesystem=fs)

        assert cfg.filesystem == fs
        py_socket.PySocketPlugin.validate(cfg)

    def test_validate__missing_launcher_file__raises_parser_error(self, tmp_path: Path) -> None:
        """Verify plugin configuration validation raises ParserError when launcher file is missing."""

        fs = contract.PluginFilesystem.from_root(tmp_path)
        options = py_socket.PySocketPlugin.extract_options({})
        cfg = py_socket.PySocketPlugin.build_config("127.0.0.1", 9000, options, filesystem=fs)

        with pytest.raises(config.ParserError, match="Client launcher file does not exist"):
            py_socket.PySocketPlugin.validate(cfg)


class TestPySocketPluginRuntime:
    """Verify PySocketPlugin runtime creation and asset delivery."""

    def test_build_runtime__renders_bundled_launcher__substitutes_connection_parameters(self) -> None:
        """Verify default bundled py_socket_client.py renders with substituted values."""

        options = py_socket.PySocketPlugin.extract_options({})
        cfg = py_socket.PySocketPlugin.build_config("192.168.1.50", 5555, options)
        runtime = py_socket.PySocketPlugin.build_runtime(cfg)

        delivery = runtime.launcher
        assert isinstance(delivery, contract.LauncherDelivery)
        script = delivery.text
        assert "192.168.1.50" in script
        assert "5555" in script
        assert "$HOST" not in script
        assert "$PORT" not in script
        assert "$ACKNOWLEDGE" not in script
        assert "$DECLUSOR_HOST" not in script
        assert "$DECLUSOR_PORT" not in script
        assert "$DECLUSOR_ACKNOWLEDGE" not in script

    def test_build_runtime__creates_connection__returns_py_socket_connection_instance(self) -> None:
        """Verify runtime creates a valid py_socket.PySocketConnection instance."""

        options = py_socket.PySocketPlugin.extract_options({})
        cfg = py_socket.PySocketPlugin.build_config("127.0.0.1", 9000, options)
        dummy_trans = testing.DummyTransport(peer_address="127.0.0.1:9000")

        runtime = py_socket.PySocketPlugin.build_runtime(cfg)
        client_connection = runtime.create_connection(dummy_trans)

        assert isinstance(client_connection, py_socket.PySocketConnection)
