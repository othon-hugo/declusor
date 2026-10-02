from pathlib import Path

import pytest

from declusor import command, config


def test_execute_command_dto_valid() -> None:
    """ExecuteCommandDTO should accept a valid non-empty command string."""

    dto = command.ExecuteCommandDTO(command_line="uname -a")
    assert dto.command_line == "uname -a"


@pytest.mark.parametrize("invalid_cmd", ["", "   ", "\t\n"])
def test_execute_command_dto_rejects_empty(invalid_cmd: str) -> None:
    """ExecuteCommandDTO should reject empty or whitespace-only commands."""

    with pytest.raises(config.InvalidOperation, match="Command line cannot be empty"):
        command.ExecuteCommandDTO(command_line=invalid_cmd)


def test_execute_file_dto_valid(tmp_path: Path) -> None:
    """ExecuteFileDTO should accept an existing file path."""

    test_file = tmp_path / "script.sh"
    test_file.write_text("echo hello")

    dto = command.ExecuteFileDTO(filepath=test_file)
    assert dto.filepath == test_file


def test_execute_file_dto_rejects_missing_file(tmp_path: Path) -> None:
    """ExecuteFileDTO should reject a non-existent file path."""

    missing = tmp_path / "nonexistent.sh"
    with pytest.raises(config.InvalidOperation):
        command.ExecuteFileDTO(filepath=missing)


@pytest.mark.parametrize("invalid_path", ["", "   ", "\t\n"])
def test_execute_file_dto_rejects_empty_path(invalid_path: str) -> None:
    """ExecuteFileDTO should reject empty or whitespace-only file paths."""

    with pytest.raises(config.InvalidOperation, match="File path cannot be empty"):
        command.ExecuteFileDTO(filepath=invalid_path)


def test_execute_file_dto_rejects_null_bytes() -> None:
    """ExecuteFileDTO should reject file paths containing null bytes."""

    with pytest.raises(config.InvalidOperation, match="File path cannot contain null bytes"):
        command.ExecuteFileDTO(filepath="/tmp/script\x00.sh")


def test_upload_file_dto_valid(tmp_path: Path) -> None:
    """UploadFileDTO should accept an existing file path."""

    test_file = tmp_path / "payload.bin"
    test_file.write_bytes(b"\x00\x01\x02")

    dto = command.UploadFileDTO(filepath=test_file)
    assert dto.filepath == test_file
    assert dto.destination is None


def test_upload_file_dto_with_valid_destination(tmp_path: Path) -> None:
    """UploadFileDTO should accept an existing file path and a valid destination."""

    test_file = tmp_path / "payload.bin"
    test_file.write_bytes(b"\x00\x01\x02")

    dto = command.UploadFileDTO(filepath=test_file, destination=" /tmp/dest.bin ")
    assert dto.filepath == test_file
    assert dto.destination == "/tmp/dest.bin"


def test_upload_file_dto_rejects_missing_file(tmp_path: Path) -> None:
    """UploadFileDTO should reject a non-existent file path."""

    missing = tmp_path / "nonexistent.bin"
    with pytest.raises(config.InvalidOperation):
        command.UploadFileDTO(filepath=missing)


@pytest.mark.parametrize("invalid_path", ["", "   ", "\t\n"])
def test_upload_file_dto_rejects_empty_path(invalid_path: str) -> None:
    """UploadFileDTO should reject empty or whitespace-only file paths."""

    with pytest.raises(config.InvalidOperation, match="File path cannot be empty"):
        command.UploadFileDTO(filepath=invalid_path)


def test_upload_file_dto_rejects_null_bytes() -> None:
    """UploadFileDTO should reject file paths containing null bytes."""

    with pytest.raises(config.InvalidOperation, match="File path cannot contain null bytes"):
        command.UploadFileDTO(filepath="/tmp/payload\x00.bin")


@pytest.mark.parametrize("invalid_dest", ["", "   ", "\t\n"])
def test_upload_file_dto_rejects_empty_destination(tmp_path: Path, invalid_dest: str) -> None:
    """UploadFileDTO should reject empty or whitespace-only destination paths."""

    test_file = tmp_path / "payload.bin"
    test_file.write_bytes(b"\x00")

    with pytest.raises(config.InvalidOperation, match="Destination path cannot be empty"):
        command.UploadFileDTO(filepath=test_file, destination=invalid_dest)


def test_upload_file_dto_rejects_destination_null_bytes(tmp_path: Path) -> None:
    """UploadFileDTO should reject destination paths containing null bytes."""

    test_file = tmp_path / "payload.bin"
    test_file.write_bytes(b"\x00")

    with pytest.raises(config.InvalidOperation, match="Destination path cannot contain null bytes"):
        command.UploadFileDTO(filepath=test_file, destination="/tmp/out\x00.bin")


@pytest.mark.parametrize("invalid_dest", ["/tmp/out\n.bin", "/tmp/out\r.bin", "/tmp/out\x1b.bin"])
def test_upload_file_dto_rejects_destination_control_characters(tmp_path: Path, invalid_dest: str) -> None:
    """UploadFileDTO should reject destination paths containing control characters or newlines."""

    test_file = tmp_path / "payload.bin"
    test_file.write_bytes(b"\x00")

    with pytest.raises(config.InvalidOperation, match="Destination path cannot contain control characters"):
        command.UploadFileDTO(filepath=test_file, destination=invalid_dest)


def test_load_module_dto_valid() -> None:
    """LoadModuleDTO should accept a module name or relative module path."""

    dto = command.LoadModuleDTO(module_name="discovery/sysinfo")
    assert dto.module_name == "discovery/sysinfo"

    dto_sub = command.LoadModuleDTO(module_name="custom/module/name")
    assert dto_sub.module_name == "custom/module/name"


@pytest.mark.parametrize("invalid_name", ["", "   ", "\t\n"])
def test_load_module_dto_rejects_empty(invalid_name: str) -> None:
    """LoadModuleDTO should reject empty or whitespace-only names."""

    with pytest.raises(config.InvalidOperation, match="Module name cannot be empty"):
        command.LoadModuleDTO(module_name=invalid_name)


def test_shell_dto_defaults() -> None:
    """LaunchShellDTO should allow instantiation with defaults."""

    dto = command.LaunchShellDTO()
    assert dto.banner is None


def test_execute_code_dto_valid() -> None:
    """ExecuteCodeDTO should accept a valid non-empty code string."""

    dto = command.ExecuteCodeDTO(code="print('hello')")
    assert dto.code == "print('hello')"


@pytest.mark.parametrize("invalid_code", ["", "   ", "\t\n"])
def test_execute_code_dto_rejects_empty(invalid_code: str) -> None:
    """ExecuteCodeDTO should reject empty or whitespace-only code."""

    with pytest.raises(config.InvalidOperation, match="Code cannot be empty"):
        command.ExecuteCodeDTO(code=invalid_code)
