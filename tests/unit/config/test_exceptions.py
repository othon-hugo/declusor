"""Unit tests for framework exceptions and error hierarchies."""

from pathlib import Path

import pytest

from declusor import command, config, contract, controller, core, presentation


class TestExceptionHierarchy:
    """Tests verifying inheritance hierarchies across all domain exceptions."""

    def test_declusor_exception__subclass__inherits_from_built_in_exception(self) -> None:
        """Verify DeclusorException inherits directly from built-in Exception."""

        assert issubclass(config.DeclusorException, Exception)

    def test_connection_exceptions__hierarchy__inherit_from_connection_error_and_declusor_exception(self) -> None:
        """Verify connection error family inherits from ConnectionError and DeclusorException."""

        assert issubclass(config.ConnectionError, config.DeclusorException)
        assert issubclass(config.ConnectionClosed, config.ConnectionError)
        assert issubclass(config.ConnectionTimeoutError, config.ConnectionError)
        assert issubclass(config.ConnectionHandshakeError, config.ConnectionError)

    def test_storage_exceptions__hierarchy__inherit_from_storage_error_and_invalid_operation(self) -> None:
        """Verify storage errors inherit from StorageError, InvalidOperation, and DeclusorException."""

        assert issubclass(config.StorageError, config.DeclusorException)
        assert issubclass(config.StorageValidationError, config.StorageError)
        assert issubclass(config.StorageValidationError, config.InvalidOperation)

    def test_command_exceptions__hierarchy__inherit_from_command_error_and_invalid_operation(self) -> None:
        """Verify command errors inherit from CommandError, InvalidOperation, and DeclusorException."""

        assert issubclass(config.CommandError, config.DeclusorException)
        assert issubclass(config.CommandValidationError, config.CommandError)
        assert issubclass(config.CommandValidationError, config.InvalidOperation)

    def test_plugin_exceptions__hierarchy__inherit_from_plugin_error_and_declusor_exception(self) -> None:
        """Verify plugin errors inherit from PluginError and DeclusorException."""

        assert issubclass(config.PluginError, config.DeclusorException)
        assert issubclass(config.PluginNotFoundError, config.PluginError)
        assert issubclass(config.PluginValidationError, config.PluginError)
        assert issubclass(config.LauncherDeliveryError, config.PluginError)

    def test_router_exceptions__hierarchy__inherit_from_router_error_and_value_error(self) -> None:
        """Verify router errors inherit from RouterError and ValueError."""

        assert issubclass(config.RouterError, config.DeclusorException)
        assert issubclass(config.DuplicateRouteError, config.RouterError)
        assert issubclass(config.DuplicateRouteError, ValueError)

    def test_leaf_exceptions__hierarchy__inherit_from_declusor_exception(self) -> None:
        """Verify remaining domain exceptions inherit directly from DeclusorException."""

        assert issubclass(config.ControllerError, config.DeclusorException)
        assert issubclass(config.ParserError, config.DeclusorException)
        assert issubclass(config.PromptError, config.DeclusorException)
        assert issubclass(config.InvalidOperation, config.DeclusorException)


class TestDeclusorWarning:
    """Tests for DeclusorWarning diagnostic warning class."""

    def test_declusor_warning__subclass__inherits_from_warning(self) -> None:
        """Verify DeclusorWarning inherits from the built-in Warning class."""

        assert issubclass(config.DeclusorWarning, Warning)

    def test_declusor_warning__initialization__stores_description_and_formats_str(self) -> None:
        """Verify DeclusorWarning stores description and matches string representation."""

        warning = config.DeclusorWarning("experimental feature enabled")

        assert warning.description == "experimental feature enabled"
        assert str(warning) == "experimental feature enabled"

    def test_declusor_warning__keyword_argument__raises_type_error_due_to_positional_only(self) -> None:
        """Verify passing description as a keyword argument raises TypeError."""

        with pytest.raises(TypeError, match="positional-only"):
            config.DeclusorWarning(description="diagnostic message")  # type: ignore[call-arg]


