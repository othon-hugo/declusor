from collections.abc import Sequence

from declusor import contract, core


class DummyApplication:
    """Fully-typed test double for Application lifecycle in CLI and integration tests."""

    def __init__(
        self,
        parse_result: core.DeclusorOptions | None = None,
        parse_error: BaseException | None = None,
        run_error: BaseException | None = None,
    ) -> None:
        self.parse_result: core.DeclusorOptions = (
            parse_result
            if parse_result is not None
            else {
                "host": "127.0.0.1",
                "port": 9000,
                "client": contract.ClientConfig(
                    kind="dummy",
                    host="127.0.0.1",
                    port=9000,
                    data_paths=None,
                    options={},
                ),
            }
        )
        self.parse_error: BaseException | None = parse_error
        self.run_error: BaseException | None = run_error
        self.parse_calls: list[Sequence[str] | None] = []
        self.run_calls: list[core.DeclusorOptions] = []

    def parse(self, argv: Sequence[str] | None = None, /) -> core.DeclusorOptions:
        """Simulate parsing command-line options."""

        self.parse_calls.append(argv)

        if self.parse_error is not None:
            raise self.parse_error

        return self.parse_result

    def run(self, options: core.DeclusorOptions, /) -> None:
        """Simulate running the application lifecycle."""

        self.run_calls.append(options)

        if self.run_error is not None:
            raise self.run_error
