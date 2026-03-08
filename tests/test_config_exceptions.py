"""Tests for ``declusor.config.exceptions``.

Verifies the custom exception hierarchy: ``DeclusorException`` as the root,
domain-specific subclasses (``InvalidOperation``, ``ParserError``, ``RouterError``,
``PromptError``, ``ControllerError``, ``ConnectionFailure``), and the ``ExitRequest``
control-flow exception.
"""

import pytest

# =============================================================================
# Tests: DeclusorException (base class)
# =============================================================================


def test_declusor_exception_inherits_from_exception() -> None:
    """``DeclusorException`` must be a subclass of the built-in ``Exception``."""


def test_declusor_exception_is_catchable_as_exception() -> None:
    """Raising ``DeclusorException`` must be catchable in an ``except Exception`` block."""


# =============================================================================
# Tests: InvalidOperation
# =============================================================================


def test_invalid_operation_stores_description() -> None:
    """The ``description`` attribute must hold the string passed to the constructor."""


def test_invalid_operation_str_contains_prefix_and_description() -> None:
    """``str(exc)`` must produce ``"invalid operation: <description>"``."""


def test_invalid_operation_inherits_from_declusor_exception() -> None:
    """``InvalidOperation`` must be a subclass of ``DeclusorException``."""


def test_invalid_operation_accepts_empty_description() -> None:
    """An empty description must not raise; ``str(exc)`` yields ``"invalid operation: "``."""


# =============================================================================
# Tests: ConnectionFailure
# =============================================================================


def test_connection_failure_inherits_from_declusor_exception() -> None:
    """``ConnectionFailure`` must be a subclass of ``DeclusorException``."""


def test_connection_failure_does_not_shadow_builtin_connection_error() -> None:
    """``ConnectionFailure`` must *not* be an instance of the built-in ``ConnectionError``."""


# =============================================================================
# Tests: ParserError
# =============================================================================


def test_parser_error_inherits_from_declusor_exception() -> None:
    """``ParserError`` must be a subclass of ``DeclusorException``."""


def test_parser_error_message_is_preserved() -> None:
    """The message passed to the constructor must be accessible via ``str(exc)``."""


# =============================================================================
# Tests: RouterError
# =============================================================================


def test_router_error_stores_route() -> None:
    """The ``route`` attribute must hold the route name passed to the constructor."""


def test_router_error_str_includes_route() -> None:
    """``str(exc)`` must contain ``"invalid route: '<route>'"``."""


def test_router_error_optional_description_default_none() -> None:
    """When no ``description`` keyword is passed, ``exc.description`` must be ``None``."""


def test_router_error_optional_description_stored() -> None:
    """A provided ``description`` keyword must be stored on the exception."""


def test_router_error_inherits_from_declusor_exception() -> None:
    """``RouterError`` must be a subclass of ``DeclusorException``."""


# =============================================================================
# Tests: PromptError
# =============================================================================


def test_prompt_error_stores_argument() -> None:
    """The ``argument`` attribute must hold the argument string."""


def test_prompt_error_str_includes_argument() -> None:
    """``str(exc)`` must contain ``"invalid argument: '<argument>'"``."""


def test_prompt_error_inherits_from_declusor_exception() -> None:
    """``PromptError`` must be a subclass of ``DeclusorException``."""


# =============================================================================
# Tests: ControllerError
# =============================================================================


def test_controller_error_stores_description() -> None:
    """The ``description`` attribute must hold the error description."""


def test_controller_error_str_contains_prefix_and_description() -> None:
    """``str(exc)`` must produce ``"controller error: <description>"``."""


def test_controller_error_inherits_from_declusor_exception() -> None:
    """``ControllerError`` must be a subclass of ``DeclusorException``."""


# =============================================================================
# Tests: ExitRequest
# =============================================================================


def test_exit_request_inherits_from_declusor_exception() -> None:
    """``ExitRequest`` must be a subclass of ``DeclusorException``."""


def test_exit_request_is_catchable_as_declusor_exception() -> None:
    """Raising ``ExitRequest`` must be catchable in an ``except DeclusorException`` block."""


def test_exit_request_is_distinct_from_other_exception_types() -> None:
    """``isinstance`` checks must distinguish ``ExitRequest`` from ``InvalidOperation`` and ``ParserError``."""


def test_exit_request_no_args_produces_empty_message() -> None:
    """``ExitRequest()`` with no arguments must have ``str(exc) == ""`` or similar."""
