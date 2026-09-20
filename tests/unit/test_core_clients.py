from socket import socket

from declusor import interface, util
from declusor.core.clients import ClientRegistry
from declusor.core.parser import DeclusorParser


class FakeRuntime(interface.IClientRuntime):
    """Minimal runtime used to satisfy the fake plugin contract."""

    @property
    def client_script(self) -> str:
        """Return an empty bootstrap script."""

        return ""

    def create_connection(self, connection: socket, /) -> interface.IConnection:
        """The fake runtime does not create real connections."""

        raise NotImplementedError


class FakePlugin(interface.IClientPlugin):
    """Client plugin used to verify registry isolation."""

    name = "fake"

    @classmethod
    def configure_parser(cls, parser: util.Parser, /) -> None:
        """Register no client-specific arguments."""

    @classmethod
    def build_config(cls, args: util.Namespace, /) -> interface.ClientConfig:
        """Build a configuration identifying the fake client."""

        return interface.ClientConfig(cls.name, args.host, args.port)

    @classmethod
    def validate(cls, client_config: interface.ClientConfig, /) -> None:
        """Accept the fake configuration."""

    @classmethod
    def build_runtime(cls, client_config: interface.ClientConfig, /) -> interface.IClientRuntime:
        """Build the fake runtime."""

        return FakeRuntime()


def test_registries_are_isolated() -> None:
    """Registering a plugin must not affect another registry instance."""

    first = ClientRegistry()
    second = ClientRegistry()

    first.register(FakePlugin)

    assert first.names() == ("fake",)
    assert second.names() == ()


def test_parser_uses_injected_registry(monkeypatch) -> None:
    """The parser must resolve clients only from its injected registry."""

    registry = ClientRegistry()
    registry.register(FakePlugin)
    monkeypatch.setattr("sys.argv", ["declusor", "127.0.0.1", "9000", "--client", "fake"])

    options = DeclusorParser(registry, name="declusor").parse()

    assert options["client"].kind == "fake"
