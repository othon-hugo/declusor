from pathlib import Path

import pytest

from declusor import config, contract, core, main, testing, util


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


def test_base_path_attributes() -> None:
    """Verify BasePath directory paths are resolved Path objects."""

    assert isinstance(config.BasePath.ROOT_DIR, Path)
    assert isinstance(config.BasePath.PLUGINS_DIR, Path)
    assert isinstance(config.BasePath.USER_DIR, Path)
    assert isinstance(config.BasePath.USER_PLUGINS_DIR, Path)
    assert isinstance(config.BasePath.USER_DATA_DIR, Path)
    assert isinstance(config.BasePath.USER_DATA_PATHS, config.DataPaths)
    assert isinstance(config.BasePath.DATA_DIR, Path)
    assert isinstance(config.BasePath.LAUNCHERS_DIR, Path)
    assert isinstance(config.BasePath.HELPERS_DIR, Path)
    assert isinstance(config.BasePath.MODULES_DIR, Path)
    assert isinstance(config.BasePath.CLIENTS_DIR, Path)
    assert isinstance(config.BasePath.LIBRARY_DIR, Path)
    assert isinstance(config.BasePath.DATA_PATHS, config.DataPaths)


class DummyPathClientPlugin(contract.IClientPlugin):
    """Dummy client plugin for testing data path derivation."""

    name = "dummy_path_client"
    description = "Dummy path client"

    @classmethod
    def configure_parser(cls, parser: util.Parser, /) -> None:
        pass

    @classmethod
    def build_config(cls, args: util.Namespace, data_paths: config.DataPaths | None = None, /) -> contract.ClientConfig:
        resolved_paths = data_paths or config.BasePath.DATA_PATHS
        client_paths = resolved_paths.for_client(cls.name)
        launcher = client_paths.launcher / "client.sh"
        return contract.ClientConfig(
            kind=cls.name,
            host=getattr(args, "host", "127.0.0.1"),
            port=getattr(args, "port", 9000),
            data_paths=resolved_paths,
            options={"launcher_path": launcher},
        )

    @classmethod
    def validate(cls, client_config: contract.ClientConfig, /) -> None:
        pass

    @classmethod
    def build_runtime(cls, client_config: contract.ClientConfig, /) -> contract.IClientRuntime:
        return testing.DummyClientRuntime()


def test_parser_builds_client_paths_from_data_root(tmp_path: Path) -> None:
    """Client configuration must derive all data paths from ``--data-root``."""

    launcher_dir = tmp_path / "dummy_path_client" / "launchers"
    launcher_dir.mkdir(parents=True)
    launcher_file = launcher_dir / "client.sh"
    launcher_file.write_text("", encoding="utf-8")

    registry = core.ClientPluginRegistry()
    registry.register(DummyPathClientPlugin)

    options = core.DeclusorParser(registry, name="declusor").parse(
        ("127.0.0.1", "9000", "--client", "dummy_path_client", "--data-root", str(tmp_path)),
    )

    data_paths = options["client"].data_paths
    assert data_paths == config.DataPaths.from_root(tmp_path)
    assert options["client"].options["launcher_path"] == launcher_file


def test_application_directory_validation_does_not_change_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Validating data paths must not mutate the process working directory."""

    for directory in ("launchers", "modules", "helpers"):
        (tmp_path / directory).mkdir()

    working_directory = tmp_path / "working"
    working_directory.mkdir()
    monkeypatch.chdir(working_directory)

    main.Application._validate_directories(config.DataPaths.from_root(tmp_path))

    assert Path.cwd() == working_directory
