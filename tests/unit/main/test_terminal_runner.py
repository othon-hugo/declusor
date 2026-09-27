from declusor import core, testing
from declusor.main.terminal import run_terminal_app


def test_run_terminal_app_with_injected_application(dummy_app: testing.DummyApplication) -> None:
    """run_terminal_app dispatches execution to injected Application and returns 0."""

    cfg = testing.create_dummy_options()
    exit_code = run_terminal_app(cfg, application=dummy_app)

    assert exit_code == 0
    assert dummy_app.run_calls == [cfg]


def test_run_terminal_app_uses_provided_plugin_manager(dummy_app: testing.DummyApplication) -> None:
    """run_terminal_app passes plugin_manager when provided."""

    manager = core.PluginManager()
    cfg = testing.create_dummy_options()

    exit_code = run_terminal_app(cfg, plugin_manager=manager, application=dummy_app)

    assert exit_code == 0
    assert dummy_app.run_calls == [cfg]
