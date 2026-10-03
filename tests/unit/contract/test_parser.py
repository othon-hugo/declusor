"""Unit tests for argument parser contracts and type definitions."""

import argparse
from typing import Any

from declusor import contract


class TestParsedArguments:
    """Tests for ParsedArguments TypedDict base class."""

    def test_parsed_arguments__typed_dict_subclass__allows_typed_mapping_access(self) -> None:
        """Verify ParsedArguments subclass permits static and runtime dictionary access."""

        class _PluginOptions(contract.ParsedArguments):
            host: str
            port: int
            debug: bool

        options: _PluginOptions = {
            "host": "127.0.0.1",
            "port": 8080,
            "debug": False,
        }

        assert options["host"] == "127.0.0.1"
        assert options["port"] == 8080
        assert options["debug"] is False

    def test_parsed_arguments__empty_instance__initializes_empty_mapping(self) -> None:
        """Verify base ParsedArguments can be instantiated as an empty mapping."""

        options: contract.ParsedArguments = {}

        assert len(options) == 0
        assert dict(options) == {}


class TestIArgumentParser:
    """Tests for IArgumentParser runtime-checkable protocol."""

    def test_iargument_parser__valid_parser__isinstance_returns_true(self) -> None:
        """Verify object implementing add_argument satisfies IArgumentParser protocol."""

        class _ConcreteParser:
            """Minimal parser implementing add_argument."""

            def __init__(self) -> None:
                self.calls: list[tuple[tuple[str, ...], dict[str, Any]]] = []

            def add_argument(self, *name_or_flags: str, **kwargs: Any) -> object:
                self.calls.append((name_or_flags, kwargs))
                return None

        parser = _ConcreteParser()

        assert isinstance(parser, contract.IArgumentParser)

        parser.add_argument("-p", "--port", type=int, default=9000)
        assert len(parser.calls) == 1
        assert parser.calls[0] == (("-p", "--port"), {"type": int, "default": 9000})

    def test_iargument_parser__argparse_instance__isinstance_returns_true(self) -> None:
        """Verify standard library ArgumentParser satisfies IArgumentParser protocol."""

        parser = argparse.ArgumentParser()

        assert isinstance(parser, contract.IArgumentParser)

    def test_iargument_parser__missing_add_argument__isinstance_returns_false(self) -> None:
        """Verify object missing add_argument method fails IArgumentParser protocol check."""

        class _InvalidParser:
            """Object missing add_argument."""

        assert not isinstance(_InvalidParser(), contract.IArgumentParser)
        assert not isinstance(object(), contract.IArgumentParser)

    def test_iargument_parser__runtime_checkable__protocol_is_runtime_checkable(self) -> None:
        """Verify IArgumentParser is decorated with runtime_checkable."""

        assert getattr(contract.IArgumentParser, "_is_runtime_protocol", False) is True
