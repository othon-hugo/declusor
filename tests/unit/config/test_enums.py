import pytest

from declusor import config


def test_operation_code_enum() -> None:
    """Verify OperationCode enum values."""

    assert isinstance(config.OperationCode.EXEC_FILE, str)
    assert isinstance(config.OperationCode.STORE_FILE, str)


def test_execution_mode_enum_members() -> None:
    """Verify ExecutionMode enum members and string representations."""

    assert config.ExecutionMode.CLI.value == "cli"
    assert config.ExecutionMode.API.value == "api"
    assert config.ExecutionMode.MCP.value == "mcp"
    assert config.ExecutionMode.HTTP.value == "http"


def test_execution_mode_default() -> None:
    """Verify ExecutionMode.default() returns CLI mode."""

    assert config.ExecutionMode.default() == config.ExecutionMode.CLI
    assert config.Settings.DEFAULT_EXECUTION_MODE == config.ExecutionMode.CLI


@pytest.mark.parametrize(
    ("input_str", "expected_mode"),
    [
        ("cli", config.ExecutionMode.CLI),
        ("CLI", config.ExecutionMode.CLI),
        ("  Cli  ", config.ExecutionMode.CLI),
        ("api", config.ExecutionMode.API),
        ("API", config.ExecutionMode.API),
        ("mcp", config.ExecutionMode.MCP),
        ("MCP", config.ExecutionMode.MCP),
        ("http", config.ExecutionMode.HTTP),
        ("HTTP", config.ExecutionMode.HTTP),
    ],
)
def test_execution_mode_from_string_success(input_str: str, expected_mode: config.ExecutionMode) -> None:
    """Verify ExecutionMode.from_string parses valid mode names case-insensitively."""

    assert config.ExecutionMode.from_string(input_str) == expected_mode


def test_execution_mode_from_string_invalid() -> None:
    """Verify ExecutionMode.from_string raises ValueError for unrecognized strings."""

    with pytest.raises(ValueError, match="Invalid execution mode: 'unknown'"):
        config.ExecutionMode.from_string("unknown")
