from pathlib import Path

from declusor import app


def test_create_application_discovers_builtin_plugins() -> None:
    """Application factory must discover built-in plugins automatically."""

    declusor_app = app.create_terminal_application()
    available = declusor_app.plugin_manager.names()

    assert "shell_socket" in available
    assert "py_socket" in available


def test_create_application_discovers_custom_plugins_via_search_dirs(tmp_path: Path) -> None:
    """Application factory must incorporate custom search directories."""

    custom_plugin_dir = tmp_path / "extra_client"
    custom_plugin_dir.mkdir()

    plugin_code = """
from collections.abc import Mapping
from declusor import contract

class ExtraClientConfig(contract.ParsedArguments, total=False):
    pass

class ExtraClientPlugin(contract.IPluginExtension[ExtraClientConfig]):
    name = "extra_client"
    description = "Extra client loaded via custom search path"
    options_type = ExtraClientConfig

    @classmethod
    def configure_parser(cls, parser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> ExtraClientConfig:
        return ExtraClientConfig()

    @classmethod
    def build_config(cls, host, port, options, /, filesystem=None, mode=None):
        return None

    @classmethod
    def validate(cls, plugin_config, /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config, /):
        return None
"""
    (custom_plugin_dir / "plugin.py").write_text(plugin_code, encoding="utf-8")

    declusor_app = app.create_terminal_application(search_dirs=[tmp_path])
    available = declusor_app.plugin_manager.names()

    assert "shell_socket" in available
    assert "py_socket" in available
    assert "extra_client" in available
