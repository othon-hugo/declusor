from pathlib import Path

import declusor_shell_socket as shell_socket
import pytest

from declusor import contract, testing


class TestShellSocketConformance(testing.PluginConformanceTestSuite):
    """Verify ShellSocketPlugin strictly complies with the IClientPlugin contract."""

    @pytest.fixture
    def plugin_class(self) -> type[contract.IClientPlugin]:
        return shell_socket.ShellSocketPlugin

    @pytest.fixture
    def sample_options(self, tmp_path: Path) -> dict[str, Path]:
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
