"""Unit tests for terminal REPL runner bootstrap in declusor.main.terminal."""

from typing import Any

import pytest

from declusor import config, contract, core, testing, transport
from declusor.main.terminal import run_terminal_app


class TestRunTerminalApp:
    """Tests verifying run_terminal_app entrypoint and bootstrap orchestration."""

    def test_run_terminal_app__with_injected_application__dispatches_execution_and_returns_zero(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """run_terminal_app dispatches execution directly to injected Application and returns 0."""

        cfg = testing.create_dummy_plugin_config()
        exit_code = run_terminal_app(cfg, application=dummy_app)

        assert exit_code == 0
        assert dummy_app.run_calls == [cfg]

    def test_run_terminal_app__with_injected_plugin_manager__passes_manager_to_factory(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """run_terminal_app forwards injected plugin_manager to application factory."""

        manager = core.PluginManager()
        cfg = testing.create_dummy_plugin_config()
        factory_kwargs: dict[str, Any] = {}

        def tracking_factory(*, plugin_manager: core.PluginManager | None = None) -> core.Application:
            factory_kwargs["plugin_manager"] = plugin_manager
            return dummy_app

        exit_code = run_terminal_app(
            cfg,
            plugin_manager=manager,
            application_factory=tracking_factory,
        )

        assert exit_code == 0
        assert factory_kwargs.get("plugin_manager") is manager
        assert dummy_app.run_calls == [cfg]

    def test_run_terminal_app__with_custom_application_factory__invokes_factory_and_executes_result(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """run_terminal_app invokes custom application factory when application is omitted."""

        cfg = testing.create_dummy_plugin_config()
        factory_invoked = False

        def custom_factory(*, plugin_manager: core.PluginManager | None = None) -> core.Application:
            nonlocal factory_invoked
            factory_invoked = True
            return dummy_app

        exit_code = run_terminal_app(cfg, application_factory=custom_factory)

        assert exit_code == 0
        assert factory_invoked is True
        assert dummy_app.run_calls == [cfg]

    def test_run_terminal_app__with_orchestration_doubles_and_default_factory__wires_and_executes(
        self,
    ) -> None:
        """run_terminal_app wires injected doubles into default create_terminal_application factory."""

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
        registry = transport.TransportLayerRegistry()

        cfg = testing.create_dummy_plugin_config()

        exit_code = run_terminal_app(
            cfg,
            plugin_manager=custom_manager,
            view=view,
            session_runner=runner,
            input_source=input_source,
            listener_factory=lambda host, port: listener,
            transport_registry=registry,
        )

        assert exit_code == 0
        assert len(runner.run_calls) == 1

    def test_run_terminal_app__with_custom_factory_accepting_kwargs__forwards_all_doubles(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """run_terminal_app forwards all orchestration doubles to a kwargs-aware application factory."""

        captured_kwargs: dict[str, Any] = {}

        def kwargs_factory(**kwargs: Any) -> core.Application:
            captured_kwargs.update(kwargs)
            return dummy_app

        cfg = testing.create_dummy_plugin_config()
        view = testing.DummyView()
        runner = testing.DummySessionRunner()
        registry = transport.TransportLayerRegistry()

        exit_code = run_terminal_app(
            cfg,
            application_factory=kwargs_factory,
            view=view,
            session_runner=runner,
            transport_registry=registry,
        )

        assert exit_code == 0
        assert captured_kwargs.get("view") is view
        assert captured_kwargs.get("session_runner") is runner
        assert captured_kwargs.get("transport_registry") is registry
        assert dummy_app.run_calls == [cfg]

    def test_run_terminal_app__with_single_keyword_factory__passes_only_declared_parameter(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """run_terminal_app passes only plugin_manager when custom factory accepts only plugin_manager."""

        def single_param_factory(*, plugin_manager: core.PluginManager | None = None) -> core.Application:
            return dummy_app

        cfg = testing.create_dummy_plugin_config()
        view = testing.DummyView()

        exit_code = run_terminal_app(
            cfg,
            application_factory=single_param_factory,
            view=view,
        )

        assert exit_code == 0
        assert dummy_app.run_calls == [cfg]

    def test_run_terminal_app__with_zero_arg_factory__calls_factory_without_arguments(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """run_terminal_app successfully executes a zero-argument application factory."""

        cfg = testing.create_dummy_plugin_config()
        exit_code = run_terminal_app(cfg, application_factory=lambda: dummy_app)

        assert exit_code == 0
        assert dummy_app.run_calls == [cfg]

    def test_run_terminal_app__with_partial_kwargs_factory__passes_only_declared_parameters(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """run_terminal_app forwards only declared parameters when factory accepts a subset of kwargs."""

        captured: dict[str, Any] = {}

        def partial_factory(
            *,
            plugin_manager: core.PluginManager | None = None,
            view: contract.IView | None = None,
        ) -> core.Application:
            captured["plugin_manager"] = plugin_manager
            captured["view"] = view
            return dummy_app

        manager = core.PluginManager()
        view = testing.DummyView()
        runner = testing.DummySessionRunner()
        cfg = testing.create_dummy_plugin_config()

        exit_code = run_terminal_app(
            cfg,
            plugin_manager=manager,
            application_factory=partial_factory,
            view=view,
            session_runner=runner,
        )

        assert exit_code == 0
        assert captured["plugin_manager"] is manager
        assert captured["view"] is view
        assert dummy_app.run_calls == [cfg]

    def test_run_terminal_app__when_factory_raises_internal_type_error__propagates_without_retry(
        self,
    ) -> None:
        """run_terminal_app does not swallow internal TypeError from factory logic or invoke it twice."""

        call_count = 0

        def buggy_factory(**kwargs: Any) -> core.Application:
            nonlocal call_count
            call_count += 1
            raise TypeError("internal logic error")

        cfg = testing.create_dummy_plugin_config()

        with pytest.raises(TypeError, match="internal logic error"):
            run_terminal_app(cfg, application_factory=buggy_factory)

        assert call_count == 1

    def test_run_terminal_app__when_application_raises_connection_error__propagates_exception(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """run_terminal_app propagates ConnectionError raised during application execution."""

        dummy_app.run_error = config.ConnectionError("Connection timed out.")
        cfg = testing.create_dummy_plugin_config()

        with pytest.raises(config.ConnectionError, match="Connection timed out."):
            run_terminal_app(cfg, application=dummy_app)

    def test_run_terminal_app__when_application_raises_invalid_operation__propagates_exception(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """run_terminal_app propagates InvalidOperation raised during application execution."""

        dummy_app.run_error = config.InvalidOperation("Invalid operation requested.")
        cfg = testing.create_dummy_plugin_config()

        with pytest.raises(config.InvalidOperation, match="Invalid operation requested."):
            run_terminal_app(cfg, application=dummy_app)

    def test_run_terminal_app_keyword_only__rejects_positional_plugin_manager(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """run_terminal_app rejects plugin_manager passed as positional argument."""

        manager = core.PluginManager()
        cfg = testing.create_dummy_plugin_config()

        with pytest.raises(TypeError):
            run_terminal_app(cfg, manager)  # type: ignore[misc]

    def test_run_terminal_app_keyword_only__rejects_positional_application(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """run_terminal_app rejects application passed as positional argument."""

        cfg = testing.create_dummy_plugin_config()

        with pytest.raises(TypeError):
            run_terminal_app(cfg, None, dummy_app)  # type: ignore[misc]

    def test_run_terminal_app_keyword_only__rejects_positional_application_factory(
        self,
        dummy_app: testing.DummyApplication,
    ) -> None:
        """run_terminal_app rejects application_factory passed as positional argument."""

        cfg = testing.create_dummy_plugin_config()

        with pytest.raises(TypeError):
            run_terminal_app(cfg, None, None, lambda **_: dummy_app)  # type: ignore[misc]

    def test_run_terminal_app_keyword_only__rejects_positional_transport_registry(
        self,
    ) -> None:
        """run_terminal_app rejects transport_registry passed as positional argument."""

        cfg = testing.create_dummy_plugin_config()
        registry = transport.TransportLayerRegistry()

        with pytest.raises(TypeError):
            run_terminal_app(cfg, None, None, None, registry)  # type: ignore[misc]
