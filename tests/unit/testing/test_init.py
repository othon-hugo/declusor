import declusor
from declusor import testing


class TestTestingExports:
    """Verify package exports and public symbol accessibility in declusor.testing."""

    def test_all_attribute_accessibility(self) -> None:
        """Ensure every symbol declared in __all__ is accessible on the module."""

        for symbol in testing.__all__:
            assert hasattr(testing, symbol), f"Symbol {symbol!r} in __all__ is missing from declusor.testing"

    def test_all_completeness(self) -> None:
        """Verify __all__ is sorted and contains expected public exports."""

        expected = [
            "DummyApplication",
            "DummyCommand",
            "DummyConfig",
            "DummyConnection",
            "DummyInputSource",
            "DummyOperationRenderer",
            "DummyPlugin",
            "DummyPluginFileStore",
            "DummyPluginRuntime",
            "DummyRouter",
            "DummySessionRunner",
            "DummySocket",
            "DummyTransport",
            "DummyView",
            "MemoryTransport",
            "MemoryTransportListener",
            "PluginConformanceTestSuite",
            "assert_conforms_to_client_plugin",
            "assert_conforms_to_plugin",
            "create_dummy_controller_request",
            "create_dummy_options",
            "create_dummy_plugin_config",
            "create_memory_transport_pair",
            "create_test_session",
            "doubles",
            "pytest_plugin",
        ]
        assert sorted(testing.__all__) == sorted(expected)

    def test_reexports_identity(self) -> None:
        """Verify re-exported types and functions match their origin implementations."""

        from declusor.testing.conformance import PluginConformanceTestSuite
        from declusor.testing.doubles.connection import DummyConnection
        from declusor.testing.doubles.transport import DummyTransport, MemoryTransport, MemoryTransportListener
        from declusor.testing.doubles.view import DummyView
        from declusor.testing.factories import create_test_session

        assert testing.PluginConformanceTestSuite is PluginConformanceTestSuite
        assert testing.DummyConnection is DummyConnection
        assert testing.DummyTransport is DummyTransport
        assert testing.MemoryTransport is MemoryTransport
        assert testing.MemoryTransportListener is MemoryTransportListener
        assert testing.DummyView is DummyView
        assert testing.create_test_session is create_test_session


class TestRootExports:
    """Verify the canonical package-level namespace."""

    def test_declusor_exports__canonical_symbols__are_accessible(self) -> None:
        """Every declared root package symbol is exported and accessible."""

        expected = [
            "app",
            "command",
            "config",
            "contract",
            "controller",
            "core",
            "lang",
            "main",
            "presentation",
            "testing",
            "transport",
            "util",
        ]

        assert sorted(declusor.__all__) == sorted(expected)
        for symbol in expected:
            assert hasattr(declusor, symbol), f"declusor is missing export: {symbol}"


class TestTestingDoublesExports:
    """Verify the public test-double namespace."""

    def test_testing_doubles_exports__canonical_symbols__are_accessible(self) -> None:
        """Every declared doubles symbol is exported and accessible."""

        expected = [
            "create_memory_transport_pair",
            "DummyApplication",
            "DummyCommand",
            "DummyConfig",
            "DummyConnection",
            "DummyInputSource",
            "DummyOperationRenderer",
            "DummyPlugin",
            "DummyPluginFileStore",
            "DummyPluginRuntime",
            "DummyRouter",
            "DummySessionRunner",
            "DummySocket",
            "DummyTransport",
            "DummyView",
            "MemoryTransport",
            "MemoryTransportListener",
        ]

        assert sorted(testing.doubles.__all__) == sorted(expected)
        for symbol in expected:
            assert hasattr(testing.doubles, symbol), f"declusor.testing.doubles is missing export: {symbol}"
