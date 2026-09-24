from pathlib import Path

import pytest

from declusor import config
from declusor.command import (
    ExecuteCommandDTO,
    ExecuteFileDTO,
    LaunchShellDTO,
    LoadModuleDTO,
    UploadFileDTO,
)


def test_execute_command_dto_valid() -> None:
    """ExecuteCommandDTO should accept a valid non-empty command string."""
    dto = ExecuteCommandDTO(command_line="uname -a")
    assert dto.command_line == "uname -a"


@pytest.mark.parametrize("invalid_cmd", ["", "   ", "\t\n"])
def test_execute_command_dto_rejects_empty(invalid_cmd: str) -> None:
    """ExecuteCommandDTO should reject empty or whitespace-only commands."""
    with pytest.raises(config.InvalidOperation, match="Command line cannot be empty"):
        ExecuteCommandDTO(command_line=invalid_cmd)


def test_execute_file_dto_valid(tmp_path: Path) -> None:
    """ExecuteFileDTO should accept an existing file path."""
    test_file = tmp_path / "script.sh"
    test_file.write_text("echo hello")

    dto = ExecuteFileDTO(filepath=test_file)
    assert dto.filepath == test_file


def test_execute_file_dto_rejects_missing_file(tmp_path: Path) -> None:
    """ExecuteFileDTO should reject a non-existent file path."""
    missing = tmp_path / "nonexistent.sh"
    with pytest.raises(config.InvalidOperation):
        ExecuteFileDTO(filepath=missing)


def test_upload_file_dto_valid(tmp_path: Path) -> None:
    """UploadFileDTO should accept an existing file path."""
    test_file = tmp_path / "payload.bin"
    test_file.write_bytes(b"\x00\x01\x02")

    dto = UploadFileDTO(filepath=test_file)
    assert dto.filepath == test_file


def test_upload_file_dto_rejects_missing_file(tmp_path: Path) -> None:
    """UploadFileDTO should reject a non-existent file path."""
    missing = tmp_path / "nonexistent.bin"
    with pytest.raises(config.InvalidOperation):
        UploadFileDTO(filepath=missing)


def test_load_module_dto_valid() -> None:
    """LoadModuleDTO should accept a clean module name."""
    dto = LoadModuleDTO(module_name="discovery/sysinfo")
    assert dto.module_name == "discovery/sysinfo"


@pytest.mark.parametrize("invalid_name", ["", "   ", "../escape", "..\\escape", "/etc/passwd"])
def test_load_module_dto_rejects_invalid_names(invalid_name: str) -> None:
    """LoadModuleDTO should reject empty names and path traversal attempts."""
    with pytest.raises(config.InvalidOperation):
        LoadModuleDTO(module_name=invalid_name)


def test_shell_dto_defaults() -> None:
    """LaunchShellDTO should allow instantiation with defaults."""
    dto = LaunchShellDTO()
    assert dto.banner is None
