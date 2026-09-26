from declusor import core, main, presentation


def test_create_application_initializes_plugins() -> None:
    """Verify create_application loads built-in plugins into manager."""

    app = main.create_application()
    assert isinstance(app, main.Application)
    assert isinstance(app, main.TerminalApplication)
    assert app.manager is not None
    assert "shell_socket" in app.manager.names()
    assert "py_socket" in app.manager.names()
    assert isinstance(app.runner, presentation.PromptLoop)


def test_create_terminal_application_initializes_plugins() -> None:
    """Verify create_terminal_application loads built-in plugins into manager."""

    app = main.create_terminal_application()
    assert isinstance(app, main.TerminalApplication)
    assert app.manager is not None
    assert "shell_socket" in app.manager.names()
    assert "py_socket" in app.manager.names()


def test_terminal_application_default_runner() -> None:
    """Verify TerminalApplication initializes with a PromptLoop runner."""

    manager = core.PluginManager()
    router = core.Router()
    view = presentation.TerminalView()
    input_source = presentation.TerminalInputSource()

    app = main.TerminalApplication(manager, router, view, input_source)
    assert isinstance(app.runner, presentation.PromptLoop)
