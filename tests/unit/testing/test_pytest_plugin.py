from collections.abc import Generator

from declusor import contract, testing


class TestPytestPluginFixtures:
    """Verify standard fixtures provided by declusor.testing.pytest_plugin."""

    def test_view_and_input_fixtures(
        self,
        dummy_view: testing.DummyView,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """Ensure view and input fixtures inject correct in-memory doubles."""

        assert isinstance(dummy_view, testing.DummyView)
        assert isinstance(dummy_input_source, testing.DummyInputSource)

    def test_connection_and_profile_fixtures(
        self,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """Ensure connection and profile fixtures inject initialized doubles."""

        assert isinstance(dummy_connection, testing.DummyConnection)
        assert isinstance(dummy_profile, testing.DummyConnectionProfile)

    def test_filestore_and_session_fixtures(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
        test_session: contract.SessionContext,
    ) -> None:
        """Ensure filestore and session fixtures inject configured doubles."""

        assert isinstance(dummy_file_store, testing.DummyPluginFileStore)
        assert isinstance(test_session, contract.SessionContext)

    def test_runtime_and_plugin_fixtures(
        self,
        dummy_runtime: testing.DummyPluginRuntime,
        dummy_plugin: Generator[type[testing.DummyPlugin], None, None],
    ) -> None:
        """Ensure runtime and plugin class fixtures inject clean doubles."""

        assert isinstance(dummy_runtime, testing.DummyPluginRuntime)
        assert issubclass(testing.DummyPlugin, contract.IPluginExtension)

    def test_router_and_application_fixtures(
        self,
        dummy_router: testing.DummyRouter,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """Ensure router and application fixtures inject correct doubles."""

        assert isinstance(dummy_router, testing.DummyRouter)
        assert isinstance(dummy_app, testing.DummyApplication)

    def test_transport_fixtures(
        self,
        dummy_transport: testing.DummyTransport,
        dummy_socket: testing.DummySocket,
        memory_transport_pair: tuple[testing.MemoryTransport, testing.MemoryTransport],
        memory_transport_listener: testing.MemoryTransportListener,
    ) -> None:
        """Ensure transport, socket, and memory transport fixtures inject functional doubles."""

        assert isinstance(dummy_transport, testing.DummyTransport)
        assert isinstance(dummy_socket, testing.DummySocket)

        client_tx, server_tx = memory_transport_pair
        assert isinstance(client_tx, testing.MemoryTransport)
        assert isinstance(server_tx, testing.MemoryTransport)
        assert isinstance(memory_transport_listener, testing.MemoryTransportListener)
