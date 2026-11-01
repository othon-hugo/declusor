"""Plugin discovery, layout detection, and dynamic module loading utilities."""

import importlib.util
import inspect
import sys
import warnings
from collections.abc import MutableMapping, MutableSequence
from pathlib import Path
from types import ModuleType

from declusor import config


def find_plugin_entry(plugin_dir: Path, /) -> Path | None:
    """Locate the Python entry file for a plugin directory.

    Supports both standard src-layout packages (``<plugin_dir>/src/<package>/``)
    and flat directory layouts (``<plugin_dir>/``).

    Args:
        plugin_dir: Root directory of the candidate plugin.

    Returns:
        Path to the entry file (``__init__.py`` or ``plugin.py``), or None if not found.
    """

    candidates: list[Path] = [
        plugin_dir / "src" / plugin_dir.name / "__init__.py",
        plugin_dir / "src" / plugin_dir.name / "plugin.py",
    ]

    src_dir = plugin_dir / "src"

    if src_dir.is_dir():
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and not child.name.startswith((".", "_")):
                candidates.append(child / "__init__.py")
                candidates.append(child / "plugin.py")

    candidates.extend(
        [
            plugin_dir / "__init__.py",
            plugin_dir / "plugin.py",
        ]
    )

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    return None


def import_plugin_from_file[T](
    module_name: str,
    file_path: Path,
    expected_type: type[T],
    /,
    *,
    module_search_path: MutableSequence[str] | None = None,
    module_registry: MutableMapping[str, ModuleType] | None = None,
) -> type[T] | None:
    """Dynamically import a module or package from file and extract a subclass of ``expected_type``.

    Args:
        module_name: Unique suffix identifier for the loaded module.
        file_path: Path to the target Python file (or package __init__.py).
        expected_type: Base class that the target class must subclass.
        module_search_path: Import search path to use while loading the plugin. Defaults to ``sys.path``.
        module_registry: Module registry to use while loading the plugin. Defaults to ``sys.modules``.

    Returns:
        First subclass of ``expected_type`` found in the module, or None on failure.
    """

    full_module_name = f"declusor_dynamic_plugin_{module_name}"
    search_locations = [str(file_path.parent)] if file_path.name == "__init__.py" else None
    active_search_path = module_search_path if module_search_path is not None else sys.path
    active_module_registry = module_registry if module_registry is not None else sys.modules

    added_sys_path: str | None = None

    if file_path.parent.parent.name == "src":
        src_path = str(file_path.parent.parent)

        if src_path not in active_search_path:
            active_search_path.insert(0, src_path)
            added_sys_path = src_path

    previous_module = active_module_registry.get(full_module_name)

    try:
        spec = importlib.util.spec_from_file_location(
            full_module_name,
            file_path,
            submodule_search_locations=search_locations,
        )

        if not spec or not spec.loader:
            return None

        module = importlib.util.module_from_spec(spec)
        active_module_registry[full_module_name] = module
        spec.loader.exec_module(module)

        for _, obj in inspect.getmembers(module, inspect.isclass):
            is_plugin_module = obj.__module__ == full_module_name or obj.__module__.startswith(f"{full_module_name}.")

            if is_plugin_module and issubclass(obj, expected_type) and obj is not expected_type:
                return obj
    except Exception as error:
        warnings.warn(
            f"Failed to import plugin candidate {file_path}: {type(error).__name__}: {error}",
            config.DeclusorWarning,
            stacklevel=2,
        )
        return None
    finally:
        if previous_module is None:
            active_module_registry.pop(full_module_name, None)
        else:
            active_module_registry[full_module_name] = previous_module

        if added_sys_path is not None and added_sys_path in active_search_path:
            active_search_path.remove(added_sys_path)

    return None
