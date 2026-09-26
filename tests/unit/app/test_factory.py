from collections.abc import Sequence
from pathlib import Path

import pytest

from declusor import app, config, core, testing


def test_create_application_defaults_to_cli() -> None:
    """Verify create_application with default mode returns a TerminalApplication."""

    declusor_app = app.create_application()
    assert isinstance(declusor_app, app.TerminalApplication)
    assert isinstance(declusor_app, core.Application)


def test_create_application_cli_mode() -> None:
    """Verify create_application with ExecutionMode.CLI returns a TerminalApplication."""

    declusor_app = app.create_application(mode=config.ExecutionMode.CLI)
    assert isinstance(declusor_app, app.TerminalApplication)


@pytest.mark.parametrize(
    "unsupported_mode",
    [
        config.ExecutionMode.API,
        config.ExecutionMode.MCP,
        config.ExecutionMode.HTTP,
    ],
)
def test_create_application_unsupported_modes_raise_invalid_operation(
    unsupported_mode: config.ExecutionMode,
) -> None:
    """Verify create_application raises InvalidOperation for modes without registered factories."""

    with pytest.raises(config.InvalidOperation, match=f"Execution mode '{unsupported_mode.value}'"):
        app.create_application(mode=unsupported_mode)


def test_register_and_get_custom_application_factory(dummy_app: testing.DummyApplication) -> None:
    """Verify registering a custom factory allows create_application to resolve that mode."""

    def custom_factory(search_dirs: Sequence[Path] | None = None) -> core.ApplicationProtocol:
        return dummy_app

    # Register custom factory for MCP
    app.register_application_factory(config.ExecutionMode.MCP, custom_factory)
    try:
        retrieved_factory = app.get_application_factory(config.ExecutionMode.MCP)
        assert retrieved_factory is custom_factory

        resolved_app = app.create_application(mode=config.ExecutionMode.MCP)
        assert resolved_app is dummy_app
    finally:
        # Restore factory registry state (re-remove custom factory)
        app._APPLICATION_FACTORIES.pop(config.ExecutionMode.MCP, None)
