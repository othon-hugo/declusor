import pytest

from declusor import config, contract, core, testing, util


class TestDummyPluginFileStore:
    """Verify behavior of the DummyPluginFileStore double."""

    def test_render_launcher_substitutions(self) -> None:
        """Ensure render_launcher substitutes host, port, and token into script."""

        store = testing.DummyPluginFileStore()
        rendered = store.render_launcher("10.0.0.1", 4444, b"\xaa\xbb")

        assert b"10.0.0.1" in rendered
        assert b"4444" in rendered
        assert b"aabb" in rendered
        assert len(store.render_calls) == 1

    def test_load_helpers(self) -> None:
        """Ensure load_all_helpers and load_helper return payloads and record calls."""

        store = testing.DummyPluginFileStore()

        helpers = store.load_all_helpers()
        assert helpers == {"default.sh": b"dummy_library_payload"}
        assert store.load_all_helpers_calls == 1

        helper = store.load_helper("default.sh")
        assert helper == b"dummy_library_payload"
        assert store.load_helper_calls == ["default.sh"]

    def test_load_modules_and_overrides(self) -> None:
        """Ensure load_module supports default and custom module registrations."""

        store = testing.DummyPluginFileStore()

        assert store.load_module("default_mod") == b"module_bytes:default_mod"

        store.set_module("custom_mod", b"custom_content")
        assert store.load_module("custom_mod") == b"custom_content"
        assert store.load_module_calls == ["default_mod", "custom_mod"]

    def test_simulated_errors(self) -> None:
        """Ensure configured errors raise on helper, module, or render operations."""

        store = testing.DummyPluginFileStore()

        store.load_library_error = config.ConnectionError("library load fail")
        with pytest.raises(config.ConnectionError, match="library load fail"):
            store.load_all_helpers()

        store.load_module_error = config.InvalidOperation("module load fail")
        with pytest.raises(config.InvalidOperation, match="module load fail"):
            store.load_module("bad_mod")

        store.render_error = config.InvalidOperation("render fail")
        with pytest.raises(config.InvalidOperation, match="render fail"):
            store.render_launcher("1.1.1.1", 1234, b"ack")

    def test_find_module_modules_prefix_normalization(self) -> None:
        """Ensure find_module normalizes module names prefixed with modules/."""

        store = testing.DummyPluginFileStore(modules={"discovery/sysinfo": b"sysinfo"})

        resolved = store.find_module("modules/discovery/sysinfo")
        assert resolved is not None
        assert resolved.name == "sysinfo"


class TestDummyPluginRuntime:
    """Verify behavior of the DummyPluginRuntime double."""

    def test_launcher_delivery_properties(self) -> None:
        """Ensure launcher exposes text and script bytes matching client_script."""

        runtime = testing.DummyPluginRuntime(client_script="echo hello")

        assert isinstance(runtime.processor, contract.IPluginProcessor)
        assert isinstance(runtime.launcher, contract.LauncherDelivery)
        assert runtime.launcher.text == "echo hello"
        assert runtime.launcher.script == b"echo hello"

    def test_create_connection_tracking(self) -> None:
        """Ensure create_connection returns target connection and records instance."""

        conn = testing.DummyConnection()
        runtime = testing.DummyPluginRuntime(connection_to_return=conn)

        dummy_transport = testing.DummyTransport()
        created = runtime.create_connection(dummy_transport)

        assert created is conn
        assert runtime.created_connections == [conn]


class TestDummyPlugin:
    """Verify behavior of the DummyPlugin extension double."""

    def test_metadata_and_parser_configuration(self) -> None:
        """Ensure DummyPlugin exposes metadata and records parser configuration."""

        testing.DummyPlugin.reset()
        assert testing.DummyPlugin.name == "dummy"

        parser = util.Parser()
        testing.DummyPlugin.configure_parser(parser)
        assert testing.DummyPlugin.configured_parsers == [parser]

    def test_options_extraction_and_config_building(self) -> None:
        """Ensure extract_options and build_config construct valid PluginConfig."""

        raw = {"sample_key": "sample_val"}
        options = testing.DummyPlugin.extract_options(raw)
        assert isinstance(options, dict)

        cfg = testing.DummyPlugin.build_config("10.0.0.5", 8000, options)
        assert cfg.kind == "dummy"
        assert cfg.host == "10.0.0.5"
        assert cfg.port == 8000
        assert cfg.options == options

    def test_validation_and_simulated_errors(self) -> None:
        """Ensure validate enforces invariants and supports error injection."""

        testing.DummyPlugin.reset()
        cfg = testing.DummyPlugin.build_config("10.0.0.5", 8000, {})

        testing.DummyPlugin.validate(cfg)

        testing.DummyPlugin.validation_error = config.ParserError("invalid options")
        with pytest.raises(config.ParserError, match="invalid options"):
            testing.DummyPlugin.validate(cfg)

    def test_build_runtime_and_reset(self) -> None:
        """Ensure build_runtime instantiates IPluginRuntime and reset() clears state."""

        testing.DummyPlugin.reset()
        cfg = testing.DummyPlugin.build_config("10.0.0.5", 8000, {})
        runtime = testing.DummyPlugin.build_runtime(cfg)

        assert isinstance(runtime, contract.IPluginRuntime)

        parser = util.Parser()
        testing.DummyPlugin.configure_parser(parser)
        assert len(testing.DummyPlugin.configured_parsers) == 1

        testing.DummyPlugin.reset()
        assert len(testing.DummyPlugin.configured_parsers) == 0
        assert testing.DummyPlugin.validation_error is None


