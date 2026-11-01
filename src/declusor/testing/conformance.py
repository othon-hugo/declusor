"""Reusable conformance test suite verifying plugin contract implementations."""

import dataclasses
import inspect
import threading
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from declusor import command, config, contract, controller, util
from declusor.testing import doubles


def assert_conforms_to_client_plugin[T: contract.ParsedArguments](
    plugin_cls: type[contract.IPluginExtension[T]],
    *,
    sample_options: Mapping[str, object] | None = None,
    tmp_path: Path | None = None,
) -> None:
    """Verify that a class satisfies the structural and behavioral invariants of IPluginExtension.

    Args:
        plugin_cls: The plugin class to test.
        sample_options: Optional custom CLI option mapping.
        tmp_path: Optional temporary directory for asset file validation.
    """

    assert inspect.isclass(plugin_cls), f"{plugin_cls!r} must be a class."
    assert issubclass(plugin_cls, contract.IPluginExtension), f"{plugin_cls!r} must subclass contract.IPluginExtension."

    plugin_cls.reset()

    # Invariant 1: Metadata presence
    assert isinstance(plugin_cls.name, str) and plugin_cls.name.strip(), "plugin.name must be a non-empty string."
    assert isinstance(plugin_cls.description, str), "plugin.description must be a string."
    assert isinstance(plugin_cls.version, str), "plugin.version must be a string."
    assert plugin_cls.options_type is not None, "plugin.options_type must be defined."
    assert isinstance(plugin_cls.routes, Mapping), "plugin.routes must be a mapping."
    assert isinstance(plugin_cls.supported_launcher_kinds, frozenset), "plugin.supported_launcher_kinds must be a frozenset."
    assert len(plugin_cls.supported_launcher_kinds) > 0, "plugin.supported_launcher_kinds cannot be empty."
    for kind in plugin_cls.supported_launcher_kinds:
        assert isinstance(kind, config.LauncherKind), f"Invalid launcher kind in supported_launcher_kinds: {kind!r}."

    assert isinstance(plugin_cls.supported_transport_layers, frozenset), "plugin.supported_transport_layers must be a frozenset."
    for layer in plugin_cls.supported_transport_layers:
        assert isinstance(layer, (config.TransportLayer, str)), f"Invalid transport layer in supported_transport_layers: {layer!r}."

    normalized_routes: set[str] = set()
    for route, registration in plugin_cls.routes.items():
        assert isinstance(route, str) and route.strip(), "plugin.routes must use non-empty string names."
        normalized_route = route.strip()
        assert normalized_route not in {"help", "exit"}, f"plugin.routes cannot override protected route {normalized_route!r}."
        assert normalized_route not in normalized_routes, f"plugin.routes contains duplicate normalized route {normalized_route!r}."
        assert isinstance(registration, contract.RouteRegistration), f"plugin.routes[{normalized_route!r}] must be RouteRegistration."
        normalized_routes.add(normalized_route)

    # Invariant 2: Parser configuration
    parser = util.Parser(prog="test")
    plugin_cls.configure_parser(parser)

    # Invariant 3: Config construction via extract_options and build_config
    options = plugin_cls.extract_options(sample_options or {})

    if tmp_path is not None:
        filesystem = contract.PluginFilesystem.from_root(tmp_path)
        filesystem.launchers.mkdir(parents=True, exist_ok=True)
        filesystem.helpers.mkdir(parents=True, exist_ok=True)
        filesystem.modules.mkdir(parents=True, exist_ok=True)
        for ext in (".py", ".sh", ".bash", ".ps1", ".bat", ""):
            (filesystem.launchers / f"{plugin_cls.name}_client{ext}").write_text("# client")
            (filesystem.launchers / f"{plugin_cls.name}_stager{ext}").write_text("# stager")
            (filesystem.launchers / f"{plugin_cls.name}{ext}").write_text("# client")
        plugin_config = plugin_cls.build_config("127.0.0.1", 9000, options, filesystem=filesystem)
    else:
        plugin_config = plugin_cls.build_config("127.0.0.1", 9000, options)

    assert isinstance(plugin_config, contract.PluginConfig), f"build_config must return PluginConfig, got {type(plugin_config)}."
    assert plugin_config.kind == plugin_cls.name, f"plugin_config.kind ({plugin_config.kind}) must match plugin.name ({plugin_cls.name})."
    assert plugin_config.host == "127.0.0.1"
    assert plugin_config.port == 9000
    assert plugin_config.options_type == plugin_cls.options_type

    # Invariant 4: Validation
    plugin_cls.validate(plugin_config)

    # Invariant 5: Runtime creation
    for kind in plugin_cls.supported_launcher_kinds:
        kind_config = dataclasses.replace(plugin_config, launcher_kind=kind)
        plugin_cls.validate(kind_config)
        kind_runtime = plugin_cls.build_runtime(kind_config)

        assert isinstance(kind_runtime, contract.IPluginRuntime), f"build_runtime must return IPluginRuntime, got {type(kind_runtime)}."
        assert isinstance(kind_runtime.launcher, contract.LauncherDelivery), "runtime.launcher must return a LauncherDelivery instance."
        assert kind_runtime.launcher.kind == kind, f"runtime.launcher.kind ({kind_runtime.launcher.kind}) must match requested kind ({kind})."

    runtime = plugin_cls.build_runtime(plugin_config)
    assert isinstance(runtime, contract.IPluginRuntime), f"build_runtime must return IPluginRuntime, got {type(runtime)}."
    assert isinstance(runtime.launcher, contract.LauncherDelivery), "runtime.launcher must return a LauncherDelivery instance."
    assert isinstance(runtime.processor, contract.IPluginProcessor), "runtime.processor must implement IPluginProcessor."
    all_helpers = runtime.processor.load_all_helpers()
    assert isinstance(all_helpers, Mapping), "runtime.processor.load_all_helpers() must return a Mapping."

    # Invariant 6: Connection instantiation and behavioral lifecycle
    dummy_transport = doubles.DummyTransport()
    connection = runtime.create_connection(dummy_transport)
    assert isinstance(connection, contract.IConnection), f"create_connection must return IConnection, got {type(connection)}."
    initial_state = connection.state
    assert initial_state in (contract.ConnectionState.CREATED, contract.ConnectionState.CONNECTED), (
        f"Initial state must be CREATED or CONNECTED, got {initial_state}."
    )

    if connection.state == contract.ConnectionState.CREATED:
        with pytest.raises(config.ConnectionError):
            connection.write(b"conformance_probe")
        with pytest.raises(config.ConnectionError):
            list(connection.read())
    else:
        connection.write(b"conformance_probe")
        assert len(dummy_transport.written_bytes) > 0, "Transport must record bytes after connection.write()."

    connection.close()
    assert connection.state == contract.ConnectionState.CLOSED, f"Connection state after close() must be CLOSED, got {connection.state}."
    assert dummy_transport.is_closed, "Transport must be closed after connection.close()."

    # Idempotent close
    connection.close()

    # Reject operations on closed connection
    with pytest.raises(config.ConnectionClosed):
        connection.write(b"probe_after_close")

    with pytest.raises(config.ConnectionError):
        connection.handshake()


