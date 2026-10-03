"""Unit tests for PromptLoop command reading, tokenization, and route dispatching in declusor.presentation.prompt."""

from typing import cast

from declusor import contract, presentation, testing


def _terminate_controller(
    session: contract.SessionContext,
    request: contract.IControllerRequest[contract.ControllerArguments],
    /,
) -> contract.ControllerResult:
    """Terminate the prompt loop."""

    return contract.ControllerResult(action=contract.ControllerAction.TERMINATE)


class TestPromptLoopCommandReading:
    """Tests verifying input reading and prompt presentation behavior in PromptLoop."""

    def test_prompt_loop_read_command__passes_prompt_prefix_to_input_source(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """PromptLoop passes its formatted prompt prefix to input_source.read_command."""

        dummy_input_source.feed_inputs("exit")
        dummy_router.connect("exit", _terminate_controller)

        prompt = presentation.PromptLoop(
            "custom_app",
            router=dummy_router,
            session=test_session,
        )
        prompt.run()

        assert dummy_input_source.prompts == ["[custom_app] "]

    def test_prompt_loop_read_command_empty_lines__skips_and_reprompts_until_non_empty(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """PromptLoop skips empty or whitespace-only lines and re-prompts until input is non-empty."""

        dummy_input_source.feed_inputs("", "   ", "\t  \n", "exit")
        dummy_router.connect("exit", _terminate_controller)

        prompt = presentation.PromptLoop(
            "loop_app",
            router=dummy_router,
            session=test_session,
        )
        prompt.run()

        assert len(dummy_input_source.prompts) == 4
        assert dummy_router.locate_calls == ["exit"]


class TestPromptLoopRouteDispatch:
    """Tests verifying command line splitting and ControllerRequest instantiation."""

    def test_prompt_loop_route_single_token__creates_request_with_empty_request_line(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """Single-token commands instantiate ControllerRequest with an empty request_line."""

        received_requests: list[contract.IControllerRequest[contract.ControllerArguments]] = []

        def info_controller(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerResult:
            received_requests.append(req)
            return contract.ControllerResult(action=contract.ControllerAction.TERMINATE)

        dummy_input_source.feed_inputs("status")
        dummy_router.connect("status", info_controller)

        prompt = presentation.PromptLoop(router=dummy_router, session=test_session)
        prompt.run()

        assert len(received_requests) == 1
        assert received_requests[0].request_line == ""

    def test_prompt_loop_route_with_arguments__creates_request_with_stripped_arguments(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """Commands with arguments strip surrounding argument whitespace for ControllerRequest."""

        received_requests: list[contract.IControllerRequest[contract.ControllerArguments]] = []

        def echo_controller(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerResult:
            received_requests.append(req)
            return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

        dummy_input_source.feed_inputs("echo   hello world from declusor   ", "exit")
        dummy_router.connect("echo", echo_controller)
        dummy_router.connect("exit", _terminate_controller)

        prompt = presentation.PromptLoop(router=dummy_router, session=test_session)
        prompt.run()

        assert len(received_requests) == 1
        assert received_requests[0].request_line == "hello world from declusor"

    def test_prompt_loop_route_with_leading_whitespace__locates_route_and_preserves_arguments(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """Commands with leading whitespace correctly resolve the route and strip arguments."""

        received_requests: list[contract.IControllerRequest[contract.ControllerArguments]] = []

        def ping_controller(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerResult:
            received_requests.append(req)
            return contract.ControllerResult(action=contract.ControllerAction.TERMINATE)

        dummy_input_source.feed_inputs("   ping   127.0.0.1   ")
        dummy_router.connect("ping", ping_controller)

        prompt = presentation.PromptLoop(router=dummy_router, session=test_session)
        prompt.run()

        assert dummy_router.locate_calls == ["ping"]
        assert len(received_requests) == 1
        assert received_requests[0].request_line == "127.0.0.1"

    def test_prompt_loop_route_single_token_with_surrounding_whitespace__creates_empty_request_line(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """Single-token commands with surrounding whitespace correctly resolve route and pass empty request line."""

        received_requests: list[contract.IControllerRequest[contract.ControllerArguments]] = []

        def whoami_controller(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerResult:
            received_requests.append(req)
            return contract.ControllerResult(action=contract.ControllerAction.TERMINATE)

        dummy_input_source.feed_inputs("   whoami   ")
        dummy_router.connect("whoami", whoami_controller)

        prompt = presentation.PromptLoop(router=dummy_router, session=test_session)
        prompt.run()

        assert dummy_router.locate_calls == ["whoami"]
        assert len(received_requests) == 1
        assert received_requests[0].request_line == ""

    def test_prompt_loop_route_multiple_commands_in_sequence__executes_all_in_order(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """PromptLoop sequentially reads and dispatches multiple commands in execution order."""

        execution_order: list[str] = []

        def make_recorder(name: str) -> contract.Controller:
            def controller(
                session: contract.SessionContext,
                req: contract.IControllerRequest[contract.ControllerArguments],
            ) -> contract.ControllerResult:
                execution_order.append(name)
                return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

            return controller

        dummy_input_source.feed_inputs("step1", "step2", "step3", "exit")
        dummy_router.connect("step1", make_recorder("step1"))
        dummy_router.connect("step2", make_recorder("step2"))
        dummy_router.connect("step3", make_recorder("step3"))
        dummy_router.connect("exit", _terminate_controller)

        prompt = presentation.PromptLoop(router=dummy_router, session=test_session)
        prompt.run()

        assert execution_order == ["step1", "step2", "step3"]
        assert dummy_router.locate_calls == ["step1", "step2", "step3", "exit"]


class TestPromptLoopResultHandling:
    """Tests verifying controller response evaluation and output messaging."""

    def test_prompt_loop_controller_returns_continue_with_message__writes_message_to_view_and_continues(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
        dummy_view: testing.DummyView,
    ) -> None:
        """PromptLoop outputs message to view when ControllerResult contains a message on CONTINUE."""

        dummy_input_source.feed_inputs("run_step", "exit")

        def step_controller(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerResult:
            return contract.ControllerResult(
                action=contract.ControllerAction.CONTINUE,
                message="Step completed successfully.",
            )

        dummy_router.connect("run_step", step_controller)
        dummy_router.connect("exit", _terminate_controller)

        prompt = presentation.PromptLoop(router=dummy_router, session=test_session)
        prompt.run()

        assert dummy_view.messages == ["Step completed successfully."]

    def test_prompt_loop_controller_returns_continue_without_message__continues_without_writing_message(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
        dummy_view: testing.DummyView,
    ) -> None:
        """PromptLoop emits no message when ControllerResult message is None on CONTINUE."""

        dummy_input_source.feed_inputs("silent_step", "exit")

        def silent_controller(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerResult:
            return contract.ControllerResult(
                action=contract.ControllerAction.CONTINUE,
                message=None,
            )

        dummy_router.connect("silent_step", silent_controller)
        dummy_router.connect("exit", _terminate_controller)

        prompt = presentation.PromptLoop(router=dummy_router, session=test_session)
        prompt.run()

        assert dummy_view.messages == []

    def test_prompt_loop_controller_returns_terminate_with_message__writes_message_and_exits(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
        dummy_view: testing.DummyView,
    ) -> None:
        """PromptLoop outputs message to view before terminating when ControllerResult terminates."""

        dummy_input_source.feed_inputs("bye")

        def bye_controller(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerResult:
            return contract.ControllerResult(
                action=contract.ControllerAction.TERMINATE,
                message="Session terminated by operator.",
            )

        dummy_router.connect("bye", bye_controller)

        prompt = presentation.PromptLoop(router=dummy_router, session=test_session)
        prompt.run()

        assert dummy_view.messages == ["Session terminated by operator."]

    def test_prompt_loop_controller_returns_raw_terminate_action__terminates_cleanly(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """PromptLoop terminates cleanly when a controller returns a raw ControllerAction.TERMINATE."""

        dummy_input_source.feed_inputs("quit_raw")

        def raw_exit_controller(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerAction:
            return contract.ControllerAction.TERMINATE

        dummy_router.connect("quit_raw", cast(contract.Controller, raw_exit_controller))

        prompt = presentation.PromptLoop(router=dummy_router, session=test_session)
        prompt.run()

        assert dummy_router.locate_calls == ["quit_raw"]

    def test_prompt_loop_controller_returns_raw_continue_action__continues_loop(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """PromptLoop continues loop when a controller returns a raw ControllerAction.CONTINUE."""

        dummy_input_source.feed_inputs("continue_raw", "exit")

        def raw_continue_controller(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerAction:
            return contract.ControllerAction.CONTINUE

        dummy_router.connect("continue_raw", cast(contract.Controller, raw_continue_controller))
        dummy_router.connect("exit", _terminate_controller)

        prompt = presentation.PromptLoop(router=dummy_router, session=test_session)
        prompt.run()

        assert dummy_router.locate_calls == ["continue_raw", "exit"]

    def test_prompt_loop_controller_returns_none__defaults_to_continue(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """PromptLoop treats a controller returning None as ControllerAction.CONTINUE."""

        dummy_input_source.feed_inputs("noop", "exit")

        def none_controller(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> None:
            return None

        dummy_router.connect("noop", cast(contract.Controller, none_controller))
        dummy_router.connect("exit", _terminate_controller)

        prompt = presentation.PromptLoop(router=dummy_router, session=test_session)
        prompt.run()

        assert dummy_router.locate_calls == ["noop", "exit"]
