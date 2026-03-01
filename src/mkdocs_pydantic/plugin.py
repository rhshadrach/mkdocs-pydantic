from __future__ import annotations

from pathlib import Path

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files
from mkdocs.structure.nav import Navigation, Page, Section, StructureItem

from mkdocs_pydantic.make_md import MakeMd
from mkdocs_pydantic.structs import ModelFile, PydanticEntry


class MkdocsPydantic(BasePlugin):
    def __init__(self):
        self.pydantic_entries: list[PydanticEntry] = []

    def on_nav(self, nav: Navigation, config: MkDocsConfig, files: Files) -> Navigation:
        for pydantic_entry in self.pydantic_entries:
            curr = nav.items
            for crumb in pydantic_entry.int_breadcrumbs[:-1]:
                if isinstance(curr, Section):
                    curr = curr.children[crumb]
                else:
                    curr = curr[crumb]

            obj: Page | Section
            if len(pydantic_entry.model_file.children) == 0:
                obj = Page(
                    title=pydantic_entry.name, file=pydantic_entry.file, config=config
                )
            else:
                children = make_section(
                    model_file=pydantic_entry.model_file, config=config
                )
                obj = Section(title=pydantic_entry.name, children=children)

            if isinstance(curr, Section):
                curr.children[pydantic_entry.int_breadcrumbs[-1]] = obj
            else:
                curr[pydantic_entry.int_breadcrumbs[-1]] = obj
        print(nav)  # noqa: T201
        return nav

    def on_files(self, files: Files, config: MkDocsConfig):
        self.pydantic_entries = find_pydantic_items(config["nav"], files, config)
        return files


def make_section(model_file: ModelFile, config) -> list[StructureItem]:
    result = [Page(title=model_file.name, file=model_file.file, config=config)]
    for child in model_file.children:
        if len(child.children) == 0:
            obj = Page(title=child.name, file=child.file, config=config)
        else:
            children = make_section(model_file=child, config=config)
            obj = Section(title=child.name, children=children)
        result.append(obj)
    return result


def find_pydantic_items(data, files, config, breadcrumbs=None, int_breadcrumbs=None):
    pydantic_entries = []
    if breadcrumbs is None:
        breadcrumbs = []
    if int_breadcrumbs is None:
        int_breadcrumbs = []

    if isinstance(data, list):
        # Recurse into each item in the list
        for idx, item in enumerate(data):
            pydantic_entries.extend(
                find_pydantic_items(
                    item, files, config, breadcrumbs, [*int_breadcrumbs, idx]
                )
            )
    elif isinstance(data, dict):
        # Recurse into each value in the dictionary
        for key, value in data.items():
            pydantic_entries.extend(
                find_pydantic_items(
                    value, files, config, [*breadcrumbs, key], int_breadcrumbs
                )
            )
    elif isinstance(data, str) and data.startswith("pydantic:::"):
        class_path = data[len("pydantic:::") :]
        path = Path("/".join(e for e in breadcrumbs[:-1]))
        make_md = MakeMd(class_path)
        entry = make_md.extend_files(
            class_path, breadcrumbs, int_breadcrumbs, files, config, rel_path=path
        )
        pydantic_entries.append(entry)

    return pydantic_entries
