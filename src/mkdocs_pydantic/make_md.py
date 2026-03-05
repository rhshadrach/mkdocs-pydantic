from __future__ import annotations

import io
import pprint
from pathlib import Path
from typing import Any, ForwardRef

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from mkdocs_pydantic.structs import Node


def run(
    model: type[BaseModel], rel_path: Path, name: str | None, prefix: str | None = None
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


def make_markdown(klass: type[BaseModel], name: str, prefix: str) -> str:
    result = f"# {name}\n\n"
    for field_name, field in klass.model_fields.items():
        result += f"{markdown_field(field_name, field, prefix=prefix, level=2)}---\n\n"
    return result


def markdown_field(name: str, field: FieldInfo, prefix: str, level: int) -> str:
    result = ""
    toc_label = f'{{ data-toc-label="{name}" }}'
    result += f"{'#' * level} {prefix}.{name} {toc_label}\n\n"

    if field.deprecated:
        result += "**Deprecated**\n\n"

    if field.title is not None:
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
        result += "- Required\n"
    else:
        result += f"- Default: {formatted_default(field.default)}\n"

    # Aliases
    if field.alias is not None:
        result += f"- Alias: `{field.alias}`\n"
    if field.validation_alias is not None:
        result += f"- Validation alias: `{field.validation_alias}`\n"
    if field.serialization_alias is not None:
        result += f"- Serialization alias: `{field.serialization_alias}`\n"

    # Numeric constraints
    constraints = _format_constraints(field)
    if constraints:
        result += f"- Constraints: {constraints}\n"

    # String/collection constraints
    if field.metadata:
        min_len = _get_metadata(field, "min_length")
        max_len = _get_metadata(field, "max_length")
        pattern = _get_metadata(field, "pattern")
        if min_len is not None:
            result += f"- Min length: {min_len}\n"
        if max_len is not None:
            result += f"- Max length: {max_len}\n"
        if pattern is not None:
            result += f"- Pattern: `{pattern}`\n"

    # Other attributes
    if field.frozen:
        result += "- Frozen (immutable)\n"
    if field.exclude:
        result += "- Excluded from serialization\n"

    # Examples
    if field.examples:
        result += f"- Examples: {', '.join(f'`{e}`' for e in field.examples)}\n"

    # JSON schema extra
    if field.json_schema_extra is not None:
        if isinstance(field.json_schema_extra, dict):
            for key, value in field.json_schema_extra.items():
                result += f"- {key}: `{value}`\n"

    result += "\n"
    return result


def _format_constraints(field: FieldInfo) -> str:
    parts: list[str] = []
    ge = _get_metadata(field, "ge")
    gt = _get_metadata(field, "gt")
    le = _get_metadata(field, "le")
    lt = _get_metadata(field, "lt")
    multiple_of = _get_metadata(field, "multiple_of")
    if gt is not None:
        parts.append(f"> {gt}")
    if ge is not None:
        parts.append(f">= {ge}")
    if lt is not None:
        parts.append(f"< {lt}")
    if le is not None:
        parts.append(f"<= {le}")
    if multiple_of is not None:
        parts.append(f"multiple of {multiple_of}")
    return ", ".join(parts)


def _get_metadata(field: FieldInfo, attr: str) -> Any:
    for item in field.metadata:
        if hasattr(item, attr):
            return getattr(item, attr)
    return None


def formatted_default(obj: Any) -> str:
    buf = io.StringIO()
    pprint.pprint(obj, stream=buf)  # noqa: T203
    pretty_default = buf.getvalue().strip()
    if "\n" in pretty_default:
        result = f"\n```\n{pretty_default}\n```\n"
    else:
        result = f"`{pretty_default}`"
    return result


def extract_submodels(model: type[BaseModel]) -> list[tuple[str, type[BaseModel]]]:
    result: list[tuple[str, type[BaseModel]]] = []
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
            if not issubclass(field.annotation, BaseModel):
                continue
        except TypeError:
            # issubclass raises on things that aren't classes.
            continue
        result.append((name, field.annotation))
    return result
