from pathlib import Path

from declusor import config, core
from declusor.main.app import Application
from declusor.plugin import ShellSocketPlugin


def test_parser_builds_client_paths_from_data_root(tmp_path: Path) -> None:
    """Client configuration must derive all data paths from ``--data-root``."""

    launcher_dir = tmp_path / "shell_socket" / "launchers"
    launcher_dir.mkdir(parents=True)
    (launcher_dir / ShellSocketPlugin.name).write_text("", encoding="utf-8")

    registry = core.ClientRegistry()
    registry.register(ShellSocketPlugin)
    options = core.DeclusorParser(registry, name="declusor").parse(
        ("127.0.0.1", "9000", "--data-root", str(tmp_path)),
    )

    data_paths = options["client"].data_paths
    assert data_paths == config.DataPaths.from_root(tmp_path)
    assert options["client"].options["client_path"] == launcher_dir / ShellSocketPlugin.name


def test_application_directory_validation_does_not_change_cwd(tmp_path: Path, monkeypatch) -> None:
    """Validating data paths must not mutate the process working directory."""

    for directory in ("clients", "modules", "library"):
        (tmp_path / directory).mkdir()

    working_directory = tmp_path / "working"
    working_directory.mkdir()
    monkeypatch.chdir(working_directory)

    Application._validate_directories(config.DataPaths.from_root(tmp_path))

    assert Path.cwd() == working_directory
