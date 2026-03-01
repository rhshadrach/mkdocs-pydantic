from __future__ import annotations

import io
import pprint
from pathlib import Path
from typing import Any, ForwardRef

from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from pydantic_settings import BaseSettings

from mkdocs_pydantic.structs import Node

HTML_HR = '<hr stype="height:3px;border-width:0;color:gray;background-color:gray">'


class MakeMd:
    def __init__(self, fully_qualified_name: str) -> None:
        self.fully_qualified_name = fully_qualified_name

    @staticmethod
    def formatted_default(obj: Any) -> str:
        buf = io.StringIO()
        pprint.pprint(obj, stream=buf)  # noqa: T203
        pretty_default = buf.getvalue().strip()
        if "\n" in pretty_default:
            result = f"\n```\n{pretty_default}\n```\n"
        else:
            result = f"`{pretty_default}`"
        return result

    def markdown_property(self, name: str) -> str:
        result = (
            f"::: {self.fully_qualified_name}.{name}\n"
            f"    handler: python\n"
            f"    options:\n"
            f"      show_root_heading: true\n"
            f"      show_root_full_path: false\n"
            f"      show_source: false\n"
            f"      show_signature: false\n"
            f"      separate_signature: false\n"
            f"      heading_level: 3\n"
        )
        return result

    def markdown_field(
        self, name: str, field: FieldInfo, prefix: str, level: int = 3
    ) -> str:
        result = ""
        toc_label = f'{{ data-toc-label="{name}" }}'
        result += f"{'#' * level} {prefix}.{name} {toc_label}\n\n"

        if field.title is None:
            result += f"{field.title}\n\n"
        if field.description is not None:
            result += f"{field.description}\n\n"

        annotation = field.annotation
        assert annotation is not None
        if str(annotation).startswith("<class "):
            annotation_str = annotation.__name__
        else:
            annotation_str = str(annotation).replace("typing.", "")
        result += f"- Type: {annotation_str}\n"

        if field.default is PydanticUndefined:
            result += "- Required\n\n"
        else:
            result += f"- Default: {self.formatted_default(field.default)}\n\n"
        return result

    def make_markdown(self, klass: type[BaseSettings], prefix: str) -> str:
        name = klass.__name__
        # TODO: Get title from klass?
        title = name
        result = f"# {title}\n\n"
        for name, field in klass.model_fields.items():
            result += (
                f"{self.markdown_field(name, field, prefix=prefix, level=2)}---\n\n"
            )
        return result

    def sub_models(self, model: type[BaseSettings]) -> list[tuple[str, FieldInfo]]:
        result: list[tuple[str, FieldInfo]] = []
        for name, field in model.model_fields.items():
            if isinstance(field.annotation, ForwardRef):
                # TODO: Add test for this case.
                raise ValueError(
                    f"{model.__name__} contains a ForwardRef on the field {name}."
                    " The model must be rebuilt."
                )
            if field.annotation is None:
                # TODO: Why skip?
                continue
            try:
                if not issubclass(field.annotation, BaseSettings):
                    continue
            except TypeError:
                # issubclass raises on things that aren't classes.
                continue
            result.append((name, field))
        return result

    def extend_files(self, model: type[BaseSettings], rel_path: Path) -> Node:
        result = self.extend_files_sub(model, rel_path, prefix=model.__name__)
        return result

    def extend_files_sub(
        self, model: type[BaseSettings], rel_path: Path, prefix: str
    ) -> Node:
        if len(self.sub_models(model)) > 0:
            rel_path /= model.__name__
        markdown = self.make_markdown(model, prefix)
        name = model.__name__ if len(self.sub_models(model)) == 0 else "index"
        model_file = Node(
            name=model.__name__,
            path=rel_path / f"{name}.md",
            markdown=markdown,
            children=[],
        )

        for name, field in self.sub_models(model):
            assert field.annotation is not None
            assert issubclass(field.annotation, BaseSettings)
            model_file.children.append(
                self.extend_files_sub(field.annotation, rel_path, prefix + f".{name}")
            )
        return model_file
