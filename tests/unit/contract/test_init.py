"""Tests for the public exports of declusor.contract."""

from declusor import contract


class TestContractExports:
    """Verify the canonical public contract API."""

    def test_contract_exports__canonical_symbols__are_accessible(self) -> None:
        """Every declared public contract symbol is exported and accessible."""

        expected = [
            "ArgumentDefinitions",
            "ConnectionClosed",
            "ConnectionError",
            "ConnectionHandshakeError",
            "ConnectionState",
            "ConnectionTimeoutError",
            "Controller",
            "ControllerAction",
            "ControllerArguments",
            "ControllerResult",
            "IArgumentParser",
            "ICommand",
            "IConnection",
            "IControllerRequest",
            "IEntryPoint",
            "IInputSource",
            "InvalidOperation",
            "IOperationRenderer",
            "IPluginExtension",
            "IPluginProcessor",
            "IPluginRuntime",
            "IReadlineAdapter",
            "IRouter",
            "ISessionRunner",
            "ISocket",
            "ITransport",
            "ITransportLayer",
            "ITransportListener",
            "IView",
            "LauncherDelivery",
            "ParsedArguments",
            "PluginConfig",
            "PluginExtensionType",
            "PluginFilesystem",
            "RouteHelp",
            "RouteRegistration",
            "RouteTable",
            "SessionContext",
        ]

        assert sorted(contract.__all__) == sorted(expected)
        assert len(contract.__all__) == 38

        for symbol in expected:
            assert symbol in dir(contract), f"declusor.contract is missing export: {symbol}"
            assert not symbol.startswith("_")
