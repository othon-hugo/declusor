from collections.abc import Mapping

from declusor import contract


class DummyPluginFileStore(contract.IPluginProcessor):
    """Fully-typed in-memory file store for client scripts, libraries, and modules."""

    def __init__(
        self,
        script_template: str = "#!/bin/sh\n# Host: {host}:{port}\n# Ack: {acknowledge}",
        library_bytes: bytes = b"dummy_library_payload",
        modules: dict[str, bytes] | None = None,
        helpers_map: dict[str, bytes] | None = None,
    ) -> None:
        self.script_template: str = script_template
        self.library_bytes: bytes = library_bytes
        self.modules: dict[str, bytes] = dict(modules) if modules is not None else {}
        self.helpers_map: dict[str, bytes] = dict(helpers_map) if helpers_map is not None else {"default.sh": library_bytes}
        self.load_module_calls: list[str] = []
        self.load_helper_calls: list[str] = []
        self.load_all_helpers_calls: int = 0
        self.render_calls: list[tuple[str, int, bytes]] = []
        self.load_library_error: BaseException | None = None
        self.load_module_error: BaseException | None = None
        self.render_error: BaseException | None = None

    def set_module(self, name: str, content: bytes) -> None:
        """Register a module name and content payload."""

        self.modules[name] = content

    def render_launcher(self, host: str, port: int, acknowledge: bytes, /) -> bytes:
        """Render client script from configured template as bytes."""

        if self.render_error is not None:
            raise self.render_error

        self.render_calls.append((host, port, acknowledge))
        rendered_str = self.script_template.format(host=host, port=port, acknowledge=acknowledge.hex())

        return rendered_str.encode("utf-8")

    def load_helper(self, helper: str, /) -> bytes:
        """Return configured helper library payload."""

        if self.load_library_error is not None:
            raise self.load_library_error

        self.load_helper_calls.append(helper)

        return self.helpers_map.get(helper, self.library_bytes)

    def load_all_helpers(self) -> Mapping[str, bytes]:
        """Return all configured helper libraries."""

        if self.load_library_error is not None:
            raise self.load_library_error

        self.load_all_helpers_calls += 1

        return dict(self.helpers_map)

    @property
    def helpers(self) -> bytes:
        """Compatibility helper returning concatenated helper libraries."""

        return b"\n".join(self.load_all_helpers().values())

    def load_module(self, module: str, /) -> bytes:
        """Return configured or synthesised module payload."""

        if self.load_module_error is not None:
            raise self.load_module_error

        self.load_module_calls.append(module)

        if module in self.modules:
            return self.modules[module]

        return f"module_bytes:{module}".encode()

    def get_module(self, module_name: str, /) -> bytes:
        """Compatibility alias for load_module."""

        return self.load_module(module_name)
