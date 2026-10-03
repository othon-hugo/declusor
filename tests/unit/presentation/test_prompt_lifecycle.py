"""Unit tests for PromptLoop lifecycle, initialization, and invariants in declusor.presentation.prompt."""

import pytest

from declusor import config, contract, presentation, testing


def _terminate_controller(
    session: contract.SessionContext,
    request: contract.IControllerRequest[contract.ControllerArguments],
    /,
) -> contract.ControllerResult:
    """Deterministic controller returning terminate action."""

    return contract.ControllerResult(action=contract.ControllerAction.TERMINATE)


class TestPromptLoopInitialization:
    """Tests verifying PromptLoop initialization, prompt prefixing, and dependencies."""

    def test_prompt_loop_default_initialization__binds_project_name_prompt_and_empty_dependencies(self) -> None:
        """PromptLoop defaults prompt string to [PROJECT_NAME] and holds None for dependencies."""

        prompt = presentation.PromptLoop()

        assert prompt._prompt == f"[{config.PROJECT_NAME}] "
        assert prompt.session is None
        assert prompt._router is None

    def test_prompt_loop_custom_name__formats_bracketed_prefix(self) -> None:
        """PromptLoop surrounds custom name argument with brackets and trailing space."""

        prompt = presentation.PromptLoop("operator_cli")

        assert prompt._prompt == "[operator_cli] "

    def test_prompt_loop_constructor_injection__stores_router_and_session(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
    ) -> None:
        """PromptLoop records injected router and session instances."""

        prompt = presentation.PromptLoop(
            "test_shell",
            router=dummy_router,
            session=test_session,
        )

        assert prompt.session is test_session
        assert prompt._router is dummy_router

    def test_prompt_loop_contract_conformance__implements_isession_runner(self) -> None:
        """PromptLoop satisfies the ISessionRunner contract interface."""

        prompt = presentation.PromptLoop("test_shell")

        assert isinstance(prompt, contract.ISessionRunner)

    def test_prompt_loop_name_parameter_positional_only__raises_type_error(self) -> None:
        """PromptLoop enforces positional-only argument passing for the name parameter."""

        with pytest.raises(TypeError, match="positional-only"):
            presentation.PromptLoop(name="custom_cli")  # type: ignore[call-arg]

    def test_prompt_loop_session_property_is_read_only__modifying_raises_attribute_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """PromptLoop.session is a read-only property and cannot be reassigned."""

        prompt = presentation.PromptLoop("test_shell")

        with pytest.raises(AttributeError):
            prompt.session = test_session  # type: ignore[misc]


class TestPromptLoopInvariants:
    """Tests verifying fail-fast invariant checks when PromptLoop dependencies are missing."""

    def test_prompt_loop_run_without_session_and_router__raises_invalid_operation(self) -> None:
        """PromptLoop.run raises InvalidOperation when invoked with no session or router configured."""

        prompt = presentation.PromptLoop("test_shell")

        with pytest.raises(config.InvalidOperation, match="PromptLoop requires an active session and router"):
            prompt.run()

    def test_prompt_loop_run_with_missing_session__raises_invalid_operation(
        self,
        dummy_router: testing.DummyRouter,
    ) -> None:
        """PromptLoop.run raises InvalidOperation when router is present but session is missing."""

        prompt = presentation.PromptLoop("test_shell", router=dummy_router)

        with pytest.raises(config.InvalidOperation, match="PromptLoop requires an active session and router"):
            prompt.run()

    def test_prompt_loop_run_with_missing_router__raises_invalid_operation(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """PromptLoop.run raises InvalidOperation when session is present but router is missing."""

        prompt = presentation.PromptLoop("test_shell", session=test_session)

        with pytest.raises(config.InvalidOperation, match="PromptLoop requires an active session and router"):
            prompt.run()

    def test_prompt_loop_run_with_session_lacking_input_source__raises_invalid_operation(
        self,
        dummy_router: testing.DummyRouter,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """PromptLoop.run raises InvalidOperation when active session has no input source."""

        session_without_input = contract.SessionContext(
            connection=dummy_connection,
            view=dummy_view,
            plugin_processor=dummy_file_store,
            input_source=None,
        )

        prompt = presentation.PromptLoop(
            "test_shell",
            router=dummy_router,
            session=session_without_input,
        )

        with pytest.raises(
            config.InvalidOperation,
            match="PromptLoop requires an active session with an input source",
        ):
            prompt.run()


class TestPromptLoopSessionRunnerProtocol:
    """Tests verifying ISessionRunner polymorphic execution and parameter overrides."""

    def test_prompt_loop_run_as_session_runner__executes_with_positional_arguments(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """PromptLoop can be driven via ISessionRunner.run(session, router) protocol."""

        runner: contract.ISessionRunner = presentation.PromptLoop("runner_cli")
        dummy_input_source.feed_inputs("quit")
        dummy_router.connect("quit", _terminate_controller)

        runner.run(test_session, dummy_router)

        assert dummy_router.locate_calls == ["quit"]

    def test_prompt_loop_run_arguments_override_constructor_defaults(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Positional arguments passed to run() override session and router from constructor."""

        fallback_router = testing.DummyRouter()
        fallback_session = testing.create_test_session(
            connection=dummy_connection,
            view=dummy_view,
            input_source=dummy_input_source,
            files=dummy_file_store,
        )

        prompt = presentation.PromptLoop(
            "override_cli",
            router=fallback_router,
            session=fallback_session,
        )

        dummy_input_source.feed_inputs("exit")
        dummy_router.connect("exit", _terminate_controller)

        prompt.run(test_session, dummy_router)

        assert dummy_router.locate_calls == ["exit"]
        assert fallback_router.locate_calls == []

    def test_prompt_loop_run_keyword_arguments__raises_type_error(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
    ) -> None:
        """PromptLoop.run enforces positional-only argument passing for session and router."""

        prompt = presentation.PromptLoop("test_cli")

        with pytest.raises(TypeError, match="positional-only"):
            prompt.run(session=test_session, router=dummy_router)  # type: ignore[call-arg]