class PluginConformanceTestSuite[T: contract.ParsedArguments]:
    """Base pytest test suite for verifying full contract conformance of a client plugin.

    Plugin authors can simply subclass this in their test suite and define the
    ``plugin_class`` fixture.

    Example::

        class TestMyPluginConformance(PluginConformanceTestSuite[MyConfig]):
            @pytest.fixture
            def plugin_class(self) -> type[contract.IPluginExtension[MyConfig]]:
                return MyPlugin
    """

    @pytest.fixture
    def plugin_class(self) -> type[contract.IPluginExtension[T]]:
        """Subclasses must override this to provide the plugin class under test."""

        raise NotImplementedError

    @pytest.fixture
    def sample_options(self) -> Mapping[str, object]:
        """Optional custom option mapping for the plugin."""

        return {}

    def test_plugin_metadata(self, plugin_class: type[contract.IPluginExtension[T]]) -> None:
        """Verify plugin defines valid name, description, and version."""

        assert isinstance(plugin_class.name, str) and plugin_class.name.strip()
        assert isinstance(plugin_class.description, str)
        assert isinstance(plugin_class.version, str)
        assert plugin_class.options_type is not None
        assert isinstance(plugin_class.routes, Mapping)
        assert isinstance(plugin_class.supported_launcher_kinds, frozenset)
        assert len(plugin_class.supported_launcher_kinds) > 0
        assert isinstance(plugin_class.supported_transport_layers, frozenset)

    def test_configure_parser_callable(self, plugin_class: type[contract.IPluginExtension[T]]) -> None:
        """Verify configure_parser accepts a Parser without error."""

        parser = util.Parser(prog="conformance")
        plugin_class.configure_parser(parser)

    def test_build_config_contract(
        self,
        plugin_class: type[contract.IPluginExtension[T]],
        sample_options: Mapping[str, object],
        tmp_path: Path,
    ) -> None:
        """Verify build_config returns an immutable PluginConfig instance matching the plugin."""

        filesystem = contract.PluginFilesystem.from_root(tmp_path)
        options = plugin_class.extract_options(sample_options)
        plugin_config = plugin_class.build_config("10.0.0.1", 4444, options, filesystem=filesystem)

        assert isinstance(plugin_config, contract.PluginConfig)
        assert plugin_config.kind == plugin_class.name
        assert plugin_config.host == "10.0.0.1"
        assert plugin_config.port == 4444

    def test_full_conformance(
        self,
        plugin_class: type[contract.IPluginExtension[T]],
        sample_options: Mapping[str, object],
        tmp_path: Path,
    ) -> None:
        """Run full contract invariant suite."""

        assert_conforms_to_client_plugin(
            plugin_class,
            sample_options=sample_options,
            tmp_path=tmp_path,
        )


