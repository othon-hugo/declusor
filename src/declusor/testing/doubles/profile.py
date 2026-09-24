from declusor import config, contract


class DummyConnectionProfile(contract.IConnectionProfile):
    """Fully-typed in-memory connection profile with configurable operation command rendering."""

    def __init__(
        self,
        name: str = "dummy_profile",
        buffer_size: int = 4096,
        timeout: float | None = 5.0,
        rendered_commands: dict[config.OperationCode, str | None] | None = None,
    ) -> None:
        self._name = name
        self._buffer_size = buffer_size
        self._timeout = timeout
        self.rendered_commands: dict[config.OperationCode, str | None] = dict(rendered_commands) if rendered_commands is not None else {}
        self.render_calls: list[tuple[config.OperationCode, tuple[str, ...]]] = []

    @property
    def default_buffer_size(self) -> int:
        return self._buffer_size

    @property
    def default_timeout(self) -> float | None:
        return self._timeout

    def set_rendered_command(self, opcode: config.OperationCode, rendered: str | None) -> None:
        """Configure the returned rendered command string for an operation code."""

        self.rendered_commands[opcode] = rendered

    def render_operation_command(self, opcode: config.OperationCode, /, *args: str) -> str | None:
        """Return configured rendered command or a deterministic default string."""

        self.render_calls.append((opcode, args))

        if opcode in self.rendered_commands:
            return self.rendered_commands[opcode]

        args_str = f" {' '.join(args)}" if args else ""

        return f"{opcode.value}{args_str}"
