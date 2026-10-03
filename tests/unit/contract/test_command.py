"""Unit tests for the ICommand abstract contract and execution lifecycle."""

import pytest

from declusor import contract, testing


class StreamingCommand(contract.ICommand):
    """Concrete command double demonstrating an interleaved streaming execution pattern."""

    def __init__(self) -> None:
        """Initialize recorded streaming execution steps."""

        self.stream_steps: list[str] = []

    def send_request(self, session: contract.SessionContext, /) -> None:
        """Record transmission step within streaming coordination."""

        self.stream_steps.append("send_request")

    def read_response(self, session: contract.SessionContext, /) -> None:
        """Record receive step within streaming coordination."""

        self.stream_steps.append("read_response")

    def execute(self, session: contract.SessionContext, /) -> None:
        """Coordinate interleaved streaming across the session."""

        self.send_request(session)
        self.read_response(session)
        self.send_request(session)
        self.read_response(session)
        self.stream_steps.append("streaming_completed")


class IncompleteCommandMissingRead(contract.ICommand):
    """Concrete command subclass omitting read_response implementation."""

    def send_request(self, session: contract.SessionContext, /) -> None:
        """Transmit request."""


class IncompleteCommandMissingSend(contract.ICommand):
    """Concrete command subclass omitting send_request implementation."""

    def read_response(self, session: contract.SessionContext, /) -> None:
        """Read response."""


class MinimalSuperCallingCommand(contract.ICommand):
    """Command double delegating directly to abstract super methods."""

    def send_request(self, session: contract.SessionContext, /) -> None:
        """Delegate to superclass abstract method."""

        super().send_request(session)  # type: ignore[safe-super]

    def read_response(self, session: contract.SessionContext, /) -> None:
        """Delegate to superclass abstract method."""

        super().read_response(session)  # type: ignore[safe-super]


class TestICommandAbstraction:
    """Tests verifying ICommand abstract class enforcement and instantiation invariants."""

    def test_icommand_instantiation__direct_call__raises_type_error(self) -> None:
        """Direct instantiation of ICommand raises TypeError due to abstract methods."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            contract.ICommand()  # type: ignore[abstract]

    def test_icommand_instantiation__missing_send_request__raises_type_error(self) -> None:
        """Subclass missing send_request implementation raises TypeError upon instantiation."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteCommandMissingSend()  # type: ignore[abstract]

    def test_icommand_instantiation__missing_read_response__raises_type_error(self) -> None:
        """Subclass missing read_response implementation raises TypeError upon instantiation."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteCommandMissingRead()  # type: ignore[abstract]

    def test_icommand_super_calls__raise_not_implemented_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """Verify abstract method default implementations raise NotImplementedError when called."""

        command = MinimalSuperCallingCommand()

        with pytest.raises(NotImplementedError):
            command.send_request(test_session)

        with pytest.raises(NotImplementedError):
            command.read_response(test_session)


class TestICommandExecutionLifecycle:
    """Tests verifying default ICommand execution ordering, parameter conventions, and overrides."""

    def test_icommand_execute__default_lifecycle__invokes_send_request_then_read_response_in_order(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """Default execute invocation calls send_request followed by read_response in exact order."""

        command = testing.DummyCommand()

        command.execute(test_session)

        assert command.call_sequence == ["send_request", "read_response"]

    def test_icommand_execute__keyword_session_argument__raises_type_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """ICommand.execute enforces positional-only session argument and rejects keyword passing."""

        command = testing.DummyCommand()

        with pytest.raises(TypeError, match="positional-only"):
            command.execute(session=test_session)  # type: ignore[call-arg]

    def test_icommand_send_request__keyword_session_argument__raises_type_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """ICommand.send_request enforces positional-only session argument and rejects keyword passing."""

        command = testing.DummyCommand()

        with pytest.raises(TypeError, match="positional-only"):
            command.send_request(session=test_session)  # type: ignore[call-arg]

    def test_icommand_read_response__keyword_session_argument__raises_type_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """ICommand.read_response enforces positional-only session argument and rejects keyword passing."""

        command = testing.DummyCommand()

        with pytest.raises(TypeError, match="positional-only"):
            command.read_response(session=test_session)  # type: ignore[call-arg]

    def test_icommand_execute__send_request_failure__aborts_before_read_response(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """Failure during send_request raises immediately and prevents read_response invocation."""

        command = testing.DummyCommand(send_request_error=RuntimeError("transmission error"))

        with pytest.raises(RuntimeError, match="transmission error"):
            command.execute(test_session)

        assert command.call_sequence == ["send_request"]

    def test_icommand_execute__custom_streaming_override__executes_overridden_coordination(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """Subclasses can override execute to coordinate custom patterns such as bidirectional streaming."""

        streaming_command = StreamingCommand()

        streaming_command.execute(test_session)

        assert streaming_command.stream_steps == [
            "send_request",
            "read_response",
            "send_request",
            "read_response",
            "streaming_completed",
        ]
