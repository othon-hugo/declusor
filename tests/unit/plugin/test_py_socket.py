from pathlib import Path
from unittest.mock import MagicMock

import pytest

from declusor import config, connection, contract
from declusor.plugin import PySocketPlugin

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client_config(tmp_path: Path) -> contract.ClientConfig:
    """Build a ``ClientConfig`` pointing to a launcher inside ``tmp_path``."""
    data_paths = config.DataPaths.from_root(tmp_path)
    client_data = data_paths.for_client("py_socket")
    client_path = client_data.launcher / "py_socket_client.py"

    return contract.ClientConfig(
        kind=PySocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={"client_path": client_path},
        data_paths=data_paths,
    )


def _write_launcher(tmp_path: Path) -> Path:
    """Create a minimal launcher template under the namespaced launchers dir."""
    client_data = config.DataPaths.from_root(tmp_path).for_client("py_socket")
    client_data.launcher.mkdir(parents=True, exist_ok=True)
    client_path = client_data.launcher / "py_socket_client.py"
    client_path.write_text(
        "HOST = '$HOST'\nPORT = int('$PORT')\nACK = bytes.fromhex('$ACKNOWLEDGE')",
        encoding="utf-8",
    )
    return client_path


# ---------------------------------------------------------------------------
# build_runtime tests
# ---------------------------------------------------------------------------


def test_build_runtime_renders_configured_client_script(tmp_path: Path) -> None:
    """The runtime must embed host and port into the rendered client script."""

    _write_launcher(tmp_path)
    client_config = _make_client_config(tmp_path)

    runtime = PySocketPlugin.build_runtime(client_config)

    assert "127.0.0.1" in runtime.client_script
    assert "9000" in runtime.client_script


def test_build_runtime_creates_py_socket_connection(tmp_path: Path) -> None:
    """The runtime must produce a PySocketConnection for every accepted socket."""

    _write_launcher(tmp_path)
    client_config = _make_client_config(tmp_path)

    runtime = PySocketPlugin.build_runtime(client_config)
    client_connection = runtime.create_connection(MagicMock())

    assert isinstance(client_connection, connection.PySocketConnection)


# ---------------------------------------------------------------------------
# validate tests
# ---------------------------------------------------------------------------


def test_validate_passes_when_launcher_exists(tmp_path: Path) -> None:
    """validate() must succeed silently when the launcher file is present."""

    _write_launcher(tmp_path)
    client_config = _make_client_config(tmp_path)

    PySocketPlugin.validate(client_config)  # must not raise


def test_validate_raises_when_launcher_missing(tmp_path: Path) -> None:
    """validate() must raise ParserError when the launcher file does not exist."""

    client_config = _make_client_config(tmp_path)
    # Launcher directory exists but no file is written

    with pytest.raises(config.ParserError):
        PySocketPlugin.validate(client_config)
