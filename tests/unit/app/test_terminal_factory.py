"""Unit tests for create_terminal_application factory and automated bootstrap wiring."""

from pathlib import Path

import pytest

from declusor import app, config, contract, core, presentation, testing, transport


class TestCreateTerminalApplicationDefaults:
    """Tests verifying default bootstrap behavior of create_terminal_application."""

    def test_create_terminal_application__default_args__returns_terminal_application_instance(self) -> None:
        """create_terminal_application returns an instance of TerminalApplication and core.Application."""

        declusor_app = app.create_terminal_application()

        assert isinstance(declusor_app, app.TerminalApplication)
        assert isinstance(declusor_app, core.Application)

    def test_create_terminal_application__default_args__discovers_builtin_plugins(self) -> None:
        """create_terminal_application discovers built-in plugins by default."""

        declusor_app = app.create_terminal_application()

        plugin_names = declusor_app.plugin_manager.names()
        assert "shell_socket" in plugin_names
        assert "py_socket" in plugin_names

    def test_create_terminal_application__default_args__wires_router_with_canonical_routes(self) -> None:
        """create_terminal_application wires router with all standard command routes."""

        declusor_app = app.create_terminal_application()

        expected_routes = {"help", "execute", "load", "shell", "upload", "command", "eval", "exit"}
        assert expected_routes.issubset(set(declusor_app.router.routes))
        assert len(declusor_app.router.routes) >= 8

    def test_create_terminal_application__default_args__wires_terminal_view(self) -> None:
        """create_terminal_application wires an interactive TerminalView."""

        declusor_app = app.create_terminal_application()

        assert isinstance(declusor_app.view, presentation.TerminalView)

    def test_create_terminal_application__default_args__wires_terminal_input_source(self) -> None:
        """create_terminal_application wires a TerminalInputSource."""

        declusor_app = app.create_terminal_application()

        assert isinstance(declusor_app.input_source, presentation.TerminalInputSource)

    def test_create_terminal_application__default_args__wires_prompt_loop_session_runner(self) -> None:
        """create_terminal_application wires a PromptLoop session runner configured with project name."""

        declusor_app = app.create_terminal_application()

        assert isinstance(declusor_app.session_runner, presentation.PromptLoop)
        assert declusor_app.session_runner._prompt == f"[{config.PROJECT_NAME}] "

    def test_create_terminal_application__default_args__wires_default_transport_registry(self) -> None:
        """create_terminal_application initializes default transport registry."""

        declusor_app = app.create_terminal_application()

        assert isinstance(declusor_app.transport_registry, transport.TransportLayerRegistry)
        assert "xor" in declusor_app.transport_registry.names()

    def test_create_terminal_application__default_args__wires_default_launcher_renderer(self) -> None:
        """create_terminal_application initializes default launcher renderer bound to view."""

        declusor_app = app.create_terminal_application()

        assert isinstance(declusor_app._launcher_renderer, core.LauncherRenderer)

    def test_create_terminal_application__default_args__wires_tcp_listener_factory(self) -> None:
        """create_terminal_application initializes default TcpListener factory."""

        declusor_app = app.create_terminal_application()

        assert declusor_app._listener_factory is transport.TcpListener

    def test_create_terminal_application__multiple_calls__produce_independent_instances(self) -> None:
        """Sequential factory calls produce independent application and component instances."""

        app_1 = app.create_terminal_application()
        app_2 = app.create_terminal_application()

        assert app_1 is not app_2
        assert app_1.router is not app_2.router
        assert app_1.view is not app_2.view
        assert app_1.input_source is not app_2.input_source
        assert app_1.session_runner is not app_2.session_runner
        assert app_1.plugin_manager is not app_2.plugin_manager


