"""Contract conformance test for PySocketPlugin."""

from pathlib import Path
from typing import Any

import pytest
from py_socket import PySocketPlugin

from declusor import contract
from declusor.testing import PluginConformanceTestSuite


class TestPySocketConformance(PluginConformanceTestSuite):
    """Verify PySocketPlugin strictly complies with the IClientPlugin contract."""

    @pytest.fixture
    def plugin_class(self) -> type[contract.IClientPlugin]:
        return PySocketPlugin

    @pytest.fixture
    def sample_options(self, tmp_path: Path) -> dict[str, Any]:
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
