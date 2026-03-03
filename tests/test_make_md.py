from __future__ import annotations

from pathlib import Path
from typing import ForwardRef

import pytest
from pydantic import BaseModel, Field
from pydantic_core import PydanticUndefined

from mkdocs_pydantic.make_md import (
    extract_submodels,
    formatted_default,
    make_markdown,
    markdown_field,
    run,
)

# ---- Test models ----


class FlatModel(BaseModel):
    name: str = Field(description="The name")
    count: int = Field(default=0, description="A count")


class Inner(BaseModel):
    value: int = Field(description="Inner value")


class Nested(BaseModel):
    label: str = Field(description="A label")
    inner: Inner = Field(description="Nested inner model")


class GenericFields(BaseModel):
    items: list[int] = Field(default=[], description="A list of ints")
    name: str = Field(description="A name")


class Level3(BaseModel):
    z: int = Field(description="z")


class Level2(BaseModel):
    y: str = Field(description="y")
    level3: Level3 = Field(description="level 3")


Level2.model_rebuild()


class Level1(BaseModel):
    x: int = Field(description="x")
    level2: Level2 = Field(description="level 2")


Level1.model_rebuild()


# ---- extract_submodels ----


class TestExtractSubmodels:
    def test_flat_model_no_submodels(self) -> None:
        result = extract_submodels(FlatModel)
        assert result == []

    def test_nested_model_has_submodel(self) -> None:
        result = extract_submodels(Nested)
        assert len(result) == 1
        assert result[0] == ("inner", Inner)

    def test_generic_fields_skipped(self) -> None:
        result = extract_submodels(GenericFields)
        assert result == []

    def test_forward_ref_raises(self) -> None:
        class BadModel(BaseModel):
            ref: int = 0

        # Manually inject a ForwardRef annotation to simulate an unresolved ref
        BadModel.model_fields["ref"].annotation = ForwardRef("SomeModel")  # type: ignore[assignment]
        with pytest.raises(ValueError, match="ForwardRef"):
            extract_submodels(BadModel)


# ---- formatted_default ----


class TestFormattedDefault:
    def test_single_line_backtick_wrapped(self) -> None:
        result = formatted_default(42)
        assert result == "`42`"

    def test_string_default(self) -> None:
        result = formatted_default("hello")
        assert result == "`'hello'`"

    def test_multi_line_code_block(self) -> None:
        long_dict = {f"key_{i}": i for i in range(20)}
        result = formatted_default(long_dict)
        assert result.startswith("\n```\n")
        assert result.endswith("\n```\n")

    def test_list_default(self) -> None:
        result = formatted_default([1, 2, 3])
        assert result == "`[1, 2, 3]`"


# ---- markdown_field ----


class TestMarkdownField:
    def test_heading_with_toc_label(self) -> None:
        field = FlatModel.model_fields["name"]
        result = markdown_field("name", field, prefix="FlatModel", level=2)
        assert '## FlatModel.name { data-toc-label="name" }' in result

    def test_description_included(self) -> None:
        field = FlatModel.model_fields["name"]
        result = markdown_field("name", field, prefix="FlatModel", level=2)
        assert "The name" in result

    def test_plain_class_type_annotation(self) -> None:
        field = FlatModel.model_fields["name"]
        result = markdown_field("name", field, prefix="FlatModel", level=2)
        assert "- Type: str\n" in result

    def test_generic_type_annotation(self) -> None:
        field = GenericFields.model_fields["items"]
        result = markdown_field("items", field, prefix="GenericFields", level=2)
        assert "- Type: list[int]\n" in result

    def test_required_field(self) -> None:
        field = FlatModel.model_fields["name"]
        assert field.default is PydanticUndefined
        result = markdown_field("name", field, prefix="FlatModel", level=2)
        assert "- Required\n" in result

    def test_default_field(self) -> None:
        field = FlatModel.model_fields["count"]
        result = markdown_field("count", field, prefix="FlatModel", level=2)
        assert "- Default: `0`\n" in result


# ---- make_markdown ----


class TestMakeMarkdown:
    def test_generates_heading_and_fields(self) -> None:
        result = make_markdown(FlatModel, name="FlatModel", prefix="FlatModel")
        assert result.startswith("# FlatModel\n\n")
        assert "FlatModel.name" in result
        assert "FlatModel.count" in result
        assert "---" in result


# ---- run ----


class TestRun:
    def test_flat_model_single_node(self) -> None:
        node = run(FlatModel, rel_path=Path("."), name=None)
        assert node.name == "FlatModel"
        assert node.path == Path("FlatModel.md")
        assert len(node.children) == 0
        assert "# FlatModel" in node.markdown

    def test_nested_model_index_with_children(self) -> None:
        node = run(Nested, rel_path=Path("."), name=None)
        assert node.name == "Nested"
        assert node.path == Path("Nested/index.md")
        assert len(node.children) == 1
        child = node.children[0]
        assert child.name == "Inner"
        assert child.path == Path("Nested/Inner.md")
        assert len(child.children) == 0

    def test_custom_name(self) -> None:
        node = run(FlatModel, rel_path=Path("."), name="CustomName")
        assert node.name == "CustomName"
        # Filename uses model.__name__, not the name parameter
        assert node.path == Path("FlatModel.md")

    def test_custom_prefix(self) -> None:
        node = run(FlatModel, rel_path=Path("."), name=None, prefix="MyPrefix")
        assert "MyPrefix.name" in node.markdown
        assert "MyPrefix.count" in node.markdown

    def test_three_level_nesting(self) -> None:
        node = run(Level1, rel_path=Path("."), name=None)
        assert node.name == "Level1"
        assert node.path == Path("Level1/index.md")
        assert len(node.children) == 1

        l2 = node.children[0]
        assert l2.name == "Level2"
        assert l2.path == Path("Level1/Level2/index.md")
        assert len(l2.children) == 1

        l3 = l2.children[0]
        assert l3.name == "Level3"
        assert l3.path == Path("Level1/Level2/Level3.md")
        assert len(l3.children) == 0

    def test_rel_path_applied(self) -> None:
        node = run(FlatModel, rel_path=Path("docs/models"), name=None)
        assert node.path == Path("docs/models/FlatModel.md")
