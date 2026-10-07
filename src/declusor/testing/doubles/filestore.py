import os
from collections.abc import Mapping
from pathlib import Path

from declusor import contract


class DummyPluginFileStore(contract.IPluginProcessor):
    """Fully-typed in-memory file store for client scripts, libraries, and modules."""

    def __init__(
        self,
        script_template: str = "#!/bin/sh\n# Host: {host}:{port}\n# Ack: {acknowledge}",
        library_bytes: bytes = b"dummy_library_payload",
        modules: dict[str, bytes] | None = None,
        helpers_map: dict[str, bytes] | None = None,
        filesystem: contract.PluginFilesystem | None = None,
    ) -> None:
        self.script_template: str = script_template
        self.library_bytes: bytes = library_bytes
        self.modules: dict[str, bytes] = dict(modules) if modules is not None else {}
        self.helpers_map: dict[str, bytes] = dict(helpers_map) if helpers_map is not None else {"default.sh": library_bytes}
        self.missing_modules: set[str] = set()
        self.missing_helpers: set[str] = set()
        self.load_module_calls: list[str] = []
        self.load_helper_calls: list[str] = []
        self.load_all_helpers_calls: int = 0
        self.render_calls: list[tuple[str, int, bytes]] = []
        self.load_library_error: BaseException | None = None
        self.load_module_error: BaseException | None = None
        self.find_module_error: BaseException | None = None
        self.find_helper_error: BaseException | None = None
        self.render_error: BaseException | None = None

        if filesystem is not None:
            self._filesystem = filesystem
        else:
            root = Path("/tmp/dummy_assets")
            self._filesystem = contract.PluginFilesystem(
                root=root,
                assets=root,
                launchers=root / "launchers",
                helpers=root / "helpers",
                modules=root / "modules",
            )

    @property
    def filesystem(self) -> contract.PluginFilesystem:
        """In-memory or mock plugin filesystem layout."""

        return self._filesystem

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

    def find_module(self, module_name: str, /) -> Path | None:
        """Return path to requested module if configured or present."""

        if self.find_module_error is not None:
            raise self.find_module_error

        if module_name in self.missing_modules:
            return None

        clean_name = module_name.removeprefix("modules/").removeprefix(f"modules{os.sep}")
        if clean_name in self.missing_modules:
            return None

        if self.modules and module_name not in self.modules and clean_name not in self.modules:
            return None

        return (self._filesystem.modules / clean_name).resolve()

    def find_helper(self, helper_name: str, /) -> Path | None:
        """Return path to requested helper library."""

        if self.find_helper_error is not None:
            raise self.find_helper_error

        if helper_name in self.missing_helpers:
            return None

        return (self._filesystem.helpers / helper_name).resolve()

    def load_helper(self, helper_path: Path | str, /) -> bytes:
        """Return configured helper library payload."""

        if self.load_library_error is not None:
            raise self.load_library_error

        path_obj = Path(helper_path)
        try:
            rel_name = path_obj.relative_to(self._filesystem.helpers).as_posix()
        except ValueError:
            rel_name = path_obj.as_posix()

        self.load_helper_calls.append(rel_name)

        return self.helpers_map.get(rel_name, self.library_bytes)

    def load_all_helpers(self) -> Mapping[str, bytes]:
        """Return all configured helper libraries."""

        if self.load_library_error is not None:
            raise self.load_library_error

        self.load_all_helpers_calls += 1

        return dict(self.helpers_map)

    def load_module(self, module_path: Path | str, /) -> bytes:
        """Return configured or synthesised module payload."""

        if self.load_module_error is not None:
            raise self.load_module_error

        path_obj = Path(module_path)
        try:
            rel_name = path_obj.relative_to(self._filesystem.modules).as_posix()
        except ValueError:
            rel_name = path_obj.as_posix()

        self.load_module_calls.append(rel_name)

        if rel_name in self.modules:
            return self.modules[rel_name]

        if str(module_path) in self.modules:
            return self.modules[str(module_path)]

        return f"module_bytes:{rel_name}".encode()
