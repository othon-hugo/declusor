"""Unit tests for public package exports in declusor.app.__init__."""

from declusor import app
from declusor.app import terminal


class TestAppExports:
    """Tests verifying public symbols exported by declusor.app."""

    def test_app_all__contains_all_canonical_public_symbols(self) -> None:
        """The app package exports exactly the expected public symbols in __all__."""

        expected = [
            "TerminalApplication",
            "create_terminal_application",
        ]

        assert sorted(app.__all__) == sorted(expected)
        assert len(app.__all__) == 2

    def test_app_exports__every_symbol_in_all__is_accessible_on_module(self) -> None:
        """Every symbol declared in __all__ is an accessible attribute of the app module."""

        for name in app.__all__:
            assert hasattr(app, name), f"declusor.app is missing expected export: {name}"

    def test_app_exports__submodule_symbols__match_terminal_module(self) -> None:
        """Component classes and factories match their underlying submodule definitions."""

        assert app.TerminalApplication is terminal.TerminalApplication
        assert app.create_terminal_application is terminal.create_terminal_application

    def test_app_exports__contains_no_private_symbols(self) -> None:
        """The app __all__ export list contains no private or underscore-prefixed symbols."""

        for symbol in app.__all__:
            assert not symbol.startswith("_"), f"Unexpected private symbol in app.__all__: {symbol}"
