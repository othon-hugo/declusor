import sys
from pathlib import Path

from declusor.util import plugin


class SampleBase:
    """Base class for plugin discovery tests."""


class SamplePlugin(SampleBase):
    """Concrete sample plugin subclass."""


class TestFindPluginEntry:
    """Verify find_plugin_entry layout heuristics and candidate precedence."""

    def test_find_plugin_entry__src_layout_init__returns_init_path(self, tmp_path: Path) -> None:
        """Verify find_plugin_entry discovers src/<plugin_name>/__init__.py."""

        plugin_dir = tmp_path / "my_plugin"
        target = plugin_dir / "src" / "my_plugin" / "__init__.py"
        target.parent.mkdir(parents=True)
        target.write_text("# entry", encoding="utf-8")

        assert plugin.find_plugin_entry(plugin_dir) == target

    def test_find_plugin_entry__src_layout_plugin_py__returns_plugin_py_path(self, tmp_path: Path) -> None:
        """Verify find_plugin_entry discovers src/<plugin_name>/plugin.py."""

        plugin_dir = tmp_path / "my_plugin"
        target = plugin_dir / "src" / "my_plugin" / "plugin.py"
        target.parent.mkdir(parents=True)
        target.write_text("# entry", encoding="utf-8")

        assert plugin.find_plugin_entry(plugin_dir) == target

    def test_find_plugin_entry__src_layout_differing_package_name__finds_inner_package(self, tmp_path: Path) -> None:
        """Verify find_plugin_entry discovers package inside src even if package name differs from dir name."""

        plugin_dir = tmp_path / "outer_repo"
        target = plugin_dir / "src" / "declusor_custom_pkg" / "__init__.py"
        target.parent.mkdir(parents=True)
        target.write_text("# entry", encoding="utf-8")

        assert plugin.find_plugin_entry(plugin_dir) == target

    def test_find_plugin_entry__src_layout_ignores_hidden_and_private_dirs__skips_invalid_dirs(self, tmp_path: Path) -> None:
        """Verify find_plugin_entry ignores hidden (.git) and private (__pycache__) directories in src."""

        plugin_dir = tmp_path / "repo"
        src = plugin_dir / "src"
        (src / ".git").mkdir(parents=True)
        (src / ".git" / "plugin.py").write_text("# hidden", encoding="utf-8")
        (src / "__pycache__").mkdir(parents=True)
        (src / "__pycache__" / "plugin.py").write_text("# cache", encoding="utf-8")

        valid_entry = src / "real_pkg" / "plugin.py"
        valid_entry.parent.mkdir(parents=True)
        valid_entry.write_text("# valid", encoding="utf-8")

        assert plugin.find_plugin_entry(plugin_dir) == valid_entry

    def test_find_plugin_entry__src_layout_ignores_plain_files_in_src__skips_files(self, tmp_path: Path) -> None:
        """Verify plain files located directly inside src/ are ignored during candidate collection."""

        plugin_dir = tmp_path / "repo"
        src = plugin_dir / "src"
        src.mkdir(parents=True)
        (src / "README.md").write_text("# Readme", encoding="utf-8")
        (src / "setup.py").write_text("# setup", encoding="utf-8")

        assert plugin.find_plugin_entry(plugin_dir) is None

    def test_find_plugin_entry__flat_layout_init__returns_init_path(self, tmp_path: Path) -> None:
        """Verify find_plugin_entry discovers __init__.py directly under plugin_dir."""

        plugin_dir = tmp_path / "flat_plugin"
        plugin_dir.mkdir()
        target = plugin_dir / "__init__.py"
        target.write_text("# entry", encoding="utf-8")

        assert plugin.find_plugin_entry(plugin_dir) == target

    def test_find_plugin_entry__flat_layout_plugin_py__returns_plugin_py_path(self, tmp_path: Path) -> None:
        """Verify find_plugin_entry discovers plugin.py directly under plugin_dir."""

        plugin_dir = tmp_path / "flat_plugin"
        plugin_dir.mkdir()
        target = plugin_dir / "plugin.py"
        target.write_text("# entry", encoding="utf-8")

        assert plugin.find_plugin_entry(plugin_dir) == target

    def test_find_plugin_entry__precedence__prefers_src_layout_over_flat_layout(self, tmp_path: Path) -> None:
        """Verify src-layout entry takes precedence over flat root entry files."""

        plugin_dir = tmp_path / "my_plugin"
        src_entry = plugin_dir / "src" / "my_plugin" / "__init__.py"
        src_entry.parent.mkdir(parents=True)
        src_entry.write_text("# src entry", encoding="utf-8")

        flat_entry = plugin_dir / "__init__.py"
        flat_entry.write_text("# flat entry", encoding="utf-8")

        assert plugin.find_plugin_entry(plugin_dir) == src_entry

    def test_find_plugin_entry__precedence__prefers_init_over_plugin_py(self, tmp_path: Path) -> None:
        """Verify __init__.py takes precedence over plugin.py in the same directory."""

        plugin_dir = tmp_path / "my_plugin"
        plugin_dir.mkdir()
        init_entry = plugin_dir / "__init__.py"
        init_entry.write_text("# init", encoding="utf-8")
        plugin_entry = plugin_dir / "plugin.py"
        plugin_entry.write_text("# plugin", encoding="utf-8")

        assert plugin.find_plugin_entry(plugin_dir) == init_entry

    def test_find_plugin_entry__empty_directory__returns_none(self, tmp_path: Path) -> None:
        """Verify find_plugin_entry returns None when directory contains no entry files."""

        empty_dir = tmp_path / "empty_dir"
        empty_dir.mkdir()

        assert plugin.find_plugin_entry(empty_dir) is None

    def test_find_plugin_entry__nonexistent_directory__returns_none(self, tmp_path: Path) -> None:
        """Verify find_plugin_entry returns None when target directory does not exist."""

        assert plugin.find_plugin_entry(tmp_path / "does_not_exist") is None


