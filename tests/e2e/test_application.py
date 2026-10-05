import shlex
import subprocess
import sys

import declusor_py_socket as py_socket

from declusor import config, core, presentation, testing, transport


class TestApplicationE2E:
    """End-to-end integration tests for Application lifecycle and execution."""

    def test_application_run__client_disconnect_during_command__reports_error_and_closes_listener(self) -> None:
        """Report a real client disconnect during command I/O and release the listener."""

        listener = transport.TcpListener("127.0.0.1", 0)
        plugin_config = py_socket.PySocketPlugin.build_config(
            "127.0.0.1",
            listener.port,
            py_socket.PySocketPlugin.extract_options({}),
        )
        runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)
        launcher_command = shlex.split(runtime.launcher.wrapped_text)
        launcher_command[0] = sys.executable

        client_process: subprocess.Popen[bytes] | None = None

        def disconnect_then_run_command(prompt: str) -> str:
            assert client_process is not None
            client_process.kill()
            client_process.wait(timeout=5.0)
            return "command 'echo should_not_run'"

        router = core.Router()
        view = testing.DummyView()
        input_source = presentation.TerminalInputSource(reader=disconnect_then_run_command)
        session_runner = presentation.PromptLoop("declusor_disconnect_e2e", router=router, session=None)
        plugin_manager = core.PluginManager()
        plugin_manager.register(py_socket.PySocketPlugin)
        app = core.Application(
            router,
            view,
            plugin_manager=plugin_manager,
            session_runner=session_runner,
            input_source=input_source,
            listener_factory=lambda host, port: listener,
        )

        try:
            client_process = subprocess.Popen(
                launcher_command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            app.run(plugin_config)

            assert len(view.errors) == 1
            assert isinstance(view.errors[0], config.ConnectionClosed)
            assert listener.is_closed
        finally:
            listener.close()
            if client_process is not None:
                if client_process.poll() is None:
                    client_process.kill()
                client_process.wait(timeout=5.0)

    def test_application_run__built_in_python_client__dispatches_repl_command(self) -> None:
        """Exercise the full application path with a spawned built-in Python agent."""

        listener = transport.TcpListener("127.0.0.1", 0)
        plugin_config = py_socket.PySocketPlugin.build_config(
            "127.0.0.1",
            listener.port,
            py_socket.PySocketPlugin.extract_options({}),
        )
        runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)
        launcher_command = shlex.split(runtime.launcher.wrapped_text)
        launcher_command[0] = sys.executable

        router = core.Router()
        view = testing.DummyView()
        input_source = testing.DummyInputSource(["command 'echo declusor_real_client_e2e'", "exit"])
        session_runner = presentation.PromptLoop("declusor_e2e", router=router, session=None)
        plugin_manager = core.PluginManager()
        plugin_manager.register(py_socket.PySocketPlugin)
        app = core.Application(
            router,
            view,
            plugin_manager=plugin_manager,
            session_runner=session_runner,
            input_source=input_source,
            listener_factory=lambda host, port: listener,
        )

        client_process: subprocess.Popen[bytes] | None = None

        try:
            client_process = subprocess.Popen(
                launcher_command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            app.run(plugin_config)

            response = b"".join(view.binary_data)
            assert b"declusor_real_client_e2e" in response, (
                f"unexpected response {response!r}; errors={view.errors!r}; messages={view.messages!r}; prompts={input_source.prompts!r}"
            )
            assert listener.is_closed
            assert client_process.wait(timeout=5.0) == 0
        finally:
            listener.close()
            if client_process is not None:
                if client_process.poll() is None:
                    client_process.kill()
                client_process.wait(timeout=5.0)

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
