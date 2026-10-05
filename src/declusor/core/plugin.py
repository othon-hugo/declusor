import importlib.metadata
import inspect
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from declusor import config, contract, util


class PluginRegistry:
    """Registry of client plugins available to the application.

    The registry maps a stable client identifier to its plugin implementation.
    It prevents the application parser from depending on concrete clients.
    """

    def __init__(self) -> None:
        """Create an empty client registry."""

        self._plugins: dict[str, contract.PluginExtensionType] = {}

    def register(self, plugin: contract.PluginExtensionType, /) -> None:
        """Register a client plugin.

        Args:
            plugin: Plugin class to register.

        Raises:
            ValueError: If another plugin already uses the same name.
        """

        if plugin.name in self._plugins:
            raise ValueError(f"Client already registered: {plugin.name}")

        self._plugins[plugin.name] = plugin

    def get(self, name: str, /) -> contract.PluginExtensionType:
        """Retrieve a registered client plugin.

        Args:
            name: Registered client identifier.

        Returns:
            Plugin associated with ``name``.

        Raises:
            config.PluginNotFoundError: If no plugin matches ``name``.
        """

        try:
            return self._plugins[name]
        except KeyError as e:
            raise config.PluginNotFoundError(name, available_plugins=self.names()) from e

    def names(self) -> tuple[str, ...]:
        """Return the registered client identifiers.

        Returns:
            Sorted tuple containing the available client names.
        """

        return tuple(sorted(self._plugins))


