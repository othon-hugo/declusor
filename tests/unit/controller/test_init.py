"""Unit tests for public package exports in declusor.controller.__init__."""

from declusor import config, controller
from declusor.controller import (
    command,
    eval,
    execute,
    load,
    shell,
    upload,
)
from declusor.controller import (
    exit as exit_module,
)
from declusor.controller import (
    help as help_module,
)


class TestControllerExports:
    """Tests verifying public symbols exported by declusor.controller."""

    def test_controller_all__contains_all_seventeen_public_symbols(self) -> None:
        """The controller package exports exactly the seventeen canonical public symbols."""

        expected = [
            "CommandArguments",
            "ControllerError",
            "EvalArguments",
            "ExecuteArguments",
            "ExitArguments",
            "HelpArguments",
            "LoadArguments",
            "ShellArguments",
            "UploadArguments",
            "call_command",
            "call_eval",
            "call_execute",
            "call_exit",
            "call_load",
            "call_shell",
            "call_upload",
            "create_help_controller",
        ]

        assert sorted(controller.__all__) == sorted(expected)
        assert len(controller.__all__) == 17

    def test_controller_exports__every_symbol_in_all__is_accessible_on_module(self) -> None:
        """Every symbol declared in __all__ is an accessible attribute of the controller module."""

        for name in controller.__all__:
            assert hasattr(controller, name), f"declusor.controller is missing expected export: {name}"

    def test_controller_exports__exception_reexports__match_config_exceptions(self) -> None:
        """Exception symbols re-exported from controller are identical to config definitions."""

        assert controller.ControllerError is config.ControllerError

    def test_controller_exports__submodule_functions__match_underlying_callables(self) -> None:
        """Controller functions match their respective submodule definitions."""

        assert controller.call_eval is eval.call_eval
        assert controller.call_command is command.call_command
        assert controller.call_execute is execute.call_execute
        assert controller.call_exit is exit_module.call_exit
        assert controller.call_load is load.call_load
        assert controller.call_shell is shell.call_shell
        assert controller.call_upload is upload.call_upload
        assert controller.create_help_controller is help_module.create_help_controller

    def test_controller_exports__argument_types__match_underlying_types(self) -> None:
        """Controller argument TypedDicts match their respective submodule definitions."""

        assert controller.EvalArguments is eval.EvalArguments
        assert controller.CommandArguments is command.CommandArguments
        assert controller.ExecuteArguments is execute.ExecuteArguments
        assert controller.ExitArguments is exit_module.ExitArguments
        assert controller.HelpArguments is help_module.HelpArguments
        assert controller.LoadArguments is load.LoadArguments
        assert controller.ShellArguments is shell.ShellArguments
        assert controller.UploadArguments is upload.UploadArguments
