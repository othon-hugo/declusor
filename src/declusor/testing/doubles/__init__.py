"""Reusable, fully-typed test doubles implementing Declusor contracts.

Provides mock-free, deterministic test doubles for consoles, connections,
profiles, file stores, runtimes, plugins, routers, sockets, and applications.
"""

from declusor.testing.doubles.application import DummyApplication
from declusor.testing.doubles.command import DummyCommand
from declusor.testing.doubles.connection import DummyConnection
from declusor.testing.doubles.console import DummyConsole
from declusor.testing.doubles.filestore import DummyClientFileStore
from declusor.testing.doubles.plugins import DummyClientPlugin, DummyClientRuntime
from declusor.testing.doubles.profile import DummyConnectionProfile
from declusor.testing.doubles.router import DummyRouter
from declusor.testing.doubles.socket import DummySocket

__all__ = [
    "DummyApplication",
    "DummyClientFileStore",
    "DummyClientPlugin",
    "DummyClientRuntime",
    "DummyCommand",
    "DummyConnection",
    "DummyConnectionProfile",
    "DummyConsole",
    "DummyRouter",
    "DummySocket",
]
