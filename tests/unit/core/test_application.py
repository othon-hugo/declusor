"""Unit tests for Application orchestration and connection lifecycle in declusor.core.application."""

from collections.abc import Sequence
from pathlib import Path

import pytest

from declusor import config, contract, controller, core, testing, transport


class CompleterInputSource(testing.DummyInputSource):
    """Test double input source supporting setup_completer hook."""

    def __init__(self, inputs: Sequence[str] | None = None) -> None:
        super().__init__(inputs)
        self.completer_routes: tuple[str, ...] | None = None
        self.assets_dir: Path | None = None

    def setup_completer(self, routes: tuple[str, ...], assets_dir: Path | None = None, /) -> None:
        self.completer_routes = routes
        self.assets_dir = assets_dir


class TestApplicationInitialization:
    """Tests verifying Application dependency injection and route initialization."""

    def test_application__init__registers_all_nine_core_routes(self) -> None:
        """Application registers all core command routes upon initialization."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()
        input_source = testing.DummyInputSource()

        app = core.Application(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
            input_source=input_source,
        )

        expected_routes = {"help", "execute", "load", "shell", "upload", "command", "code", "eval", "exit"}
        assert expected_routes.issubset(set(app._router.routes))
        assert len(app._router.routes) >= 9

    def test_application__init__binds_controllers_to_expected_routes(self) -> None:
        """Application registers canonical controller functions for all standard routes."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        app = core.Application(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
        )

        assert app._router.locate("load") is controller.call_load
        assert app._router.locate("command") is controller.call_command
        assert app._router.locate("code") is controller.call_code
        assert app._router.locate("eval") is controller.call_code
        assert app._router.locate("shell") is controller.call_shell
        assert app._router.locate("upload") is controller.call_upload
        assert app._router.locate("execute") is controller.call_execute
        assert app._router.locate("exit") is controller.call_exit
        assert callable(app._router.locate("help"))

    def test_application__init_positional_only__rejects_keyword_arguments(self) -> None:
        """Application.__init__ enforces positional-only router and view parameters."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        with pytest.raises(TypeError, match="positional-only"):
            core.Application(
                router=router,  # type: ignore[call-arg]
                view=view,
                plugin_manager=manager,
                session_runner=runner,
            )

    def test_application__init_existing_route_collision__raises_duplicate_route_error(self) -> None:
        """When the router already has a core route registered, initialization raises DuplicateRouteError."""

        router = core.Router()
        router.connect("help", controller.call_exit)
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        with pytest.raises(config.DuplicateRouteError) as exc_info:
            core.Application(
                router,
                view,
                plugin_manager=manager,
                session_runner=runner,
            )

        assert exc_info.value.route == "help"

    def test_application__properties__exposes_injected_registry_and_plugin_manager(self) -> None:
        """Application exposes transport_registry and plugin_manager via properties."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()
        custom_registry = transport.TransportLayerRegistry()

        app = core.Application(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
            transport_registry=custom_registry,
        )

        assert app.plugin_manager is manager
        assert app.transport_registry is custom_registry

    def test_application__init_defaults__initializes_default_listener_factory_renderer_and_registry(self) -> None:
        """When optional dependencies are omitted, default implementations are used."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        app = core.Application(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
        )

        assert app._listener_factory is transport.TcpListener
        assert isinstance(app._launcher_renderer, core.LauncherRenderer)
        assert app.transport_registry is not None

    def test_application__register_plugin__delegates_registration_to_plugin_manager(self) -> None:
        """register_plugin registers client plugin directly in plugin_manager."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        app = core.Application(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
        )

        testing.DummyPlugin.reset()
        app.register_plugin(testing.DummyPlugin)

        assert testing.DummyPlugin.name in app.plugin_manager.names()

    def test_application__register_plugin_positional_only__rejects_keyword_arguments(self) -> None:
        """The register_plugin method enforces positional-only plugin argument."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        app = core.Application(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
        )

        testing.DummyPlugin.reset()
        with pytest.raises(TypeError, match="positional-only"):
            app.register_plugin(plugin=testing.DummyPlugin)  # type: ignore[call-arg]


class TestApplicationLifecycle:
    """Tests verifying Application.run lifecycle coordination."""

    def test_application_run__standard_lifecycle__renders_launcher_completes_handshake_and_runs_session(self, tmp_path: Path) -> None:
        """Application.run orchestrates launcher delivery, listener accept, handshake, and runner."""

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(
            client_script="launcher_script_payload",
            connection_to_return=dummy_conn,
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

        app = core.Application(
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
            port=9000,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
        )

        app.run(plugin_config)

        assert dummy_conn.initialize_called
        assert "launcher_script_payload" in view.messages
        assert len(runner.run_calls) == 1

        active_session, active_router = runner.run_calls[0]
        assert active_router is router
        assert active_session.connection is dummy_conn
        assert active_session.view is view
        assert active_session.input is input_source
        assert active_session.plugin is dummy_runtime.processor
        assert dummy_conn.closed is True
        assert listener.is_closed is True

    def test_application_run__with_input_source_completer__passes_registered_routes_to_setup_completer(self, tmp_path: Path) -> None:
        """When input_source defines setup_completer, application passes router routes to it."""

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

        app = core.Application(
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
            port=9000,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
        )

        app.run(plugin_config)

        assert input_source.completer_routes is not None
        assert set(input_source.completer_routes) == set(router.routes)
        assert input_source.assets_dir == fs.assets

    def test_application_run__with_legacy_single_arg_setup_completer__passes_routes_gracefully(self, tmp_path: Path) -> None:
        """When input_source defines a single-arg setup_completer, application passes router routes gracefully."""

        class LegacyCompleterInputSource(testing.DummyInputSource):
            def __init__(self) -> None:
                super().__init__()
                self.completer_routes: tuple[str, ...] | None = None

            def setup_completer(self, routes: tuple[str, ...], /) -> None:
                self.completer_routes = routes

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        router = core.Router()
        view = testing.DummyView()
        input_source = LegacyCompleterInputSource()
        runner = testing.DummySessionRunner()

        listener = testing.MemoryTransportListener()
        _ = listener.create_client()

        app = core.Application(
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
            port=9000,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
        )

        app.run(plugin_config)

        assert input_source.completer_routes is not None
        assert set(input_source.completer_routes) == set(router.routes)

    def test_application_run__input_source_none__runs_cleanly_with_none_input_source_in_session(self, tmp_path: Path) -> None:
        """When input_source is None, session is initialized with input_source=None."""

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

        app = core.Application(
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
            port=9000,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
        )

        app.run(plugin_config)

        assert len(runner.run_calls) == 1
        active_session, _ = runner.run_calls[0]
        assert active_session.input is None

    def test_application_run__silent_launcher_output_mode__suppresses_launcher_in_view(self, tmp_path: Path) -> None:
        """When launcher_output_mode is SILENT, view receives no messages."""

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(
            client_script="secret_launcher",
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

        app = core.Application(
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

        app.run(plugin_config)

        assert len(view.messages) == 0

    def test_application_run__file_launcher_output_mode__writes_launcher_to_file(self, tmp_path: Path) -> None:
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

        app = core.Application(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
            listener_factory=lambda host, port: listener,
        )

        output_file = tmp_path / "out" / "launcher.sh"
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

        app.run(plugin_config)

        assert output_file.is_file()
        assert output_file.read_text(encoding="utf-8") == "file_launcher_payload"
        assert len(view.messages) == 0

    def test_application_run__custom_launcher_wrapper__applies_wrapper_template_override(self, tmp_path: Path) -> None:
        """When launcher_wrapper is specified on config, it overrides delivery wrapper template."""

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(
            client_script="raw_script",
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

        app = core.Application(
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
            launcher_wrapper="python3 -c '$DECLUSOR_SCRIPT'",
        )

        app.run(plugin_config)

        assert "python3 -c 'raw_script'" in view.messages

    def test_application_run__default_launcher_wrapper_on_delivery__preserves_delivery_wrapper_when_config_is_none(self, tmp_path: Path) -> None:
        """When config.launcher_wrapper is None, delivery.wrapper_template is preserved."""

        dummy_conn = testing.DummyConnection()
        delivery = contract.LauncherDelivery(
            script=b"stager",
            wrapper_template="/bin/sh -c '$DECLUSOR_SCRIPT'",
        )
        dummy_runtime = testing.DummyPluginRuntime(
            connection_to_return=dummy_conn,
            launcher_delivery=delivery,
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

        app = core.Application(
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
            launcher_wrapper=None,
        )

        app.run(plugin_config)

        assert "/bin/sh -c 'stager'" in view.messages

    def test_application_run_positional_only__rejects_keyword_arguments(self, tmp_path: Path) -> None:
        """The run method enforces positional-only config parameter delivery."""

        router = core.Router()
        view = testing.DummyView()
        manager = core.PluginManager()
        runner = testing.DummySessionRunner()

        app = core.Application(
            router,
            view,
            plugin_manager=manager,
            session_runner=runner,
        )

        fs = contract.PluginFilesystem.from_root(tmp_path)
        plugin_config = contract.PluginConfig(
            kind="dummy",
            host="127.0.0.1",
            port=9000,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
        )

        with pytest.raises(TypeError, match="positional-only"):
            app.run(config=plugin_config)  # type: ignore[call-arg]

    def test_application_run__passes_config_host_and_port_to_listener_factory(self, tmp_path: Path) -> None:
        """Application.run invokes listener_factory with host and port from config."""

        listener = testing.MemoryTransportListener()
        _ = listener.create_client()
        captured_endpoints: list[tuple[str, int]] = []

        def tracking_listener_factory(host: str, port: int) -> contract.ITransportListener:
            captured_endpoints.append((host, port))
            return listener

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        app = core.Application(
            core.Router(),
            testing.DummyView(),
            plugin_manager=manager,
            session_runner=testing.DummySessionRunner(),
            listener_factory=tracking_listener_factory,
        )

        fs = contract.PluginFilesystem.from_root(tmp_path)
        plugin_config = contract.PluginConfig(
            kind=testing.DummyPlugin.name,
            host="192.168.1.100",
            port=4444,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
        )

        app.run(plugin_config)

        assert captured_endpoints == [("192.168.1.100", 4444)]
        assert listener.is_closed is True
        assert dummy_conn.closed is True

    def test_application_run__unknown_plugin_kind__raises_plugin_not_found_error_before_listener(self, tmp_path: Path) -> None:
        """Application.run raises PluginNotFoundError when config.kind is not registered in manager."""

        listener_created = False

        def tracking_listener_factory(host: str, port: int) -> contract.ITransportListener:
            nonlocal listener_created
            listener_created = True
            return testing.MemoryTransportListener()

        manager = core.PluginManager()
        app = core.Application(
            core.Router(),
            testing.DummyView(),
            plugin_manager=manager,
            session_runner=testing.DummySessionRunner(),
            listener_factory=tracking_listener_factory,
        )

        fs = contract.PluginFilesystem.from_root(tmp_path)
        plugin_config = contract.PluginConfig(
            kind="unregistered_kind",
            host="127.0.0.1",
            port=9000,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
        )

        with pytest.raises(config.PluginNotFoundError) as exc_info:
            app.run(plugin_config)

        assert exc_info.value.plugin_name == "unregistered_kind"
        assert listener_created is False

    def test_application_run__launcher_delivery_failure__raises_launcher_delivery_error_before_listener(self, tmp_path: Path) -> None:
        """Application.run raises LauncherDeliveryError when launcher rendering fails, before listener creation."""

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

        app = core.Application(
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
            port=9000,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
            launcher_output_mode=config.LauncherOutputMode.FILE,
            launcher_output_path=None,
        )

        with pytest.raises(config.LauncherDeliveryError, match="output_path must be set"):
            app.run(plugin_config)

        assert listener_created is False

    def test_application_run__listener_accept_error__propagates_exception_and_closes_listener(self, tmp_path: Path) -> None:
        """Application.run propagates listener accept exception and guarantees listener cleanup."""

        class FailingListener(testing.MemoryTransportListener):
            def accept(self, timeout: float | None = None) -> contract.ITransport:
                raise config.ConnectionError("Listener accept encountered an unrecoverable network failure.")

        failing_listener = FailingListener()

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        app = core.Application(
            core.Router(),
            testing.DummyView(),
            plugin_manager=manager,
            session_runner=testing.DummySessionRunner(),
            listener_factory=lambda host, port: failing_listener,
        )

        fs = contract.PluginFilesystem.from_root(tmp_path)
        plugin_config = contract.PluginConfig(
            kind=testing.DummyPlugin.name,
            host="127.0.0.1",
            port=9000,
            options=contract.ParsedArguments(),
            options_type=contract.ParsedArguments,
            filesystem=fs,
        )

        with pytest.raises(config.ConnectionError, match="Listener accept encountered"):
            app.run(plugin_config)

        assert failing_listener.is_closed is True

    def test_application_run__connection_handshake_error__propagates_and_closes_connection_and_listener(self, tmp_path: Path) -> None:
        """Application.run propagates handshake failure and guarantees connection and listener cleanup."""

        listener = testing.MemoryTransportListener()
        _ = listener.create_client()

        dummy_conn = testing.DummyConnection()
        dummy_conn.initialize_error = config.ConnectionError("Protocol handshake timed out.")
        dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        app = core.Application(
            core.Router(),
            testing.DummyView(),
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
        )

        with pytest.raises(config.ConnectionError, match="Protocol handshake timed out"):
            app.run(plugin_config)

        assert dummy_conn.closed is True
        assert listener.is_closed is True

    def test_application_run__session_runner_error__propagates_and_closes_connection_and_listener(self, tmp_path: Path) -> None:
        """Application.run propagates session runner exception and guarantees connection and listener cleanup."""

        listener = testing.MemoryTransportListener()
        _ = listener.create_client()

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        runner = testing.DummySessionRunner(run_error=RuntimeError("Session execution aborted by user."))

        app = core.Application(
            core.Router(),
            testing.DummyView(),
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
        )

        with pytest.raises(RuntimeError, match="Session execution aborted by user"):
            app.run(plugin_config)

        assert dummy_conn.closed is True
        assert listener.is_closed is True

    def test_application_run__completer_setup_none__proceeds_without_error(self, tmp_path: Path) -> None:
        """Application.run handles an input source whose setup_completer attribute is None."""

        class InputSourceWithNoneCompleter(testing.DummyInputSource):
            setup_completer = None

        listener = testing.MemoryTransportListener()
        _ = listener.create_client()

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        app = core.Application(
            core.Router(),
            testing.DummyView(),
            plugin_manager=manager,
            session_runner=testing.DummySessionRunner(),
            input_source=InputSourceWithNoneCompleter(),
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
        )

        app.run(plugin_config)

        assert dummy_conn.closed is True
        assert listener.is_closed is True


class TestApplicationTransportPipelines:
    """Tests verifying composable transport layer pipeline wrapping in Application."""

    def test_application_run__no_transport_layers__passes_unwrapped_transport_to_connection(self, tmp_path: Path) -> None:
        """When transport_layers is empty, raw accepted transport is passed to connection."""

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

        app = core.Application(
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
            transport_layers=(),
        )

        app.run(plugin_config)

        assert len(dummy_runtime.received_transports) == 1
        assert isinstance(dummy_runtime.received_transports[0], testing.MemoryTransport)

    def test_application_run__single_transport_layer__wraps_accepted_transport(self, tmp_path: Path) -> None:
        """Application.run wraps the accepted transport with the configured transport layer."""

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

        app = core.Application(
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

        app.run(plugin_config)

        assert len(dummy_runtime.received_transports) == 1
        received = dummy_runtime.received_transports[0]
        assert isinstance(received, contract.ITransportLayer)
        assert isinstance(received.underlying, testing.MemoryTransport)

    def test_application_run__multiple_stacked_layers__wraps_transports_in_order(self, tmp_path: Path) -> None:
        """Application.run stacks multiple transport layers in order."""

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

        app = core.Application(
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
            transport_layers=("xor", "xor"),
        )

        app.run(plugin_config)

        assert len(dummy_runtime.received_transports) == 1
        outer = dummy_runtime.received_transports[0]
        assert isinstance(outer, contract.ITransportLayer)
        inner = outer.underlying
        assert isinstance(inner, contract.ITransportLayer)
        assert isinstance(inner.underlying, testing.MemoryTransport)
