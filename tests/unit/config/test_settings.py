from pathlib import Path

from declusor import config, core, main
from plugins import shell_socket


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


def test_base_path_attributes() -> None:
    """Verify BasePath directory paths are resolved Path objects."""

    assert isinstance(config.BasePath.ROOT_DIR, Path)
    assert isinstance(config.BasePath.PLUGINS_DIR, Path)
    assert isinstance(config.BasePath.USER_PLUGINS_DIR, Path)
    assert isinstance(config.BasePath.DATA_DIR, Path)
    assert isinstance(config.BasePath.DATA_PATHS, config.DataPaths)


def test_parser_builds_client_paths_from_data_root(tmp_path: Path) -> None:
    """Client configuration must derive all data paths from ``--data-root``."""

    launcher_dir = tmp_path / "shell_socket" / "launchers"
    launcher_dir.mkdir(parents=True)
    launcher_file = launcher_dir / "shell_socket_client.sh"
    launcher_file.write_text("", encoding="utf-8")

    registry = core.ClientRegistry()
    registry.register(ShellSocketPlugin)

    options = core.DeclusorParser(registry, name="declusor").parse(
        ("127.0.0.1", "9000", "--data-root", str(tmp_path)),
    )

    data_paths = options["client"].data_paths
    assert data_paths == config.DataPaths.from_root(tmp_path)
    assert options["client"].options["launcher_path"] == launcher_file


def test_application_directory_validation_does_not_change_cwd(tmp_path: Path, monkeypatch) -> None:
    """Validating data paths must not mutate the process working directory."""

    for directory in ("clients", "modules", "library"):
        (tmp_path / directory).mkdir()

    working_directory = tmp_path / "working"
    working_directory.mkdir()
    monkeypatch.chdir(working_directory)

    Application._validate_directories(config.DataPaths.from_root(tmp_path))

    assert Path.cwd() == working_directory
