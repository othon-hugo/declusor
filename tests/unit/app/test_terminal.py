from declusor import app, core, presentation


def test_create_application_initializes_plugins() -> None:
    """Verify create_application loads built-in plugins into manager."""

    declusor_app = app.create_application()
    assert isinstance(declusor_app, core.Application)
    assert isinstance(declusor_app, app.TerminalApplication)
    assert declusor_app.manager is not None
    assert "shell_socket" in declusor_app.manager.names()
    assert "py_socket" in declusor_app.manager.names()
    assert isinstance(declusor_app.runner, presentation.PromptLoop)


def test_create_terminal_application_initializes_plugins() -> None:
    """Verify create_terminal_application loads built-in plugins into manager."""

    declusor_app = app.create_terminal_application()
    assert isinstance(declusor_app, app.TerminalApplication)
    assert declusor_app.manager is not None
    assert "shell_socket" in declusor_app.manager.names()
    assert "py_socket" in declusor_app.manager.names()


def test_terminal_application_default_runner() -> None:
    """Verify TerminalApplication initializes with a PromptLoop runner."""

    manager = core.PluginManager()
    router = core.Router()
    view = presentation.TerminalView()
    input_source = presentation.TerminalInputSource()

    declusor_app = app.TerminalApplication(manager, router, view, input_source)
    assert isinstance(declusor_app.runner, presentation.PromptLoop)
