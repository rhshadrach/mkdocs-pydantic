from __future__ import annotations

import io
import pprint
from pathlib import Path
from typing import Any, ForwardRef

from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from pydantic_settings import BaseSettings

from mkdocs_pydantic.structs import Node


def run(
    model: type[BaseSettings],
    rel_path: Path,
    name: str | None,
    prefix: str | None = None,
) -> Node:
    if name is None:
        name = model.__name__
    if prefix is None:
        prefix = model.__name__

    submodels = extract_submodels(model)
    if len(submodels) > 0:
        rel_path /= name

    markdown = make_markdown(model, name, prefix)
    filename = f"{model.__name__}.md" if len(submodels) == 0 else "index.md"
    model_file = Node(
        name=name, path=rel_path / filename, markdown=markdown, children=[]
    )

    for name, submodel in submodels:
        model_file.children.append(
            run(submodel, rel_path, name=None, prefix=prefix + f".{name}")
        )
    return model_file


def make_markdown(klass: type[BaseSettings], name: str, prefix: str) -> str:
    result = f"# {name}\n\n"
    for field_name, field in klass.model_fields.items():
        result += f"{markdown_field(field_name, field, prefix=prefix, level=2)}---\n\n"
    return result


def markdown_field(name: str, field: FieldInfo, prefix: str, level: int) -> str:
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
        result += f"- Default: {formatted_default(field.default)}\n\n"
    return result


def formatted_default(obj: Any) -> str:
    buf = io.StringIO()
    pprint.pprint(obj, stream=buf)  # noqa: T203
    pretty_default = buf.getvalue().strip()
    if "\n" in pretty_default:
        result = f"\n```\n{pretty_default}\n```\n"
    else:
        result = f"`{pretty_default}`"
    return result


def extract_submodels(
    model: type[BaseSettings],
) -> list[tuple[str, type[BaseSettings]]]:
    result: list[tuple[str, type[BaseSettings]]] = []
    for name, field in model.model_fields.items():
        if isinstance(field.annotation, ForwardRef):
            # TODO: Add test for this case.
            raise ValueError(
                f"{model.__name__} contains a ForwardRef on the field {name}."
                " The model must be rebuilt."
            )
        if field.annotation is None:
            continue
        try:
            if not issubclass(field.annotation, BaseSettings):
                continue
        except TypeError:
            # issubclass raises on things that aren't classes.
            continue
        result.append((name, field.annotation))
    return result
