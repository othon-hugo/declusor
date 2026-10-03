"""Unit tests for ControllerRequest presentation component in declusor.presentation.request."""

import dataclasses

import pytest

from declusor import config, contract, presentation


class SampleArguments(contract.ControllerArguments):
    """Sample typed argument schema for testing."""

    cmd: str
    count: int


class NetworkArguments(contract.ControllerArguments, total=False):
    """Typed argument schema with host and port."""

    host: str
    port: int
    timeout: int | None


class OptionalArguments(contract.ControllerArguments, total=False):
    """Sample typed argument schema with optional fields."""

    target: str | None
    limit: int | None


class TestControllerRequestInitialization:
    """Tests verifying ControllerRequest initialization, immutability, and contract conformance."""

    def test_controller_request_contract_conformance__implements_icontroller_request(self) -> None:
        """ControllerRequest satisfies the IControllerRequest generic contract interface."""

        req = presentation.ControllerRequest[contract.ControllerArguments]()

        assert isinstance(req, contract.IControllerRequest)

    def test_controller_request_default_initialization__defaults_request_line_to_empty_string(self) -> None:
        """ControllerRequest initializes request_line to an empty string when unspecified."""

        req = presentation.ControllerRequest[contract.ControllerArguments]()

        assert req.request_line == ""

    def test_controller_request_explicit_initialization__stores_provided_request_line(self) -> None:
        """ControllerRequest preserves the exact raw request_line provided at construction."""

        req = presentation.ControllerRequest[contract.ControllerArguments]("run --target localhost:8080")

        assert req.request_line == "run --target localhost:8080"

    def test_controller_request_immutability__modifying_request_line_raises_frozen_instance_error(self) -> None:
        """ControllerRequest is a frozen dataclass and forbids field mutation after construction."""

        req = presentation.ControllerRequest[contract.ControllerArguments]("initial")

        with pytest.raises(dataclasses.FrozenInstanceError):
            req.request_line = "modified"  # type: ignore[misc]

    def test_controller_request_equality__instances_with_same_request_line_are_equal(self) -> None:
        """Two ControllerRequest instances with identical request lines compare equal."""

        req1 = presentation.ControllerRequest[contract.ControllerArguments]("execute --force")
        req2 = presentation.ControllerRequest[contract.ControllerArguments]("execute --force")
        req3 = presentation.ControllerRequest[contract.ControllerArguments]("execute --dry-run")

        assert req1 == req2
        assert req1 != req3

    def test_controller_request_repr__contains_class_name_and_request_line(self) -> None:
        """ControllerRequest string representation includes class name and request_line content."""

        req = presentation.ControllerRequest[contract.ControllerArguments]("status")

        assert repr(req) == "ControllerRequest(request_line='status')"


