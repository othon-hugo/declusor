from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from declusor import config, contract


def test_plugin_filesystem_from_root_with_nested_assets(tmp_path: Path) -> None:
    """PluginFilesystem resolves nested assets directory when present."""

    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()

    fs = contract.PluginFilesystem.from_root(tmp_path)

    assert fs.root == tmp_path.resolve()
    assert fs.assets == assets_dir.resolve()
    assert fs.launchers == assets_dir.resolve() / "launchers"
    assert fs.modules == assets_dir.resolve() / "modules"
    assert fs.helpers == assets_dir.resolve() / "helpers"


def test_plugin_filesystem_from_root_fallback_when_root_is_assets(tmp_path: Path) -> None:
    """PluginFilesystem falls back to root directory directly when assets/ subdir is absent."""

    fs = contract.PluginFilesystem.from_root(tmp_path)

    assert fs.root == tmp_path.resolve()
    assert fs.assets == tmp_path.resolve()
    assert fs.launchers == tmp_path.resolve() / "launchers"
    assert fs.modules == tmp_path.resolve() / "modules"
    assert fs.helpers == tmp_path.resolve() / "helpers"


def test_plugin_filesystem_from_root_raises_when_path_does_not_exist(tmp_path: Path) -> None:
    """PluginFilesystem raises PluginValidationError when target directory does not exist."""

    non_existent = tmp_path / "does_not_exist"

    with pytest.raises(config.PluginValidationError, match="Plugin assets directory not found at"):
        contract.PluginFilesystem.from_root(non_existent)


def test_plugin_filesystem_is_immutable(tmp_path: Path) -> None:
    """PluginFilesystem must be frozen against modification."""

    fs = contract.PluginFilesystem.from_root(tmp_path)

    with pytest.raises(FrozenInstanceError):
        fs.root = tmp_path / "other"  # type: ignore[misc]
