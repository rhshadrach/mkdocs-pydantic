from __future__ import annotations

import dataclasses

from mkdocs.structure.files import File


@dataclasses.dataclass
class PydanticEntry:
    class_path: str
    breadcrumbs: list[int]
    root: Node


@dataclasses.dataclass
class Node:
    name: str
    file: File
    children: list[Node]
