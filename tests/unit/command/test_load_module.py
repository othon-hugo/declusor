"""Unit tests for LoadModuleDTO and LoadModule in declusor.command."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from declusor import config, contract, testing, util
from declusor.command.load_module import LoadModule, LoadModuleDTO


class TrackingPluginFileStore(testing.DummyPluginFileStore):
    """Plugin file store test double tracking find_module invocations."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Initialize tracking store with call history."""

        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.find_module_calls: list[str] = []

    def find_module(self, module_name: str, /) -> Path | None:
        """Record module lookup and delegate to dummy implementation."""

        self.find_module_calls.append(module_name)
        return super().find_module(module_name)


class TestLoadModuleDTO:
    """Tests verifying LoadModuleDTO parameter normalization, validation, and immutability."""

    def test_load_module_dto_init__valid_module_name__preserves_identifier(self) -> None:
        """LoadModuleDTO accepts a standard module identifier without modification."""

        module_name = "discovery/sysinfo"
        dto = LoadModuleDTO(module_name=module_name)

        assert dto.module_name == module_name

    def test_load_module_dto_init__nested_path__preserves_relative_path(self) -> None:
        """LoadModuleDTO accepts nested relative module paths."""

        module_name = "custom/module/name"
        dto = LoadModuleDTO(module_name=module_name)

        assert dto.module_name == module_name

    def test_load_module_dto_init__surrounding_whitespace__strips_whitespace(self) -> None:
        """LoadModuleDTO strips leading and trailing whitespace from module names."""

        raw_name = "  discovery/sysinfo  \t\n"
        expected_name = "discovery/sysinfo"
        dto = LoadModuleDTO(module_name=raw_name)

        assert dto.module_name == expected_name

    @pytest.mark.parametrize(
        "invalid_name",
        [
            "",
            " ",
            "\t",
            "\n",
            "\r\n",
            "   \t\n   ",
        ],
    )
    def test_load_module_dto_init__empty_or_whitespace__raises_command_validation_error(
        self,
        invalid_name: str,
    ) -> None:
        """LoadModuleDTO rejects empty or whitespace-only module names with CommandValidationError."""

        with pytest.raises(config.CommandValidationError) as exc_info:
            LoadModuleDTO(module_name=invalid_name)

        assert exc_info.value.field == "module_name"
        assert exc_info.value.value == invalid_name
        assert isinstance(exc_info.value, config.InvalidOperation)
        assert isinstance(exc_info.value, config.CommandError)
        assert "Module name cannot be empty." in str(exc_info.value)

    def test_load_module_dto_immutability__reassign_attribute__raises_frozen_instance_error(self) -> None:
        """LoadModuleDTO is frozen and raises FrozenInstanceError on attribute mutation."""

        dto = LoadModuleDTO(module_name="discovery/sysinfo")

        with pytest.raises(FrozenInstanceError):
            dto.module_name = "other/module"  # type: ignore[misc]

    def test_load_module_dto_equality__identical_normalized_names__evaluates_equal(self) -> None:
        """LoadModuleDTO instances with matching normalized names compare equal and share hash."""

        dto_first = LoadModuleDTO(module_name="discovery/sysinfo")
        dto_second = LoadModuleDTO(module_name="  discovery/sysinfo  ")

        assert dto_first == dto_second
        assert hash(dto_first) == hash(dto_second)


