from __future__ import annotations

import dataclasses

from mkdocs.structure.files import File


@dataclasses.dataclass
class PydanticEntry:
    class_path: str
    breadcrumbs: list[str]
    int_breadcrumbs: list[int]
    name: str
    file: File
    model_file: ModelFile


@dataclasses.dataclass
class ModelFile:
    name: str
    file: File
    children: list[ModelFile]