class InteractiveShellTestSuite[TConnection: contract.IConnection, TProcessor: contract.IPluginProcessor](ABC):
    """Base conformance test suite verifying interactive remote shell support in client plugins.

    Client plugins supporting interactive shell operations can inherit from this suite
    to verify bidirectional terminal streaming, prompt loop integration, cooperative
    cancellation on KeyboardInterrupt, and network disconnect handling without delimiter leaks.
    """

    @pytest.fixture
    @abstractmethod
    def plugin_class(self) -> contract.PluginExtensionType:
        """Subclasses must provide the client plugin extension class under test."""

        raise NotImplementedError

    @property
    def forbidden_delimiters(self) -> Sequence[bytes]:
        """Delimiters or control tokens that must never leak into raw view output."""

        return ()

    @abstractmethod
    def create_connected_session(
        self,
        tmp_path: Path,
        transport: contract.ITransport,
        timeout: float,
    ) -> tuple[TConnection, TProcessor]:
        """Establish and return a connected connection and plugin processor over the given transport."""

        raise NotImplementedError

    @abstractmethod
    def run_mock_client_responder(
        self,
        client_transport: contract.ITransport,
        responses: Mapping[str, bytes],
        stop_event: threading.Event,
    ) -> None:
        """Run simulated client responder servicing commands until stop_event is signaled."""

        raise NotImplementedError

    @abstractmethod
    def run_mock_client_abrupt_disconnect(
        self,
        client_transport: contract.ITransport,
    ) -> None:
        """Simulate client-side abrupt network disconnect during an active shell session."""

        raise NotImplementedError

    def is_connection_idle(self, connection: TConnection) -> bool:
        """Check if connection is in an idle state ready for the next command."""

        return True

    def test_plugin_declares_canonical_shell_route(
        self,
        plugin_class: contract.PluginExtensionType,
    ) -> None:
        """Verify plugin declares a 'shell' route wired to controller.call_shell."""

        assert "shell" in plugin_class.routes, f"Plugin {plugin_class.name} must declare a 'shell' route."
        registration = plugin_class.routes["shell"]
        assert registration.controller is controller.call_shell, (
            f"Plugin {plugin_class.name} 'shell' route controller must be controller.call_shell, got {registration.controller}."
        )

    def test_launch_shell__multiple_interactive_commands__streams_outputs_without_delimiter_leak(
        self,
        tmp_path: Path,
    ) -> None:
        """Verify interactive shell executes multiple commands, streams output, and prevents delimiter leaks."""

        client_transport, server_transport = doubles.create_memory_transport_pair()
        initial_timeout = 2.0
        connection, processor = self.create_connected_session(tmp_path, server_transport, initial_timeout)

        responses: Mapping[str, bytes] = {
            "echo alpha": b"alpha_output_ok\n",
            "echo beta": b"beta_output_ok\n",
        }
        interactions = (
            ("echo alpha", b"alpha_output_ok"),
            ("echo beta", b"beta_output_ok"),
        )

        view = doubles.DummyView()
        input_source = doubles.PacedInteractiveInputSource(
            interactions,
            view,
            is_idle_predicate=lambda: self.is_connection_idle(connection),
            timeout=3.0,
        )
        session = contract.SessionContext(
            connection=connection,
            view=view,
            plugin_processor=processor,
            input_source=input_source,
        )

        banner = "=== Interactive Remote Shell ==="
        cmd = command.LaunchShell(command.LaunchShellDTO(banner=banner))

        stop_responder = threading.Event()
        responder_thread = threading.Thread(
            target=self.run_mock_client_responder,
            args=(client_transport, responses, stop_responder),
            daemon=True,
        )
        responder_thread.start()

        try:
            session.execute(cmd)

            assert any(banner in msg for msg in view.messages), f"Banner {banner!r} missing from view messages."

            accumulated_output = b"".join(view.binary_data)
            assert b"alpha_output_ok" in accumulated_output, "Output from first interactive command was not received."
            assert b"beta_output_ok" in accumulated_output, "Output from second interactive command was not received."

            for delimiter in self.forbidden_delimiters:
                assert delimiter not in accumulated_output, f"Forbidden delimiter {delimiter!r} leaked into view."

            assert not view.errors, f"Unexpected view errors occurred: {view.errors}"
            assert not cmd._task_pool.errors, f"Unexpected task pool errors: {cmd._task_pool.errors}"

            stop_responder.set()
            responder_thread.join(timeout=2.0)
            assert not responder_thread.is_alive(), "Responder thread failed to terminate."

            for thread in cmd._task_pool._threads:
                assert not thread.is_alive(), f"Task pool thread {thread.name} remained alive."

            assert connection.timeout == initial_timeout, (
                f"Connection timeout was not restored (expected {initial_timeout}, got {connection.timeout})."
            )
        finally:
            stop_responder.set()
            responder_thread.join(timeout=1.0)
            client_transport.close()
            server_transport.close()
            connection.close()

    def test_launch_shell__immediate_keyboard_interrupt_before_input__exits_cleanly_without_error(
        self,
        tmp_path: Path,
    ) -> None:
        """Verify immediate KeyboardInterrupt exits cleanly without modifying connection state."""

        client_transport, server_transport = doubles.create_memory_transport_pair()
        initial_timeout = 2.0
        connection, processor = self.create_connected_session(tmp_path, server_transport, initial_timeout)

        view = doubles.DummyView()
        input_source = doubles.DisconnectAwareInputSource(input_exception=KeyboardInterrupt())
        session = contract.SessionContext(
            connection=connection,
            view=view,
            plugin_processor=processor,
            input_source=input_source,
        )

        cmd = command.LaunchShell(command.LaunchShellDTO())

        try:
            session.execute(cmd)

            assert not view.errors, f"Unexpected view errors occurred: {view.errors}"
            assert not cmd._task_pool.errors, f"Unexpected task pool errors: {cmd._task_pool.errors}"
            assert connection.state == contract.ConnectionState.CONNECTED, f"Connection state changed unexpectedly: {connection.state}"
            assert connection.timeout == initial_timeout, (
                f"Connection timeout was not restored (expected {initial_timeout}, got {connection.timeout})."
            )
            for thread in cmd._task_pool._threads:
                assert not thread.is_alive(), f"Task pool thread {thread.name} remained alive."
        finally:
            client_transport.close()
            server_transport.close()
            connection.close()

    def test_launch_shell__client_disconnects_during_command__terminates_gracefully(
        self,
        tmp_path: Path,
    ) -> None:
        """Verify shell terminates cleanly when remote client abruptly disconnects during command execution."""

        client_transport, server_transport = doubles.create_memory_transport_pair()
        initial_timeout = 2.0
        connection, processor = self.create_connected_session(tmp_path, server_transport, initial_timeout)

        view = doubles.DummyView()
        cmd = command.LaunchShell(command.LaunchShellDTO())
        input_source = doubles.DisconnectAwareInputSource(
            inputs=["long_running_task\n"],
            stop_event=cmd._stop_event,
            timeout=3.0,
        )
        session = contract.SessionContext(
            connection=connection,
            view=view,
            plugin_processor=processor,
            input_source=input_source,
        )

        disconnect_thread = threading.Thread(
            target=self.run_mock_client_abrupt_disconnect,
            args=(client_transport,),
            daemon=True,
        )
        disconnect_thread.start()

        try:
            session.execute(cmd)

            assert not view.errors, f"Unexpected view errors occurred: {view.errors}"
            assert not cmd._task_pool.errors, f"Unexpected task pool errors: {cmd._task_pool.errors}"
            assert cmd._stop_event.is_set(), "Stop event was not set upon remote client disconnect."

            disconnect_thread.join(timeout=2.0)
            assert not disconnect_thread.is_alive(), "Disconnect thread failed to terminate."

            for thread in cmd._task_pool._threads:
                assert not thread.is_alive(), f"Task pool thread {thread.name} remained alive."

            assert connection.timeout == initial_timeout, (
                f"Connection timeout was not restored (expected {initial_timeout}, got {connection.timeout})."
            )
        finally:
            disconnect_thread.join(timeout=1.0)
            client_transport.close()
            server_transport.close()
            connection.close()
