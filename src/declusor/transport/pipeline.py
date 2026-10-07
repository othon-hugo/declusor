from collections.abc import Callable, Sequence
from typing import Final

from declusor import config, contract

from .xor_transport import XorTransport

type TransportLayerFactory = Callable[[contract.ITransport], contract.ITransport]
"""Callable that wraps an ITransport into another ITransport (e.g. ITransportLayer)."""


class TransportPipeline:
    """Sequential pipeline of transport layers applied to a base transport."""

    def __init__(self, layers: Sequence[TransportLayerFactory] = ()) -> None:
        """Initialize the pipeline with an ordered sequence of layer factories.

        Args:
            layers: Sequence of transport layer factory callables.
        """

        self._layers: Final[tuple[TransportLayerFactory, ...]] = tuple(layers)

    @property
    def layers(self) -> tuple[TransportLayerFactory, ...]:
        """Ordered sequence of layer factory callables."""

        return self._layers

    def wrap(self, transport: contract.ITransport, /) -> contract.ITransport:
        """Wrap a base transport sequentially through all configured layers.

        Args:
            transport: The initial (base) transport channel.

        Returns:
            The outer-most decorated transport channel.
        """

        current = transport

        for layer in self._layers:
            current = layer(current)

        return current


class TransportLayerRegistry:
    """Registry of named transport layer factories for runtime composition.

    Allows registering transport layers by name (e.g. 'xor') and building
    composable pipelines from an ordered list of names passed via CLI or API.
    """

    def __init__(self) -> None:
        """Initialize an empty transport layer registry."""

        self._factories: dict[str, TransportLayerFactory] = {}

    def register(self, name: str, factory: TransportLayerFactory, /) -> None:
        """Register a transport layer factory under a normalized name.

        Args:
            name: Layer identifier (e.g. 'xor').
            factory: Callable accepting an ITransport and returning a decorated ITransport.

        Raises:
            ValueError: If name is empty or already registered.
        """

        normalized = name.strip().lower()

        if not normalized:
            raise ValueError("Transport layer name cannot be empty.")

        self._factories[normalized] = factory

    def get(self, name: str, /) -> TransportLayerFactory:
        """Retrieve a transport layer factory by name.

        Args:
            name: Layer identifier to look up.

        Returns:
            The registered factory callable.

        Raises:
            KeyError: If the layer name is not registered.
        """

        normalized = name.strip().lower()

        try:
            return self._factories[normalized]
        except KeyError as err:
            available = self.names()
            raise KeyError(f"Unknown transport layer: {name!r}. Available: {available}") from err

    def names(self) -> tuple[str, ...]:
        """Return a sorted tuple of registered transport layer names."""

        return tuple(sorted(self._factories))

    def build_pipeline(self, layer_names: Sequence[str], /) -> TransportPipeline:
        """Build a TransportPipeline from an ordered sequence of registered layer names.

        Args:
            layer_names: Sequence of layer names to resolve and stack.

        Returns:
            TransportPipeline ready to wrap an accepted transport.

        Raises:
            KeyError: If any requested layer name is unknown.
        """

        factories = [self.get(name) for name in layer_names]

        return TransportPipeline(factories)


def default_transport_registry() -> TransportLayerRegistry:
    """Build the default TransportLayerRegistry pre-configured with built-in layers."""

    registry = TransportLayerRegistry()
    registry.register("xor", lambda transport: XorTransport(transport, config.DEFAULT_XOR_KEY))

    return registry
