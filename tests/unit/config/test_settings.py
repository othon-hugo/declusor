"""Unit tests for framework settings and global constants."""

from pathlib import Path

from declusor import config


class TestProjectMetadataSettings:
    """Tests for project metadata constants."""

    def test_settings__project_name__matches_expected_string(self) -> None:
        """Verify PROJECT_NAME matches the framework name."""

        assert config.PROJECT_NAME == "declusor"

    def test_settings__project_description__matches_expected_string(self) -> None:
        """Verify PROJECT_DESCRIPTION provides the standard framework description."""

        assert config.PROJECT_DESCRIPTION == "A fast, modular, and extensible reverse-shell framework and payload delivery handler."


class TestPathSettings:
    """Tests for directory and path resolution constants."""

    def test_settings__root_dir__is_absolute_and_contains_project_markers(self) -> None:
        """Verify ROOT_DIR is an absolute resolved directory pointing to repository root."""

        assert isinstance(config.ROOT_DIR, Path)
        assert config.ROOT_DIR.is_absolute()
        assert (config.ROOT_DIR / "pyproject.toml").exists()

    def test_settings__plugins_dir__is_child_of_root_dir(self) -> None:
        """Verify PLUGINS_DIR resolves to the repository plugins directory."""

        expected = (config.ROOT_DIR / "plugins").resolve()
        assert expected == config.PLUGINS_DIR

    def test_settings__user_dir__is_child_of_home_dir(self) -> None:
        """Verify USER_DIR resolves to ~/.declusor under the user's home directory."""

        expected = (Path.home() / ".declusor").resolve()
        assert expected == config.USER_DIR

    def test_settings__user_plugins_dir__is_child_of_user_dir(self) -> None:
        """Verify USER_PLUGINS_DIR resolves to ~/.declusor/plugins."""

        expected = (config.USER_DIR / "plugins").resolve()
        assert expected == config.USER_PLUGINS_DIR


class TestProtocolSettings:
    """Tests for protocol, handshake, and cryptography constants."""

    def test_settings__default_server_ack__is_null_byte(self) -> None:
        """Verify DEFAULT_SERVER_ACK is a single null byte."""

        assert config.DEFAULT_SERVER_ACK == b"\x00"

    def test_settings__default_client_ack_seed__matches_expected_bytes(self) -> None:
        """Verify DEFAULT_CLIENT_ACK_SEED matches the standard byte sequence."""

        assert config.DEFAULT_CLIENT_ACK_SEED == b"declusor"

    def test_settings__default_xor_key__is_non_empty_bytes(self) -> None:
        """Verify DEFAULT_XOR_KEY is a non-empty byte sequence."""

        assert config.DEFAULT_XOR_KEY == b"declusor"


class TestDefaultModeSettings:
    """Tests for default mode and plugin configuration constants."""

    def test_settings__default_declusor_plugin__is_shell_socket(self) -> None:
        """Verify DEFAULT_DECLUSOR_PLUGIN defaults to SHELL_SOCKET."""

        assert config.DEFAULT_DECLUSOR_PLUGIN == config.DeclusorPlugins.SHELL_SOCKET

    def test_settings__default_execution_mode__is_cli(self) -> None:
        """Verify DEFAULT_EXECUTION_MODE defaults to CLI."""

        assert config.DEFAULT_EXECUTION_MODE == config.ExecutionMode.CLI

    def test_settings__default_launcher_output_mode__is_terminal(self) -> None:
        """Verify DEFAULT_LAUNCHER_OUTPUT_MODE defaults to TERMINAL."""

        assert config.DEFAULT_LAUNCHER_OUTPUT_MODE == config.LauncherOutputMode.TERMINAL
