from collections.abc import Mapping
from pathlib import Path

from declusor import config, contract, core, testing


def test_settings_constants() -> None:
    """Verify module-level constants."""

    assert config.PROJECT_NAME == "declusor"
    assert "payload" in config.PROJECT_DESCRIPTION.lower()
    assert config.DEFAULT_SERVER_ACK == b"\x00"
    assert config.DEFAULT_CLIENT_ACK_SEED == b"declusor"


def test_plugin_filesystem_attributes(tmp_path: Path) -> None:
    """Verify PluginFilesystem attributes derived from root."""

    assets_dir = tmp_path / "assets"
    assets_dir.mkdir(parents=True)

    paths = contract.PluginFilesystem.from_root(tmp_path)
    assert paths.root == tmp_path
    assert paths.assets == assets_dir
    assert paths.launchers == assets_dir / "launchers"
    assert paths.helpers == assets_dir / "helpers"
    assert paths.modules == assets_dir / "modules"


def test_root_and_plugin_directories() -> None:
    """Module must declare root and plugin discovery directories."""

    assert isinstance(config.ROOT_DIR, Path)
    assert isinstance(config.PLUGINS_DIR, Path)
    assert isinstance(config.USER_DIR, Path)
    assert isinstance(config.USER_PLUGINS_DIR, Path)


class DummyPathConfig(contract.ParsedArguments, total=False):
    """Configuration options for DummyPathClientPlugin."""

    launcher_path: Path


class DummyPathClientPlugin(contract.IPluginExtension[DummyPathConfig]):
    """Dummy client plugin for testing data path derivation."""

    name = "dummy_path_plugin"
    description = "Dummy path client"
    version = "1.0.0"
    options_type = DummyPathConfig

    @classmethod
    def configure_parser(cls, parser: contract.IArgumentParser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> DummyPathConfig:
        return DummyPathConfig()

    @classmethod
    def build_config(
        cls,
        host: str,
        port: int,
        options: DummyPathConfig,
        /,
        filesystem: contract.PluginFilesystem | None = None,
        mode: config.ExecutionMode = config.DEFAULT_EXECUTION_MODE,
    ) -> contract.PluginConfig[DummyPathConfig]:
        assert filesystem is not None

        launcher = filesystem.launchers / "client.sh"
        options["launcher_path"] = launcher

        return contract.PluginConfig(
            kind=cls.name,
            host=host,
            port=port,
            filesystem=filesystem,
            options=options,
            options_type=cls.options_type,
            mode=mode,
        )

    @classmethod
    def validate(cls, plugin_config: contract.PluginConfig[DummyPathConfig], /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config: contract.PluginConfig[DummyPathConfig], /) -> contract.IPluginRuntime:
        return testing.DummyPluginRuntime()


def test_parser_builds_client_paths_from_data_root(tmp_path: Path) -> None:
    """Client configuration must derive all data paths from ``--assets-dir``."""

    assets_dir = tmp_path / "assets"
    launcher_dir = assets_dir / "launchers"
    launcher_dir.mkdir(parents=True)
    launcher_file = launcher_dir / "client.sh"
    launcher_file.write_text("", encoding="utf-8")

    manager = core.PluginManager()
    manager.register(DummyPathClientPlugin)

    plugin_config = core.DeclusorParser(name="declusor").parse(
        manager,
        ("127.0.0.1", "9000", "--plugin", "dummy_path_plugin", "--assets-dir", str(tmp_path)),
    )

    filesystem = plugin_config.filesystem
    assert filesystem == contract.PluginFilesystem.from_root(tmp_path)
    assert plugin_config.options.get("launcher_path") == launcher_file
