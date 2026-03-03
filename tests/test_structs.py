from __future__ import annotations

from pathlib import Path

import pytest
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.nav import Section
from mkdocs.structure.pages import Page

from mkdocs_pydantic.structs import Node, PydanticEntry


def make_config(tmp_path: Path) -> MkDocsConfig:
    docs_dir = tmp_path / "docs"
    site_dir = tmp_path / "site"
    docs_dir.mkdir()
    site_dir.mkdir()
    cfg = MkDocsConfig()
    cfg.load_dict(
        {"site_name": "test", "docs_dir": str(docs_dir), "site_dir": str(site_dir)}
    )
    errors, warnings = cfg.validate()
    assert not errors, errors
    return cfg


# ---- Node.file ----


class TestNodeFile:
    def test_raises_when_file_not_set(self) -> None:
        node = Node(name="test", path=Path("test.md"), markdown="# Test", children=[])
        with pytest.raises(ValueError, match="file has not been added"):
            _ = node.file


# ---- Node.add_files ----


class TestNodeAddFiles:
    def test_writes_markdown_and_sets_file(self, tmp_path: Path) -> None:
        config = make_config(tmp_path)
        node = Node(name="test", path=Path("test.md"), markdown="# Hello", children=[])
        files = Files([])
        node.add_files(files, config)

        assert node._file is not None
        assert node.file.src_path == "test.md"
        assert len(files) == 1

        # Check the file was written to disk
        assert node.file.abs_src_path is not None
        written = Path(node.file.abs_src_path).read_text()
        assert written == "# Hello"

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        config = make_config(tmp_path)
        node = Node(
            name="deep", path=Path("a/b/c/deep.md"), markdown="# Deep", children=[]
        )
        files = Files([])
        node.add_files(files, config)

        assert node.file.abs_src_path is not None
        assert Path(node.file.abs_src_path).exists()
        assert "a/b/c/deep.md" in node.file.src_path

    def test_recursive_with_children(self, tmp_path: Path) -> None:
        config = make_config(tmp_path)
        child = Node(
            name="child", path=Path("parent/child.md"), markdown="# Child", children=[]
        )
        parent = Node(
            name="parent",
            path=Path("parent/index.md"),
            markdown="# Parent",
            children=[child],
        )
        files = Files([])
        parent.add_files(files, config)

        assert len(files) == 2
        assert parent._file is not None
        assert child._file is not None


# ---- Node.make_children ----


class TestNodeMakeChildren:
    def test_returns_page_for_self_and_children(self, tmp_path: Path) -> None:
        config = make_config(tmp_path)
        child = Node(
            name="child", path=Path("parent/child.md"), markdown="# Child", children=[]
        )
        parent = Node(
            name="parent",
            path=Path("parent/index.md"),
            markdown="# Parent",
            children=[child],
        )
        files = Files([])
        parent.add_files(files, config)

        children = parent.make_children(config)
        assert len(children) == 2
        # First is the parent's own page
        assert isinstance(children[0], Page)
        assert children[0].title == "parent"
        # Second is the child page
        assert isinstance(children[1], Page)
        assert children[1].title == "child"

    def test_nested_child_becomes_section(self, tmp_path: Path) -> None:
        config = make_config(tmp_path)
        grandchild = Node(
            name="grandchild",
            path=Path("p/c/grandchild.md"),
            markdown="# GC",
            children=[],
        )
        child = Node(
            name="child",
            path=Path("p/c/index.md"),
            markdown="# Child",
            children=[grandchild],
        )
        parent = Node(
            name="parent",
            path=Path("p/index.md"),
            markdown="# Parent",
            children=[child],
        )
        files = Files([])
        parent.add_files(files, config)

        children = parent.make_children(config)
        assert len(children) == 2
        assert isinstance(children[0], Page)
        assert isinstance(children[1], Section)
        assert children[1].title == "child"


# ---- PydanticEntry.make_nav_object ----


class TestPydanticEntryMakeNavObject:
    def test_no_children_returns_page(self, tmp_path: Path) -> None:
        config = make_config(tmp_path)
        node = Node(name="leaf", path=Path("leaf.md"), markdown="# Leaf", children=[])
        files = Files([])
        node.add_files(files, config)

        entry = PydanticEntry(class_path="a.b.Leaf", breadcrumbs=[0], root=node)
        obj = entry.make_nav_object(config)
        assert isinstance(obj, Page)
        assert obj.title == "leaf"

    def test_with_children_returns_section(self, tmp_path: Path) -> None:
        config = make_config(tmp_path)
        child = Node(
            name="child", path=Path("parent/child.md"), markdown="# Child", children=[]
        )
        parent = Node(
            name="parent",
            path=Path("parent/index.md"),
            markdown="# Parent",
            children=[child],
        )
        files = Files([])
        parent.add_files(files, config)

        entry = PydanticEntry(class_path="a.b.Parent", breadcrumbs=[0], root=parent)
        obj = entry.make_nav_object(config)
        assert isinstance(obj, Section)
        assert obj.title == "parent"
        assert len(obj.children) == 2
