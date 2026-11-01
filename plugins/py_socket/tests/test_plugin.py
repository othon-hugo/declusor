"""Unit tests verifying PySocketPlugin parser configuration, config builder, and runtime creation."""

from pathlib import Path

import pytest
from declusor import config, contract, testing

import declusor_py_socket as py_socket


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
        (launchers / "py_socket_stager.py").write_text("import socket", encoding="utf-8")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        options = py_socket.PySocketPlugin.extract_options({})
        cfg = py_socket.PySocketPlugin.build_config("127.0.0.1", 9000, options, filesystem=fs)

        assert cfg.filesystem == fs
        py_socket.PySocketPlugin.validate(cfg)

    def test_validate__missing_client_launcher_file__raises_parser_error(self, tmp_path: Path) -> None:
        """Verify plugin configuration validation raises ParserError when client launcher file is missing."""

        fs = contract.PluginFilesystem.from_root(tmp_path)
        options = py_socket.PySocketPlugin.extract_options({})
        cfg = py_socket.PySocketPlugin.build_config("127.0.0.1", 9000, options, filesystem=fs)

        with pytest.raises(config.ParserError, match="Client launcher file does not exist"):
            py_socket.PySocketPlugin.validate(cfg)

    def test_validate__missing_stager_launcher_file_when_staged__raises_parser_error(self, tmp_path: Path) -> None:
        """Verify plugin validation raises ParserError when stager file is missing for staged launcher."""

        launchers = tmp_path / "launchers"
        launchers.mkdir()
        (launchers / "py_socket_client.py").write_text("#!/usr/bin/env python3", encoding="utf-8")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        options = py_socket.PySocketPlugin.extract_options({})
        cfg = py_socket.PySocketPlugin.build_config("127.0.0.1", 9000, options, filesystem=fs)

        with pytest.raises(config.ParserError, match="Stager launcher file does not exist"):
            py_socket.PySocketPlugin.validate(cfg)


class TestPySocketPluginRuntime:
    """Verify PySocketPlugin runtime creation and asset delivery."""

    def test_build_runtime__renders_bundled_staged_launcher_by_default(self) -> None:
        """Verify default bundled stager renders with substituted parameters."""

        options = py_socket.PySocketPlugin.extract_options({})
        cfg = py_socket.PySocketPlugin.build_config("192.168.1.50", 5555, options)
        runtime = py_socket.PySocketPlugin.build_runtime(cfg)

        delivery = runtime.launcher
        assert isinstance(delivery, contract.LauncherDelivery)
        assert delivery.kind == config.LauncherKind.STAGED
        assert delivery.wrapper_template == py_socket.PySocketRuntime.STAGED_WRAPPER_TEMPLATE
        assert delivery.wrapped_text == f"python3 -c '{delivery.text}'"
        assert "192.168.1.50" in delivery.text
        assert "5555" in delivery.text
        assert "$DECLUSOR_HOST" not in delivery.text
        assert "$DECLUSOR_PORT" not in delivery.text

    def test_build_runtime__renders_bundled_stageless_launcher__substitutes_connection_parameters(self) -> None:
        """Verify stageless launcher renders with hex-encoded payload."""

        import dataclasses

        options = py_socket.PySocketPlugin.extract_options({})
        base_cfg = py_socket.PySocketPlugin.build_config("192.168.1.50", 5555, options)
        cfg = dataclasses.replace(base_cfg, launcher_kind=config.LauncherKind.STAGELESS)
        runtime = py_socket.PySocketPlugin.build_runtime(cfg)

        delivery = runtime.launcher
        assert isinstance(delivery, contract.LauncherDelivery)
        assert delivery.kind == config.LauncherKind.STAGELESS
        assert delivery.wrapper_template == py_socket.PySocketRuntime.DEFAULT_WRAPPER_TEMPLATE
        assert "bytes.fromhex(" in delivery.wrapped_text
        assert delivery.text in delivery.wrapped_text

        decoded = bytes.fromhex(delivery.text).decode("utf-8")
        assert "192.168.1.50" in decoded
        assert "5555" in decoded
        assert "$HOST" not in decoded
        assert "$PORT" not in decoded
        assert "$ACKNOWLEDGE" not in decoded
        assert "$DECLUSOR_HOST" not in decoded
        assert "$DECLUSOR_PORT" not in decoded
        assert "$DECLUSOR_ACK" not in decoded

    def test_build_runtime__creates_connection__returns_py_socket_connection_instance(self) -> None:
        """Verify runtime creates a valid py_socket.PySocketConnection instance."""

        options = py_socket.PySocketPlugin.extract_options({})
        cfg = py_socket.PySocketPlugin.build_config("127.0.0.1", 9000, options)
        dummy_trans = testing.DummyTransport(peer_address="127.0.0.1:9000")

        runtime = py_socket.PySocketPlugin.build_runtime(cfg)
        client_connection = runtime.create_connection(dummy_trans)

        assert isinstance(client_connection, py_socket.PySocketConnection)
