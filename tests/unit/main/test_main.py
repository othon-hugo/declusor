"""Unit tests for main composition root and CLI entry point in declusor.main.main."""

import io
import sys
from typing import Any

import pytest

from declusor import config, core, main, testing, transport


class TestMainDispatch:
    """Tests verifying CLI argument handling and dispatching in main()."""

    def test_main__with_explicit_argv__parses_and_executes_application(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """main parses explicit argv sequence and executes injected application returning 0."""

        exit_code = main.main(["127.0.0.1", "9000"], application=dummy_app)

        assert exit_code == 0
        assert len(dummy_app.run_calls) == 1
        assert dummy_app.run_calls[0].host == "127.0.0.1"
        assert dummy_app.run_calls[0].port == 9000
        assert dummy_app.run_calls[0].kind == testing.DummyPlugin.name

    def test_main__with_argv_none__reads_arguments_from_sys_argv(
        self,
        dummy_app: testing.DummyApplication,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """main falls back to sys.argv[1:] when argv is omitted or None."""

        monkeypatch.setattr(sys, "argv", ["declusor", "10.0.0.1", "8888"])
        exit_code = main.main(None, application=dummy_app)

        assert exit_code == 0
        assert len(dummy_app.run_calls) == 1
        assert dummy_app.run_calls[0].host == "10.0.0.1"
        assert dummy_app.run_calls[0].port == 8888

    def test_main__with_argv_tuple__converts_to_list_and_executes(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """main accepts non-list sequence for argv and executes application successfully."""

        exit_code = main.main(("127.0.0.1", "9000"), application=dummy_app)

        assert exit_code == 0
        assert len(dummy_app.run_calls) == 1

    def test_main__with_comprehensive_cli_options__populates_plugin_config_fields(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """main parses timeout, launcher output, and wrapper flags into resulting plugin config."""

        exit_code = main.main(
            [
                "127.0.0.1",
                "9000",
                "-p",
                testing.DummyPlugin.name,
                "-m",
                "cli",
                "-t",
                "12.5",
                "--launcher-output",
                "silent",
            ],
            application=dummy_app,
        )

        assert exit_code == 0
        assert len(dummy_app.run_calls) == 1
        parsed_config = dummy_app.run_calls[0]
        assert parsed_config.timeout == 12.5
        assert parsed_config.launcher_output_mode == config.LauncherOutputMode.SILENT
        assert parsed_config.launcher_wrapper is None

    def test_main_keyword_only__rejects_positional_application(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """main rejects application instance passed as positional argument."""

        with pytest.raises(TypeError):
            main.main(["127.0.0.1", "9000"], dummy_app)  # type: ignore[misc]


class TestMainPluginManagerResolution:
    """Tests verifying plugin manager resolution and fallback behavior in main()."""

    def test_main__with_injected_application__uses_application_plugin_manager(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """main derives plugin manager from injected application when plugin_manager is omitted."""

        exit_code = main.main(["127.0.0.1", "9000"], application=dummy_app)

        assert exit_code == 0
        assert len(dummy_app.run_calls) == 1

    def test_main__with_explicit_plugin_manager__overrides_application_plugin_manager(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """Explicitly passed plugin_manager takes precedence over application.plugin_manager."""

        custom_manager = core.PluginManager()
        custom_manager.register(testing.DummyPlugin)

        exit_code = main.main(
            ["127.0.0.1", "9000"],
            application=dummy_app,
            plugin_manager=custom_manager,
        )

        assert exit_code == 0
        assert len(dummy_app.run_calls) == 1

    def test_main__when_plugin_manager_and_application_omitted__discovers_default_plugins(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """main discovers default plugins when neither plugin_manager nor application is provided."""

        factory_called = False

        def tracking_factory(*, plugin_manager: core.PluginManager | None = None, **_: Any) -> core.Application:
            nonlocal factory_called
            factory_called = True
            assert plugin_manager is not None
            return dummy_app

        exit_code = main.main(
            ["127.0.0.1", "9000", "-p", "shell_socket"],
            application_factory=tracking_factory,
        )

        assert exit_code == 0
        assert factory_called is True
        assert len(dummy_app.run_calls) == 1


class TestMainApplicationFactory:
    """Tests verifying application factory delegation and transport registry forwarding."""

    def test_main__with_custom_application_factory__invokes_factory_and_executes_result(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """main delegates to custom application_factory when application instance is omitted."""

        factory_called = False

        def custom_factory(*, plugin_manager: core.PluginManager | None = None, **_: Any) -> core.Application:
            nonlocal factory_called
            factory_called = True
            return dummy_app

        exit_code = main.main(
            ["127.0.0.1", "9000"],
            plugin_manager=dummy_app.plugin_manager,
            application_factory=custom_factory,
        )

        assert exit_code == 0
        assert factory_called is True
        assert len(dummy_app.run_calls) == 1

    def test_main__with_injected_transport_registry__forwards_registry_to_parser_and_runner(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """main validates CLI transport layer against explicitly injected transport registry."""

        registry = transport.TransportLayerRegistry()
        registry.register("dummy_layer", lambda t: t)

        exit_code = main.main(
            ["127.0.0.1", "9000", "--transport-layer", "dummy_layer"],
            application=dummy_app,
            transport_registry=registry,
        )

        assert exit_code == 0
        assert dummy_app.run_calls[0].transport_layers == ("dummy_layer",)

    def test_main__with_application_transport_registry__uses_it_when_transport_registry_omitted(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """main derives transport registry from application when transport_registry is omitted."""

        dummy_app.transport_registry.register("app_layer", lambda t: t)

        exit_code = main.main(
            ["127.0.0.1", "9000", "--transport-layer", "app_layer"],
            application=dummy_app,
        )

        assert exit_code == 0
        assert dummy_app.run_calls[0].transport_layers == ("app_layer",)


class TestMainExecutionModes:
    """Tests verifying execution mode dispatching and unsupported mode rejection in main()."""

    def test_main__when_mode_is_cli__runs_terminal_app_and_returns_zero(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """main executes run_terminal_app when mode is CLI and returns 0."""

        exit_code = main.main(["127.0.0.1", "9000", "--mode", "cli"], application=dummy_app)

        assert exit_code == 0
        assert len(dummy_app.run_calls) == 1

    def test_main__when_mode_is_unsupported_mcp__writes_error_and_returns_one(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """main returns 1 and outputs error message when unsupported mcp mode is requested."""

        exit_code = main.main(["127.0.0.1", "9000", "--mode", "mcp"])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Execution mode 'mcp' is not supported yet." in captured.err

    def test_main__when_mode_is_unsupported_api__writes_error_and_returns_one(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """main returns 1 and outputs error message when unsupported api mode is requested."""

        exit_code = main.main(["127.0.0.1", "9000", "--mode", "api"])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Execution mode 'api' is not supported yet." in captured.err

    def test_main__when_mode_is_unsupported_http__writes_error_and_returns_one(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """main returns 1 and outputs error message when unsupported http mode is requested."""

        exit_code = main.main(["127.0.0.1", "9000", "--mode", "http"])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Execution mode 'http' is not supported yet." in captured.err

    def test_main__when_mode_is_unsupported_with_custom_stderr__writes_diagnostic_to_custom_stream(
        self,
    ) -> None:
        """main directs unsupported mode diagnostic output to injected stderr stream."""

        custom_err = io.StringIO()
        exit_code = main.main(["127.0.0.1", "9000", "--mode", "mcp"], stderr=custom_err)

        assert exit_code == 1
        assert "Execution mode 'mcp' is not supported yet." in custom_err.getvalue()


class TestMainExceptionHandling:
    """Tests verifying domain exception and interrupt exit code mappings in main()."""

    def test_main__when_parser_error_invalid_option__prints_parser_error_and_returns_two(
        self,
        dummy_app: testing.DummyApplication,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """main catches ParserError from unrecognized flags, prints diagnostic, and returns 2."""

        exit_code = main.main(["--bad-option"], application=dummy_app)

        assert exit_code == 2
        captured = capsys.readouterr()
        assert "parser error:" in captured.err

    def test_main__when_parser_error_empty_argv__prints_parser_error_and_returns_two(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """main catches ParserError from missing required arguments and returns 2."""

        exit_code = main.main([])

        assert exit_code == 2
        captured = capsys.readouterr()
        assert "parser error:" in captured.err

    def test_main__when_parser_error_invalid_port__prints_parser_error_and_returns_two(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """main catches ParserError from out-of-range port numbers and returns 2."""

        exit_code = main.main(["127.0.0.1", "70000"])

        assert exit_code == 2
        captured = capsys.readouterr()
        assert "parser error:" in captured.err

    def test_main__when_parser_error_with_custom_stderr__writes_to_custom_stream_and_returns_two(
        self,
    ) -> None:
        """main writes parser errors to custom stderr stream when provided."""

        custom_err = io.StringIO()
        exit_code = main.main(["--invalid-argument"], stderr=custom_err)

        assert exit_code == 2
        assert "parser error:" in custom_err.getvalue()

    def test_main__when_connection_error_raised__prints_declusor_error_and_returns_one(
        self,
        dummy_app: testing.DummyApplication,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """main catches ConnectionError, prints declusor error to stderr, and returns 1."""

        dummy_app.run_error = config.ConnectionError("connection failed")
        exit_code = main.main(["127.0.0.1", "9000"], application=dummy_app)

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "declusor error: connection failed" in captured.err

    def test_main__when_invalid_operation_raised__prints_declusor_error_and_returns_one(
        self,
        dummy_app: testing.DummyApplication,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """main catches InvalidOperation, prints declusor error, and returns 1."""

        dummy_app.run_error = config.InvalidOperation("operation rejected")
        exit_code = main.main(["127.0.0.1", "9000"], application=dummy_app)

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "declusor error: invalid operation: operation rejected" in captured.err

    def test_main__when_router_error_raised__prints_declusor_error_and_returns_one(
        self,
        dummy_app: testing.DummyApplication,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """main catches RouterError, prints declusor error, and returns 1."""

        dummy_app.run_error = config.RouterError("unknown command")
        exit_code = main.main(["127.0.0.1", "9000"], application=dummy_app)

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "declusor error: invalid route: 'unknown command'" in captured.err

    def test_main__when_storage_error_raised__prints_declusor_error_and_returns_one(
        self,
        dummy_app: testing.DummyApplication,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """main catches StorageError, prints declusor error, and returns 1."""

        dummy_app.run_error = config.StorageError("disk read failure")
        exit_code = main.main(["127.0.0.1", "9000"], application=dummy_app)

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "declusor error: disk read failure" in captured.err

    def test_main__when_declusor_error_with_custom_stderr__writes_to_custom_stream_and_returns_one(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """main writes DeclusorException diagnostics to custom stderr stream when provided."""

        custom_err = io.StringIO()
        dummy_app.run_error = config.ConnectionError("custom error message")
        exit_code = main.main(["127.0.0.1", "9000"], application=dummy_app, stderr=custom_err)

        assert exit_code == 1
        assert "declusor error: custom error message" in custom_err.getvalue()

    def test_main__when_keyboard_interrupt_raised__returns_zero_silently(
        self,
        dummy_app: testing.DummyApplication,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """main catches KeyboardInterrupt and returns 0 without writing errors."""

        dummy_app.run_error = KeyboardInterrupt()
        exit_code = main.main(["127.0.0.1", "9000"], application=dummy_app)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.err == ""
        assert captured.out == ""

    def test_main__when_system_exit_zero_raised__returns_zero_silently(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """main catches SystemExit(0) and returns 0 exit code."""

        dummy_app.run_error = SystemExit(0)
        exit_code = main.main(["127.0.0.1", "9000"], application=dummy_app)

        assert exit_code == 0

    def test_main__when_system_exit_non_zero_raised__returns_exit_code(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """main catches SystemExit(code) and returns the specified integer exit code."""

        dummy_app.run_error = SystemExit(42)
        exit_code = main.main(["127.0.0.1", "9000"], application=dummy_app)

        assert exit_code == 42


class TestMainAgentOrchestration:
    """Tests verifying programmatic agent orchestration and in-memory execution via main()."""

    def test_main__full_headless_orchestration_with_doubles__executes_cleanly_and_returns_zero(
        self,
    ) -> None:
        """main orchestrates full in-memory headless execution using injected test doubles."""

        custom_manager = core.PluginManager()
        custom_manager.register(testing.DummyPlugin)

        dummy_conn = testing.DummyConnection()
        dummy_runtime = testing.DummyPluginRuntime(connection_to_return=dummy_conn)
        testing.DummyPlugin.reset()
        testing.DummyPlugin.runtime_instance = dummy_runtime

        view = testing.DummyView()
        runner = testing.DummySessionRunner()
        input_source = testing.DummyInputSource()
        listener = testing.MemoryTransportListener()
        _ = listener.create_client()
        err_stream = io.StringIO()

        exit_code = main.main(
            ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name],
            plugin_manager=custom_manager,
            view=view,
            session_runner=runner,
            input_source=input_source,
            listener_factory=lambda host, port: listener,
            stderr=err_stream,
        )

        assert exit_code == 0
        assert err_stream.getvalue() == ""
        assert len(runner.run_calls) == 1
        session, _ = runner.run_calls[0]
        assert session.connection is dummy_conn
        assert session.view is view
        assert session.input is input_source

    def test_main__custom_stderr_redirection__leaves_sys_stderr_unpolluted(
        self,
        dummy_app: testing.DummyApplication,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Passing custom stderr stream keeps sys.stderr clean when errors occur."""

        custom_err = io.StringIO()
        dummy_app.run_error = config.ConnectionError("isolated socket failure")

        exit_code = main.main(
            ["127.0.0.1", "9000"],
            application=dummy_app,
            stderr=custom_err,
        )

        assert exit_code == 1
        assert "declusor error: isolated socket failure" in custom_err.getvalue()

        captured = capsys.readouterr()
        assert captured.err == ""
