import dataclasses
from pathlib import Path

import declusor_shell_socket as shell_socket
import pytest

from declusor import config, contract, testing


class TestShellSocketPluginConfig:
    """Verify ShellSocketPlugin configuration extraction, creation, and validation."""

    def test_build_config__default_assets__uses_bundled_assets(self) -> None:
        """When filesystem is None, plugin builds default PluginFilesystem from bundled assets."""

        options = shell_socket.ShellSocketPlugin.extract_options({})
        cfg = shell_socket.ShellSocketPlugin.build_config("127.0.0.1", 9000, options)

        assert cfg.kind == "shell_socket"
        assert cfg.host == "127.0.0.1"
        assert cfg.port == 9000
        assert cfg.filesystem is not None
        shell_socket.ShellSocketPlugin.validate(cfg)

    def test_build_config__custom_filesystem__resolves_against_custom_filesystem(self, tmp_path: Path) -> None:
        """When custom filesystem is provided, plugin resolves against that filesystem."""

        launchers = tmp_path / "launchers"
        launchers.mkdir()
        (launchers / "shell_socket_client.sh").write_text("#!/bin/sh", encoding="utf-8")
        (launchers / "shell_socket_stager.sh").write_text("#!/bin/sh", encoding="utf-8")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        options = shell_socket.ShellSocketPlugin.extract_options({})
        cfg = shell_socket.ShellSocketPlugin.build_config("127.0.0.1", 9000, options, filesystem=fs)

        assert cfg.filesystem == fs
        shell_socket.ShellSocketPlugin.validate(cfg)

    def test_validate__missing_client_launcher_file__raises_parser_error(self, tmp_path: Path) -> None:
        """Verify plugin configuration validation raises ParserError when client launcher file is missing."""

        fs = contract.PluginFilesystem.from_root(tmp_path)
        options = shell_socket.ShellSocketPlugin.extract_options({})
        cfg = shell_socket.ShellSocketPlugin.build_config("127.0.0.1", 9000, options, filesystem=fs)

        with pytest.raises(config.ParserError, match="Client launcher file does not exist"):
            shell_socket.ShellSocketPlugin.validate(cfg)

    def test_validate__missing_stager_launcher_file_when_staged__raises_parser_error(self, tmp_path: Path) -> None:
        """Verify plugin validation raises ParserError when stager file is missing for staged launcher."""

        launchers = tmp_path / "launchers"
        launchers.mkdir()
        (launchers / "shell_socket_client.sh").write_text("#!/bin/sh", encoding="utf-8")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        options = shell_socket.ShellSocketPlugin.extract_options({})
        cfg = shell_socket.ShellSocketPlugin.build_config("127.0.0.1", 9000, options, filesystem=fs)

        with pytest.raises(config.ParserError, match="Stager launcher file does not exist"):
            shell_socket.ShellSocketPlugin.validate(cfg)


class TestShellSocketPluginRuntime:
    """Verify ShellSocketPlugin runtime creation and asset delivery."""

    def test_build_runtime__renders_bundled_staged_launcher_by_default(self) -> None:
        """Verify default bundled stager renders with substituted parameters."""

        options = shell_socket.ShellSocketPlugin.extract_options({})
        cfg = shell_socket.ShellSocketPlugin.build_config("192.168.1.50", 5555, options)
        runtime = shell_socket.ShellSocketPlugin.build_runtime(cfg)

        delivery = runtime.launcher
        assert isinstance(delivery, contract.LauncherDelivery)
        assert delivery.kind == config.LauncherKind.STAGED
        assert delivery.wrapper_template == shell_socket.ShellSocketRuntime.STAGED_WRAPPER_TEMPLATE
        assert delivery.wrapped_text == f"bash -c '{delivery.text}'"
        assert "192.168.1.50" in delivery.text
        assert "5555" in delivery.text
        assert "$DECLUSOR_HOST" not in delivery.text
        assert "$DECLUSOR_PORT" not in delivery.text

    def test_build_runtime__renders_bundled_stageless_launcher__substitutes_connection_parameters(self) -> None:
        """Verify stageless launcher renders with hex-encoded payload."""

        options = shell_socket.ShellSocketPlugin.extract_options({})
        base_cfg = shell_socket.ShellSocketPlugin.build_config("192.168.1.50", 5555, options)
        cfg = dataclasses.replace(base_cfg, launcher_kind=config.LauncherKind.STAGELESS)
        runtime = shell_socket.ShellSocketPlugin.build_runtime(cfg)

        delivery = runtime.launcher
        assert isinstance(delivery, contract.LauncherDelivery)
        assert delivery.kind == config.LauncherKind.STAGELESS
        assert delivery.wrapper_template == shell_socket.ShellSocketRuntime.DEFAULT_WRAPPER_TEMPLATE
        assert "bash -c '" in delivery.wrapped_text
        assert "while IFS= read -r -n2 byte" in delivery.wrapped_text
        assert delivery.text in delivery.wrapped_text

        decoded = bytes.fromhex(delivery.text).decode("utf-8")
        assert "/dev/tcp/192.168.1.50/5555" in decoded
        assert "$DECLUSOR_HOST" not in decoded
        assert "$DECLUSOR_PORT" not in decoded
        assert "$DECLUSOR_ACK" not in decoded
        assert "$data" in decoded

    def test_build_runtime__creates_connection__returns_shell_socket_connection_instance(self) -> None:
        """Verify runtime creates a valid shell_socket.ShellSocketConnection instance."""

        options = shell_socket.ShellSocketPlugin.extract_options({})
        cfg = shell_socket.ShellSocketPlugin.build_config("127.0.0.1", 9000, options)
        dummy_trans = testing.DummyTransport(peer_address="127.0.0.1:9000")

        runtime = shell_socket.ShellSocketPlugin.build_runtime(cfg)
        client_connection = runtime.create_connection(dummy_trans)

        assert isinstance(client_connection, shell_socket.ShellSocketConnection)
