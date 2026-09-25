from pathlib import Path

from declusor import main


def test_create_application_discovers_builtin_plugins() -> None:
    """Application factory must discover built-in plugins automatically."""

    app = main.create_application()
    available = app.manager.names()

    assert "shell_socket" in available
    assert "py_socket" in available


def test_create_application_discovers_custom_plugins_via_search_dirs(tmp_path: Path) -> None:
    """Application factory must incorporate custom search directories."""

    custom_plugin_dir = tmp_path / "extra_client"
    custom_plugin_dir.mkdir()

    plugin_code = """
from declusor import contract

class ExtraPlugin(contract.IPlugin):
    name = "extra_client"
    description = "Extra client loaded via custom search path"

    @classmethod
    def configure_parser(cls, parser, /) -> None:
        pass

    @classmethod
    def build_config(cls, args, data_paths=None, /):
        return None

    @classmethod
    def validate(cls, plugin_config, /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config, /):
        return None
"""
    (custom_plugin_dir / "plugin.py").write_text(plugin_code, encoding="utf-8")

    app = main.create_application(search_dirs=[tmp_path])
    available = app.manager.names()

    assert "shell_socket" in available
    assert "py_socket" in available
    assert "extra_client" in available
