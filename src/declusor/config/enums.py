from enum import StrEnum


class OperationCode(StrEnum):
    """Enumeration of file operation codes."""

    EXEC_FILE = "EXECUTE_FILE"
    STORE_FILE = "STORE_FILE"
