from pathlib import Path

from declusor import config


def test_settings_constants() -> None:
    """Verify module-level constants."""

    assert config.PROJECT_NAME == "declusor"
    assert "payload" in config.PROJECT_DESCRIPTION.lower()
    assert config.DEFAULT_SERVER_ACK == b"\x00"
    assert config.DEFAULT_CLIENT_ACK_SEED == b"declusor"
    assert config.DEFAULT_LAUNCHER_OUTPUT_MODE == config.LauncherOutputMode.TERMINAL


def test_root_and_plugin_directories() -> None:
    """Module must declare root and plugin discovery directories."""

    assert isinstance(config.ROOT_DIR, Path)
    assert isinstance(config.PLUGINS_DIR, Path)
    assert isinstance(config.USER_DIR, Path)
    assert isinstance(config.USER_PLUGINS_DIR, Path)
