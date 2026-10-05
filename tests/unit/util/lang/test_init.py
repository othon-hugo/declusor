"""Tests for the public exports of declusor.util.lang."""

from declusor.util import lang


class TestLangExports:
    """Verify the canonical public language utility API."""

    def test_lang_exports__canonical_symbols__are_accessible(self) -> None:
        """Every declared public language utility symbol is exported and accessible."""

        expected = ["python"]

        assert sorted(lang.__all__) == expected
        for symbol in expected:
            assert hasattr(lang, symbol), f"declusor.util.lang is missing export: {symbol}"
            assert not symbol.startswith("_")