class TestDummyRouter:
    """Verify behavior of the DummyRouter double."""

    def test_connect_and_locate_flow(self) -> None:
        """Ensure connect registers routes and locate dispatches controller."""

        router = testing.DummyRouter()

        def sample_handler(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerResult:
            """Sample documentation."""
            return contract.ControllerResult()

        router.connect("sample", sample_handler)

        assert "sample" in router.routes
        assert router.locate("sample") is sample_handler
        assert router.locate_calls == ["sample"]
        assert router.help("sample") == contract.RouteHelp()

    def test_set_route_help_override(self) -> None:
        """Ensure set_route_help customizes the route help metadata."""

        router = testing.DummyRouter()

        def dummy_handler(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerResult:
            return contract.ControllerResult()

        router.connect("cmd", dummy_handler)
        router.set_route_help("cmd", contract.RouteHelp("Short description.", "Additional details."))

        assert router.help("cmd") == contract.RouteHelp("Short description.", "Additional details.")

    def test_duplicate_route_error(self) -> None:
        """Ensure connecting an existing route raises DuplicateRouteError."""

        router = testing.DummyRouter()

        def handler(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerResult:
            return contract.ControllerResult()

        router.connect("dup", handler)

        with pytest.raises(config.DuplicateRouteError, match="route already exists"):
            router.connect("dup", handler)

    def test_unknown_route_error(self) -> None:
        """Ensure locating an unmapped route raises RouterError."""

        router = testing.DummyRouter()

        with pytest.raises(config.RouterError):
            router.locate("nonexistent_command")


class TestDummyCommand:
    """Verify behavior of the DummyCommand double."""

    def test_execution_sequence(self, test_session: contract.SessionContext) -> None:
        """Ensure execute runs send_request followed by read_response."""

        cmd = testing.DummyCommand()
        test_session.execute(cmd)

        assert cmd.call_sequence == ["send_request", "read_response"]

    def test_simulated_errors(self, test_session: contract.SessionContext) -> None:
        """Ensure send_request_error and read_response_error raise properly."""

        err_cmd = testing.DummyCommand(send_request_error=config.CommandError("send failed"))
        with pytest.raises(config.CommandError, match="send failed"):
            test_session.execute(err_cmd)

        read_err_cmd = testing.DummyCommand(read_response_error=config.CommandError("read failed"))
        with pytest.raises(config.CommandError, match="read failed"):
            test_session.execute(read_err_cmd)


class TestDummySessionRunner:
    """Verify behavior of the DummySessionRunner double."""

    def test_run_invocation_recording(
        self,
        test_session: contract.SessionContext,
        dummy_router: testing.DummyRouter,
    ) -> None:
        """Ensure run records invocations with passed session and router."""

        runner = testing.DummySessionRunner()
        runner.run(test_session, dummy_router)

        assert len(runner.run_calls) == 1
        assert runner.run_calls[0] == (test_session, dummy_router)

    def test_simulated_run_error(
        self,
        test_session: contract.SessionContext,
        dummy_router: testing.DummyRouter,
    ) -> None:
        """Ensure run_error raises when run is invoked."""

        runner = testing.DummySessionRunner(run_error=config.DeclusorException("runner failed"))

        with pytest.raises(config.DeclusorException, match="runner failed"):
            runner.run(test_session, dummy_router)


class TestDummyApplication:
    """Verify behavior of the DummyApplication double."""

    def test_run_calls_recording(self) -> None:
        """Ensure run records PluginConfig calls."""

        cfg = testing.create_dummy_plugin_config()
        app = testing.DummyApplication()

        app.run(cfg)
        assert app.run_calls == [cfg]

    def test_register_plugin(self) -> None:
        """Ensure register_plugin adds plugin to internal PluginManager."""

        app = testing.DummyApplication()
        assert isinstance(app.manager, core.PluginManager)

        app.register_plugin(testing.DummyPlugin)
        assert testing.DummyPlugin.name in app.manager.names()

    def test_simulated_run_error(self) -> None:
        """Ensure run_error raises when run is invoked."""

        cfg = testing.create_dummy_plugin_config()
        app = testing.DummyApplication()
        app.run_error = config.ConnectionError("run failed")

        with pytest.raises(config.ConnectionError, match="run failed"):
            app.run(cfg)

    def test_collaborator_injection(self) -> None:
        """Ensure DummyApplication provides access to underlying collaborators."""

        app = testing.DummyApplication()
        assert app.transport_registry is not None
        assert app.router is not None
        assert app.view is not None
