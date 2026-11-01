"""Deterministic command test double recording request and response calls."""

from dataclasses import dataclass, field

from declusor import contract


@dataclass
class DummyCommand(contract.ICommand):
    """Command double tracking execution sequencing for lifecycle testing."""

    call_sequence: list[str] = field(default_factory=list)
    """Recorded list of called method names in invocation order."""

    send_request_error: BaseException | None = None
    """Optional exception to raise when send_request is invoked."""

    read_response_error: BaseException | None = None
    """Optional exception to raise when read_response is invoked."""

    def send_request(self, session: contract.SessionContext, /) -> None:
        """Record send_request invocation and raise configured error if set."""

        self.call_sequence.append("send_request")

        if self.send_request_error is not None:
            raise self.send_request_error

    def read_response(self, session: contract.SessionContext, /) -> None:
        """Record read_response invocation and raise configured error if set."""

        self.call_sequence.append("read_response")

        if self.read_response_error is not None:
            raise self.read_response_error
