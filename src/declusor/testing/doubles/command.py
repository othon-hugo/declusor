from dataclasses import dataclass, field

from declusor import contract


@dataclass
class DummyCommand(contract.ICommand):
    """Command double tracking execution sequencing for lifecycle testing."""

    call_sequence: list[str] = field(default_factory=list)
    send_request_error: BaseException | None = None
    read_response_error: BaseException | None = None

    def send_request(self, session: contract.SessionContext) -> None:
        self.call_sequence.append("send_request")

        if self.send_request_error is not None:
            raise self.send_request_error

    def read_response(self, session: contract.SessionContext) -> None:
        self.call_sequence.append("read_response")

        if self.read_response_error is not None:
            raise self.read_response_error
