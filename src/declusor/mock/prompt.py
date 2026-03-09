from declusor import interface


class MockPrompt(interface.IPrompt):
    """A mock implementation of IPrompt for testing."""

    def __init__(self) -> None:
        self.run_called = False

    def run(self) -> None:
        self.run_called = True