class TestControllerRequestArgumentParsing:
    """Tests verifying ControllerRequest argument parsing, type conversion, and error handling."""

    def test_controller_request_parse_arguments__typed_positionals_and_scalars(self) -> None:
        """parse_arguments resolves typed positionals and converts types according to schema."""

        req = presentation.ControllerRequest[SampleArguments]("echo 42")
        definitions: contract.ArgumentDefinitions = {"cmd": str, "count": int}

        parsed, unknown = req.parse_arguments(definitions=definitions)

        assert parsed["cmd"] == "echo"
        assert parsed["count"] == 42
        assert unknown == []

    def test_controller_request_parse_arguments__positionals_with_optional_int(self) -> None:
        """parse_arguments parses string and int positionals alongside optional trailing int."""

        req = presentation.ControllerRequest[NetworkArguments]("localhost 8080 30")
        definitions: contract.ArgumentDefinitions = {
            "host": str,
            "port": int,
            "timeout": int | None,
        }

        parsed, unknown = req.parse_arguments(definitions=definitions)

        assert parsed["host"] == "localhost"
        assert parsed["port"] == 8080
        assert parsed["timeout"] == 30
        assert unknown == []

    def test_controller_request_parse_arguments_unsupported_type__raises_invalid_operation(self) -> None:
        """parse_arguments raises InvalidOperation when schema contains an unsupported type."""

        req = presentation.ControllerRequest[contract.ControllerArguments]("val 1.5")
        definitions: contract.ArgumentDefinitions = {"val": str, "rate": float}

        with pytest.raises(config.InvalidOperation, match="Argument type <class 'float'> for 'rate' is not supported"):
            req.parse_arguments(definitions=definitions)

    def test_controller_request_parse_arguments_with_optional_fields__resolves_none_when_omitted(self) -> None:
        """parse_arguments populates None for omitted optional fields in total=False schema."""

        req = presentation.ControllerRequest[OptionalArguments]("")
        definitions: contract.ArgumentDefinitions = {
            "target": str | None,
            "limit": int | None,
        }

        parsed, unknown = req.parse_arguments(definitions=definitions)

        assert parsed.get("target") is None
        assert parsed.get("limit") is None
        assert unknown == []

    def test_controller_request_parse_arguments_empty_line_with_required_arguments__raises_parser_error(self) -> None:
        """parse_arguments raises ParserError when required arguments are absent in empty request."""

        req = presentation.ControllerRequest[SampleArguments]("")
        definitions: contract.ArgumentDefinitions = {"cmd": str, "count": int}

        with pytest.raises(config.ParserError, match="the following arguments are required"):
            req.parse_arguments(definitions=definitions)

    def test_controller_request_parse_arguments_type_conversion_failure__raises_parser_error(self) -> None:
        """parse_arguments raises ParserError when token cannot be converted to target schema type."""

        req = presentation.ControllerRequest[SampleArguments]("echo not_a_number")
        definitions: contract.ArgumentDefinitions = {"cmd": str, "count": int}

        with pytest.raises(config.ParserError, match="invalid int value"):
            req.parse_arguments(definitions=definitions)

    def test_controller_request_parse_arguments_unrecognized_tokens_default_rejected__raises_parser_error(self) -> None:
        """parse_arguments raises ParserError on unrecognized tokens when allow_unknown is False."""

        req = presentation.ControllerRequest[SampleArguments]("echo 5 unexpected_extra")
        definitions: contract.ArgumentDefinitions = {"cmd": str, "count": int}

        with pytest.raises(config.ParserError, match="unrecognized arguments"):
            req.parse_arguments(definitions=definitions, allow_unknown=False)

    def test_controller_request_parse_arguments_unrecognized_tokens_allowed__returns_unknown_list(self) -> None:
        """parse_arguments returns remaining tokens in unknown list when allow_unknown is True."""

        req = presentation.ControllerRequest[SampleArguments]("echo 5 extra1 extra2")
        definitions: contract.ArgumentDefinitions = {"cmd": str, "count": int}

        parsed, unknown = req.parse_arguments(definitions=definitions, allow_unknown=True)

        assert parsed["cmd"] == "echo"
        assert parsed["count"] == 5
        assert unknown == ["extra1", "extra2"]

    def test_controller_request_parse_arguments_empty_definitions_and_empty_line__returns_empty_dict(self) -> None:
        """parse_arguments returns empty dictionary and unknown list when definitions and line are empty."""

        req = presentation.ControllerRequest[contract.ControllerArguments]("")
        definitions: contract.ArgumentDefinitions = {}

        parsed, unknown = req.parse_arguments(definitions=definitions)

        assert parsed == {}
        assert unknown == []

    def test_controller_request_parse_arguments_empty_definitions_with_tokens_allowed__returns_unknown_list(self) -> None:
        """parse_arguments with empty definitions and allow_unknown=True returns all tokens in unknown list."""

        req = presentation.ControllerRequest[contract.ControllerArguments]("first second third")
        definitions: contract.ArgumentDefinitions = {}

        parsed, unknown = req.parse_arguments(definitions=definitions, allow_unknown=True)

        assert parsed == {}
        assert unknown == ["first", "second", "third"]

    def test_controller_request_parse_arguments_empty_definitions_with_tokens_rejected__raises_parser_error(self) -> None:
        """parse_arguments with empty definitions and allow_unknown=False raises ParserError on tokens."""

        req = presentation.ControllerRequest[contract.ControllerArguments]("unexpected_token")
        definitions: contract.ArgumentDefinitions = {}

        with pytest.raises(config.ParserError, match="unrecognized arguments"):
            req.parse_arguments(definitions=definitions, allow_unknown=False)

    def test_controller_request_parse_arguments_unclosed_quotes__raises_controller_error(self) -> None:
        """parse_arguments raises ControllerError when shlex encounters an unclosed quotation mark."""

        req = presentation.ControllerRequest[SampleArguments]('run "unclosed parameter')
        definitions: contract.ArgumentDefinitions = {"cmd": str, "count": int}

        with pytest.raises(config.ControllerError, match="Parsing error"):
            req.parse_arguments(definitions=definitions)

    def test_controller_request_parse_arguments_quoted_arguments__preserves_quoted_string_spaces(self) -> None:
        """parse_arguments preserves internal spaces inside quoted string tokens."""

        class QuotedArguments(contract.ControllerArguments):
            cmd: str
            message: str

        req = presentation.ControllerRequest[QuotedArguments]('broadcast "hello operational world"')
        definitions: contract.ArgumentDefinitions = {"cmd": str, "message": str}

        parsed, unknown = req.parse_arguments(definitions=definitions)

        assert parsed["cmd"] == "broadcast"
        assert parsed["message"] == "hello operational world"
        assert unknown == []