class TestConnectionExceptions:
    """Tests for ConnectionError and its concrete subclasses."""

    def test_connection_closed__default_arguments__sets_standard_message_and_none_peer(self) -> None:
        """Verify ConnectionClosed defaults to standard message and None peer address."""

        err = config.ConnectionClosed()

        assert str(err) == "Connection is closed."
        assert err.peer_address is None

    def test_connection_closed__custom_arguments__stores_message_and_peer_address(self) -> None:
        """Verify ConnectionClosed preserves custom message and peer address."""

        err = config.ConnectionClosed("remote peer disconnected", peer_address="192.168.1.100:4444")

        assert str(err) == "remote peer disconnected"
        assert err.peer_address == "192.168.1.100:4444"

    def test_connection_timeout_error__default_arguments__stores_none_timeout_and_operation(self) -> None:
        """Verify ConnectionTimeoutError defaults timeout and operation to None."""

        err = config.ConnectionTimeoutError("socket read timed out")

        assert str(err) == "socket read timed out"
        assert err.timeout is None
        assert err.operation is None

    def test_connection_timeout_error__custom_arguments__stores_timeout_and_operation(self) -> None:
        """Verify ConnectionTimeoutError preserves timeout duration and operation name."""

        err = config.ConnectionTimeoutError("handshake timed out", timeout=5.0, operation="handshake")

        assert str(err) == "handshake timed out"
        assert err.timeout == 5.0
        assert err.operation == "handshake"

    def test_connection_handshake_error__default_arguments__sets_standard_message_and_none_tokens(self) -> None:
        """Verify ConnectionHandshakeError defaults to standard message and None tokens."""

        err = config.ConnectionHandshakeError()

        assert str(err) == "Handshake failed."
        assert err.expected_ack is None
        assert err.received_ack is None

    def test_connection_handshake_error__custom_tokens__stores_expected_and_received_acks(self) -> None:
        """Verify ConnectionHandshakeError preserves expected and received ACK tokens."""

        err = config.ConnectionHandshakeError(
            "handshake token mismatch",
            expected_ack=b"\x00\x01",
            received_ack=b"\xff\xfe",
        )

        assert str(err) == "handshake token mismatch"
        assert err.expected_ack == b"\x00\x01"
        assert err.received_ack == b"\xff\xfe"


class TestStorageExceptions:
    """Tests for StorageError and StorageValidationError."""

    def test_storage_error__string_path__converts_to_path_object(self) -> None:
        """Verify StorageError converts string path to Path instance."""

        err = config.StorageError("failed to write payload", path="/tmp/payload.bin")

        assert str(err) == "failed to write payload"
        assert err.path == Path("/tmp/payload.bin")
        assert isinstance(err.path, Path)

    def test_storage_error__path_instance__preserves_path_object(self) -> None:
        """Verify StorageError preserves provided Path instance."""

        expected_path = Path("/var/log/session.log")
        err = config.StorageError("permission denied", path=expected_path)

        assert str(err) == "permission denied"
        assert err.path == expected_path

    def test_storage_error__none_path__sets_path_to_none(self) -> None:
        """Verify StorageError defaults path to None when omitted."""

        err = config.StorageError("storage subsystem failure")

        assert str(err) == "storage subsystem failure"
        assert err.path is None

    def test_storage_validation_error__initialization__preserves_path_and_description(self) -> None:
        """Verify StorageValidationError populates path, description, and string representation."""

        err = config.StorageValidationError("relative path not allowed", path="../malicious.bin")

        assert str(err) == "invalid operation: relative path not allowed"
        assert err.description == "relative path not allowed"
        assert err.path == Path("../malicious.bin")

    def test_storage_validation_error__none_path__sets_path_to_none(self) -> None:
        """Verify StorageValidationError allows omitting path."""

        err = config.StorageValidationError("invalid filename")

        assert str(err) == "invalid operation: invalid filename"
        assert err.description == "invalid filename"
        assert err.path is None

    def test_storage_validation_error__multiple_inheritance__caught_by_both_types(self) -> None:
        """Verify StorageValidationError is an instance of both StorageError and InvalidOperation."""

        err = config.StorageValidationError("corrupt asset header", path="/data/asset.dat")

        assert isinstance(err, config.StorageError)
        assert isinstance(err, config.InvalidOperation)


