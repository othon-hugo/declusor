from pathlib import Path

from declusor import util


class DummyBase:
    pass


class DummyChild(DummyBase):
    pass


def test_find_plugin_entry_flat_layout(tmp_path: Path) -> None:
    """find_plugin_entry finds __init__.py or plugin.py in flat directories."""

    plugin_dir = tmp_path / "flat_plugin"
    plugin_dir.mkdir()
    entry = plugin_dir / "plugin.py"
    entry.write_text("# entry", encoding="utf-8")

    found = util.find_plugin_entry(plugin_dir)
    assert found == entry


def test_find_plugin_entry_src_layout(tmp_path: Path) -> None:
    """find_plugin_entry finds package entry files in src/<plugin_name>/ layout."""

    plugin_dir = tmp_path / "src_plugin"
    src_pkg = plugin_dir / "src" / "src_plugin"
    src_pkg.mkdir(parents=True)
    entry = src_pkg / "__init__.py"
    entry.write_text("# entry", encoding="utf-8")

    found = util.find_plugin_entry(plugin_dir)
    assert found == entry


def test_find_plugin_entry_nonexistent_or_empty(tmp_path: Path) -> None:
    """find_plugin_entry returns None when no valid Python entry file exists."""

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    assert util.find_plugin_entry(empty_dir) is None
    assert util.find_plugin_entry(tmp_path / "nonexistent") is None


def test_import_plugin_from_file_success(tmp_path: Path) -> None:
    """import_plugin_from_file imports a valid subclass of expected_type."""

    script = tmp_path / "custom.py"
    script.write_text(
        "from tests.unit.util.test_plugins import DummyBase\nclass ConcretePlugin(DummyBase):\n    pass\n",
        encoding="utf-8",
    )

    loaded = util.import_plugin_from_file("test_mod", script, DummyBase)
    assert loaded is not None
    assert issubclass(loaded, DummyBase)
    assert loaded.__name__ == "ConcretePlugin"


def test_import_plugin_from_file_no_matching_class(tmp_path: Path) -> None:
    """import_plugin_from_file returns None when no subclass of expected_type is defined."""

    script = tmp_path / "unrelated.py"
    script.write_text("class Unrelated:\n    pass\n", encoding="utf-8")

    loaded = util.import_plugin_from_file("unrelated_mod", script, DummyBase)
    assert loaded is None


def test_import_plugin_from_file_syntax_error(tmp_path: Path) -> None:
    """import_plugin_from_file returns None and handles syntax errors defensively."""

    script = tmp_path / "invalid.py"
    script.write_text("this is invalid python syntax !!!", encoding="utf-8")

    loaded = util.import_plugin_from_file("invalid_mod", script, DummyBase)
    assert loaded is None
