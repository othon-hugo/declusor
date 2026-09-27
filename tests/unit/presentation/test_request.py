from typing import TypedDict

import pytest

from declusor import config, contract, presentation


class SampleArguments(contract.ControllerArguments):
    """Sample typed arguments for testing."""

    cmd: str
    count: int


class OptionalArguments(contract.ControllerArguments, total=False):
    """Sample typed arguments with optional fields."""

    target: str | None


def test_controller_request_default_initialization() -> None:
    """ControllerRequest defaults request_line to empty string."""

    req = presentation.ControllerRequest[contract.ControllerArguments]()

    assert req.request_line == ""
    assert isinstance(req, contract.IControllerRequest)


def test_controller_request_explicit_initialization() -> None:
    """ControllerRequest preserves raw request_line passed at construction."""

    req = presentation.ControllerRequest[contract.ControllerArguments]("run --target localhost")

    assert req.request_line == "run --target localhost"


def test_controller_request_parse_arguments_typed() -> None:
    """ControllerRequest parses typed arguments matching schema."""

    req = presentation.ControllerRequest[SampleArguments]("echo 5")
    parsed, unknown = req.parse_arguments({"cmd": str, "count": int})

    assert parsed["cmd"] == "echo"
    assert parsed["count"] == 5
    assert unknown == []


def test_controller_request_parse_arguments_optional() -> None:
    """ControllerRequest parses optional arguments schema."""

    req = presentation.ControllerRequest[OptionalArguments]("")
    parsed, unknown = req.parse_arguments({"target": str | None})

    assert parsed.get("target") is None
    assert unknown == []


def test_controller_request_parse_unknown_rejected_by_default() -> None:
    """ControllerRequest raises ParserError when unexpected arguments are passed."""

    req = presentation.ControllerRequest[SampleArguments]("echo 5 extra_arg")

    with pytest.raises(config.ParserError, match="unrecognized arguments"):
        req.parse_arguments({"cmd": str, "count": int}, allow_unknown=False)


def test_controller_request_parse_unknown_allowed() -> None:
    """ControllerRequest returns unknown tokens when allow_unknown=True."""

    req = presentation.ControllerRequest[SampleArguments]("echo 5 extra1 extra2")
    parsed, unknown = req.parse_arguments({"cmd": str, "count": int}, allow_unknown=True)

    assert parsed["cmd"] == "echo"
    assert parsed["count"] == 5
    assert unknown == ["extra1", "extra2"]
