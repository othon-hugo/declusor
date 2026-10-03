"""Unit tests for public package exports in declusor.presentation.__init__."""

from declusor import config, presentation
from declusor.presentation.input_source import TerminalInputSource
from declusor.presentation.prompt import PromptLoop
from declusor.presentation.request import ControllerRequest
from declusor.presentation.view import TerminalView


class TestPresentationExports:
    """Tests verifying public symbols exported by declusor.presentation."""

    def test_presentation_all__contains_all_five_public_symbols(self) -> None:
        """The presentation package exports exactly the five canonical public symbols."""

        expected = [
            "ControllerRequest",
            "PromptError",
            "PromptLoop",
            "TerminalInputSource",
            "TerminalView",
        ]

        assert sorted(presentation.__all__) == sorted(expected)
        assert len(presentation.__all__) == 5

    def test_presentation_exports__every_symbol_in_all__is_accessible_on_module(self) -> None:
        """Every symbol declared in __all__ is an accessible attribute of the presentation module."""

        for name in presentation.__all__:
            assert hasattr(presentation, name), f"declusor.presentation is missing expected export: {name}"

    def test_presentation_exports__exception_reexports__match_config_exceptions(self) -> None:
        """Exception symbols re-exported from presentation are identical to config definitions."""

        assert presentation.PromptError is config.PromptError

    def test_presentation_exports__component_classes__match_submodule_classes(self) -> None:
        """Presentation classes exported from presentation match their submodule definitions."""

        assert presentation.ControllerRequest is ControllerRequest
        assert presentation.PromptLoop is PromptLoop
        assert presentation.TerminalInputSource is TerminalInputSource
        assert presentation.TerminalView is TerminalView
