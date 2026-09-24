from pathlib import Path

from declusor import config, contract, core, testing, util


def test_settings_constants() -> None:
    """Verify core Settings class constants."""

    assert config.Settings.PROJECT_NAME == "declusor"


def test_data_paths_for_client(tmp_path: Path) -> None:
    """Verify DataPaths.for_client derives proper ClientDataPaths hierarchy."""

    data_paths = config.DataPaths.from_root(tmp_path)

    client_paths = data_paths.for_client("test_client")
    assert client_paths.root == tmp_path / "test_client"
    assert client_paths.launcher == tmp_path / "test_client" / "launchers"
    assert client_paths.helpers == tmp_path / "test_client" / "helpers"
    assert client_paths.modules == tmp_path / "test_client" / "modules"


def test_data_paths_attributes_and_aliases(tmp_path: Path) -> None:
    """Verify DataPaths attributes and backward-compatible aliases."""

    paths = config.DataPaths.from_root(tmp_path)
    assert paths.root == tmp_path
    assert paths.launchers == tmp_path / "launchers"
    assert paths.helpers == tmp_path / "helpers"
    assert paths.modules == tmp_path / "modules"
    assert paths.clients == paths.launchers
    assert paths.library == paths.helpers


def test_base_path_contains_only_application_and_plugin_directories() -> None:
    """BasePath must only declare root and plugin discovery directories."""

    assert isinstance(config.BasePath.ROOT_DIR, Path)
    assert isinstance(config.BasePath.PLUGINS_DIR, Path)
    assert isinstance(config.BasePath.USER_DIR, Path)
    assert isinstance(config.BasePath.USER_PLUGINS_DIR, Path)

    # Invariant: monolithic data paths are completely eliminated from BasePath
    assert not hasattr(config.BasePath, "DATA_DIR")
    assert not hasattr(config.BasePath, "LAUNCHERS_DIR")
    assert not hasattr(config.BasePath, "HELPERS_DIR")
    assert not hasattr(config.BasePath, "MODULES_DIR")
    assert not hasattr(config.BasePath, "CLIENTS_DIR")
    assert not hasattr(config.BasePath, "LIBRARY_DIR")
    assert not hasattr(config.BasePath, "DATA_PATHS")
    assert not hasattr(config.BasePath, "USER_DATA_DIR")
    assert not hasattr(config.BasePath, "USER_DATA_PATHS")


class DummyPathPlugin(contract.IPlugin):
    """Dummy plugin for testing data path derivation."""

    name = "dummy_path_plugin"
    description = "Dummy path client"

    @classmethod
    def configure_parser(cls, parser: util.Parser, /) -> None:
        pass

    @classmethod
    def build_config(cls, args: util.Namespace, data_paths: config.DataPaths | None = None, /) -> contract.PluginConfig:
        assert data_paths is not None

        client_paths = data_paths.for_client(cls.name)
        launcher = client_paths.launcher / "client.sh"

        return contract.PluginConfig(
            kind=cls.name,
            host=getattr(args, "host", "127.0.0.1"),
            port=getattr(args, "port", 9000),
            data_paths=data_paths,
            options={"launcher_path": launcher},
        )

    @classmethod
    def validate(cls, plugin_config: contract.PluginConfig, /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config: contract.PluginConfig, /) -> contract.IPluginRuntime:
        return testing.DummyPluginRuntime()


def test_parser_builds_client_paths_from_data_root(tmp_path: Path) -> None:
    """Client configuration must derive all data paths from ``--data-root``."""

    launcher_dir = tmp_path / "dummy_path_plugin" / "launchers"
    launcher_dir.mkdir(parents=True)
    launcher_file = launcher_dir / "client.sh"
    launcher_file.write_text("", encoding="utf-8")

    manager = core.PluginManager()
    manager.register(DummyPathPlugin)

    options = core.DeclusorParser(manager, name="declusor").parse(
        ("127.0.0.1", "9000", "--plugin", "dummy_path_plugin", "--data-root", str(tmp_path)),
    )

    data_paths = options["plugin"].data_paths
    assert data_paths == config.DataPaths.from_root(tmp_path)
    assert options["plugin"].options["launcher_path"] == launcher_file
