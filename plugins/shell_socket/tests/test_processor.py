from pathlib import Path

import declusor_shell_socket as shell_socket
import pytest

from declusor import config, contract


def test_load_all_helpers_returns_mapping(tmp_path: Path) -> None:
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


def test_load_all_helpers_returns_empty_when_directory_missing(tmp_path: Path) -> None:
    """Verify load_all_helpers returns empty dictionary when helpers directory does not exist."""

    fs = contract.PluginFilesystem.from_root(tmp_path)
    processor = shell_socket.ShellSocketProcessor(fs)

    assert processor.load_all_helpers() == {}


def test_load_helper_success(tmp_path: Path) -> None:
    """Verify load_helper loads a specific helper library by name."""

    helpers = tmp_path / "helpers"
    helpers.mkdir(parents=True)
    (helpers / "util.sh").write_bytes(b"echo util")

    fs = contract.PluginFilesystem.from_root(tmp_path)
    processor = shell_socket.ShellSocketProcessor(fs)

    assert processor.load_helper("util.sh") == b"echo util"


def test_load_helper_rejects_path_traversal(tmp_path: Path) -> None:
    """Verify load_helper rejects path traversal attempts."""

    helpers = tmp_path / "helpers"
    helpers.mkdir(parents=True)
    (tmp_path / "secret.sh").write_bytes(b"secret")

    fs = contract.PluginFilesystem.from_root(tmp_path)
    processor = shell_socket.ShellSocketProcessor(fs)

    with pytest.raises(config.InvalidOperation, match="outside permitted directory"):
        processor.load_helper("../secret.sh")


def test_load_module_success(tmp_path: Path) -> None:
    """Verify load_module reads modules from the designated modules directory."""

    modules = tmp_path / "modules"
    modules.mkdir(parents=True)
    (modules / "example.sh").write_bytes(b"echo module")

    fs = contract.PluginFilesystem.from_root(tmp_path)
    processor = shell_socket.ShellSocketProcessor(fs)

    assert processor.load_module("example.sh") == b"echo module"


def test_load_module_rejects_traversal_and_wrong_extension(tmp_path: Path) -> None:
    """Verify load_module rejects path traversal escapes and unauthorized file extensions."""

    modules = tmp_path / "modules"
    modules.mkdir(parents=True)
    (tmp_path / "outside.txt").write_bytes(b"outside")

    fs = contract.PluginFilesystem.from_root(tmp_path)
    processor = shell_socket.ShellSocketProcessor(fs)

    with pytest.raises(config.InvalidOperation):
        processor.load_module("../outside.txt")

    with pytest.raises(config.InvalidOperation):
        processor.load_module("outside.txt")


def test_render_launcher_substitutions(tmp_path: Path) -> None:
    """Verify render_launcher formats launcher script template with host, port, and hex ACK."""

    launchers = tmp_path / "launchers"
    launchers.mkdir(parents=True)
    launcher = launchers / "shell_socket_client.sh"
    launcher.write_text("HOST=$DECLUSOR_HOST PORT=$DECLUSOR_PORT ACK=$DECLUSOR_ACKNOWLEDGE", encoding="utf-8")

    fs = contract.PluginFilesystem.from_root(tmp_path)
    processor = shell_socket.ShellSocketProcessor(fs)

    rendered = processor.render_launcher("127.0.0.1", 4444, b"\x01\x02")

    assert rendered == b"HOST=127.0.0.1 PORT=4444 ACK=\\x01\\x02"
