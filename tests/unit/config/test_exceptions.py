import pytest

from declusor import config


def test_exception_hierarchy() -> None:
    """Verify that all domain exceptions inherit from DeclusorException."""

    assert issubclass(config.DeclusorException, Exception)
    assert issubclass(config.ConnectionError, config.DeclusorException)
    assert issubclass(config.ConnectionClosed, config.ConnectionError)
    assert issubclass(config.ConnectionTimeoutError, config.ConnectionError)
    assert issubclass(config.ConnectionHandshakeError, config.ConnectionError)
    assert issubclass(config.PromptError, config.DeclusorException)
    assert issubclass(config.InvalidOperation, config.DeclusorException)
    assert issubclass(config.CommandError, config.DeclusorException)
    assert issubclass(config.CommandValidationError, config.CommandError)
    assert issubclass(config.CommandValidationError, config.InvalidOperation)
    assert issubclass(config.ControllerError, config.DeclusorException)
    assert issubclass(config.ParserError, config.DeclusorException)
    assert issubclass(config.RouterError, config.DeclusorException)
    assert issubclass(config.PluginError, config.DeclusorException)
    assert issubclass(config.PluginValidationError, config.PluginError)


def test_declusor_warning_hierarchy() -> None:
    """Verify DeclusorWarning inherits from Warning."""

    assert issubclass(config.DeclusorWarning, Warning)

    warning = config.DeclusorWarning("test warning")
    assert warning.description == "test warning"
    assert str(warning) == "test warning"


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


def test_router_error_formatting() -> None:
    """Verify RouterError formatting with and without description."""

    err_without_desc = config.RouterError("help")
    assert err_without_desc.route == "help"
    assert err_without_desc.description is None
    assert str(err_without_desc) == "invalid route: 'help'"

    err_with_desc = config.RouterError("exec", "route missing")
    assert err_with_desc.route == "exec"
    assert err_with_desc.description == "route missing"
    assert str(err_with_desc) == "invalid route: 'exec' (route missing)"


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
        config.PromptError("arg"),
        config.InvalidOperation("op"),
        config.CommandError("cmd"),
        config.CommandValidationError("val"),
        config.ControllerError("ctl"),
        config.ParserError("parse"),
        config.RouterError("route"),
        config.PluginError("plug"),
        config.PluginValidationError("plug_val"),
    ]

    for exc in exceptions:
        with pytest.raises(config.DeclusorException):
            raise exc
