import base64
from pathlib import Path

import declusor_py_socket as py_socket
import pytest

from declusor import config, contract


class TestPySocketProcessor:
    """Tests for PySocketProcessor asset loading, traversal prevention, and stager rendering."""

    def test_load_all_helpers__valid_directory__returns_mapping(self, tmp_path: Path) -> None:
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

    def test_load_all_helpers__missing_directory__returns_empty_mapping(self, tmp_path: Path) -> None:
        """Verify load_all_helpers returns empty dictionary when helpers directory does not exist."""

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = py_socket.PySocketProcessor(fs)

        assert processor.load_all_helpers() == {}

    def test_load_helper__valid_name__returns_file_bytes(self, tmp_path: Path) -> None:
        """Verify load_helper loads a specific helper library by name."""

        helpers = tmp_path / "helpers"
        helpers.mkdir(parents=True)
        (helpers / "util.py").write_bytes(b"# helper util")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = py_socket.PySocketProcessor(fs)

        assert processor.load_helper("util.py") == b"# helper util"

    def test_load_helper__relative_path_traversal__raises_invalid_operation(self, tmp_path: Path) -> None:
        """Verify load_helper rejects relative dot-dot path traversal attempts."""

        helpers = tmp_path / "helpers"
        helpers.mkdir(parents=True)
        (tmp_path / "secret.py").write_bytes(b"# secret")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = py_socket.PySocketProcessor(fs)

        with pytest.raises(config.InvalidOperation, match="outside permitted directory"):
            processor.load_helper("../secret.py")

    def test_load_helper__absolute_path_traversal__raises_invalid_operation(self, tmp_path: Path) -> None:
        """Verify load_helper rejects absolute path outside the permitted helpers directory."""

        helpers = tmp_path / "helpers"
        helpers.mkdir(parents=True)
        secret_file = tmp_path / "secret.py"
        secret_file.write_bytes(b"# secret")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = py_socket.PySocketProcessor(fs)

        with pytest.raises(config.InvalidOperation, match="outside permitted directory"):
            processor.load_helper(str(secret_file))

    def test_helpers__concatenates_all_helpers_with_double_newline(self, tmp_path: Path) -> None:
        """Verify helpers concatenates all helper library scripts."""

        helpers = tmp_path / "helpers"
        helpers.mkdir(parents=True)
        (helpers / "a.py").write_bytes(b"# helper a")
        (helpers / "b.py").write_bytes(b"# helper b")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = py_socket.PySocketProcessor(fs)

        assert processor.helpers == b"# helper a\n\n# helper b"

    def test_load_module__valid_name__returns_file_bytes(self, tmp_path: Path) -> None:
        """Verify load_module reads modules from the designated modules directory."""

        modules = tmp_path / "modules"
        modules.mkdir(parents=True)
        (modules / "info.py").write_bytes(b"# info module")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = py_socket.PySocketProcessor(fs)

        assert processor.load_module("info.py") == b"# info module"

    def test_load_module__relative_and_absolute_traversal__raises_invalid_operation(self, tmp_path: Path) -> None:
        """Verify load_module rejects relative and absolute path traversal escapes."""

        modules = tmp_path / "modules"
        modules.mkdir(parents=True)
        outside_file = tmp_path / "outside.py"
        outside_file.write_bytes(b"outside")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = py_socket.PySocketProcessor(fs)

        with pytest.raises(config.InvalidOperation, match="outside the permitted modules directory"):
            processor.load_module("../outside.py")

        with pytest.raises(config.InvalidOperation, match="outside the permitted modules directory"):
            processor.load_module(str(outside_file))

    def test_load_module__unauthorized_extension__raises_invalid_operation(self, tmp_path: Path) -> None:
        """Verify load_module rejects unauthorized file extensions."""

        modules = tmp_path / "modules"
        modules.mkdir(parents=True)
        (modules / "bad.sh").write_bytes(b"bad")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = py_socket.PySocketProcessor(fs)

        with pytest.raises(config.InvalidOperation, match="unsupported extension"):
            processor.load_module("bad.sh")

    def test_render_launcher__valid_parameters__substitutes_template_variables(self, tmp_path: Path) -> None:
        """Verify render_launcher formats launcher script template with host, port, and hex ACK."""

        launchers = tmp_path / "launchers"
        launchers.mkdir(parents=True)
        launcher = launchers / "py_socket_client.py"
        launcher.write_text("HOST = '$HOST'\nPORT = int('$PORT')\nACK = bytes.fromhex('$ACKNOWLEDGE')", encoding="utf-8")

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = py_socket.PySocketProcessor(fs)

        rendered = processor.render_launcher("127.0.0.1", 9000, b"\x01\x02")
        decoded = base64.b64decode(rendered).decode("utf-8")

        assert decoded == "HOST = '127.0.0.1'\nPORT = int('9000')\nACK = bytes.fromhex('0102')"

    def test_render_launcher__sanitizes_comments_docstrings_annotations_and_asserts(self, tmp_path: Path) -> None:
        """Verify render_launcher strips comments, docstrings, type annotations, and asserts."""

        launchers = tmp_path / "launchers"
        launchers.mkdir(parents=True)
        launcher = launchers / "py_socket_client.py"
        launcher.write_text(
            '# Development comment\n"""Module docstring."""\n'
            'def ping(val: int) -> bool:\n    """Function docstring."""\n    assert val > 0\n    return True\n'
            "HOST = '$HOST'\n",
            encoding="utf-8",
        )

        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = py_socket.PySocketProcessor(fs)

        rendered = processor.render_launcher("127.0.0.1", 9000, b"\x01\x02")
        decoded = base64.b64decode(rendered).decode("utf-8")

        assert "Development comment" not in decoded
        assert "Module docstring" not in decoded
        assert "Function docstring" not in decoded
        assert "assert val > 0" not in decoded
        assert ": int" not in decoded
        assert "-> bool" not in decoded
        assert "HOST = '127.0.0.1'" in decoded
