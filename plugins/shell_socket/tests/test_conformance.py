from pathlib import Path
from typing import Any

import pytest
from shell_socket import ShellSocketPlugin

from declusor import contract
from declusor.testing import PluginConformanceTestSuite


class TestShellSocketConformance(PluginConformanceTestSuite):
    """Verify ShellSocketPlugin strictly complies with the IClientPlugin contract."""

    @pytest.fixture
    def plugin_class(self) -> type[contract.IClientPlugin]:
        return ShellSocketPlugin

    @pytest.fixture
    def sample_options(self, tmp_path: Path) -> dict[str, Any]:
        launcher = tmp_path / "client.sh"
        launcher.write_text("test")
        helpers = tmp_path / "helpers"
        helpers.mkdir(exist_ok=True)
        modules = tmp_path / "modules"
        modules.mkdir(exist_ok=True)
        return {
            "launcher_path": launcher,
            "helpers_dir": helpers,
            "modules_dir": modules,
        }
