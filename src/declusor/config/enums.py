from enum import StrEnum


class ClientFile(StrEnum):
    """Enumeration of available client script files."""

    SHELL_SOCKET = "shell_socket.sh"
    PY_SOCKET = "py_socket"


class OperationCode(StrEnum):
    """Enumeration of file operation codes."""

    EXEC_FILE = "EXECUTE_FILE"
    STORE_FILE = "STORE_FILE"
