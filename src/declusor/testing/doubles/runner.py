from declusor import contract


class DummySessionRunner(contract.ISessionRunner):
    """Deterministic test double for ISessionRunner tracking execution invocations."""

    def __init__(self, run_error: BaseException | None = None) -> None:
        self.run_calls: list[tuple[contract.SessionContext, contract.IRouter]] = []
        self.run_error: BaseException | None = run_error

    def run(self, session: contract.SessionContext, router: contract.IRouter, /) -> None:
        """Record the session run invocation, or raise configured error."""

        self.run_calls.append((session, router))

        if self.run_error is not None:
            raise self.run_error
