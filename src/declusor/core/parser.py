"""Command-line argument parser, typed namespaces, and configuration builder."""

import argparse
import dataclasses
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from declusor import config, contract, transport, util

if TYPE_CHECKING:
    from .plugin import PluginManager


class DeclusorNamespace(argparse.Namespace):
    """Strongly-typed namespace for Declusor CLI arguments."""

    host: str = ""
    """Listening IP address or hostname."""

    port: int = 0
    """Listening TCP port number."""

    plugin: str | None = None
    """Selected client plugin name."""

    mode: str = config.DEFAULT_EXECUTION_MODE.value
    """Application execution mode identifier."""

    launcher_kind: str = config.DEFAULT_LAUNCHER_KIND.value
    """Client launcher delivery kind (staged or stageless)."""

    launcher_output: str = config.DEFAULT_LAUNCHER_OUTPUT_MODE.value
    """Client launcher delivery output destination mode."""

    launcher_wrapper: str | None = None
    """Custom shell wrapper template string."""

    timeout: float | None = None
    """Network connection timeout in seconds."""

    assets_dir: Path | None = None
    """Custom assets root directory path."""

    plugin_dir: Path | None = None
    """Custom external drop-in plugin directory path."""

    transport_layers: list[str] | None = None
    """Sequence of composable transport layer identifiers."""


