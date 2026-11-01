"""Shell socket client operation renderer translating opcodes to Bash syntax."""

from dataclasses import dataclass, field
from typing import Final

from declusor import config, contract, util


@dataclass(frozen=True)
class ShellSocketRenderer(contract.IOperationRenderer):
    """Translates OperationCode values to Bash shell command strings.

    Composes primitive helper calls (storage, execution, encoding) into
    executable Bash shell statements evaluated by the client launcher. This
    renderer is pure data — it never performs I/O.
    """

    _supported_operations: Final[frozenset[config.OperationCode]] = field(
        default_factory=lambda: frozenset(
            {
                config.OperationCode.EXEC_COMMAND,
                config.OperationCode.EXEC_CODE,
                config.OperationCode.EXEC_FILE,
                config.OperationCode.STORE_FILE,
                config.OperationCode.LOAD_MODULE,
            }
        )
    )
    """Set of operation codes supported by this renderer."""

    def __post_init__(self) -> None:
        """Freeze supported operations into an immutable frozenset."""

        object.__setattr__(self, "_supported_operations", frozenset(self._supported_operations))

    @property
    def supported_operations(self) -> frozenset[config.OperationCode]:
        """Set of supported operation codes."""

        return self._supported_operations

    def render_operation_command(self, opcode: config.OperationCode, /, *args: object) -> str | None:
        """Build the shell execution statement for a given operation code."""

        if opcode not in self._supported_operations:
            return None

        match opcode:
            case config.OperationCode.EXEC_COMMAND:
                return self.render_exec_command(*args)
            case config.OperationCode.EXEC_CODE:
                return self.render_exec_code(*args)
            case config.OperationCode.STORE_FILE:
                return self.render_store_file(*args)
            case config.OperationCode.EXEC_FILE | config.OperationCode.LOAD_MODULE:
                return self.render_payload_execution(*args)
            case _:
                return None

    @staticmethod
    def render_exec_command(*args: object) -> str:
        """Render shell command execution statement."""

        return str(args[0]).rstrip("\r\n") if args else ""

    @staticmethod
    def render_exec_code(*args: object) -> str:
        """Render shell code execution statement."""

        return str(args[0]).rstrip("\r\n") if args else ""

    @staticmethod
    def render_store_file(*args: object) -> str | None:
        """Render file storage statement decoding base64 payload."""

        if not args:
            return None

        src_file_b64 = str(args[0])

        if len(args) > 1 and args[1]:
            return f"decode_b64 {util.quote(src_file_b64)} | store_file {util.quote(str(args[1]))}"

        return f"decode_b64 {util.quote(src_file_b64)} | store_file"

    @staticmethod
    def render_payload_execution(*args: object) -> str | None:
        """Render executable payload statement detecting script vs binary."""

        if not args:
            return None

        data_b64 = str(args[0])
        extra_args = (" " + " ".join(util.quote(str(a)) for a in args[1:])) if len(args) > 1 else ""

        try:
            raw_bytes = util.convert_base64_to_bytes(data_b64)
            raw_bytes.decode("utf-8")

            return f'execute_source "$(decode_b64 {util.quote(data_b64)})"{extra_args}'
        except UnicodeDecodeError:
            return f'execute_binary --cleanup "$(decode_b64 {util.quote(data_b64)} | store_file)"{extra_args}'
        except Exception:
            return f'execute_source "$(decode_b64 {util.quote(data_b64)})"{extra_args}'
