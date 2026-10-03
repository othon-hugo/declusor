"""Unit tests for the plugin filesystem contract."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from declusor import config, contract


class TestPluginFilesystem:
    """Tests for PluginFilesystem."""

    def test_plugin_filesystem_mutation__reassign_root__raises_frozen_instance_error(self, tmp_path: Path) -> None:
        """Verify PluginFilesystem is frozen against attribute mutation."""

        fs = contract.PluginFilesystem.from_root(tmp_path)

        with pytest.raises(FrozenInstanceError):
            fs.root = tmp_path / "other"  # type: ignore[misc]

    def test_plugin_filesystem_from_root__with_nested_assets_directory__resolves_subdirectories(self, tmp_path: Path) -> None:
        """Verify PluginFilesystem resolves nested assets directory and expected subdirectories."""

        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()

        fs = contract.PluginFilesystem.from_root(tmp_path)

        assert fs.root == tmp_path.resolve()
        assert fs.assets == assets_dir.resolve()
        assert fs.launchers == assets_dir.resolve() / "launchers"
        assert fs.modules == assets_dir.resolve() / "modules"
        assert fs.helpers == assets_dir.resolve() / "helpers"
        assert fs.root.is_absolute()
        assert fs.assets.is_absolute()
        assert fs.launchers.is_absolute()
        assert fs.modules.is_absolute()
        assert fs.helpers.is_absolute()

    def test_plugin_filesystem_from_root__without_nested_assets_directory__falls_back_to_root(self, tmp_path: Path) -> None:
        """Verify PluginFilesystem falls back to root directory directly when assets/ is absent."""

        fs = contract.PluginFilesystem.from_root(tmp_path)

        assert fs.root == tmp_path.resolve()
        assert fs.assets == tmp_path.resolve()
        assert fs.launchers == tmp_path.resolve() / "launchers"
        assert fs.modules == tmp_path.resolve() / "modules"
        assert fs.helpers == tmp_path.resolve() / "helpers"

    def test_plugin_filesystem_from_root__nonexistent_root_path__raises_plugin_validation_error(self, tmp_path: Path) -> None:
        """Verify PluginFilesystem raises PluginValidationError when target directory does not exist."""

        non_existent = tmp_path / "does_not_exist"

        with pytest.raises(config.PluginValidationError, match="Plugin assets directory not found at"):
            contract.PluginFilesystem.from_root(non_existent)

    def test_plugin_filesystem_from_root__path_with_user_tilde__expands_home_directory(self) -> None:
        """Verify PluginFilesystem expands user tilde symbol to the home directory."""

        tilde_path = Path("~")

        fs = contract.PluginFilesystem.from_root(tilde_path)

        assert fs.root == Path.home().resolve()
        assert fs.assets == Path.home().resolve()

    def test_plugin_filesystem_from_root__symlink_path__resolves_to_target_canonical_path(self, tmp_path: Path) -> None:
        """Verify PluginFilesystem resolves symlinks to their canonical real path."""

        real_dir = tmp_path / "real_dir"
        real_dir.mkdir()
        symlink_dir = tmp_path / "symlink_dir"
        symlink_dir.symlink_to(real_dir)

        fs = contract.PluginFilesystem.from_root(symlink_dir)

        assert fs.root == real_dir.resolve()
        assert fs.assets == real_dir.resolve()

    def test_plugin_filesystem_from_root__relative_path_with_parent_traversal__resolves_canonical_path(self, tmp_path: Path) -> None:
        """Verify PluginFilesystem normalizes relative paths with parent segment traversal."""

        sub_dir = tmp_path / "sub"
        sub_dir.mkdir()
        relative_path = sub_dir / ".." / "sub"

        fs = contract.PluginFilesystem.from_root(relative_path)

        assert fs.root == sub_dir.resolve()
        assert ".." not in fs.root.parts