class TestInvalidOperationException:
    """Tests for InvalidOperation exception."""

    def test_invalid_operation__initialization__formats_prefix_and_stores_description(self) -> None:
        """Verify InvalidOperation prepends 'invalid operation: ' to description."""

        err = config.InvalidOperation("session not established")

        assert err.description == "session not established"
        assert str(err) == "invalid operation: session not established"

    def test_invalid_operation__keyword_argument__raises_type_error_due_to_positional_only(self) -> None:
        """Verify passing description as a keyword argument raises TypeError."""

        with pytest.raises(TypeError, match="positional-only"):
            config.InvalidOperation(description="cannot execute")  # type: ignore[call-arg]


class TestCommandExceptions:
    """Tests for CommandError and CommandValidationError."""

    def test_command_error__defaults__stores_description_and_none_command_name(self) -> None:
        """Verify CommandError formats message and defaults command_name to None."""

        err = config.CommandError("unrecognized command verb")

        assert err.description == "unrecognized command verb"
        assert err.command_name is None
        assert str(err) == "command error: unrecognized command verb"

    def test_command_error__with_command_name__stores_command_name(self) -> None:
        """Verify CommandError preserves command_name when specified."""

        err = config.CommandError("dispatch failed", command_name="sysinfo")

        assert err.description == "dispatch failed"
        assert err.command_name == "sysinfo"
        assert str(err) == "command error: dispatch failed"

    def test_command_error__keyword_argument__raises_type_error_due_to_positional_only(self) -> None:
        """Verify passing description as a keyword argument raises TypeError."""

        with pytest.raises(TypeError, match="positional-only"):
            config.CommandError(description="syntax error")  # type: ignore[call-arg]

    def test_command_validation_error__defaults__stores_none_field_value_and_command_name(self) -> None:
        """Verify CommandValidationError defaults field, value, and command_name to None."""

        err = config.CommandValidationError("validation failed")

        assert err.description == "command error: validation failed"
        assert err.field is None
        assert err.value is None
        assert err.command_name is None
        assert str(err) == "invalid operation: command error: validation failed"

    def test_command_validation_error__with_all_arguments__stores_attributes_and_satisfies_types(self) -> None:
        """Verify CommandValidationError preserves field, value, and command_name."""

        err = config.CommandValidationError(
            "port out of range",
            field="port",
            value=70000,
            command_name="listen",
        )

        assert err.description == "command error: port out of range"
        assert err.field == "port"
        assert err.value == 70000
        assert err.command_name == "listen"
        assert isinstance(err, config.CommandError)
        assert isinstance(err, config.InvalidOperation)
        assert str(err) == "invalid operation: command error: port out of range"

    def test_command_validation_error__keyword_argument_for_description__raises_type_error(self) -> None:
        """Verify passing description as a keyword argument raises TypeError."""

        with pytest.raises(TypeError, match="positional-only"):
            config.CommandValidationError(description="missing argument", field="cmd")  # type: ignore[call-arg]


class TestControllerError:
    """Tests for ControllerError exception."""

    def test_controller_error__defaults__stores_description_and_none_controller_name(self) -> None:
        """Verify ControllerError formats message and defaults controller_name to None."""

        err = config.ControllerError("failed to instantiate handler")

        assert err.description == "failed to instantiate handler"
        assert err.controller_name is None
        assert str(err) == "controller error: failed to instantiate handler"

    def test_controller_error__with_controller_name__stores_controller_name(self) -> None:
        """Verify ControllerError preserves controller_name when provided."""

        err = config.ControllerError("routing loop detected", controller_name="ShellController")

        assert err.description == "routing loop detected"
        assert err.controller_name == "ShellController"
        assert str(err) == "controller error: routing loop detected"

    def test_controller_error__keyword_argument__raises_type_error_due_to_positional_only(self) -> None:
        """Verify passing description as a keyword argument raises TypeError."""

        with pytest.raises(TypeError, match="positional-only"):
            config.ControllerError(description="dispatch exception")  # type: ignore[call-arg]


