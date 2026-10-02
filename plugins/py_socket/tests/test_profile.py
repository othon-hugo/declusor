import declusor_py_socket as py_socket
import pytest

from declusor import config


def test_py_socket_profile_render_operation_command_exec_file() -> None:
    """Verify EXEC_FILE opcode renders execute_base64_encoded_value call."""

    profile = py_socket.DEFAULT_PY_SOCKET
    rendered = profile.render_operation_command(config.OperationCode.EXEC_FILE, "AAAA==")
    assert rendered == "execute_base64_encoded_value('AAAA==')"


def test_py_socket_profile_render_operation_command_store_file() -> None:
    """Verify STORE_FILE opcode renders store_base64_encoded_value call with destination path."""

    profile = py_socket.DEFAULT_PY_SOCKET
    rendered = profile.render_operation_command(config.OperationCode.STORE_FILE, "AAAA==", "/tmp/out")
    assert rendered == "store_base64_encoded_value('AAAA==', '/tmp/out')"


def test_py_socket_profile_supported_functions_are_immutable() -> None:
    """Verify supported functions mapping in PySocketProfile cannot be modified."""

    profile = py_socket.PySocketProfile()
    with pytest.raises(TypeError):
        profile._supported_functions[config.OperationCode.EXEC_FILE] = "changed"  # type: ignore[index]


def test_py_socket_profile_render_operation_command_with_special_characters() -> None:
    """Verify render_operation_command safely quotes arguments containing quotes and special characters."""

    profile = py_socket.DEFAULT_PY_SOCKET
    rendered = profile.render_operation_command(config.OperationCode.STORE_FILE, "payload", "path with 'quotes' & $vars")
    assert rendered == "store_base64_encoded_value('payload', \"path with 'quotes' & $vars\")"
    assert profile.render_operation_command(config.OperationCode.EXEC_FILE) == "execute_base64_encoded_value()"

    empty_profile = py_socket.PySocketProfile(_supported_functions={})
    assert empty_profile.render_operation_command(config.OperationCode.EXEC_FILE) is None


def test_py_socket_profile_render_operation_command_load_module() -> None:
    """Verify LOAD_MODULE opcode renders execute_base64_encoded_value call."""

    profile = py_socket.DEFAULT_PY_SOCKET
    rendered = profile.render_operation_command(config.OperationCode.LOAD_MODULE, "b64_mod_data==")
    assert rendered == "execute_base64_encoded_value('b64_mod_data==')"


def test_py_socket_profile_render_operation_command_exec_code() -> None:
    """Verify EXEC_CODE opcode returns Python code unaltered."""

    profile = py_socket.DEFAULT_PY_SOCKET

    py_code = "import os\nprint(os.getpid())"
    assert profile.render_operation_command(config.OperationCode.EXEC_CODE, py_code) == py_code

    py_shebang = "#!/usr/bin/env python\nprint('hello')"
    assert profile.render_operation_command(config.OperationCode.EXEC_CODE, py_shebang) == py_shebang

    assert profile.render_operation_command(config.OperationCode.EXEC_CODE) == ""


def test_py_socket_profile_render_operation_command_exec_command_shell() -> None:
    """Verify EXEC_COMMAND deterministically wraps commands in execute_system_command."""

    profile = py_socket.DEFAULT_PY_SOCKET

    cmd = "uname -a && whoami"
    expected = "execute_system_command('uname -a && whoami')"
    assert profile.render_operation_command(config.OperationCode.EXEC_COMMAND, cmd) == expected

    cmd_quotes = "echo 'hello world' \"nested\""
    expected_quotes = "execute_system_command('echo \\'hello world\\' \"nested\"')"
    assert profile.render_operation_command(config.OperationCode.EXEC_COMMAND, cmd_quotes) == expected_quotes


def test_py_socket_profile_render_operation_command_exec_command_empty() -> None:
    """Verify EXEC_COMMAND with empty or missing arguments returns empty execute_system_command call."""

    profile = py_socket.DEFAULT_PY_SOCKET

    assert profile.render_operation_command(config.OperationCode.EXEC_COMMAND) == "execute_system_command('')"
    assert profile.render_operation_command(config.OperationCode.EXEC_COMMAND, "") == "execute_system_command('')"
