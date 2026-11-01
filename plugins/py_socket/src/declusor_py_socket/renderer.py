"""Python socket client operation renderer translating opcodes to Python syntax."""

from dataclasses import dataclass, field
from typing import Final

from declusor import config, contract, util


@dataclass(frozen=True)
class PySocketRenderer(contract.IOperationRenderer):
    """Translates OperationCode values to Python function call syntax.

    Composes primitive helper calls (storage, execution, encoding) into
    executable Python statements evaluated by the client launcher. This renderer
    is pure data — it never performs I/O.
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

    def render_operation_command(self, opcode: "config.OperationCode", /, *args: object) -> str | None:
        """Build the Python execution statement for a given operation code."""

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
        """Render system command execution statement."""

        command = str(args[0]).rstrip("\r\n") if args else ""

        return f"execute_system_command({util.quote(command)})"

    @staticmethod
    def render_exec_code(*args: object) -> str:
        """Render Python source code execution statement."""

        code = args[0] if args else ""

        return f"execute_source({code!r})"

    @staticmethod
    def render_store_file(*args: object) -> str | None:
        """Render file storage statement decoding base64 payload."""

        if not args:
            return None

        src_data_b64 = args[0]

        if len(args) > 1 and args[1]:
            return f"store_file(decode_base64({src_data_b64!r}), {args[1]!r})"

        return f"store_file(decode_base64({src_data_b64!r}))"

    @staticmethod
    def render_payload_execution(*args: object) -> str | None:
        """Render executable payload statement detecting script vs binary."""

        if not args:
            return None

        src_data_b64 = str(args[0])

        try:
            raw_bytes = util.convert_base64_to_bytes(src_data_b64)
            raw_bytes.decode("utf-8")

            return f"execute_source(decode_base64({src_data_b64!r}).decode('utf-8'))"
        except UnicodeDecodeError:
            return f"execute_binary(store_file(decode_base64({src_data_b64!r})), cleanup=True)"
        except Exception:
            return f"execute_source(decode_base64({src_data_b64!r}).decode('utf-8'))"
