from pathlib import Path

import pytest

from declusor import config


def test_exception_hierarchy() -> None:
    """Verify that all domain exceptions inherit from DeclusorException."""

    assert issubclass(config.DeclusorException, Exception)
    assert issubclass(config.ConnectionError, config.DeclusorException)
    assert issubclass(config.ConnectionClosed, config.ConnectionError)
    assert issubclass(config.ConnectionTimeoutError, config.ConnectionError)
    assert issubclass(config.ConnectionHandshakeError, config.ConnectionError)
    assert issubclass(config.StorageError, config.DeclusorException)
    assert issubclass(config.StorageValidationError, config.StorageError)
    assert issubclass(config.StorageValidationError, config.InvalidOperation)
    assert issubclass(config.PromptError, config.DeclusorException)
    assert issubclass(config.InvalidOperation, config.DeclusorException)
    assert issubclass(config.CommandError, config.DeclusorException)
    assert issubclass(config.CommandValidationError, config.CommandError)
    assert issubclass(config.CommandValidationError, config.InvalidOperation)
    assert issubclass(config.ControllerError, config.DeclusorException)
    assert issubclass(config.ParserError, config.DeclusorException)
    assert issubclass(config.RouterError, config.DeclusorException)
    assert issubclass(config.DuplicateRouteError, config.RouterError)
    assert issubclass(config.DuplicateRouteError, ValueError)
    assert issubclass(config.PluginError, config.DeclusorException)
    assert issubclass(config.PluginNotFoundError, config.PluginError)
    assert issubclass(config.PluginValidationError, config.PluginError)
    assert issubclass(config.LauncherDeliveryError, config.PluginError)


def test_declusor_warning_hierarchy() -> None:
    """Verify DeclusorWarning inherits from Warning."""

    assert issubclass(config.DeclusorWarning, Warning)

    warning = config.DeclusorWarning("test warning")
    assert warning.description == "test warning"
    assert str(warning) == "test warning"


def test_connection_exceptions_attributes() -> None:
    """Verify attributes and formatting for ConnectionError subclasses."""

    closed = config.ConnectionClosed("lost peer", peer_address="192.168.1.5:4444")
    assert str(closed) == "lost peer"
    assert closed.peer_address == "192.168.1.5:4444"

    timeout = config.ConnectionTimeoutError("read timed out", timeout=3.5, operation="read")
    assert str(timeout) == "read timed out"
    assert timeout.timeout == 3.5
    assert timeout.operation == "read"

    handshake = config.ConnectionHandshakeError("bad ack", expected_ack=b"good", received_ack=b"bad")
    assert str(handshake) == "bad ack"
    assert handshake.expected_ack == b"good"
    assert handshake.received_ack == b"bad"


def test_storage_exceptions_attributes() -> None:
    """Verify attributes and formatting for StorageError and StorageValidationError."""

    err = config.StorageError("read failed", path="/var/data.bin")
    assert str(err) == "read failed"
    assert err.path == Path("/var/data.bin")

    val_err = config.StorageValidationError("empty file path", path="")
    assert "empty file path" in str(val_err)
    assert isinstance(val_err, config.InvalidOperation)
    assert isinstance(val_err, config.StorageError)


def test_plugin_exceptions_attributes() -> None:
    """Verify attributes for PluginError, PluginNotFoundError, and LauncherDeliveryError."""

    base_plugin_err = config.PluginError("load failed", plugin_name="custom_plugin")
    assert base_plugin_err.plugin_name == "custom_plugin"

    not_found = config.PluginNotFoundError("missing_plugin", available_plugins=("plugin_a", "plugin_b"))
    assert not_found.plugin_name == "missing_plugin"
    assert not_found.available_plugins == ("plugin_a", "plugin_b")
    assert "missing_plugin" in str(not_found)
    assert "'plugin_a', 'plugin_b'" in str(not_found)

    val_err = config.PluginValidationError("invalid class", candidate=int, plugin_name="bad_plugin")
    assert val_err.candidate is int
    assert val_err.plugin_name == "bad_plugin"

    delivery_err = config.LauncherDeliveryError("write failed", output_path="/tmp/launch.sh", plugin_name="sh")
    assert delivery_err.output_path == Path("/tmp/launch.sh")
    assert delivery_err.plugin_name == "sh"


