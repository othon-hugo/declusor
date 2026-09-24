from declusor import config


def test_client_file_enum() -> None:
    """Verify ClientFile enum values."""
    assert config.ClientFile.SHELL_SOCKET == "shell_socket.sh"
    assert config.ClientFile.PY_SOCKET == "py_socket"
    assert isinstance(config.ClientFile.SHELL_SOCKET, str)


def test_operation_code_enum() -> None:
    """Verify OperationCode enum values."""
    assert config.OperationCode.EXEC_FILE == "EXECUTE_FILE"
    assert config.OperationCode.STORE_FILE == "STORE_FILE"
    assert isinstance(config.OperationCode.EXEC_FILE, str)