class TestParserError:
    """Tests for ParserError exception."""

    def test_parser_error__initialization__formats_message_and_inherits_declusor_exception(self) -> None:
        """Verify ParserError formats standard message and inherits from DeclusorException."""

        err = config.ParserError("unrecognized option: --bad-flag")

        assert str(err) == "unrecognized option: --bad-flag"
        assert isinstance(err, config.DeclusorException)


class TestRouterExceptions:
    """Tests for RouterError and DuplicateRouteError."""

    def test_router_error__without_description__formats_route_only(self) -> None:
        """Verify RouterError formats route without description suffix."""

        err = config.RouterError("exec")

        assert err.route == "exec"
        assert err.description is None
        assert str(err) == "invalid route: 'exec'"

    def test_router_error__with_description__formats_route_and_description(self) -> None:
        """Verify RouterError formats route with parenthesized description."""

        err = config.RouterError("upload", "endpoint inactive")

        assert err.route == "upload"
        assert err.description == "endpoint inactive"
        assert str(err) == "invalid route: 'upload' (endpoint inactive)"

    def test_duplicate_route_error__default_description__formats_default_text(self) -> None:
        """Verify DuplicateRouteError formats standard default description."""

        err = config.DuplicateRouteError("exec")

        assert err.route == "exec"
        assert err.description == "route already exists."
        assert str(err) == "invalid route: 'exec' (route already exists.)"

    def test_duplicate_route_error__custom_description__formats_custom_text(self) -> None:
        """Verify DuplicateRouteError preserves custom description."""

        err = config.DuplicateRouteError("exec", "route already bound to py_socket")

        assert err.route == "exec"
        assert err.description == "route already bound to py_socket"
        assert str(err) == "invalid route: 'exec' (route already bound to py_socket)"

    def test_duplicate_route_error__multiple_inheritance__caught_by_both_router_and_value_error(self) -> None:
        """Verify DuplicateRouteError is caught by both RouterError and ValueError handlers."""

        err = config.DuplicateRouteError("download")

        assert isinstance(err, config.RouterError)
        assert isinstance(err, ValueError)


