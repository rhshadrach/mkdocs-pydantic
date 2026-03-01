from __future__ import annotations

import dataclasses
import os
from pathlib import Path

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File, Files


@dataclasses.dataclass
class PydanticEntry:
    class_path: str
    breadcrumbs: list[int]
    root: Node

    def add_files(self, files: Files, config: MkDocsConfig) -> None:
        self.root.add_files(files, config)


@dataclasses.dataclass
class Node:
    name: str
    path: Path
    markdown: str
    children: list[Node]
    _file: File | None = None

    @property
    def file(self) -> File:
        if self._file is None:
            raise ValueError("file has not been added yet.")
        return self._file

    def add_files(self, files: Files, config: MkDocsConfig) -> None:
        file = File(
            path=str(self.path),
            src_dir=config["docs_dir"],
            dest_dir=config["site_dir"],
            use_directory_urls=config["use_directory_urls"],
        )
        assert file.abs_src_path is not None
        base_path = Path(file.abs_src_path).parent
        os.makedirs(base_path, exist_ok=True)
        with open(file.abs_src_path, "w") as fh:
            fh.write(self.markdown)
        self._file = file
        files.append(self.file)
        for child in self.children:
            child.add_files(files, config)
