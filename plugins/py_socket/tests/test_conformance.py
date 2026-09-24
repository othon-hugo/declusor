from pathlib import Path

import declusor_py_socket as py_socket
import pytest

from declusor import contract, testing


class TestPySocketConformance(testing.PluginConformanceTestSuite):
    """Verify PySocketPlugin strictly complies with the IPlugin contract."""

    @pytest.fixture
    def plugin_class(self) -> type[contract.IPlugin]:
        return py_socket.PySocketPlugin

    @pytest.fixture
    def sample_options(self, tmp_path: Path) -> dict[str, Path]:
        launcher = tmp_path / "py_socket_client.py"
        launcher.write_text("# py_socket test launcher")
        helpers = tmp_path / "helpers"
        helpers.mkdir(exist_ok=True)
        modules = tmp_path / "modules"
        modules.mkdir(exist_ok=True)

        return {
            "launcher_path": launcher,
            "helpers_dir": helpers,
            "modules_dir": modules,
        }