class TestCreateTerminalApplicationInjectedDependencies:
    """Tests verifying create_terminal_application behavior with injected dependencies."""

    def test_create_terminal_application__with_custom_plugin_manager__bypasses_default_discovery(self) -> None:
        """create_terminal_application uses injected plugin manager without running discovery."""

        custom_manager = core.PluginManager()
        testing.DummyPlugin.reset()
        custom_manager.register(testing.DummyPlugin)

        declusor_app = app.create_terminal_application(plugin_manager=custom_manager)

        assert declusor_app.plugin_manager is custom_manager
        assert declusor_app.plugin_manager.names() == (testing.DummyPlugin.name,)
        assert "shell_socket" not in declusor_app.plugin_manager.names()

    def test_create_terminal_application__with_search_dirs__passes_search_dirs_to_discovery(
        self,
        tmp_path: Path,
    ) -> None:
        """create_terminal_application passes search_dirs to plugin manager discovery."""

        declusor_app = app.create_terminal_application(search_dirs=[tmp_path])

        assert isinstance(declusor_app, app.TerminalApplication)
        assert "shell_socket" in declusor_app.plugin_manager.names()

    def test_create_terminal_application__with_empty_search_dirs__discovers_builtin_plugins(self) -> None:
        """create_terminal_application with empty search_dirs still discovers built-in plugins."""

        declusor_app = app.create_terminal_application(search_dirs=[])

        assert isinstance(declusor_app, app.TerminalApplication)
        assert "shell_socket" in declusor_app.plugin_manager.names()

    def test_create_terminal_application__with_custom_transport_registry__attaches_injected_registry(self) -> None:
        """create_terminal_application forwards custom transport registry to application."""

        custom_registry = transport.TransportLayerRegistry()

        declusor_app = app.create_terminal_application(transport_registry=custom_registry)

        assert declusor_app.transport_registry is custom_registry

    def test_create_terminal_application__with_custom_listener_factory__attaches_injected_factory(self) -> None:
        """create_terminal_application forwards custom listener factory to application."""

        listener = testing.MemoryTransportListener()

        def custom_factory(host: str, port: int) -> contract.ITransportListener:
            return listener

        declusor_app = app.create_terminal_application(listener_factory=custom_factory)

        assert declusor_app._listener_factory is custom_factory

    def test_create_terminal_application__with_custom_launcher_renderer__attaches_injected_renderer(self) -> None:
        """create_terminal_application forwards custom launcher renderer to application."""

        custom_view = testing.DummyView()
        custom_renderer = core.LauncherRenderer(custom_view)

        declusor_app = app.create_terminal_application(launcher_renderer=custom_renderer)

        assert declusor_app._launcher_renderer is custom_renderer

    def test_create_terminal_application__with_custom_router__attaches_injected_router(self) -> None:
        """create_terminal_application forwards custom router and registers standard routes."""

        custom_router = core.Router()

        declusor_app = app.create_terminal_application(router=custom_router)

        assert declusor_app.router is custom_router
        assert "help" in custom_router.routes

    def test_create_terminal_application__with_custom_view__attaches_injected_view(self) -> None:
        """create_terminal_application forwards custom view to application."""

        custom_view = testing.DummyView()

        declusor_app = app.create_terminal_application(view=custom_view)

        assert declusor_app.view is custom_view

    def test_create_terminal_application__with_custom_input_source__attaches_injected_input_source(self) -> None:
        """create_terminal_application forwards custom input source to application."""

        custom_input = testing.DummyInputSource()

        declusor_app = app.create_terminal_application(input_source=custom_input)

        assert declusor_app.input_source is custom_input

    def test_create_terminal_application__with_custom_session_runner__attaches_injected_session_runner(self) -> None:
        """create_terminal_application forwards custom session runner to application."""

        custom_runner = testing.DummySessionRunner()

        declusor_app = app.create_terminal_application(session_runner=custom_runner)

        assert declusor_app.session_runner is custom_runner

    def test_create_terminal_application__with_all_injected_parameters(self, tmp_path: Path) -> None:
        """create_terminal_application honors all injected dependencies simultaneously."""

        custom_manager = core.PluginManager()
        testing.DummyPlugin.reset()
        custom_manager.register(testing.DummyPlugin)

        custom_registry = transport.TransportLayerRegistry()
        custom_view = testing.DummyView()
        custom_renderer = core.LauncherRenderer(custom_view)
        custom_router = core.Router()
        custom_input = testing.DummyInputSource()
        custom_runner = testing.DummySessionRunner()
        listener = testing.MemoryTransportListener()

        def custom_factory(host: str, port: int) -> contract.ITransportListener:
            return listener

        declusor_app = app.create_terminal_application(
            search_dirs=[tmp_path],
            plugin_manager=custom_manager,
            transport_registry=custom_registry,
            listener_factory=custom_factory,
            launcher_renderer=custom_renderer,
            router=custom_router,
            view=custom_view,
            input_source=custom_input,
            session_runner=custom_runner,
        )

        assert declusor_app.plugin_manager is custom_manager
        assert declusor_app.transport_registry is custom_registry
        assert declusor_app._listener_factory is custom_factory
        assert declusor_app._launcher_renderer is custom_renderer
        assert declusor_app.router is custom_router
        assert declusor_app.view is custom_view
        assert declusor_app.input_source is custom_input
        assert declusor_app.session_runner is custom_runner

    def test_create_terminal_application__orchestration_in_memory_run__executes_cleanly_without_live_io(
        self,
        tmp_path: Path,
    ) -> None:
        """create_terminal_application enables full in-memory agent orchestration and execution."""

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(
            connection_to_return=dummy_conn,
            launcher_delivery=contract.LauncherDelivery(script=b"#!/bin/sh\necho agent_ready"),
        )
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        custom_manager = core.PluginManager()
        custom_manager.register(testing.DummyPlugin)

        view = testing.DummyView()
        runner = testing.DummySessionRunner()
        listener = testing.MemoryTransportListener()
        _ = listener.create_client()

        orchestrated_app = app.create_terminal_application(
            plugin_manager=custom_manager,
            view=view,
            session_runner=runner,
            input_source=testing.DummyInputSource(),
            listener_factory=lambda host, port: listener,
        )

        fs = contract.PluginFilesystem.from_root(tmp_path)
        plugin_config = contract.PluginConfig(
            kind=testing.DummyPlugin.name,
            host="127.0.0.1",
            port=9999,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
        )

        orchestrated_app.run(plugin_config)

        assert dummy_conn.initialize_called
        assert "echo agent_ready" in "\n".join(view.messages)
        assert len(runner.run_calls) == 1