class TestLoadModule:
    """Tests verifying LoadModule request rendering, validation safety, and response streaming."""

    def test_load_module_send_request__missing_plugin_filestore__raises_command_error(
        self,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """LoadModule raises CommandError if SessionContext has no plugin file store configured."""

        session_without_plugin = contract.SessionContext(
            connection=dummy_connection,
            view=dummy_view,
            input_source=dummy_input_source,
            plugin_processor=None,  # type: ignore[arg-type]
        )
        dto = LoadModuleDTO(module_name="discovery/sysinfo")
        command = LoadModule(dto)

        with pytest.raises(config.CommandError, match="Client file store is not configured for this session."):
            command.send_request(session_without_plugin)

    def test_load_module_send_request__queries_plugin_filestore_with_dto_module_name(
        self,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """LoadModule queries the session file store using the exact module name from the DTO."""

        module_name = "custom/network/scanner"
        module_bytes = b"scan_network_code"
        tracking_store = TrackingPluginFileStore()
        tracking_store.set_module(module_name, module_bytes)

        session = testing.create_test_session(
            connection=dummy_connection,
            view=dummy_view,
            input_source=dummy_input_source,
            files=tracking_store,
        )
        dto = LoadModuleDTO(module_name=module_name)
        command = LoadModule(dto)

        command.send_request(session)

        assert tracking_store.find_module_calls == [module_name]

    def test_load_module_send_request__module_not_found__raises_invalid_operation(
        self,
        test_session: contract.SessionContext,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """LoadModule raises InvalidOperation when the requested module cannot be found."""

        missing_module = "nonexistent/module"
        dummy_file_store.missing_modules.add(missing_module)

        dto = LoadModuleDTO(module_name=missing_module)
        command = LoadModule(dto)

        with pytest.raises(config.InvalidOperation, match=f"Module '{missing_module}' could not be found."):
            command.send_request(test_session)

    def test_load_module_send_request__path_traversal_outside_permitted_directory__raises_invalid_operation(
        self,
        test_session: contract.SessionContext,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """LoadModule raises InvalidOperation when module path resolves outside permitted directory."""

        traversal_module = "../../etc/shadow"
        dummy_file_store.set_module(traversal_module, b"root:*:18000:0:99999:7:::")

        dto = LoadModuleDTO(module_name=traversal_module)
        command = LoadModule(dto)

        with pytest.raises(
            config.InvalidOperation,
            match=f"Module path '{traversal_module}' is outside the permitted modules directory.",
        ):
            command.send_request(test_session)

    def test_load_module_send_request__loads_module_bytes_from_filestore(
        self,
        test_session: contract.SessionContext,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """LoadModule reads module bytes through the session file store load_module method."""

        module_name = "discovery/sysinfo"
        module_bytes = b"#!/bin/sh\nuname -a\n"
        dummy_file_store.set_module(module_name, module_bytes)

        dto = LoadModuleDTO(module_name=module_name)
        command = LoadModule(dto)

        command.send_request(test_session)

        assert dummy_file_store.load_module_calls == [module_name]

    def test_load_module_send_request__encodes_module_bytes_to_base64_and_invokes_renderer(
        self,
        test_session: contract.SessionContext,
        dummy_file_store: testing.DummyPluginFileStore,
        dummy_renderer: testing.DummyOperationRenderer,
    ) -> None:
        """LoadModule encodes payload to base64 and invokes renderer with LOAD_MODULE opcode."""

        module_name = "discovery/sysinfo"
        module_bytes = b"import sys; print(sys.platform)"
        expected_base64 = util.convert_to_base64(module_bytes)

        dummy_file_store.set_module(module_name, module_bytes)
        dto = LoadModuleDTO(module_name=module_name)
        command = LoadModule(dto)

        command.send_request(test_session)

        assert dummy_renderer.render_calls == [(config.OperationCode.LOAD_MODULE, (expected_base64,))]

    def test_load_module_send_request__renderer_returns_none__raises_invalid_operation(
        self,
        test_session: contract.SessionContext,
        dummy_file_store: testing.DummyPluginFileStore,
        dummy_renderer: testing.DummyOperationRenderer,
    ) -> None:
        """LoadModule raises InvalidOperation when the profile renderer returns None."""

        module_name = "discovery/sysinfo"
        dummy_file_store.set_module(module_name, b"sample_bytes")
        dummy_renderer.set_rendered_command(config.OperationCode.LOAD_MODULE, None)

        dto = LoadModuleDTO(module_name=module_name)
        command = LoadModule(dto)

        with pytest.raises(config.InvalidOperation, match="Failed to generate script data for module loading."):
            command.send_request(test_session)

    def test_load_module_send_request__renderer_returns_empty_string__raises_invalid_operation(
        self,
        test_session: contract.SessionContext,
        dummy_file_store: testing.DummyPluginFileStore,
        dummy_renderer: testing.DummyOperationRenderer,
    ) -> None:
        """LoadModule raises InvalidOperation when the profile renderer returns an empty string."""

        module_name = "discovery/sysinfo"
        dummy_file_store.set_module(module_name, b"sample_bytes")
        dummy_renderer.set_rendered_command(config.OperationCode.LOAD_MODULE, "")

        dto = LoadModuleDTO(module_name=module_name)
        command = LoadModule(dto)

        with pytest.raises(config.InvalidOperation, match="Failed to generate script data for module loading."):
            command.send_request(test_session)

    def test_load_module_send_request__successful_render__transmits_utf8_payload_to_connection(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_file_store: testing.DummyPluginFileStore,
        dummy_renderer: testing.DummyOperationRenderer,
    ) -> None:
        """LoadModule encodes rendered script data into UTF-8 bytes and writes to connection."""

        module_name = "discovery/sysinfo"
        rendered_script = "load_module_payload_data_v1"
        dummy_file_store.set_module(module_name, b"module_raw_bytes")
        dummy_renderer.set_rendered_command(config.OperationCode.LOAD_MODULE, rendered_script)

        dto = LoadModuleDTO(module_name=module_name)
        command = LoadModule(dto)

        command.send_request(test_session)

        assert dummy_connection.written == [rendered_script.encode("utf-8")]

    def test_load_module_read_response__stream_chunks__forwards_all_chunks_to_view(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
    ) -> None:
        """LoadModule reads all response chunks from connection and writes them to the view."""

        response_chunks = [b"module loaded: ok\n", b"ready for execution\n"]
        dummy_connection.incoming_chunks = response_chunks

        dto = LoadModuleDTO(module_name="discovery/sysinfo")
        command = LoadModule(dto)

        command.read_response(test_session)

        assert dummy_view.binary_data == response_chunks

    def test_load_module_lifecycle__via_session_execute__transmits_and_streams_response(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
        dummy_file_store: testing.DummyPluginFileStore,
        dummy_renderer: testing.DummyOperationRenderer,
    ) -> None:
        """Executing LoadModule via SessionContext coordinates both request transmission and response streaming."""

        module_name = "discovery/sysinfo"
        rendered_script = "load_module_lifecycle_rendered"
        response_chunks = [b"[+] module loaded\n", b"[+] status: active\n"]

        dummy_file_store.set_module(module_name, b"sample_payload")
        dummy_renderer.set_rendered_command(config.OperationCode.LOAD_MODULE, rendered_script)
        dummy_connection.incoming_chunks = response_chunks

        dto = LoadModuleDTO(module_name=module_name)
        command = LoadModule(dto)

        test_session.execute(command)

        assert dummy_file_store.load_module_calls == [module_name]
        assert dummy_renderer.render_calls[0][0] == config.OperationCode.LOAD_MODULE
        assert dummy_connection.written == [rendered_script.encode("utf-8")]
        assert dummy_view.binary_data == response_chunks
