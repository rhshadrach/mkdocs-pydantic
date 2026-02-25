from __future__ import annotations

import os
from pathlib import Path

from mkdocs.plugins import BasePlugin
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.nav import Navigation, Section, Page
from mkdocs.structure.files import File

from mkdocs_pydantic.make_md import MakeMd

class MkdocsPydantic(BasePlugin):
    def __init__(self):
        self.pydantic_items: list[tuple[str, list[int | str]]] = []
        self.files: dict[tuple[int, ...], list[File]] = {}

    def on_nav(self, nav: Navigation, config: MkDocsConfig, files: Files) -> Navigation:
        for k, (class_path, breadcrumbs, int_breadcrumbs) in enumerate(self.pydantic_items):
            curr = nav.items
            for k, crumb in enumerate(int_breadcrumbs[:-1]):
                if isinstance(curr, Section):
                    curr = curr.children[crumb]
                else:
                    curr = curr[crumb]
            print(int_breadcrumbs, tuple(int_breadcrumbs))
            print(self.files.values())
            for file in self.files[tuple(int_breadcrumbs)]:
                if isinstance(curr, Section):
                    curr.children[int_breadcrumbs[-1]] = Page(title=f"Page {k}", file=file, config=config)
                else:
                    curr[int_breadcrumbs[-1]] = Page(title=f"Page {k}", file=file, config=config)
        return nav

    def on_files(self, files: Files, config: MkDocsConfig):
        self.pydantic_items = find_pydantic_items(config["nav"])
        for k, (class_path, breadcrumbs, int_breadcrumbs) in enumerate(self.pydantic_items):
            path = Path("/".join(e for e in breadcrumbs))
            make_md = MakeMd(class_path)
            self.files[tuple(int_breadcrumbs)] = make_md.extend_files(files, config, rel_path=path)
        return files


def find_pydantic_items(data, breadcrumbs=None, int_breadcrumbs=None):
    """
    Recursively finds all items starting with "pydantic:::" in nested lists and dictionaries.
    """
    found_items = []
    if breadcrumbs is None:
        breadcrumbs = []
    if int_breadcrumbs is None:
        int_breadcrumbs = []

    if isinstance(data, str):
        # Check if the string starts with the specific prefix
        if data.startswith("pydantic:::"):
            found_items.append((data[len("pydantic:::"):], breadcrumbs, int_breadcrumbs))
    elif isinstance(data, list):
        # Recurse into each item in the list
        for idx, item in enumerate(data):
            found_items.extend(find_pydantic_items(item, breadcrumbs, int_breadcrumbs + [idx]))
    elif isinstance(data, dict):
        # Recurse into each value in the dictionary
        for idx, (key, value) in enumerate(data.items()):
            found_items.extend(find_pydantic_items(value, breadcrumbs + [key], int_breadcrumbs))

    return found_items