"""Unit tests for public package exports in declusor.main.__init__."""

import declusor
from declusor import main
from declusor.main import terminal as terminal_module


class TestMainExports:
    """Tests verifying public symbols exported by declusor.main."""

    def test_main_all__contains_all_canonical_public_symbols(self) -> None:
        """The main package exports exactly the expected public symbols in __all__."""

        expected = [
            "run",
            "run_terminal_app",
        ]

        assert sorted(main.__all__) == sorted(expected)
        assert len(main.__all__) == 2

    def test_main_exports__every_symbol_in_all__is_accessible_on_module(self) -> None:
        """Every symbol declared in __all__ is an accessible attribute of the main module."""

        for name in main.__all__:
            assert hasattr(main, name), f"declusor.main is missing expected export: {name}"

    def test_main_exports__submodule_symbols__match_underlying_definitions(self) -> None:
        """Exported functions match their underlying submodule definitions."""

        import importlib

        main_mod = importlib.import_module("declusor.main.main")
        assert main.run is main_mod.run
        assert main.run_terminal_app is terminal_module.run_terminal_app

    def test_main_exports__contains_no_private_symbols(self) -> None:
        """The main __all__ export list contains no private or underscore-prefixed symbols."""

        for symbol in main.__all__:
            assert not symbol.startswith("_"), f"Unexpected private symbol in main.__all__: {symbol}"

    def test_root_package__exports_main_module_in_all(self) -> None:
        """The root declusor package declares main in its __all__ exports and attribute namespace."""

        assert "main" in declusor.__all__
        assert hasattr(declusor, "main")
        assert declusor.main is main