class TestCreateTerminalApplicationCallSignatures:
    """Tests verifying argument passing rules and call signatures of create_terminal_application."""

    def test_create_terminal_application_keyword_only__passing_plugin_manager_positionally__raises_type_error(
        self,
    ) -> None:
        """create_terminal_application rejects plugin_manager passed as positional argument."""

        manager = core.PluginManager()

        with pytest.raises(TypeError):
            app.create_terminal_application(None, manager)  # type: ignore[misc]

    def test_create_terminal_application_keyword_only__passing_transport_registry_positionally__raises_type_error(
        self,
    ) -> None:
        """create_terminal_application rejects transport_registry passed as positional argument."""

        registry = transport.TransportLayerRegistry()

        with pytest.raises(TypeError):
            app.create_terminal_application(None, None, registry)  # type: ignore[misc]

    def test_create_terminal_application_keyword_only__passing_listener_factory_positionally__raises_type_error(
        self,
    ) -> None:
        """create_terminal_application rejects listener_factory passed as positional argument."""

        with pytest.raises(TypeError):
            app.create_terminal_application(None, None, None, lambda h, p: testing.MemoryTransportListener())  # type: ignore[misc]

    def test_create_terminal_application_keyword_only__passing_launcher_renderer_positionally__raises_type_error(
        self,
    ) -> None:
        """create_terminal_application rejects launcher_renderer passed as positional argument."""

        renderer = core.LauncherRenderer(testing.DummyView())

        with pytest.raises(TypeError):
            app.create_terminal_application(None, None, None, None, renderer)  # type: ignore[misc]

    def test_create_terminal_application_keyword_only__passing_router_positionally__raises_type_error(self) -> None:
        """create_terminal_application rejects router passed as positional argument."""

        router = core.Router()

        with pytest.raises(TypeError):
            app.create_terminal_application(None, None, None, None, None, router)  # type: ignore[misc]

    def test_create_terminal_application_keyword_only__passing_view_positionally__raises_type_error(self) -> None:
        """create_terminal_application rejects view passed as positional argument."""

        view = testing.DummyView()

        with pytest.raises(TypeError):
            app.create_terminal_application(None, None, None, None, None, None, view)  # type: ignore[misc]

    def test_create_terminal_application_keyword_only__passing_input_source_positionally__raises_type_error(
        self,
    ) -> None:
        """create_terminal_application rejects input_source passed as positional argument."""

        source = testing.DummyInputSource()

        with pytest.raises(TypeError):
            app.create_terminal_application(None, None, None, None, None, None, None, source)  # type: ignore[misc]

    def test_create_terminal_application_keyword_only__passing_session_runner_positionally__raises_type_error(
        self,
    ) -> None:
        """create_terminal_application rejects session_runner passed as positional argument."""

        runner = testing.DummySessionRunner()

        with pytest.raises(TypeError):
            app.create_terminal_application(None, None, None, None, None, None, None, None, runner)  # type: ignore[misc]

    def test_create_terminal_application_positional__search_dirs_accepts_sequence_of_paths(
        self,
        tmp_path: Path,
    ) -> None:
        """create_terminal_application accepts search_dirs as first positional parameter."""

        declusor_app = app.create_terminal_application([tmp_path])

        assert isinstance(declusor_app, app.TerminalApplication)

    def test_create_terminal_application_keyword__search_dirs_accepts_keyword_argument(
        self,
        tmp_path: Path,
    ) -> None:
        """create_terminal_application accepts search_dirs as keyword parameter."""

        declusor_app = app.create_terminal_application(search_dirs=[tmp_path])

        assert isinstance(declusor_app, app.TerminalApplication)

    def test_create_terminal_application__none_search_dirs__behaves_identically_to_omitted(self) -> None:
        """Passing explicit search_dirs=None behaves identically to omitting it."""

        declusor_app = app.create_terminal_application(search_dirs=None)

        assert "shell_socket" in declusor_app.plugin_manager.names()
