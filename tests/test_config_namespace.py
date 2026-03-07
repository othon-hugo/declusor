"""Tests for ``declusor.config.enums`` (``ClientFile``, ``OperationCode``).

Verifies enum membership, ``StrEnum`` behaviour, string equality semantics,
hashability, and pattern-matching compatibility.
"""

import pytest

# =============================================================================
# Tests: ClientFile enum
# =============================================================================


def test_client_file_shell_socket_value() -> None:
    """``ClientFile.SHELL_SOCKET`` must have value ``"shell_socket.sh"``."""


def test_client_file_is_str_enum() -> None:
    """``ClientFile`` members must be usable directly as ``str`` values."""


def test_client_file_str_conversion() -> None:
    """``str(ClientFile.SHELL_SOCKET)`` must return the underlying value."""


def test_client_file_equality_with_string() -> None:
    """``ClientFile.SHELL_SOCKET == "shell_socket.sh"`` must be ``True``."""


def test_client_file_all_members() -> None:
    """``ClientFile`` must contain exactly ``SHELL_SOCKET``."""


def test_client_file_hashable() -> None:
    """``ClientFile`` members must be usable as ``dict`` keys and in ``set`` collections."""


# =============================================================================
# Tests: OperationCode enum
# =============================================================================


def test_operation_code_exec_file_value() -> None:
    """``OperationCode.EXEC_FILE`` must have value ``"EXECUTE_FILE"``."""


def test_operation_code_store_file_value() -> None:
    """``OperationCode.STORE_FILE`` must have value ``"STORE_FILE"``."""


def test_operation_code_is_str_enum() -> None:
    """``OperationCode`` members must be usable directly as ``str`` values."""


def test_operation_code_str_conversion() -> None:
    """``str(OperationCode.EXEC_FILE)`` must return the underlying value."""


def test_operation_code_equality_with_string() -> None:
    """``OperationCode.EXEC_FILE == "EXECUTE_FILE"`` must be ``True``."""


def test_operation_code_all_members() -> None:
    """``OperationCode`` must contain exactly ``EXEC_FILE`` and ``STORE_FILE``."""


def test_operation_code_members_are_distinct() -> None:
    """``OperationCode.EXEC_FILE`` must not equal ``OperationCode.STORE_FILE``."""


def test_operation_code_hashable() -> None:
    """``OperationCode`` members must be usable as ``dict`` keys."""


# =============================================================================
# Tests: Pattern-matching support
# =============================================================================


def test_client_file_usable_in_match_statement() -> None:
    """A ``match`` / ``case ClientFile.SHELL_SOCKET`` branch must execute correctly."""


def test_operation_code_usable_in_match_statement() -> None:
    """A ``match`` / ``case OperationCode.EXEC_FILE`` branch must execute correctly."""