class TestPluginExceptions:
    """Tests for PluginError and its concrete subclasses."""

    def test_plugin_error__defaults__stores_none_plugin_name(self) -> None:
        """Verify PluginError defaults plugin_name to None."""

        err = config.PluginError("failed to load entry point")

        assert str(err) == "failed to load entry point"
        assert err.plugin_name is None

    def test_plugin_error__with_plugin_name__stores_plugin_name(self) -> None:
        """Verify PluginError preserves plugin_name when provided."""

        err = config.PluginError("syntax error in extension", plugin_name="shell_socket")

        assert str(err) == "syntax error in extension"
        assert err.plugin_name == "shell_socket"

    def test_plugin_not_found_error__empty_available__formats_none_in_message(self) -> None:
        """Verify PluginNotFoundError displays 'none' when no available plugins are given."""

        err = config.PluginNotFoundError("missing_plugin")

        assert err.plugin_name == "missing_plugin"
        assert err.available_plugins == ()
        assert str(err) == "Unknown client 'missing_plugin'. Available clients: none"

    def test_plugin_not_found_error__with_available_list__normalizes_tuple_and_sorts_names(self) -> None:
        """Verify PluginNotFoundError normalizes list to sorted tuple in error message."""

        err = config.PluginNotFoundError("missing_plugin", available_plugins=["py_socket", "shell_socket"])

        assert err.plugin_name == "missing_plugin"
        assert err.available_plugins == ("py_socket", "shell_socket")
        assert str(err) == "Unknown client 'missing_plugin'. Available clients: 'py_socket', 'shell_socket'"

    def test_plugin_not_found_error__custom_message__overrides_default_template(self) -> None:
        """Verify PluginNotFoundError uses custom message when explicitly supplied."""

        err = config.PluginNotFoundError(
            "custom_plug",
            available_plugins=("a", "b"),
            message="Custom plugin lookup failure.",
        )

        assert str(err) == "Custom plugin lookup failure."
        assert err.plugin_name == "custom_plug"
        assert err.available_plugins == ("a", "b")

    def test_plugin_validation_error__defaults__stores_none_candidate_and_none_plugin(self) -> None:
        """Verify PluginValidationError defaults candidate and plugin_name to None."""

        err = config.PluginValidationError("missing execute() method")

        assert str(err) == "missing execute() method"
        assert err.candidate is None
        assert err.plugin_name is None

    def test_plugin_validation_error__with_candidate_and_plugin__stores_attributes(self) -> None:
        """Verify PluginValidationError preserves candidate type and plugin_name."""

        err = config.PluginValidationError(
            "incompatible extension type",
            plugin_name="custom_plugin",
            candidate=dict,
        )

        assert str(err) == "incompatible extension type"
        assert err.plugin_name == "custom_plugin"
        assert err.candidate is dict

    def test_launcher_delivery_error__defaults__stores_none_output_path_and_none_plugin(self) -> None:
        """Verify LauncherDeliveryError defaults output_path and plugin_name to None."""

        err = config.LauncherDeliveryError("failed to generate launcher")

        assert str(err) == "failed to generate launcher"
        assert err.output_path is None
        assert err.plugin_name is None

    def test_launcher_delivery_error__string_path__converts_to_path_object(self) -> None:
        """Verify LauncherDeliveryError converts string output_path to Path."""

        err = config.LauncherDeliveryError(
            "write permission denied",
            output_path="/tmp/stage/launcher.sh",
            plugin_name="shell_socket",
        )

        assert str(err) == "write permission denied"
        assert err.output_path == Path("/tmp/stage/launcher.sh")
        assert err.plugin_name == "shell_socket"

    def test_launcher_delivery_error__path_instance__preserves_path_object(self) -> None:
        """Verify LauncherDeliveryError preserves Path instance for output_path."""

        expected_path = Path("/home/user/delivery.py")
        err = config.LauncherDeliveryError(
            "target file busy",
            output_path=expected_path,
            plugin_name="py_socket",
        )

        assert str(err) == "target file busy"
        assert err.output_path == expected_path
        assert err.plugin_name == "py_socket"


class TestPromptError:
    """Tests for PromptError exception."""

    def test_prompt_error__without_description__formats_argument_only(self) -> None:
        """Verify PromptError formats argument without description suffix."""

        err = config.PromptError("--unknown")

        assert err.argument == "--unknown"
        assert err.description is None
        assert str(err) == "invalid argument: '--unknown'"

    def test_prompt_error__with_description__formats_argument_and_description(self) -> None:
        """Verify PromptError formats argument with parenthesized description."""

        err = config.PromptError("-p", "missing port value")

        assert err.argument == "-p"
        assert err.description == "missing port value"
        assert str(err) == "invalid argument: '-p' (missing port value)"


class TestCatchAllDeclusorException:
    """Tests validating universal catchability via DeclusorException."""

    @pytest.mark.parametrize(
        "exc_instance",
        [
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
        ],
    )
    def test_catch_all__all_concrete_exceptions__caught_by_declusor_exception(self, exc_instance: config.DeclusorException) -> None:
        """Verify that every concrete domain exception is caught by except DeclusorException."""

        with pytest.raises(config.DeclusorException) as exc_info:
            raise exc_instance

        assert exc_info.value is exc_instance


class TestPackageExceptionExports:
    """Tests validating exception re-exports across public domain packages."""

    def test_package_exports__domain_packages__reexport_identical_exception_classes(self) -> None:
        """Verify domain packages re-export identical exception classes from config."""

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
