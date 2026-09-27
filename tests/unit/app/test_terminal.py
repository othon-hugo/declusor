from pathlib import Path

from declusor import app, core, presentation, testing


def test_terminal_application_initialization() -> None:
    """Verify TerminalApplication initializes properly with components and runner."""

    manager = core.PluginManager()
    router = core.Router()
    view = presentation.TerminalView()
    input_source = presentation.TerminalInputSource()
    runner = testing.DummySessionRunner()

    declusor_app = app.TerminalApplication(
        router,
        view,
        plugin_manager=manager,
        session_runner=runner,
        input_source=input_source,
    )

    assert isinstance(declusor_app, core.Application)
    assert declusor_app.plugin_manager is manager


def test_create_terminal_application_initializes_plugins() -> None:
    """Verify create_terminal_application loads built-in plugins into manager."""

    declusor_app = app.create_terminal_application()

    assert isinstance(declusor_app, app.TerminalApplication)
    assert declusor_app.plugin_manager is not None
    assert "shell_socket" in declusor_app.plugin_manager.names()
    assert "py_socket" in declusor_app.plugin_manager.names()


def test_create_terminal_application_with_custom_manager() -> None:
    """Verify create_terminal_application honors injected plugin_manager."""

    custom_manager = core.PluginManager()
    custom_manager.register(testing.DummyPlugin)

    declusor_app = app.create_terminal_application(plugin_manager=custom_manager)

    assert declusor_app.plugin_manager is custom_manager
    assert testing.DummyPlugin.name in declusor_app.plugin_manager.names()


def test_create_terminal_application_with_search_dirs(tmp_path: Path) -> None:
    """Verify create_terminal_application passes search_dirs to plugin discovery."""

    declusor_app = app.create_terminal_application(search_dirs=[tmp_path])

    assert isinstance(declusor_app, app.TerminalApplication)
    assert "shell_socket" in declusor_app.plugin_manager.names()
