from declusor import core, presentation, testing, transport


class TestApplicationE2E:
    """End-to-end integration tests for Application lifecycle and execution."""

    def test_application_run_in_memory_e2e(self) -> None:
        """Exercise complete Application lifecycle end-to-end using in-memory transports and doubles."""

        router = core.Router()
        view = testing.DummyView()
        input_source = testing.DummyInputSource(["command whoami", "exit"])
        prompt_loop = presentation.PromptLoop("declusor_test", router=router, session=None)

        plugin_manager = core.PluginManager()
        plugin_manager.register(testing.DummyPlugin)

        client_tx, server_tx = testing.create_memory_transport_pair()
        listener = testing.MemoryTransportListener(incoming_transports=[server_tx])

        app = core.Application(
            router,
            view,
            plugin_manager=plugin_manager,
            session_runner=prompt_loop,
            input_source=input_source,
            listener_factory=lambda host, port: listener,
        )

        plugin_config = testing.create_dummy_plugin_config(
            kind=testing.DummyPlugin.name,
            host="127.0.0.1",
            port=9999,
        )

        app.run(plugin_config)

        # 1. Launcher was rendered to view
        assert any("dummy" in msg or "127.0.0.1" in msg for msg in view.messages)

        # 2. Listener accepted connection and closed
        assert listener.is_closed is True
        assert listener.accepted_count == 1

        # 3. Router dispatched commands
        assert "command" in router.routes
        assert "exit" in router.routes

        # 4. View captured the streamed execution output chunks from DummyConnection
        assert view.binary_data == [b"chunk1\n", b"chunk2\n"]

    def test_application_run_with_xor_transport_pipeline_e2e(self) -> None:
        """Exercise Application.run with XOR encryption transport layer pipeline end-to-end."""

        router = core.Router()
        view = testing.DummyView()
        input_source = testing.DummyInputSource(["command id", "exit"])
        prompt_loop = presentation.PromptLoop("declusor_test", router=router, session=None)

        plugin_manager = core.PluginManager()
        plugin_manager.register(testing.DummyPlugin)

        client_tx, server_tx = testing.create_memory_transport_pair()
        listener = testing.MemoryTransportListener(incoming_transports=[server_tx])

        transport_registry = transport.default_transport_registry()

        app = core.Application(
            router,
            view,
            plugin_manager=plugin_manager,
            session_runner=prompt_loop,
            input_source=input_source,
            listener_factory=lambda host, port: listener,
            transport_registry=transport_registry,
        )

        plugin_config = testing.create_dummy_plugin_config(
            kind=testing.DummyPlugin.name,
            host="127.0.0.1",
            port=9999,
            transport_layers=("xor",),
        )

        app.run(plugin_config)

        assert listener.is_closed is True
        assert listener.accepted_count == 1
        assert view.binary_data == [b"chunk1\n", b"chunk2\n"]
