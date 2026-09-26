from declusor import config


def test_operation_code_enum() -> None:
    """Verify OperationCode enum values."""

    assert isinstance(config.OperationCode.EXEC_FILE, str)
    assert isinstance(config.OperationCode.STORE_FILE, str)
