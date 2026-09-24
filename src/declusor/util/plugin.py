import importlib.util
import inspect
import sys
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")


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


def import_plugin_from_file(
    module_name: str,
    file_path: Path,
    expected_type: type[T],
    /,
) -> type[T] | None:
    """Dynamically import a module or package from file and extract a subclass of ``expected_type``.

    Args:
        module_name: Unique suffix identifier for the loaded module.
        file_path: Path to the target Python file (or package __init__.py).
        expected_type: Base class that the target class must subclass.

    Returns:
        First subclass of ``expected_type`` found in the module, or None on failure.
    """

    full_module_name = f"declusor_dynamic_plugin_{module_name}"
    search_locations = [str(file_path.parent)] if file_path.name == "__init__.py" else None

    added_sys_path: str | None = None
    if file_path.parent.parent.name == "src":
        src_path = str(file_path.parent.parent)
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
            added_sys_path = src_path

    try:
        spec = importlib.util.spec_from_file_location(
            full_module_name,
            file_path,
            submodule_search_locations=search_locations,
        )

        if not spec or not spec.loader:
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[full_module_name] = module
        spec.loader.exec_module(module)

        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, expected_type) and obj is not expected_type:
                return obj
    except Exception:
        return None
    finally:
        if added_sys_path is not None and added_sys_path in sys.path:
            sys.path.remove(added_sys_path)

    return None
