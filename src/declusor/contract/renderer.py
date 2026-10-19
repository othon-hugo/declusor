from abc import ABC, abstractmethod

from declusor import config


class IOperationRenderer(ABC):
    """Command syntax renderer for remote clients.

    Translates abstract OperationCode tokens into agent-specific command
    strings without performing network I/O.
    """

    @abstractmethod
    def render_operation_command(self, opcode: config.OperationCode, /, *args: object) -> str | None:
        """Build the command string for a given operation code.

        Maps an ``OperationCode`` to its client-side function name and appends
        each argument as a shell-quoted token. Returns ``None`` if the opcode
        is not supported by this renderer.

        Args:
            opcode: The operation to invoke on the client.
            *args: Positional string arguments forwarded to the client function.

        Returns:
            A ready-to-send command string, or ``None`` if the opcode is unsupported.
        """

        raise NotImplementedError
