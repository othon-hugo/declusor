from pathlib import Path

from declusor import config


def test_settings_constants() -> None:
    """Verify core Settings class constants."""
    assert config.Settings.PROJECT_NAME == "declusor"
    assert "Bash payloads" in config.Settings.PROJECT_DESCRIPTION
    assert config.Settings.DEFAULT_SERVER_ACK == b"\x00"
    assert config.Settings.DEFAULT_CLIENT_ACK_SEED == b"\xba\xdc\x00\xff\xee"


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