class DeclusorParser(util.Parser):
    """Parser for command-line arguments."""

    class Host(str):
        """Validated host value parsed from the command line."""

        arg_name: Final = "host"
        """Positional argument destination attribute name."""

        arg_help: Final = "IP address or hostname where the service should run"
        """Help description string."""

        def __new__(cls, value: str) -> "DeclusorParser.Host":
            """Validate host string invariant to ensure non-empty address."""

            if not value:
                raise ValueError("host cannot be empty")

            return super().__new__(cls, value)

    class Port(int):
        """Validated TCP port parsed from the command line."""

        arg_name: Final = "port"
        """Positional argument destination attribute name."""

        arg_help: Final = "port number to listen on for incoming connections"
        """Help description string."""

        def __new__(cls, value: int | str) -> "DeclusorParser.Port":
            """Validate TCP port range invariant between 0 and 65535."""

            port = int(value)

            if not 0 <= port <= 65535:
                raise ValueError("port must be between 0 and 65535")

            return super().__new__(cls, port)

    class Plugin(str):
        """Plugin name parsed from the command line."""

        arg_name: Final = "plugin"
        """CLI argument destination attribute name."""

        arg_help: Final = "agent responsible for handling requests"
        """Help description string."""

        arg_flags: Final = ("-p", "--plugin")
        """CLI flag options."""

        def __new__(cls, value: str) -> "DeclusorParser.Plugin":
            """Validate plugin name invariant to ensure non-empty string."""

            if not value:
                raise ValueError("plugin cannot be empty")

            return super().__new__(cls, value)

    class ExecutionMode(str):
        """Execution mode argument definition."""

        arg_name: Final = "mode"
        """CLI argument destination attribute name."""

        arg_help: Final = "runtime execution mode"
        """Help description string."""

        arg_flags: Final = ("-m", "--mode")
        """CLI flag options."""

        arg_choices: Final = tuple(config.ExecutionMode)
        """Permitted execution mode enum choices."""

        arg_default: Final = config.DEFAULT_EXECUTION_MODE
        """Default execution mode fallback value."""

        def __new__(cls, value: str) -> "DeclusorParser.ExecutionMode":
            """Validate and normalize execution mode choice."""

            if not value:
                raise ValueError("execution mode cannot be empty")

            try:
                mode = config.ExecutionMode.from_string(value)
            except ValueError as error:
                choices = ", ".join(repr(m.value) for m in config.ExecutionMode)
                raise ValueError(f"invalid choice: {value!r} (choose from {choices})") from error

            return super().__new__(cls, mode.value)

    class Timeout(float):
        """Network socket operation timeout argument definition."""

        arg_name: Final = "timeout"
        """CLI argument destination attribute name."""

        arg_help: Final = "network socket timeout in seconds"
        """Help description string."""

        arg_flags: Final = ("-t", "--timeout")
        """CLI flag options."""

        def __new__(cls, value: float | str) -> "DeclusorParser.Timeout":
            """Validate timeout value invariant to ensure positive float."""

            try:
                timeout = float(value)
            except (TypeError, ValueError) as error:
                raise ValueError(f"invalid timeout value: {value!r}") from error

            if timeout <= 0:
                raise ValueError("timeout must be greater than 0")

            return super().__new__(cls, timeout)

    class AssetsDir(Path):
        """Root directory containing application assets."""

        arg_name: Final = "assets_dir"
        """CLI argument destination attribute name."""

        arg_help: Final = "root directory containing client launchers, helpers, and modules"
        """Help description string."""

        arg_flags: Final = ("--assets-dir",)
        """CLI flag options."""

    class PluginDir(Path):
        """Additional directory from which plugins are discovered."""

        arg_name: Final = "plugin_dir"
        """CLI argument destination attribute name."""

        arg_help: Final = "additional directory to discover custom drop-in plugins"
        """Help description string."""

        arg_flags: Final = ("--plugin-dir",)
        """CLI flag options."""

    class LauncherKind(str):
        """Launcher delivery kind argument definition."""

        arg_name: Final = "launcher_kind"
        """CLI argument destination attribute name."""

        arg_help: Final = "client launcher kind"
        """Help description string."""

        arg_flags: Final = ("-K", "--launcher-kind")
        """CLI flag options."""

        arg_choices: Final = tuple(k.value for k in config.LauncherKind)
        """Permitted launcher kind string choices."""

        arg_default: Final = config.DEFAULT_LAUNCHER_KIND.value
        """Default launcher kind choice."""

        def __new__(cls, value: str) -> "DeclusorParser.LauncherKind":
            """Validate and normalize launcher kind."""

            if not value:
                raise ValueError("launcher kind cannot be empty")

            try:
                kind = config.LauncherKind.from_string(value)
            except ValueError as error:
                choices = ", ".join(repr(k.value) for k in config.LauncherKind)
                raise ValueError(f"invalid choice: {value!r} (choose from {choices})") from error

            return super().__new__(cls, kind.value)

    class LauncherOutput(str):
        """Launcher output mode argument definition."""

        arg_name: Final = "launcher_output"
        """CLI argument destination attribute name."""

        arg_help: Final = "client launcher delivery output mode ('{terminal}', '{silent}', '{clipboard}', or '{file}:<path>')".format(
            terminal=config.LauncherOutputMode.TERMINAL,
            silent=config.LauncherOutputMode.SILENT,
            clipboard=config.LauncherOutputMode.CLIPBOARD,
            file=config.LauncherOutputMode.FILE,
        )
        """Help description string."""

        arg_flags: Final = ("-O", "--launcher-output")
        """CLI flag options."""

        arg_default: Final = config.DEFAULT_LAUNCHER_OUTPUT_MODE.value
        """Default launcher output mode value."""

        def __new__(cls, value: str) -> "DeclusorParser.LauncherOutput":
            """Validate and normalize launcher output argument value."""

            if not value:
                raise ValueError("launcher output cannot be empty")

            normalized = value.strip()
            lower = normalized.lower()

            if lower == config.LauncherOutputMode.TERMINAL.value:
                return super().__new__(cls, config.LauncherOutputMode.TERMINAL.value)

            if lower == config.LauncherOutputMode.SILENT.value:
                return super().__new__(cls, config.LauncherOutputMode.SILENT.value)

            if lower in (config.LauncherOutputMode.CLIPBOARD.value, "clip"):
                return super().__new__(cls, config.LauncherOutputMode.CLIPBOARD.value)

            if lower.startswith("file:"):
                path_str = normalized[5:].strip()

                if not path_str:
                    raise ValueError("output path cannot be empty in 'file:<path>' launcher output mode")

                return super().__new__(cls, normalized)

            valid = (
                f"{config.LauncherOutputMode.TERMINAL.value!r}, "
                f"{config.LauncherOutputMode.SILENT.value!r}, "
                f"{config.LauncherOutputMode.CLIPBOARD.value!r}, or 'file:<path>'"
            )

            raise ValueError(f"invalid launcher output mode: {value!r} (expected {valid})")

    class LauncherWrapper(str):
        """Launcher shell wrapper template argument definition."""

        arg_name: Final = "launcher_wrapper"
        """CLI argument destination attribute name."""

        arg_help: Final = "shell invocation wrapper template containing '$DECLUSOR_SCRIPT' (e.g. \"python3 -c '$DECLUSOR_SCRIPT'\")"
        """Help description string."""

        arg_flags: Final = ("-W", "--launcher-wrapper")
        """CLI flag options."""

        def __new__(cls, value: str) -> "DeclusorParser.LauncherWrapper":
            """Validate launcher wrapper template invariant."""

            if not value:
                raise ValueError("launcher wrapper cannot be empty")

            return super().__new__(cls, value)

    class TransportLayer(str):
        """Transport layer argument definition."""

        arg_name: Final = "transport_layers"
        """CLI argument destination attribute name."""

        arg_help: Final = "composable transport layer to wrap connection (repeatable)"
        """Help description string."""

        arg_action: Final = "append"
        """Argparse action type."""

        arg_flags: Final = ("-L", "--transport-layer")
        """CLI flag options."""

        def __new__(cls, value: str) -> "DeclusorParser.TransportLayer":
            """Validate and normalize transport layer identifier."""

            if not value or not value.strip():
                raise ValueError("transport layer name cannot be empty")

            return super().__new__(cls, value.strip().lower())

    declusor_arguments: Final = (
        Host.arg_name,
        Port.arg_name,
        Plugin.arg_name,
        ExecutionMode.arg_name,
        LauncherKind.arg_name,
        LauncherOutput.arg_name,
        LauncherWrapper.arg_name,
        Timeout.arg_name,
        AssetsDir.arg_name,
        PluginDir.arg_name,
        TransportLayer.arg_name,
    )
    """Tuple of standard argument names recognized by the core Declusor engine."""

    @staticmethod
    def parse_launcher_output(value: str) -> tuple[config.LauncherOutputMode, Path | None]:
        """Convert a validated launcher output string into mode and optional destination path.

        Args:
            value: Validated launcher output string ('terminal', 'silent', 'clipboard', or 'file:<path>').

        Returns:
            Tuple of (LauncherOutputMode, Path | None).
        """

        normalized = value.strip()
        lower = normalized.lower()

        if lower == config.LauncherOutputMode.TERMINAL.value:
            return config.LauncherOutputMode.TERMINAL, None

        if lower == config.LauncherOutputMode.SILENT.value:
            return config.LauncherOutputMode.SILENT, None

        if lower in (config.LauncherOutputMode.CLIPBOARD.value, "clip"):
            return config.LauncherOutputMode.CLIPBOARD, None

        if lower.startswith("file:"):
            return config.LauncherOutputMode.FILE, Path(normalized[5:].strip())

        raise ValueError(f"invalid launcher output mode: {value!r}")

    def __init__(self, name: str, description: str = "") -> None:
        """Create a parser for command-line arguments.

        Args:
            name: Program name.
            description: Short description of the application.
        """

        super().__init__(prog=name, description=description or None)

        self._is_configured = False
        self._configure_common_arguments()

    def _configure_common_arguments(self) -> None:
        """Configure standard positional and optional command-line flags."""

        if self._is_configured:
            return

        self.add_argument(
            self.Host.arg_name,
            help=self.Host.arg_help,
            type=self.Host,
        )

        self.add_argument(
            self.Port.arg_name,
            help=self.Port.arg_help,
            type=self.Port,
        )

        self.add_argument(
            *self.Plugin.arg_flags,
            help=self.Plugin.arg_help,
            type=self.Plugin,
            default=None,
        )

        self.add_argument(
            *self.Timeout.arg_flags,
            help=self.Timeout.arg_help,
            default=None,
            type=self.Timeout,
        )

        self.add_argument(
            *self.ExecutionMode.arg_flags,
            help=self.ExecutionMode.arg_help,
            choices=self.ExecutionMode.arg_choices,
            default=self.ExecutionMode.arg_default,
            type=self.ExecutionMode,
        )

        self.add_argument(
            *self.LauncherKind.arg_flags,
            dest=self.LauncherKind.arg_name,
            help=self.LauncherKind.arg_help,
            choices=self.LauncherKind.arg_choices,
            default=self.LauncherKind.arg_default,
            type=self.LauncherKind,
        )

        self.add_argument(
            *self.LauncherWrapper.arg_flags,
            help=self.LauncherWrapper.arg_help,
            default=None,
            type=self.LauncherWrapper,
        )

        self.add_argument(
            *self.LauncherOutput.arg_flags,
            help=self.LauncherOutput.arg_help,
            default=self.LauncherOutput.arg_default,
            type=self.LauncherOutput,
        )

        self.add_argument(
            *self.TransportLayer.arg_flags,
            dest=self.TransportLayer.arg_name,
            action=self.TransportLayer.arg_action,
            help=self.TransportLayer.arg_help,
            type=self.TransportLayer,
            default=None,
        )

        self.add_argument(
            *self.AssetsDir.arg_flags,
            help=self.AssetsDir.arg_help,
            type=self.AssetsDir,
            default=None,
        )

        self.add_argument(
            *self.PluginDir.arg_flags,
            help=self.PluginDir.arg_help,
            type=self.PluginDir,
            default=None,
        )

        self._is_configured = True

    def parse(
        self,
        manager: "PluginManager",
        argv: Sequence[str] | None = None,
        /,
        *,
        transport_registry: transport.TransportLayerRegistry | None = None,
    ) -> contract.PluginConfig[contract.ParsedArguments]:
        """Parse arguments and build a validated plugin configuration.

        Args:
            manager: Plugin manager containing the client plugins available to
                the application.
            argv: Sequence of arguments to parse, excluding the program name.
            transport_registry: Optional registry to validate and resolve transport layers.

        Returns:
            Validated plugin configuration populated from command-line arguments.

        Raises:
            config.ParserError: If no plugin is available, the requested plugin
                does not exist, or the resulting configuration is invalid.
        """

        preliminary_args, _ = self.parse_known_args(argv, namespace=DeclusorNamespace())
        self._load_cli_plugin_directory(manager, preliminary_args.plugin_dir)

        Plugin = self._resolve_plugin(manager, preliminary_args.plugin)
        Plugin.configure_parser(self)

        args = self.parse_args(argv, namespace=DeclusorNamespace())

        launcher_kind = config.LauncherKind.from_string(args.launcher_kind)

        if launcher_kind not in Plugin.supported_launcher_kinds:
            supported_kinds = ", ".join(repr(k.value) for k in sorted(Plugin.supported_launcher_kinds, key=lambda k: k.value))
            raise config.ParserError(f"Plugin {Plugin.name!r} does not support launcher kind {launcher_kind.value!r}. Supported: {supported_kinds}")

        plugin_config = self._build_plugin_config(Plugin, args)
        transport_layers = self._resolve_transport_layers(args, transport_registry)

        final_config = self._assemble_final_config(plugin_config, args, launcher_kind, transport_layers)
        Plugin.validate(final_config)

        return final_config

    def _load_cli_plugin_directory(self, manager: "PluginManager", plugin_dir: Path | None, /) -> None:
        """Load external plugins from CLI directory if specified."""

        if plugin_dir is not None:
            manager.load_from_directory(
                plugin_dir,
                source_label="cli-plugin-dir",
                allow_override=True,
            )

    def _resolve_plugin(
        self,
        manager: "PluginManager",
        requested_plugin: object,
        /,
    ) -> type[contract.IPluginExtension[Any]]:
        """Resolve and validate the target plugin from available registrations."""

        available_plugins = manager.names()
        default_plugin = self._determine_default_plugin(available_plugins)
        plugin_name = requested_plugin or default_plugin

        if not plugin_name:
            raise config.ParserError("No client plugin available.")

        if not isinstance(plugin_name, str):
            raise config.ParserError(f"argument -p/--plugin: expected string, got {type(plugin_name).__name__}")

        if plugin_name not in available_plugins:
            choices = ", ".join(repr(name) for name in available_plugins)
            raise config.ParserError(f"argument -p/--plugin: invalid choice: {plugin_name!r} (choose from {choices})")

        try:
            return manager.get(plugin_name)
        except config.PluginNotFoundError as error:
            choices = ", ".join(repr(name) for name in error.available_plugins)
            raise config.ParserError(f"argument -p/--plugin: invalid choice: {plugin_name!r} (choose from {choices})") from error

    @staticmethod
    def _determine_default_plugin(available_plugins: Sequence[str], /) -> str | None:
        """Determine default plugin identifier from available plugins."""

        if config.DEFAULT_DECLUSOR_PLUGIN.value in available_plugins:
            return config.DEFAULT_DECLUSOR_PLUGIN.value

        if available_plugins:
            return available_plugins[0]

        return None

    def _build_plugin_config(
        self,
        Plugin: type[contract.IPluginExtension[Any]],
        args: DeclusorNamespace,
        /,
    ) -> contract.PluginConfig[contract.ParsedArguments]:
        """Extract options and build base plugin configuration."""

        plugin_options = {key: value for key, value in vars(args).items() if key not in self.declusor_arguments}
        plugin_filesystem = contract.PluginFilesystem.from_root(args.assets_dir) if args.assets_dir is not None else None

        options: contract.ParsedArguments = Plugin.extract_options(plugin_options)
        return Plugin.build_config(
            args.host,
            args.port,
            options,
            filesystem=plugin_filesystem,
            mode=config.ExecutionMode(args.mode),
        )

    def _resolve_transport_layers(
        self,
        args: DeclusorNamespace,
        transport_registry: transport.TransportLayerRegistry | None,
        /,
    ) -> tuple[str, ...]:
        """Validate and resolve requested transport layers against the registry."""

        registry = transport_registry or transport.default_transport_registry()
        raw_layers = args.transport_layers or []
        available_layers = registry.names()

        for layer in raw_layers:
            if layer not in available_layers:
                choices = ", ".join(repr(name) for name in available_layers)
                raise config.ParserError(f"argument --transport-layer: invalid choice: {layer!r} (choose from {choices})")

        return tuple(raw_layers)

    def _assemble_final_config(
        self,
        plugin_config: contract.PluginConfig[contract.ParsedArguments],
        args: DeclusorNamespace,
        launcher_kind: config.LauncherKind,
        transport_layers: tuple[str, ...],
        /,
    ) -> contract.PluginConfig[contract.ParsedArguments]:
        """Apply global CLI overrides to plugin configuration."""

        output_mode, output_path = self.parse_launcher_output(args.launcher_output)

        return dataclasses.replace(
            plugin_config,
            timeout=args.timeout,
            launcher_kind=launcher_kind,
            launcher_output_mode=output_mode,
            launcher_output_path=output_path,
            launcher_wrapper=args.launcher_wrapper,
            transport_layers=transport_layers,
        )