class TestImportPluginFromFile:
    """Verify dynamic module execution and class discovery via importlib."""

    def test_import_plugin_from_file__valid_subclass__returns_subclass(self, tmp_path: Path) -> None:
        """Verify import_plugin_from_file dynamically loads and returns the expected subclass."""

        file_path = tmp_path / "plugin.py"
        file_path.write_text(
            "from tests.unit.util.test_plugins import SampleBase\nclass DynamicPlugin(SampleBase):\n    pass\n",
            encoding="utf-8",
        )

        result = plugin.import_plugin_from_file("single_test", file_path, SampleBase)

        assert result is not None
        assert issubclass(result, SampleBase)
        assert result.__name__ == "DynamicPlugin"

    def test_import_plugin_from_file__multiple_classes__returns_matching_subclass(self, tmp_path: Path) -> None:
        """Verify import_plugin_from_file selects the class matching expected_type among multiple classes."""

        file_path = tmp_path / "multi.py"
        file_path.write_text(
            "from tests.unit.util.test_plugins import SampleBase\n"
            "class Helper:\n"
            "    pass\n"
            "class ConcretePlugin(SampleBase):\n"
            "    pass\n"
            "class Unrelated:\n"
            "    pass\n",
            encoding="utf-8",
        )

        result = plugin.import_plugin_from_file("multi_test", file_path, SampleBase)

        assert result is not None
        assert result.__name__ == "ConcretePlugin"

    def test_import_plugin_from_file__base_class_itself__ignores_exact_base_type(self, tmp_path: Path) -> None:
        """Verify import_plugin_from_file ignores the base class itself if defined or imported in module."""

        file_path = tmp_path / "base_only.py"
        file_path.write_text(
            "from tests.unit.util.test_plugins import SampleBase\n",
            encoding="utf-8",
        )

        result = plugin.import_plugin_from_file("base_only", file_path, SampleBase)

        assert result is None

    def test_import_plugin_from_file__no_subclass_defined__returns_none(self, tmp_path: Path) -> None:
        """Verify import_plugin_from_file returns None when module defines no subclass of expected_type."""

        file_path = tmp_path / "unrelated.py"
        file_path.write_text(
            "class CompletelyUnrelated:\n    pass\n",
            encoding="utf-8",
        )

        result = plugin.import_plugin_from_file("unrelated_test", file_path, SampleBase)

        assert result is None

    def test_import_plugin_from_file__package_init_with_relative_import__resolves_submodules(self, tmp_path: Path) -> None:
        """Verify package __init__.py correctly sets submodule_search_locations and resolves relative imports."""

        pkg_dir = tmp_path / "pkg"
        pkg_dir.mkdir()
        (pkg_dir / "helper.py").write_text(
            "from tests.unit.util.test_plugins import SampleBase\nclass InternalPlugin(SampleBase):\n    pass\n",
            encoding="utf-8",
        )
        init_file = pkg_dir / "__init__.py"
        init_file.write_text(
            "from .helper import InternalPlugin\n",
            encoding="utf-8",
        )

        result = plugin.import_plugin_from_file("relative_pkg", init_file, SampleBase)

        assert result is not None
        assert result.__name__ == "InternalPlugin"

    def test_import_plugin_from_file__src_layout__temporarily_adds_and_removes_src_from_sys_path(self, tmp_path: Path) -> None:
        """Verify src-layout modules add src to sys.path during execution and clean it up in finally."""

        src_dir = tmp_path / "src"
        pkg_dir = src_dir / "my_pkg"
        pkg_dir.mkdir(parents=True)

        init_file = pkg_dir / "__init__.py"
        init_file.write_text(
            "import sys\n"
            "from tests.unit.util.test_plugins import SampleBase\n"
            "src_path_present = any('src' in p for p in sys.path)\n"
            "class SrcPlugin(SampleBase):\n"
            "    is_src_present = src_path_present\n",
            encoding="utf-8",
        )

        src_str = str(src_dir)
        assert src_str not in sys.path

        result = plugin.import_plugin_from_file("src_sys_path_test", init_file, SampleBase)

        assert result is not None
        assert getattr(result, "is_src_present", False) is True
        assert src_str not in sys.path

    def test_import_plugin_from_file__src_already_in_sys_path__preserves_existing_sys_path(self, tmp_path: Path) -> None:
        """Verify if src is already present in sys.path, it is not removed in finally."""

        src_dir = tmp_path / "src"
        pkg_dir = src_dir / "existing_pkg"
        pkg_dir.mkdir(parents=True)
        init_file = pkg_dir / "__init__.py"
        init_file.write_text(
            "from tests.unit.util.test_plugins import SampleBase\nclass ExistingPlugin(SampleBase):\n    pass\n",
            encoding="utf-8",
        )

        src_str = str(src_dir)
        sys.path.insert(0, src_str)

        try:
            result = plugin.import_plugin_from_file("already_in_path", init_file, SampleBase)
            assert result is not None
            assert src_str in sys.path
        finally:
            if src_str in sys.path:
                sys.path.remove(src_str)

    def test_import_plugin_from_file__nonexistent_file__returns_none(self, tmp_path: Path) -> None:
        """Verify import_plugin_from_file returns None when target file does not exist."""

        assert plugin.import_plugin_from_file("missing", tmp_path / "nonexistent.py", SampleBase) is None

    def test_import_plugin_from_file__syntax_error__returns_none_defensively(self, tmp_path: Path) -> None:
        """Verify syntax errors in the target file are caught and return None."""

        bad_file = tmp_path / "bad_syntax.py"
        bad_file.write_text("invalid python code ??? = 123", encoding="utf-8")

        assert plugin.import_plugin_from_file("syntax_err", bad_file, SampleBase) is None

    def test_import_plugin_from_file__runtime_exception_during_exec__returns_none_and_restores_sys_path(self, tmp_path: Path) -> None:
        """Verify exceptions during module execution return None and safely restore sys.path."""

        src_dir = tmp_path / "src"
        pkg_dir = src_dir / "crash_pkg"
        pkg_dir.mkdir(parents=True)
        bad_file = pkg_dir / "__init__.py"
        bad_file.write_text("raise RuntimeError('intentional load crash')", encoding="utf-8")

        src_str = str(src_dir)
        assert src_str not in sys.path

        result = plugin.import_plugin_from_file("runtime_crash", bad_file, SampleBase)

        assert result is None
        assert src_str not in sys.path
