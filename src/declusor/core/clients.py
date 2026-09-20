from typing import TypeAlias

from declusor import config, interface

ClientPlugin: TypeAlias = type[interface.IClientPlugin]


class ClientRegistry:
    """Registry of client plugins available to the application.

    The registry maps a stable client identifier to its plugin implementation.
    It prevents the application parser from depending on concrete clients.
    """

    _plugins: dict[str, ClientPlugin] = {}

    @classmethod
    def register(cls, plugin: ClientPlugin, /) -> None:
        """Register a client plugin.

        Args:
            plugin: Plugin class to register.

        Raises:
            ValueError: If another plugin already uses the same name.
        """

        if plugin.name in cls._plugins:
            raise ValueError(f"Client already registered: {plugin.name}")

        cls._plugins[plugin.name] = plugin

    @classmethod
    def get(cls, name: str, /) -> ClientPlugin:
        """Retrieve a registered client plugin.

        Args:
            name: Registered client identifier.

        Returns:
            Plugin associated with ``name``.

        Raises:
            config.ParserError: If no plugin matches ``name``.
        """

        try:
            return cls._plugins[name]
        except KeyError as e:
            available = ", ".join(cls.names())
            raise config.ParserError(f"Unknown client {name!r}. Available clients: {available}") from e

    @classmethod
    def names(cls) -> tuple[str, ...]:
        """Return the registered client identifiers.

        Returns:
            Sorted tuple containing the available client names.
        """

        return tuple(sorted(cls._plugins))
