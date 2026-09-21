from abc import ABC, abstractmethod


class IPrompt(ABC):
    """Interactive command-line loop that reads, routes, and dispatches user input."""

    @abstractmethod
    def run(self) -> None:
        """Start the interactive prompt loop.

        Blocks until the user exits (via the ``exit`` command or ``KeyboardInterrupt``).
        On each iteration, reads a command, routes it through the ``IRouter``,
        and dispatches it to the appropriate controller.
        """

        raise NotImplementedError