def test_command_validation_error_attributes() -> None:
    """Verify CommandValidationError preserves InvalidOperation and CommandError inheritance with attributes."""

    err = config.CommandValidationError("code is required", field="code", value="")
    assert isinstance(err, config.CommandError)
    assert isinstance(err, config.InvalidOperation)
    assert err.field == "code"
    assert err.value == ""
    assert "code is required" in str(err)


def test_router_and_duplicate_route_error() -> None:
    """Verify RouterError and DuplicateRouteError inheritance and attributes."""

    err = config.RouterError("help", "not found")
    assert err.route == "help"
    assert err.description == "not found"
    assert str(err) == "invalid route: 'help' (not found)"

    dup = config.DuplicateRouteError("exec")
    assert dup.route == "exec"
    assert isinstance(dup, config.RouterError)
    assert isinstance(dup, ValueError)
    assert "exec" in str(dup)


def test_prompt_error_formatting() -> None:
    """Verify PromptError formatting with and without description."""

    err_without_desc = config.PromptError("foo")
    assert err_without_desc.argument == "foo"
    assert err_without_desc.description is None
    assert str(err_without_desc) == "invalid argument: 'foo'"

    err_with_desc = config.PromptError("bar", "unknown option")
    assert err_with_desc.argument == "bar"
    assert err_with_desc.description == "unknown option"
    assert str(err_with_desc) == "invalid argument: 'bar' (unknown option)"


def test_invalid_operation_formatting() -> None:
    """Verify InvalidOperation formatting."""

    err = config.InvalidOperation("file missing")
    assert err.description == "file missing"
    assert str(err) == "invalid operation: file missing"


def test_command_error_formatting() -> None:
    """Verify CommandError formatting."""

    err = config.CommandError("execution failed")
    assert err.description == "execution failed"
    assert str(err) == "command error: execution failed"


def test_controller_error_formatting() -> None:
    """Verify ControllerError formatting."""

    err = config.ControllerError("dispatch failed")
    assert err.description == "dispatch failed"
    assert str(err) == "controller error: dispatch failed"


def test_catch_all_with_declusor_exception() -> None:
    """Verify that any domain error can be caught with DeclusorException."""

    exceptions = [
        config.ConnectionError("conn"),
        config.ConnectionClosed("closed"),
        config.ConnectionTimeoutError("timeout"),
        config.ConnectionHandshakeError("handshake"),
        config.StorageError("storage"),
        config.StorageValidationError("storage_val"),
        config.PromptError("arg"),
        config.InvalidOperation("op"),
        config.CommandError("cmd"),
        config.CommandValidationError("val"),
        config.ControllerError("ctl"),
        config.ParserError("parse"),
        config.RouterError("route"),
        config.DuplicateRouteError("dup"),
        config.PluginError("plug"),
        config.PluginNotFoundError("plug_not_found"),
        config.PluginValidationError("plug_val"),
        config.LauncherDeliveryError("launcher_delivery"),
    ]

    for exc in exceptions:
        with pytest.raises(config.DeclusorException):
            raise exc


def test_package_exception_exports() -> None:
    """Verify that domain packages re-export their respective domain exceptions."""

    from declusor import command, contract, controller, core, presentation

    assert command.CommandError is config.CommandError
    assert command.CommandValidationError is config.CommandValidationError
    assert command.InvalidOperation is config.InvalidOperation

    assert controller.ControllerError is config.ControllerError

    assert core.DuplicateRouteError is config.DuplicateRouteError
    assert core.LauncherDeliveryError is config.LauncherDeliveryError
    assert core.ParserError is config.ParserError
    assert core.PluginError is config.PluginError
    assert core.PluginNotFoundError is config.PluginNotFoundError
    assert core.PluginValidationError is config.PluginValidationError
    assert core.RouterError is config.RouterError

    assert presentation.PromptError is config.PromptError

    assert contract.ConnectionError is config.ConnectionError
    assert contract.ConnectionClosed is config.ConnectionClosed
    assert contract.ConnectionTimeoutError is config.ConnectionTimeoutError
    assert contract.ConnectionHandshakeError is config.ConnectionHandshakeError
    assert contract.InvalidOperation is config.InvalidOperation
