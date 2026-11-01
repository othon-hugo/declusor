"""Tests for the public exports of declusor.config."""

from declusor import config


class TestConfigExports:
    """Verify the canonical public configuration API."""

    def test_config_exports__canonical_symbols__are_accessible(self) -> None:
        """Every declared public configuration symbol is exported and accessible."""

        expected = [
            "ChannelType",
            "CommandError",
            "CommandValidationError",
            "ConnectionClosed",
            "ConnectionError",
            "ConnectionHandshakeError",
            "ConnectionTimeoutError",
            "ControllerError",
            "CoreRoute",
            "DeclusorException",
            "DeclusorPlugins",
            "DeclusorWarning",
            "DEFAULT_BUFFER_SIZE",
            "DEFAULT_CLIENT_ACK_SEED",
            "DEFAULT_COMPLETION_BLOCKED_EXTENSIONS",
            "DEFAULT_COMPLETION_BLOCKED_NAMES",
            "DEFAULT_CONNECTION_TIMEOUT",
            "DEFAULT_DECLUSOR_PLUGIN",
            "DEFAULT_EXECUTION_MODE",
            "DEFAULT_LAUNCHER_KIND",
            "DEFAULT_LAUNCHER_OUTPUT_MODE",
            "DEFAULT_SERVER_ACK",
            "DEFAULT_TCP_BACKLOG",
            "DEFAULT_XOR_KEY",
            "ENTRY_POINT_GROUP",
            "DuplicateRouteError",
            "ExecutionMode",
            "ExitCode",
            "FramingMode",
            "InvalidOperation",
            "LauncherDeliveryError",
            "LauncherKind",
            "LauncherOutputMode",
            "MAX_TLV_FRAME_SIZE",
            "OfficialRoute",
            "OperationCode",
            "ParserError",
            "PluginError",
            "PluginNotFoundError",
            "PluginValidationError",
            "PLUGINS_DIR",
            "PROJECT_DESCRIPTION",
            "PROJECT_NAME",
            "PromptError",
            "PROTECTED_ROUTES",
            "ROOT_DIR",
            "RouteCompletionMode",
            "RouterError",
            "StorageError",
            "StorageValidationError",
            "TransportLayer",
            "USER_DIR",
            "USER_PLUGINS_DIR",
        ]

        assert sorted(config.__all__) == sorted(expected)
        for symbol in expected:
            assert symbol in dir(config), f"declusor.config is missing export: {symbol}"
            assert not symbol.startswith("_")
