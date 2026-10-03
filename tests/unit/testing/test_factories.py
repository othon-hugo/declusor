from pathlib import Path

from declusor import config, contract, testing


class TestSessionContextFactory:
    """Verify behavior of create_test_session factory."""

    def test_create_test_session_defaults(self) -> None:
        """Ensure create_test_session populates all doubles with defaults."""

        session = testing.create_test_session()

        assert isinstance(session.connection, testing.DummyConnection)
        assert isinstance(session.view, testing.DummyView)
        assert isinstance(session.input, testing.DummyInputSource)
        assert isinstance(session.plugin, testing.DummyPluginFileStore)

    def test_create_test_session_custom_collaborators(self) -> None:
        """Ensure create_test_session injects explicitly supplied collaborators."""

        custom_conn = testing.DummyConnection()
        custom_view = testing.DummyView()
        custom_input = testing.DummyInputSource()
        custom_store = testing.DummyPluginFileStore()

        session = testing.create_test_session(
            connection=custom_conn,
            view=custom_view,
            input_source=custom_input,
            files=custom_store,
        )

        assert session.connection is custom_conn
        assert session.view is custom_view
        assert session.input is custom_input
        assert session.plugin is custom_store


class TestPluginConfigFactory:
    """Verify behavior of create_dummy_plugin_config and create_dummy_options."""

    def test_create_dummy_plugin_config_defaults(self) -> None:
        """Ensure create_dummy_plugin_config uses standard defaults."""

        cfg = testing.create_dummy_plugin_config()

        assert cfg.kind == "dummy"
        assert cfg.host == "127.0.0.1"
        assert cfg.port == 9000
        assert cfg.mode == config.DEFAULT_EXECUTION_MODE
        assert cfg.options_type == testing.DummyConfig
        assert cfg.timeout is None

    def test_create_dummy_plugin_config_custom_values(self) -> None:
        """Ensure create_dummy_plugin_config applies custom parameters."""

        custom_fs = contract.PluginFilesystem(
            root=Path("/tmp/declusor_test"),
            assets=Path("/tmp/declusor_test/assets"),
            launchers=Path("/tmp/declusor_test/assets/launchers"),
            modules=Path("/tmp/declusor_test/assets/modules"),
            helpers=Path("/tmp/declusor_test/assets/helpers"),
        )
        custom_opts = testing.DummyConfig()

        cfg = testing.create_dummy_plugin_config(
            kind="custom_agent",
            host="192.168.1.100",
            port=4444,
            filesystem=custom_fs,
            options=custom_opts,
            mode=config.ExecutionMode.API,
            timeout=15.0,
            launcher_output_mode=config.LauncherOutputMode.SILENT,
            launcher_output_path=Path("/tmp/out.sh"),
            launcher_wrapper="bash -c '{}'",
            transport_layers=("xor",),
        )

        assert cfg.kind == "custom_agent"
        assert cfg.host == "192.168.1.100"
        assert cfg.port == 4444
        assert cfg.filesystem is custom_fs
        assert cfg.options is custom_opts
        assert cfg.mode == config.ExecutionMode.API
        assert cfg.timeout == 15.0
        assert cfg.launcher_output_mode == config.LauncherOutputMode.SILENT
        assert cfg.launcher_output_path == Path("/tmp/out.sh")
        assert cfg.launcher_wrapper == "bash -c '{}'"
        assert cfg.transport_layers == ("xor",)

    def test_create_dummy_options_alias(self) -> None:
        """Ensure create_dummy_options returns PluginConfig matching create_dummy_plugin_config."""

        cfg = testing.create_dummy_options()
        assert isinstance(cfg, contract.PluginConfig)
        assert cfg.kind == "dummy"


class TestControllerRequestFactory:
    """Verify behavior of create_dummy_controller_request factory."""

    def test_create_dummy_controller_request_empty(self) -> None:
        """Ensure create_dummy_controller_request creates request with empty line."""

        req = testing.create_dummy_controller_request()

        assert req.request_line == ""
        assert isinstance(req, contract.IControllerRequest)

    def test_create_dummy_controller_request_with_text(self) -> None:
        """Ensure create_dummy_controller_request retains provided input line."""

        req = testing.create_dummy_controller_request("command arg1 arg2")

        assert req.request_line == "command arg1 arg2"


class TestMemoryTransportPairFactory:
    """Verify behavior of create_memory_transport_pair factory."""

    def test_create_memory_transport_pair_returns_connected_endpoints(self) -> None:
        """Ensure create_memory_transport_pair returns client and server endpoints."""

        client, server = testing.create_memory_transport_pair()
        try:
            assert isinstance(client, testing.MemoryTransport)
            assert isinstance(server, testing.MemoryTransport)
            assert client.peer_address == "memory://server"
            assert server.peer_address == "memory://client"
        finally:
            client.close()
            server.close()
