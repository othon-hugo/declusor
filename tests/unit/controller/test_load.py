"""Unit tests for LoadArguments and call_load in declusor.controller.load."""

from typing import cast, is_typeddict

import pytest

from declusor import config, contract, testing
from declusor.controller import load as load_module


class TestLoadArguments:
    """Tests verifying LoadArguments TypedDict invariants and contract compliance."""

    def test_load_arguments__is_typeddict(self) -> None:
        """LoadArguments is a valid TypedDict type."""

        assert is_typeddict(load_module.LoadArguments)

    def test_load_arguments__declares_module_field(self) -> None:
        """LoadArguments specifies the module attribute as a string."""

        assert "module" in load_module.LoadArguments.__annotations__
        assert load_module.LoadArguments.__annotations__["module"] is str


class TestLoadController:
    """Tests verifying call_load module discovery, payload rendering, and execution."""

    def test_call_load__valid_module_in_store__loads_and_transmits_payload(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_file_store: testing.DummyPluginFileStore,
        dummy_profile: testing.DummyConnectionProfile,
        dummy_view: testing.DummyView,
    ) -> None:
        """call_load loads module from plugin store, transmits rendered payload, and returns CONTINUE."""

        dummy_file_store.set_module("discovery/sysinfo", b"sysinfo_bytes")
        dummy_profile.set_rendered_command(config.OperationCode.LOAD_MODULE, "rendered_sysinfo_load")
        req = testing.create_dummy_controller_request("discovery/sysinfo", load_module.LoadArguments)

        result = load_module.call_load(test_session, req)

        assert isinstance(result, contract.ControllerResult)
        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_file_store.load_module_calls == ["discovery/sysinfo"]
        assert dummy_connection.written == [b"rendered_sysinfo_load"]
        assert dummy_view.binary_data == [b"chunk1\n", b"chunk2\n"]

    def test_call_load__module_name_with_surrounding_whitespace__normalizes_and_loads(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_file_store: testing.DummyPluginFileStore,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """call_load normalizes whitespace in module identifiers before lookup."""

        dummy_file_store.set_module("network/portscan", b"portscan_payload")
        dummy_profile.set_rendered_command(config.OperationCode.LOAD_MODULE, "rendered_portscan")
        req = testing.create_dummy_controller_request("  network/portscan  ", load_module.LoadArguments)

        result = load_module.call_load(test_session, req)

        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_file_store.load_module_calls == ["network/portscan"]
        assert dummy_connection.written == [b"rendered_portscan"]

    def test_call_load__empty_request_line__raises_parser_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """call_load raises ParserError when module name argument is missing."""

        req = testing.create_dummy_controller_request("", load_module.LoadArguments)

        with pytest.raises(config.ParserError):
            load_module.call_load(test_session, req)

    def test_call_load__whitespace_only_request_line__raises_parser_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """call_load raises ParserError when request line consists solely of whitespace."""

        req = testing.create_dummy_controller_request("   \t  \n  ", load_module.LoadArguments)

        with pytest.raises(config.ParserError):
            load_module.call_load(test_session, req)

    def test_call_load__quoted_empty_module__raises_command_validation_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """call_load propagates CommandValidationError when parsed module name is empty."""

        req = testing.create_dummy_controller_request('""', load_module.LoadArguments)

        with pytest.raises(config.CommandValidationError) as exc_info:
            load_module.call_load(test_session, req)

        assert exc_info.value.field == "module_name"
        assert exc_info.value.value == ""
        assert isinstance(exc_info.value, config.InvalidOperation)

    def test_call_load__missing_module_in_store__raises_invalid_operation(
        self,
        test_session: contract.SessionContext,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """call_load raises InvalidOperation when module cannot be located in the file store."""

        dummy_file_store.load_module_error = config.InvalidOperation("Module missing from repository")
        req = testing.create_dummy_controller_request("missing/module", load_module.LoadArguments)

        with pytest.raises(config.InvalidOperation, match="Module missing from repository"):
            load_module.call_load(test_session, req)

    def test_call_load__unconfigured_file_store__raises_command_error(
        self,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """call_load raises CommandError when the session has no configured plugin file store."""

        session_without_store = contract.SessionContext(
            connection=dummy_connection,
            view=dummy_view,
            input_source=dummy_input_source,
            plugin_processor=cast(contract.IPluginProcessor, None),
        )
        req = testing.create_dummy_controller_request("discovery/sysinfo", load_module.LoadArguments)

        with pytest.raises(config.CommandError, match="Client file store is not configured"):
            load_module.call_load(session_without_store, req)

    def test_call_load__unrendered_operation_payload__raises_invalid_operation(
        self,
        test_session: contract.SessionContext,
        dummy_file_store: testing.DummyPluginFileStore,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """call_load raises InvalidOperation when client profile fails to render module script data."""

        dummy_file_store.set_module("discovery/sysinfo", b"payload")
        dummy_profile.set_rendered_command(config.OperationCode.LOAD_MODULE, "")
        req = testing.create_dummy_controller_request("discovery/sysinfo", load_module.LoadArguments)

        with pytest.raises(config.InvalidOperation, match="Failed to generate script data"):
            load_module.call_load(test_session, req)

    def test_call_load__connection_write_failure__propagates_exception(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_file_store: testing.DummyPluginFileStore,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """call_load propagates connection write errors without swallowing them."""

        dummy_file_store.set_module("discovery/sysinfo", b"payload")
        dummy_profile.set_rendered_command(config.OperationCode.LOAD_MODULE, "rendered_sysinfo")
        dummy_connection.write_error = config.ConnectionError("Transport failure")
        req = testing.create_dummy_controller_request("discovery/sysinfo", load_module.LoadArguments)

        with pytest.raises(config.ConnectionError, match="Transport failure"):
            load_module.call_load(test_session, req)
