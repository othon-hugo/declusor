from declusor import config


def test_client_file_enum() -> None:
    """Verify ClientFile enum values."""

    assert isinstance(config.ClientFile.SHELL_SOCKET, str)
    assert isinstance(config.ClientFile.PY_SOCKET, str)


def test_operation_code_enum() -> None:
    """Verify OperationCode enum values."""

    assert isinstance(config.OperationCode.EXEC_FILE, str)
    assert isinstance(config.OperationCode.STORE_FILE, str)
