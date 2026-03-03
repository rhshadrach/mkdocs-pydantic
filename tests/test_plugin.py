from __future__ import annotations

import pytest
from pydantic import BaseModel

from mkdocs_pydantic.plugin import find_pydantic_entries, import_class_from_string

# ---- import_class_from_string ----


class TestImportClassFromString:
    def test_valid_import(self) -> None:
        cls = import_class_from_string("mkdocs_pydantic_examples.single.SingleLevel")
        assert issubclass(cls, BaseModel)
        assert cls.__name__ == "SingleLevel"

    def test_no_dot_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="fully qualified"):
            import_class_from_string("NoDotHere")

    def test_nonexistent_module_raises(self) -> None:
        with pytest.raises(ModuleNotFoundError):
            import_class_from_string("nonexistent.module.MyClass")

    def test_nonexistent_class_raises(self) -> None:
        with pytest.raises(AttributeError):
            import_class_from_string("mkdocs_pydantic_examples.single.Nope")

    def test_non_basemodel_raises(self) -> None:
        with pytest.raises(AssertionError):
            import_class_from_string("pathlib.Path")


# ---- find_pydantic_entries ----


class TestFindPydanticEntries:
    def test_single_pydantic_entry(self) -> None:
        nav = ["pydantic:::mkdocs_pydantic_examples.single.SingleLevel"]
        entries = find_pydantic_entries(nav)
        assert len(entries) == 1
        assert entries[0].class_path == "mkdocs_pydantic_examples.single.SingleLevel"

    def test_multiple_entries(self) -> None:
        nav = [
            "pydantic:::mkdocs_pydantic_examples.single.SingleLevel",
            "pydantic:::mkdocs_pydantic_examples.two_levels.TwoLevels",
        ]
        entries = find_pydantic_entries(nav)
        assert len(entries) == 2

    def test_non_pydantic_strings_skipped(self) -> None:
        nav = ["index.md", "about.md"]
        entries = find_pydantic_entries(nav)
        assert entries == []

    def test_empty_list(self) -> None:
        entries = find_pydantic_entries([])
        assert entries == []

    def test_dict_entry_with_alias(self) -> None:
        nav = [{"MyAlias": "pydantic:::mkdocs_pydantic_examples.single.SingleLevel"}]
        entries = find_pydantic_entries(nav)
        assert len(entries) == 1
        assert entries[0].root.name == "MyAlias"

    def test_breadcrumbs_track_indices(self) -> None:
        nav = ["index.md", "pydantic:::mkdocs_pydantic_examples.single.SingleLevel"]
        entries = find_pydantic_entries(nav)
        assert len(entries) == 1
        assert entries[0].breadcrumbs == [1]

    def test_dict_keys_become_path_segments(self) -> None:
        # Nested dicts create path segments: Outer/Inner
        nav = [
            {
                "Outer": {
                    "Inner": "pydantic:::mkdocs_pydantic_examples.single.SingleLevel"
                }
            }
        ]
        entries = find_pydantic_entries(nav)
        assert len(entries) == 1
        # The outer dict key becomes a path segment via path.parent
        root_path = entries[0].root.path
        assert "Outer" in str(root_path)
        # Inner becomes the alias/name
        assert entries[0].root.name == "Inner"
