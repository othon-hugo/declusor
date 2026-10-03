"""Unit tests for the SessionContext and ISessionRunner contracts."""

import pytest

from declusor import contract, testing


class TrackingCommand(contract.ICommand):
    """Command double tracking the session instance passed to execute."""

    def __init__(self) -> None:
        """Initialize session capture state."""

        self.executed_session: contract.SessionContext | None = None

    def send_request(self, session: contract.SessionContext, /) -> None:
        """No-op request sender for abstract contract satisfaction."""

    def read_response(self, session: contract.SessionContext, /) -> None:
        """No-op response reader for abstract contract satisfaction."""

    def execute(self, session: contract.SessionContext, /) -> None:
        """Capture session context passed to execute."""

        self.executed_session = session


class IncompleteSessionRunnerMissingRun(contract.ISessionRunner):
    """Session runner subclass omitting run implementation."""


class ConcreteSessionRunner(contract.ISessionRunner):
    """Concrete session runner executing a workflow loop over session and router."""

    def __init__(self) -> None:
        """Initialize invocation tracking."""

        self.invocations: list[tuple[contract.SessionContext, contract.IRouter]] = []

    def run(self, session: contract.SessionContext, router: contract.IRouter, /) -> None:
        """Record workflow execution with session and router."""

        self.invocations.append((session, router))


class TestSessionContextLifecycle:
    """Tests verifying SessionContext initialization, collaborator retention, and defaults."""

    def test_session_context_init__optional_input_omitted__retains_collaborators_and_defaults_input_to_none(self) -> None:
        """SessionContext initializes required collaborators and sets optional input_source to None."""

        connection = testing.DummyConnection()
        view = testing.DummyView()
        plugin_processor = testing.DummyPluginFileStore()

        session = contract.SessionContext(
            connection=connection,
            view=view,
            plugin_processor=plugin_processor,
        )

        assert session.connection is connection
        assert session.view is view
        assert session.plugin is plugin_processor
        assert session.input is None

    def test_session_context_init__explicit_input_provided__retains_all_collaborators(self) -> None:
        """SessionContext retains explicit input_source alongside connection, view, and plugin_processor."""

        connection = testing.DummyConnection()
        view = testing.DummyView()
        plugin_processor = testing.DummyPluginFileStore()
        input_source = testing.DummyInputSource()

        session = contract.SessionContext(
            connection=connection,
            view=view,
            plugin_processor=plugin_processor,
            input_source=input_source,
        )

        assert session.connection is connection
        assert session.view is view
        assert session.plugin is plugin_processor
        assert session.input is input_source


class TestSessionContextProperties:
    """Tests verifying SessionContext property accessors return exact collaborator instances."""

    def test_session_context_properties__initialized_with_doubles__returns_exact_injected_instances(self) -> None:
        """Properties connection, view, input, and plugin return the exact injected collaborator instances."""

        connection = testing.DummyConnection()
        view = testing.DummyView()
        plugin_processor = testing.DummyPluginFileStore()
        input_source = testing.DummyInputSource()

        session = contract.SessionContext(
            connection=connection,
            view=view,
            plugin_processor=plugin_processor,
            input_source=input_source,
        )

        assert session.connection is connection
        assert session.view is view
        assert session.input is input_source
        assert session.plugin is plugin_processor

    def test_session_context_properties__are_read_only__reassignment_raises_attribute_error(self) -> None:
        """Verify SessionContext properties do not expose setters and reject reassignment."""

        session = contract.SessionContext(
            connection=testing.DummyConnection(),
            view=testing.DummyView(),
            plugin_processor=testing.DummyPluginFileStore(),
        )

        with pytest.raises(AttributeError):
            session.connection = testing.DummyConnection()  # type: ignore[misc]

        with pytest.raises(AttributeError):
            session.view = testing.DummyView()  # type: ignore[misc]

        with pytest.raises(AttributeError):
            session.plugin = testing.DummyPluginFileStore()  # type: ignore[misc]

        with pytest.raises(AttributeError):
            session.input = testing.DummyInputSource()  # type: ignore[misc]


class TestSessionContextExecution:
    """Tests verifying SessionContext.execute delegates execution to the command."""

    def test_session_context_execute__command_provided__delegates_to_command_execute_with_self(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """SessionContext.execute delegates execution to command.execute passing itself as session."""

        command = TrackingCommand()

        test_session.execute(command)

        assert command.executed_session is test_session

    def test_session_context_execute__dummy_command__runs_default_request_response_lifecycle(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """SessionContext.execute triggers the command's complete request-response lifecycle."""

        command = testing.DummyCommand()

        test_session.execute(command)

        assert command.call_sequence == ["send_request", "read_response"]


class TestISessionRunnerContract:
    """Tests verifying ISessionRunner abstract contract enforcement and concrete implementation."""

    def test_isession_runner_instantiation__direct_call__raises_type_error(self) -> None:
        """Direct instantiation of ISessionRunner raises TypeError due to abstract run method."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            contract.ISessionRunner()  # type: ignore[abstract]

    def test_isession_runner_instantiation__missing_run_method__raises_type_error(self) -> None:
        """Subclass missing run implementation raises TypeError upon instantiation."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteSessionRunnerMissingRun()  # type: ignore[abstract]

    def test_isession_runner_run__concrete_runner__executes_with_session_and_router(
        self,
        test_session: contract.SessionContext,
        dummy_router: testing.DummyRouter,
    ) -> None:
        """Concrete ISessionRunner executes workflow receiving session and router arguments."""

        runner = ConcreteSessionRunner()

        runner.run(test_session, dummy_router)

        assert len(runner.invocations) == 1
        assert runner.invocations[0] == (test_session, dummy_router)

    def test_isession_runner_run__keyword_arguments__raises_type_error(
        self,
        test_session: contract.SessionContext,
        dummy_router: testing.DummyRouter,
    ) -> None:
        """ISessionRunner.run enforces positional-only arguments and rejects keyword arguments."""

        runner = ConcreteSessionRunner()

        with pytest.raises(TypeError, match="positional-only"):
            runner.run(session=test_session, router=dummy_router)  # type: ignore[call-arg]

    def test_isession_runner_run__dummy_session_runner_double__records_session_and_router(
        self,
        test_session: contract.SessionContext,
        dummy_router: testing.DummyRouter,
    ) -> None:
        """DummySessionRunner double records run calls with session and router instances."""

        runner = testing.DummySessionRunner()

        runner.run(test_session, dummy_router)

        assert len(runner.run_calls) == 1
        assert runner.run_calls[0] == (test_session, dummy_router)
