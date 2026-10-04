import base64
from pathlib import Path

import declusor_shell_socket as shell_socket
import pytest

from declusor import config, contract


class TestShellSocketProcessor:
    """Tests for ShellSocketProcessor asset loading, traversal prevention, and stager rendering."""

    def test_load_all_helpers__valid_directory__returns_mapping(self, tmp_path: Path) -> None:
        """Verify load_all_helpers loads all valid shell helper scripts into a mapping."""

        helpers = tmp_path / "helpers"
        helpers.mkdir(parents=True)
        (helpers / "common.sh").write_bytes(b"echo common")
        (helpers / "network.sh").write_bytes(b"echo network")
        (helpers / "ignored.txt").write_bytes(b"ignored")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = shell_socket.ShellSocketProcessor(fs)

        loaded = processor.load_all_helpers()

        assert loaded == {
            "common.sh": b"echo common",
            "network.sh": b"echo network",
        }

    def test_load_all_helpers__missing_directory__returns_empty_mapping(self, tmp_path: Path) -> None:
        """Verify load_all_helpers returns empty dictionary when helpers directory does not exist."""

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = shell_socket.ShellSocketProcessor(fs)

        assert processor.load_all_helpers() == {}

    def test_load_helper__valid_name__returns_file_bytes(self, tmp_path: Path) -> None:
        """Verify load_helper loads a specific helper library by name."""

        helpers = tmp_path / "helpers"
        helpers.mkdir(parents=True)
        (helpers / "util.sh").write_bytes(b"echo util")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = shell_socket.ShellSocketProcessor(fs)

        assert processor.load_helper("util.sh") == b"echo util"

    def test_load_helper__relative_path_traversal__raises_invalid_operation(self, tmp_path: Path) -> None:
        """Verify load_helper rejects relative dot-dot path traversal attempts."""

        helpers = tmp_path / "helpers"
        helpers.mkdir(parents=True)
        (tmp_path / "secret.sh").write_bytes(b"secret")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = shell_socket.ShellSocketProcessor(fs)

        with pytest.raises(config.InvalidOperation, match="outside permitted directory"):
            processor.load_helper("../secret.sh")

    def test_load_helper__absolute_path_traversal__raises_invalid_operation(self, tmp_path: Path) -> None:
        """Verify load_helper rejects absolute path outside the permitted helpers directory."""

        helpers = tmp_path / "helpers"
        helpers.mkdir(parents=True)
        secret_file = tmp_path / "secret.sh"
        secret_file.write_bytes(b"secret")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = shell_socket.ShellSocketProcessor(fs)

        with pytest.raises(config.InvalidOperation, match="outside permitted directory"):
            processor.load_helper(str(secret_file))

    def test_helpers__concatenates_all_helpers(self, tmp_path: Path) -> None:
        """Verify helpers property concatenates all helper library scripts."""

        helpers = tmp_path / "helpers"
        helpers.mkdir(parents=True)
        (helpers / "a.sh").write_bytes(b"echo a")
        (helpers / "b.sh").write_bytes(b"echo b")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = shell_socket.ShellSocketProcessor(fs)

        assert processor.helpers == b"echo a\necho b"

    def test_load_module__valid_name__returns_file_bytes(self, tmp_path: Path) -> None:
        """Verify load_module reads modules from the designated modules directory."""

        modules = tmp_path / "modules"
        modules.mkdir(parents=True)
        (modules / "info.sh").write_bytes(b"echo info")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = shell_socket.ShellSocketProcessor(fs)

        assert processor.load_module("info.sh") == b"echo info"

    def test_load_module__relative_and_absolute_traversal__raises_invalid_operation(self, tmp_path: Path) -> None:
        """Verify load_module rejects relative and absolute path traversal escapes."""

        modules = tmp_path / "modules"
        modules.mkdir(parents=True)
        outside_file = tmp_path / "outside.sh"
        outside_file.write_bytes(b"outside")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = shell_socket.ShellSocketProcessor(fs)

        with pytest.raises(config.InvalidOperation, match="outside the permitted modules directory"):
            processor.load_module("../outside.sh")

        with pytest.raises(config.InvalidOperation, match="outside the permitted modules directory"):
            processor.load_module(str(outside_file))

    def test_load_module__unauthorized_extension__raises_invalid_operation(self, tmp_path: Path) -> None:
        """Verify load_module rejects unauthorized file extensions."""

        modules = tmp_path / "modules"
        modules.mkdir(parents=True)
        (modules / "outside.txt").write_bytes(b"outside")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = shell_socket.ShellSocketProcessor(fs)

        with pytest.raises(config.InvalidOperation, match="unsupported extension"):
            processor.load_module("outside.txt")

    def test_render_launcher__valid_parameters__substitutes_template_variables(self, tmp_path: Path) -> None:
        """Verify render_launcher formats launcher script template with host, port, and hex ACK."""

        launchers = tmp_path / "launchers"
        launchers.mkdir(parents=True)
        launcher = launchers / "shell_socket_client.sh"
        launcher.write_text("connect $DECLUSOR_HOST $DECLUSOR_PORT $DECLUSOR_ACKNOWLEDGE", encoding="utf-8")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = shell_socket.ShellSocketProcessor(fs)

        rendered = processor.render_launcher("127.0.0.1", 9000, b"\x01\x02")
        decoded = base64.b64decode(rendered).decode("utf-8")

        assert decoded == "connect 127.0.0.1 9000 \\x01\\x02"

    def test_find_module__with_extension_and_without_extension__finds_target_module(self, tmp_path: Path) -> None:
        """find_module resolves target module path both with and without .sh extension."""

        modules = tmp_path / "modules" / "discovery"
        modules.mkdir(parents=True)
        mod_file = modules / "sysinfo.sh"
        mod_file.write_bytes(b"# sysinfo")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = shell_socket.ShellSocketProcessor(fs)

        assert processor.find_module("discovery/sysinfo") == mod_file
        assert processor.find_module("discovery/sysinfo.sh") == mod_file

    def test_find_module__with_modules_prefix__normalizes_and_finds_module(self, tmp_path: Path) -> None:
        """find_module strips leading modules/ prefix to support autocompleted asset paths."""

        modules = tmp_path / "modules" / "discovery"
        modules.mkdir(parents=True)
        mod_file = modules / "sysinfo.sh"
        mod_file.write_bytes(b"# sysinfo")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = shell_socket.ShellSocketProcessor(fs)

        assert processor.find_module("modules/discovery/sysinfo") == mod_file
        assert processor.find_module("modules/discovery/sysinfo.sh") == mod_file