class PluginManager(PluginRegistry):
    """Dynamic discovery and lifecycle registry for Declusor client plugins.

    Discovers and registers client plugins across three tiers:
    1. **Built-in / Repository plugins directory** (e.g. ``<root>/plugins/``).
    2. **Python Entry Points** (``group="declusor.plugins"`` via PEP 621 / pip).
    3. **Drop-in / User directories** (e.g. ``~/.declusor/plugins/`` or custom CLI path).

    Enforces strict contract validation on candidate classes before registration,
    ensuring that malformed or non-conforming plugins cannot destabilize the runtime.
    """

    ENTRY_POINT_GROUP = "declusor.plugins"

    def __init__(self) -> None:
        """Initialize an empty plugin manager."""

        super().__init__()

        self._sources: dict[str, str] = {}

    def validate_plugin(self, candidate: type, /) -> None:
        """Validate that a candidate class conforms strictly to ``IPluginExtension``.

        Args:
            candidate: Class to inspect and validate.

        Raises:
            config.PluginValidationError: If the candidate does not subclass ``IPluginExtension``,
                lacks a valid name, or has unimplemented abstract methods.
        """

        if not inspect.isclass(candidate):
            raise config.PluginValidationError(f"Plugin candidate {candidate!r} must be a class.")

        if not issubclass(candidate, contract.IPluginExtension):
            raise config.PluginValidationError(f"Plugin class {candidate.__name__!r} must implement 'IPluginExtension'.")

        name = getattr(candidate, "name", None)

        if not isinstance(name, str) or not name.strip():
            raise config.PluginValidationError(f"Plugin class {candidate.__name__!r} must define a non-empty string 'name'.")

        # Check for unimplemented abstract methods
        if inspect.isabstract(candidate):
            abstract_methods: set[str] = getattr(candidate, "__abstractmethods__", set())

            raise config.PluginValidationError(
                f"Plugin class {candidate.__name__!r} has unimplemented abstract methods: {', '.join(sorted(abstract_methods))}"
            )

        routes = getattr(candidate, "routes", None)

        if not isinstance(routes, Mapping):
            raise config.PluginValidationError(
                f"Plugin class {candidate.__name__!r} must define 'routes' as a mapping of names to RouteRegistration values."
            )

        normalized_routes: set[str] = set()

        for route, registration in routes.items():
            if not isinstance(route, str) or not route.strip():
                raise config.PluginValidationError(f"Plugin class {candidate.__name__!r} must define non-empty string route names.")

            normalized_route = route.strip()

            if normalized_route in {"help", "exit"}:
                raise config.PluginValidationError(f"Plugin class {candidate.__name__!r} cannot override protected route {normalized_route!r}.")

            if normalized_route in normalized_routes:
                raise config.PluginValidationError(f"Plugin class {candidate.__name__!r} defines duplicate normalized route {normalized_route!r}.")

            if not isinstance(registration, contract.RouteRegistration):
                raise config.PluginValidationError(f"Plugin class {candidate.__name__!r} route {normalized_route!r} must be a RouteRegistration.")

            normalized_routes.add(normalized_route)

    def register(
        self,
        plugin: contract.PluginExtensionType,
        /,
        *,
        source: str = "manual",
        allow_override: bool = False,
    ) -> None:
        """Register a validated client plugin.

        Args:
            plugin: Plugin class to register.
            source: Origin identifier for debugging and precedence tracking.
            allow_override: If True, replace an existing plugin with the same name.

        Raises:
            PluginValidationError: If the plugin fails contract validation.
            ValueError: If the plugin name is already registered and ``allow_override`` is False.
        """

        self.validate_plugin(plugin)

        if plugin.name in self._plugins and not allow_override:
            existing_source = self._sources.get(plugin.name, "unknown")
            raise ValueError(f"Client plugin {plugin.name!r} already registered from {existing_source}.")

        self._plugins[plugin.name] = plugin
        self._sources[plugin.name] = source

    def get_source(self, name: str, /) -> str | None:
        """Return the source origin of a registered plugin."""

        return self._sources.get(name)

    def load_from_directory(
        self,
        directory: Path,
        /,
        *,
        source_label: str = "directory",
        allow_override: bool = True,
    ) -> list[str]:
        """Scan a directory for plugin packages and load any valid plugins found.

        A valid plugin folder contains an ``__init__.py`` or ``plugin.py`` that defines
                one or more subclasses of ``IPluginExtension``.

        Args:
            directory: Directory containing plugin subdirectories.
            source_label: Descriptive label for registered plugins.
            allow_override: Whether plugins loaded here may override earlier registrations.

        Returns:
            List of plugin names successfully registered from this directory.
        """

        if not directory.exists() or not directory.is_dir():
            return []

        loaded_names: list[str] = []

        for item in sorted(directory.iterdir()):
            if not item.is_dir() or item.name.startswith((".", "_")):
                continue

            plugin_file = util.find_plugin_entry(item)

            if not plugin_file:
                continue

            plugin_class = util.import_plugin_from_file(
                item.name,
                plugin_file,
                contract.IPluginExtension,  # type: ignore[type-abstract]
            )

            if plugin_class:
                try:
                    self.register(plugin_class, source=f"{source_label}:{item.name}", allow_override=allow_override)
                    loaded_names.append(plugin_class.name)
                except (config.PluginValidationError, ValueError):
                    continue

        return loaded_names

    def load_from_entry_points(
        self,
        *,
        group: str = ENTRY_POINT_GROUP,
        allow_override: bool = True,
        entry_points_loader: Callable[..., Iterable[Any]] | None = None,
    ) -> list[str]:
        """Discover and load client plugins registered via Python Entry Points.

        Args:
            group: Entry point group to query (default: ``declusor.plugins``).
            allow_override: Whether entry-point plugins may override earlier registrations.
            entry_points_loader: Optional loader callable for entry points querying.

        Returns:
            List of plugin names successfully loaded from entry points.
        """

        loaded_names: list[str] = []

        try:
            loader = entry_points_loader or importlib.metadata.entry_points
            discovered = loader(group=group)
        except Exception:
            return []

        for entry_point in discovered:
            try:
                candidate = entry_point.load()
                self.register(candidate, source=f"entry_point:{entry_point.name}", allow_override=allow_override)
                loaded_names.append(candidate.name)
            except Exception:
                continue

        return loaded_names

    def discover(
        self,
        search_dirs: Sequence[Path] | None = None,
        /,
        *,
        enable_entry_points: bool = True,
        entry_points_loader: Callable[..., Iterable[Any]] | None = None,
    ) -> "PluginManager":
        """Run the multi-tier plugin discovery engine.

        Precedence order (later overrides earlier):
        1. Built-in repository directory (``config.PLUGINS_DIR``).
        2. Installed Python Entry Points (``declusor.plugins``).
        3. User drop-in directory (``config.USER_PLUGINS_DIR``).
        4. Explicit custom search directories passed to ``search_dirs``.

        Args:
            search_dirs: Optional additional search directories (e.g. from CLI ``--plugin-dir``).
            enable_entry_points: Whether to query Python entry points.
            entry_points_loader: Optional custom entry points loader.

        Returns:
            The populated ``PluginManager`` instance.
        """

        # Tier 1: Built-in repository plugins
        if config.PLUGINS_DIR.exists():
            self.load_from_directory(config.PLUGINS_DIR, source_label="built-in", allow_override=True)

        # Tier 2: Entry points (pip packages)
        if enable_entry_points:
            self.load_from_entry_points(allow_override=True, entry_points_loader=entry_points_loader)

        # Tier 3: User drop-in directory (~/.declusor/plugins)
        if config.USER_PLUGINS_DIR.exists():
            self.load_from_directory(config.USER_PLUGINS_DIR, source_label="user-dropin", allow_override=True)

        # Tier 4: Explicit custom search directories (CLI flags, highest precedence)
        if search_dirs:
            for custom_dir in search_dirs:
                if custom_dir.exists():
                    self.load_from_directory(custom_dir, source_label="custom-cli", allow_override=True)

        return self
