from typing import TypeAlias

from declusor import config, contract

ClientPlugin: TypeAlias = type[contract.IClientPlugin]


class ClientRegistry:
    """Registry of client plugins available to the application.

    The registry maps a stable client identifier to its plugin implementation.
    It prevents the application parser from depending on concrete clients.
    """

    def __init__(self) -> None:
        """Create an empty client registry."""

        self._plugins: dict[str, ClientPlugin] = {}

    def register(self, plugin: ClientPlugin, /) -> None:
        """Register a client plugin.

        Args:
            plugin: Plugin class to register.

        Raises:
            ValueError: If another plugin already uses the same name.
        """

        if plugin.name in self._plugins:
            raise ValueError(f"Client already registered: {plugin.name}")

        self._plugins[plugin.name] = plugin

    def get(self, name: str, /) -> ClientPlugin:
        """Retrieve a registered client plugin.

        Args:
            name: Registered client identifier.

        Returns:
            Plugin associated with ``name``.

        Raises:
            config.ParserError: If no plugin matches ``name``.
        """

        try:
            return self._plugins[name]
        except KeyError as e:
            available = ", ".join(self.names())
            raise config.ParserError(f"Unknown client {name!r}. Available clients: {available}") from e

    def names(self) -> tuple[str, ...]:
        """Return the registered client identifiers.

        Returns:
            Sorted tuple containing the available client names.
        """

        return tuple(sorted(self._plugins))
