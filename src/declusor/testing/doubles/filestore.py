from declusor import contract


class DummyClientFileStore(contract.IPluginFileStore):
    """Fully-typed in-memory file store for client scripts, libraries, and modules."""

    def __init__(
        self,
        script_template: str = "#!/bin/sh\n# Host: {host}:{port}\n# Ack: {acknowledge}",
        library_bytes: bytes = b"dummy_library_payload",
        modules: dict[str, bytes] | None = None,
    ) -> None:
        self.script_template: str = script_template
        self.library_bytes: bytes = library_bytes
        self.modules: dict[str, bytes] = dict(modules) if modules is not None else {}
        self.load_module_calls: list[str] = []
        self.load_library_calls: int = 0
        self.render_calls: list[tuple[str, int, bytes]] = []
        self.load_library_error: BaseException | None = None
        self.load_module_error: BaseException | None = None
        self.render_error: BaseException | None = None

    def set_module(self, name: str, content: bytes) -> None:
        """Register a module name and content payload."""

        self.modules[name] = content

    def render_client_script(self, host: str, port: int, acknowledge: bytes, /) -> str:
        """Render client script from configured template."""

        if self.render_error is not None:
            raise self.render_error

        self.render_calls.append((host, port, acknowledge))

        return self.script_template.format(host=host, port=port, acknowledge=acknowledge.hex())

    def load_library(self) -> bytes:
        """Return configured library payload."""

        if self.load_library_error is not None:
            raise self.load_library_error

        self.load_library_calls += 1

        return self.library_bytes

    def load_module(self, module_name: str, /) -> bytes:
        """Return configured or synthesised module payload."""

        if self.load_module_error is not None:
            raise self.load_module_error

        self.load_module_calls.append(module_name)

        if module_name in self.modules:
            return self.modules[module_name]

        return f"module_bytes:{module_name}".encode()


DummyPluginFileStore = DummyClientFileStore
