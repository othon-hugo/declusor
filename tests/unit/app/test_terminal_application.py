"""Unit tests for TerminalApplication initialization, invariants, and lifecycle."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import pytest

from declusor import app, config, contract, controller, core, testing, transport


class CompleterInputSource(testing.DummyInputSource):
    """Test double input source supporting the setup_completer hook."""

    def __init__(self, inputs: Sequence[str] | None = None) -> None:
        super().__init__(inputs)
        self.completer_routes: tuple[str, ...] | None = None
        self.assets_dir: Path | None = None

    def setup_completer(self, routes: tuple[str, ...], assets_dir: Path | None = None, /) -> None:
        self.completer_routes = routes
        self.assets_dir = assets_dir


class TestTerminalApplicationInitialization:
    """Tests verifying TerminalApplication dependency injection and initialization."""

    def test_terminal_application__init_with_required_components__instantiates_successfully(self) -> None:
        """TerminalApplication initializes with required router, view, manager, and runner."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
        )

        assert isinstance(terminal_app, core.Application)
        assert isinstance(terminal_app, app.TerminalApplication)
        assert terminal_app.plugin_manager is manager
        assert terminal_app.router is router
        assert terminal_app.view is view
        assert terminal_app.session_runner is runner
        assert terminal_app.input_source is None
        assert terminal_app.transport_registry is not None
        assert isinstance(terminal_app._launcher_renderer, core.LauncherRenderer)
        assert terminal_app._listener_factory is transport.TcpListener

    def test_terminal_application__init_with_input_source__attaches_input_source(self) -> None:
        """TerminalApplication stores injected input source when provided."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()
        input_source = testing.DummyInputSource()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
            input_source=input_source,
        )

        assert terminal_app.input_source is input_source

    def test_terminal_application__init_with_custom_transport_registry__attaches_injected_registry(self) -> None:
        """TerminalApplication stores injected transport registry when provided."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()
        custom_registry = transport.TransportLayerRegistry()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
            transport_registry=custom_registry,
        )

        assert terminal_app.transport_registry is custom_registry

    def test_terminal_application__init_with_custom_launcher_renderer__attaches_injected_renderer(self) -> None:
        """TerminalApplication stores injected launcher renderer when provided."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()
        custom_renderer = core.LauncherRenderer(view)

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
            launcher_renderer=custom_renderer,
        )

        assert terminal_app._launcher_renderer is custom_renderer

    def test_terminal_application__init_with_custom_listener_factory__attaches_injected_factory(self) -> None:
        """TerminalApplication stores injected listener factory when provided."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()
        listener = testing.MemoryTransportListener()

        def custom_factory(host: str, port: int) -> contract.ITransportListener:
            return listener

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
            listener_factory=custom_factory,
        )

        assert terminal_app._listener_factory is custom_factory

    def test_terminal_application__is_subclass_of_core_application(self) -> None:
        """TerminalApplication is a subclass of core.Application."""

        assert issubclass(app.TerminalApplication, core.Application)

    def test_terminal_application__init_positional_only__rejects_keyword_router(self) -> None:
        """TerminalApplication.__init__ enforces positional-only router parameter."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        with pytest.raises(TypeError, match="positional-only"):
            app.TerminalApplication(
                router=router,  # type: ignore[call-arg]
                view=view,
                plugin_manager=manager,
                session_runner=runner,
            )

    def test_terminal_application__init_positional_only__rejects_keyword_view(self) -> None:
        """TerminalApplication.__init__ enforces positional-only view parameter."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        with pytest.raises(TypeError, match="positional-only"):
            app.TerminalApplication(
                router,
                view=view,  # type: ignore[call-arg]
                plugin_manager=manager,
                session_runner=runner,
            )

    def test_terminal_application__init_positional_only__rejects_both_keyword_router_and_view(self) -> None:
        """TerminalApplication.__init__ rejects router and view passed as keyword arguments."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        with pytest.raises(TypeError, match="positional-only"):
            cast(Any, app.TerminalApplication)(
                router=router,
                view=view,
                plugin_manager=manager,
                session_runner=runner,
            )

    def test_terminal_application__init_keyword_only__rejects_positional_plugin_manager(self) -> None:
        """TerminalApplication.__init__ enforces keyword-only plugin_manager parameter."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        with pytest.raises(TypeError):
            cast(Any, app.TerminalApplication)(
                router,
                view,
                manager,
                session_runner=runner,
            )

    def test_terminal_application__init_keyword_only__rejects_positional_session_runner(self) -> None:
        """TerminalApplication.__init__ enforces keyword-only session_runner parameter."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        with pytest.raises(TypeError):
            cast(Any, app.TerminalApplication)(
                router,
                view,
                runner,
                plugin_manager=manager,
            )

    def test_terminal_application__init_keyword_only__rejects_positional_input_source(self) -> None:
        """TerminalApplication.__init__ enforces keyword-only input_source parameter."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()
        input_source = testing.DummyInputSource()

        with pytest.raises(TypeError):
            cast(Any, app.TerminalApplication)(
                router,
                view,
                input_source,
                plugin_manager=manager,
                session_runner=runner,
            )

    def test_terminal_application__init_keyword_only__missing_required_plugin_manager__raises_type_error(self) -> None:
        """TerminalApplication.__init__ requires plugin_manager keyword argument."""

        router = core.Router()
        view = testing.DummyView()
        runner = testing.DummySessionRunner()

        with pytest.raises(TypeError, match="plugin_manager"):
            app.TerminalApplication(
                router,
                view,
                session_runner=runner,  # type: ignore[call-arg]
            )

    def test_terminal_application__init_keyword_only__missing_required_session_runner__raises_type_error(self) -> None:
        """TerminalApplication.__init__ requires session_runner keyword argument."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()

        with pytest.raises(TypeError, match="session_runner"):
            app.TerminalApplication(
                router,
                view,
                plugin_manager=manager,  # type: ignore[call-arg]
            )

    def test_terminal_application__init_duplicate_route__pre_existing_route_collision__raises_duplicate_route_error(
        self,
    ) -> None:
        """When router has a pre-existing standard route, initialization raises DuplicateRouteError."""

        router = core.Router()
        router.connect("help", controller.call_exit)
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        with pytest.raises(config.DuplicateRouteError) as exc_info:
            app.TerminalApplication(
                router,
                view,
                plugin_manager=manager,
                session_runner=runner,
            )

        assert exc_info.value.route == "help"

    def test_terminal_application__init_routes__registers_all_standard_routes(self) -> None:
        """TerminalApplication registers all canonical command routes upon initialization."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
        )

        expected_routes = {"help", "execute", "load", "shell", "upload", "command", "eval", "exit"}
        assert expected_routes.issubset(set(terminal_app.router.routes))
        assert len(terminal_app.router.routes) >= 8

    def test_terminal_application__init_routes__binds_expected_controllers(self) -> None:
        """TerminalApplication maps canonical routes to the expected controller functions."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
        )

        assert terminal_app.router.locate("load") is controller.call_load
        assert terminal_app.router.locate("command") is controller.call_command
        assert terminal_app.router.locate("eval") is controller.call_eval
        assert terminal_app.router.locate("shell") is controller.call_shell
        assert terminal_app.router.locate("upload") is controller.call_upload
        assert terminal_app.router.locate("execute") is controller.call_execute
        assert terminal_app.router.locate("exit") is controller.call_exit
        assert callable(terminal_app.router.locate("help"))


class TestTerminalApplicationMethods:
    """Tests verifying TerminalApplication methods and property accessors."""

    def test_register_plugin__delegates_registration_to_plugin_manager(self) -> None:
        """TerminalApplication.register_plugin delegates directly to the underlying PluginManager."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
        )

        testing.DummyPlugin.reset()
        terminal_app.register_plugin(testing.DummyPlugin)

        assert testing.DummyPlugin.name in terminal_app.plugin_manager.names()

    def test_register_plugin_positional_only__rejects_keyword_plugin(self) -> None:
        """TerminalApplication.register_plugin rejects plugin passed as keyword argument."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
        )

        testing.DummyPlugin.reset()
        with pytest.raises(TypeError, match="positional-only"):
            terminal_app.register_plugin(plugin=testing.DummyPlugin)  # type: ignore[call-arg]

    def test_plugin_manager_property__returns_injected_instance(self) -> None:
        """TerminalApplication.plugin_manager property exposes the injected manager."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
        )

        assert terminal_app.plugin_manager is manager

    def test_transport_registry_property__returns_active_registry(self) -> None:
        """TerminalApplication.transport_registry property exposes the transport registry."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()
        custom_registry = transport.TransportLayerRegistry()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
            transport_registry=custom_registry,
        )

        assert terminal_app.transport_registry is custom_registry

    def test_router_property__returns_injected_router(self) -> None:
        """TerminalApplication.router property exposes the active router."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
        )

        assert terminal_app.router is router

    def test_view_property__returns_injected_view(self) -> None:
        """TerminalApplication.view property exposes the active view."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
        )

        assert terminal_app.view is view

    def test_session_runner_property__returns_injected_session_runner(self) -> None:
        """TerminalApplication.session_runner property exposes the active session runner."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
        )

        assert terminal_app.session_runner is runner

    def test_input_source_property__returns_injected_input_source_or_none(self) -> None:
        """TerminalApplication.input_source property returns input source or None when omitted."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        app_without_input = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
        )
        assert app_without_input.input_source is None

        input_source = testing.DummyInputSource()
        app_with_input = app.TerminalApplication(
            core.Router(),
            testing.DummyView(),
            plugin_manager=manager,
            session_runner=runner,
            input_source=input_source,
        )
        assert app_with_input.input_source is input_source


class TestTerminalApplicationLifecycle:
    """Tests verifying TerminalApplication run execution and lifecycle integration."""

    def test_run__with_memory_transport_listener__executes_session_runner(self, tmp_path: Path) -> None:
        """TerminalApplication.run connects transport, delivers launcher, and executes runner."""

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(
            connection_to_return=dummy_conn,
            launcher_delivery=contract.LauncherDelivery(script=b"#!/bin/sh\necho repl_ready"),
        )
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        router = core.Router()
        view = testing.DummyView()
        input_source = testing.DummyInputSource()
        runner = testing.DummySessionRunner()

        listener = testing.MemoryTransportListener()
        _ = listener.create_client()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
            input_source=input_source,
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

        terminal_app.run(plugin_config)

        assert dummy_conn.initialize_called
        assert "echo repl_ready" in "\n".join(view.messages)
        assert len(runner.run_calls) == 1

        active_session, active_router = runner.run_calls[0]
        assert active_router is router
        assert active_session.connection is dummy_conn
        assert active_session.view is view
        assert active_session.input is input_source

    def test_run_positional_only__rejects_keyword_config(self, tmp_path: Path) -> None:
        """TerminalApplication.run rejects config passed as keyword argument."""

        manager = core.PluginManager()
        terminal_app = app.TerminalApplication(
            core.Router(),
            testing.DummyView(),
            plugin_manager=manager,
            session_runner=testing.DummySessionRunner(),
        )

        fs = contract.PluginFilesystem.from_root(tmp_path)
        plugin_config = contract.PluginConfig(
            kind="nonexistent",
            host="127.0.0.1",
            port=9999,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
        )

        with pytest.raises(TypeError, match="positional-only"):
            terminal_app.run(config=plugin_config)  # type: ignore[call-arg]

    def test_run__with_setup_completer_input_source__populates_completer_routes(self, tmp_path: Path) -> None:
        """TerminalApplication.run invokes setup_completer on input_source when supported."""

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        router = core.Router()
        view = testing.DummyView()
        input_source = CompleterInputSource()
        runner = testing.DummySessionRunner()

        listener = testing.MemoryTransportListener()
        _ = listener.create_client()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
            input_source=input_source,
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

        terminal_app.run(plugin_config)

        assert input_source.completer_routes == router.routes
        assert input_source.assets_dir == fs.assets

    def test_run__when_input_source_is_none__runs_cleanly(self, tmp_path: Path) -> None:
        """TerminalApplication.run executes cleanly when input_source is None."""

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        router = core.Router()
        view = testing.DummyView()
        runner = testing.DummySessionRunner()

        listener = testing.MemoryTransportListener()
        _ = listener.create_client()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
            input_source=None,
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

        terminal_app.run(plugin_config)

        assert len(runner.run_calls) == 1
        active_session, _ = runner.run_calls[0]
        assert active_session.input is None

    def test_run__unknown_plugin_kind__raises_plugin_not_found_error_before_listener(self, tmp_path: Path) -> None:
        """TerminalApplication.run raises PluginNotFoundError when kind is unmapped before listener creation."""

        listener_created = False

        def tracking_listener_factory(host: str, port: int) -> contract.ITransportListener:
            nonlocal listener_created
            listener_created = True
            return testing.MemoryTransportListener()

        manager = core.PluginManager()
        terminal_app = app.TerminalApplication(
            core.Router(),
            testing.DummyView(),
            plugin_manager=manager,
            session_runner=testing.DummySessionRunner(),
            listener_factory=tracking_listener_factory,
        )

        fs = contract.PluginFilesystem.from_root(tmp_path)
        plugin_config = contract.PluginConfig(
            kind="unregistered_plugin",
            host="127.0.0.1",
            port=9999,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
        )

        with pytest.raises(config.PluginNotFoundError) as exc_info:
            terminal_app.run(plugin_config)

        assert exc_info.value.plugin_name == "unregistered_plugin"
        assert listener_created is False

    def test_run__launcher_delivery_failure__raises_launcher_delivery_error_before_listener(
        self,
        tmp_path: Path,
    ) -> None:
        """TerminalApplication.run raises LauncherDeliveryError when launcher output fails before listener creation."""

        listener_created = False

        def tracking_listener_factory(host: str, port: int) -> contract.ITransportListener:
            nonlocal listener_created
            listener_created = True
            return testing.MemoryTransportListener()

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        terminal_app = app.TerminalApplication(
            core.Router(),
            testing.DummyView(),
            plugin_manager=manager,
            session_runner=testing.DummySessionRunner(),
            listener_factory=tracking_listener_factory,
        )

        fs = contract.PluginFilesystem.from_root(tmp_path)
        plugin_config = contract.PluginConfig(
            kind=testing.DummyPlugin.name,
            host="127.0.0.1",
            port=9999,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
            launcher_output_mode=config.LauncherOutputMode.FILE,
            launcher_output_path=None,
        )

        with pytest.raises(config.LauncherDeliveryError, match="output_path must be set"):
            terminal_app.run(plugin_config)

        assert listener_created is False

    def test_run__when_listener_fails__raises_connection_error(self, tmp_path: Path) -> None:
        """When the transport listener fails to accept a connection, ConnectionError is raised."""

        dummy_runtime = testing.DummyPluginRuntime()
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        router = core.Router()
        view = testing.DummyView()
        runner = testing.DummySessionRunner()

        listener = testing.MemoryTransportListener()
        listener.close()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
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

        with pytest.raises(config.ConnectionError, match="Cannot accept on closed listener"):
            terminal_app.run(plugin_config)

    def test_run__when_connection_handshake_fails__propagates_and_closes_resources(self, tmp_path: Path) -> None:
        """TerminalApplication.run propagates handshake failure and guarantees connection and listener cleanup."""

        listener = testing.MemoryTransportListener()
        _ = listener.create_client()

        dummy_conn = testing.DummyConnection()
        dummy_conn.initialize_error = config.ConnectionError("Protocol handshake timed out.")
        dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        router = core.Router()
        view = testing.DummyView()
        runner = testing.DummySessionRunner()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
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

        with pytest.raises(config.ConnectionError, match="Protocol handshake timed out."):
            terminal_app.run(plugin_config)

        assert dummy_conn.closed is True
        assert listener.is_closed is True

    def test_run__when_session_runner_raises_error__propagates_and_closes_connection(self, tmp_path: Path) -> None:
        """When the session runner raises an unhandled error, the error propagates and connection closes."""

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        router = core.Router()
        view = testing.DummyView()
        runner = testing.DummySessionRunner(run_error=RuntimeError("Terminal session interrupted"))

        listener = testing.MemoryTransportListener()
        _ = listener.create_client()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
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

        with pytest.raises(RuntimeError, match="Terminal session interrupted"):
            terminal_app.run(plugin_config)

        assert dummy_conn.closed
        assert dummy_conn.state == contract.ConnectionState.CLOSED
        assert listener.is_closed is True

    def test_run__with_silent_launcher_output_mode__suppresses_launcher_in_view(self, tmp_path: Path) -> None:
        """When launcher_output_mode is SILENT, the view receives no messages."""

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(
            client_script="secret_terminal_launcher",
            connection_to_return=dummy_conn,
        )
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        router = core.Router()
        view = testing.DummyView()
        runner = testing.DummySessionRunner()
        listener = testing.MemoryTransportListener()
        _ = listener.create_client()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
            listener_factory=lambda host, port: listener,
        )

        fs = contract.PluginFilesystem.from_root(tmp_path)
        plugin_config = contract.PluginConfig(
            kind=testing.DummyPlugin.name,
            host="127.0.0.1",
            port=9000,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
            launcher_output_mode=config.LauncherOutputMode.SILENT,
        )

        terminal_app.run(plugin_config)

        assert len(view.messages) == 0

    def test_run__with_file_launcher_output_mode__writes_launcher_to_file(self, tmp_path: Path) -> None:
        """When launcher_output_mode is FILE, launcher script is written to target file."""

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(
            client_script="file_launcher_payload",
            connection_to_return=dummy_conn,
        )
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        router = core.Router()
        view = testing.DummyView()
        runner = testing.DummySessionRunner()
        listener = testing.MemoryTransportListener()
        _ = listener.create_client()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
            listener_factory=lambda host, port: listener,
        )

        output_file = tmp_path / "out" / "terminal_launcher.sh"
        fs = contract.PluginFilesystem.from_root(tmp_path)
        plugin_config = contract.PluginConfig(
            kind=testing.DummyPlugin.name,
            host="127.0.0.1",
            port=9000,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
            launcher_output_mode=config.LauncherOutputMode.FILE,
            launcher_output_path=output_file,
        )

        terminal_app.run(plugin_config)

        assert output_file.exists()
        assert output_file.read_text(encoding="utf-8") == "file_launcher_payload"

    def test_run__custom_launcher_wrapper__applies_wrapper_template_override(self, tmp_path: Path) -> None:
        """TerminalApplication.run applies wrapper template override specified in plugin config."""

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(
            client_script="echo test_payload",
            connection_to_return=dummy_conn,
        )
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        view = testing.DummyView()
        listener = testing.MemoryTransportListener()
        _ = listener.create_client()
        terminal_app = app.TerminalApplication(
            core.Router(),
            view,
            plugin_manager=manager,
            session_runner=testing.DummySessionRunner(),
            listener_factory=lambda host, port: listener,
        )

        fs = contract.PluginFilesystem.from_root(tmp_path)
        plugin_config = contract.PluginConfig(
            kind=testing.DummyPlugin.name,
            host="127.0.0.1",
            port=9000,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
            launcher_wrapper="CUSTOM_WRAPPER: $DECLUSOR_SCRIPT :END",
        )

        terminal_app.run(plugin_config)

        assert "CUSTOM_WRAPPER: echo test_payload :END" in "\n".join(view.messages)

    def test_run__transport_pipeline__wraps_accepted_transport_with_configured_layers(self, tmp_path: Path) -> None:
        """TerminalApplication.run wraps accepted transport through configured transport layers."""

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        router = core.Router()
        view = testing.DummyView()
        runner = testing.DummySessionRunner()
        listener = testing.MemoryTransportListener()
        _ = listener.create_client()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
            listener_factory=lambda host, port: listener,
        )

        fs = contract.PluginFilesystem.from_root(tmp_path)
        plugin_config = contract.PluginConfig(
            kind=testing.DummyPlugin.name,
            host="127.0.0.1",
            port=9000,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
            transport_layers=("xor",),
        )

        terminal_app.run(plugin_config)

        assert len(dummy_runtime.received_transports) == 1
        received = dummy_runtime.received_transports[0]
        assert isinstance(received, contract.ITransportLayer)
        assert isinstance(received.underlying, testing.MemoryTransport)

    def test_run__session_context__contains_all_injected_components(self, tmp_path: Path) -> None:
        """TerminalApplication passes complete SessionContext to the session runner."""

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        router = core.Router()
        view = testing.DummyView()
        input_source = testing.DummyInputSource()
        runner = testing.DummySessionRunner()
        listener = testing.MemoryTransportListener()
        _ = listener.create_client()

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
            input_source=input_source,
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

        terminal_app.run(plugin_config)

        assert len(runner.run_calls) == 1
        active_session, active_router = runner.run_calls[0]
        assert active_session.connection is dummy_conn
        assert active_session.view is view
        assert active_session.input is input_source
        assert active_session.plugin is dummy_runtime.processor
        assert active_router is router

    def test_run__multiple_sequential_runs__executes_cleanly(self, tmp_path: Path) -> None:
        """TerminalApplication instance supports multiple sequential execution runs."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        router = core.Router()
        view = testing.DummyView()
        runner = testing.DummySessionRunner()

        listener_1 = testing.MemoryTransportListener()
        _ = listener_1.create_client()
        listener_2 = testing.MemoryTransportListener()
        _ = listener_2.create_client()

        listeners = [listener_1, listener_2]

        terminal_app = app.TerminalApplication(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
            listener_factory=lambda host, port: listeners.pop(0),
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

        terminal_app.run(plugin_config)
        terminal_app.run(plugin_config)

        assert len(runner.run_calls) == 2
