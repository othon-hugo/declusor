from pathlib import Path

import declusor_py_socket as py_socket
import pytest

from declusor import config, contract


def test_load_all_helpers_returns_mapping(tmp_path: Path) -> None:
    """Verify load_all_helpers loads all valid Python helper scripts into a mapping."""

    helpers = tmp_path / "helpers"
    helpers.mkdir(parents=True)
    (helpers / "a.py").write_bytes(b"# helper a")
    (helpers / "b.py").write_bytes(b"# helper b")
    (helpers / "ignored.txt").write_bytes(b"ignored")

    fs = contract.PluginFilesystem.from_root(tmp_path)
    processor = py_socket.PySocketProcessor(fs)

    loaded = processor.load_all_helpers()

    assert loaded == {
        "a.py": b"# helper a",
        "b.py": b"# helper b",
    }


def test_load_all_helpers_returns_empty_when_directory_missing(tmp_path: Path) -> None:
    """Verify load_all_helpers returns empty dictionary when helpers directory does not exist."""

    fs = contract.PluginFilesystem.from_root(tmp_path)
    processor = py_socket.PySocketProcessor(fs)

    assert processor.load_all_helpers() == {}


def test_load_helper_success(tmp_path: Path) -> None:
    """Verify load_helper loads a specific helper library by name."""

    helpers = tmp_path / "helpers"
    helpers.mkdir(parents=True)
    (helpers / "util.py").write_bytes(b"# helper util")

    fs = contract.PluginFilesystem.from_root(tmp_path)
    processor = py_socket.PySocketProcessor(fs)

    assert processor.load_helper("util.py") == b"# helper util"


def test_load_helper_rejects_path_traversal(tmp_path: Path) -> None:
    """Verify load_helper rejects path traversal attempts."""

    helpers = tmp_path / "helpers"
    helpers.mkdir(parents=True)
    (tmp_path / "secret.py").write_bytes(b"# secret")

    fs = contract.PluginFilesystem.from_root(tmp_path)
    processor = py_socket.PySocketProcessor(fs)

    with pytest.raises(config.InvalidOperation, match="outside permitted directory"):
        processor.load_helper("../secret.py")


def test_helpers_concatenation(tmp_path: Path) -> None:
    """Verify helpers concatenates all helper library scripts."""

    helpers = tmp_path / "helpers"
    helpers.mkdir(parents=True)
    (helpers / "a.py").write_bytes(b"# helper a")
    (helpers / "b.py").write_bytes(b"# helper b")

    fs = contract.PluginFilesystem.from_root(tmp_path)
    processor = py_socket.PySocketProcessor(fs)

    assert processor.helpers == b"# helper a\n\n# helper b"


def test_load_module_success(tmp_path: Path) -> None:
    """Verify load_module reads modules from the designated modules directory."""

    modules = tmp_path / "modules"
    modules.mkdir(parents=True)
    (modules / "info.py").write_bytes(b"# info module")

    fs = contract.PluginFilesystem.from_root(tmp_path)
    processor = py_socket.PySocketProcessor(fs)

    assert processor.load_module("info.py") == b"# info module"


def test_load_module_rejects_traversal_and_wrong_extension(tmp_path: Path) -> None:
    """Verify load_module rejects path traversal escapes and unauthorized file extensions."""

    modules = tmp_path / "modules"
    modules.mkdir(parents=True)
    (tmp_path / "outside.py").write_bytes(b"outside")

    fs = contract.PluginFilesystem.from_root(tmp_path)
    processor = py_socket.PySocketProcessor(fs)

    with pytest.raises(config.InvalidOperation):
        processor.load_module("../outside.py")

    with pytest.raises(config.InvalidOperation):
        processor.load_module("bad.sh")


def test_render_launcher_substitutions(tmp_path: Path) -> None:
    """Verify render_launcher formats launcher script template with host, port, and hex ACK."""

    launchers = tmp_path / "launchers"
    launchers.mkdir(parents=True)
    launcher = launchers / "py_socket_client.py"
    launcher.write_text("HOST = '$HOST'\nPORT = int('$PORT')\nACK = bytes.fromhex('$ACKNOWLEDGE')", encoding="utf-8")

    fs = contract.PluginFilesystem.from_root(tmp_path)
    processor = py_socket.PySocketProcessor(fs)

    rendered = processor.render_launcher("127.0.0.1", 9000, b"\x01\x02")

    assert rendered == b"HOST = '127.0.0.1'\nPORT = int('9000')\nACK = bytes.fromhex('0102')"
