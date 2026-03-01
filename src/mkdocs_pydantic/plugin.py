from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure import StructureItem
from mkdocs.structure.files import Files
from mkdocs.structure.nav import Navigation, Section
from mkdocs.structure.pages import Page
from pydantic_settings import BaseSettings

from mkdocs_pydantic.make_md import MakeMd
from mkdocs_pydantic.structs import Node, PydanticEntry


# __init_sublcass__ of BasePlugin is untyped.
# TODO: type-arg because we don't have a generic config
class MkdocsPydantic(BasePlugin):  # type: ignore[no-untyped-call, type-arg]
    def __init__(self) -> None:
        self.pydantic_entries: list[PydanticEntry] = []

    def on_nav(self, nav: Navigation, config: MkDocsConfig, files: Files) -> Navigation:
        # TODO: Improve use of curr - it's either a Section or ...?
        for pydantic_entry in self.pydantic_entries:
            curr: list[Any] = nav.items
            for crumb in pydantic_entry.breadcrumbs[:-1]:
                if isinstance(curr, Section):
                    curr = curr.children[crumb]  # type: ignore[assignment]
                else:
                    curr = curr[crumb]

            obj: Page | Section
            if len(pydantic_entry.root.children) == 0:
                obj = Page(
                    title=pydantic_entry.root.name,
                    file=pydantic_entry.root.file,
                    config=config,
                )
            else:
                children = make_section(node=pydantic_entry.root, config=config)
                obj = Section(title=pydantic_entry.root.name, children=children)

            if isinstance(curr, Section):
                curr.children[pydantic_entry.breadcrumbs[-1]] = obj
            else:
                curr[pydantic_entry.breadcrumbs[-1]] = obj
        print(nav)  # noqa: T201
        return nav

    def on_files(self, files: Files, config: MkDocsConfig) -> Files:
        self.pydantic_entries = find_pydantic_items(config["nav"])
        for entry in self.pydantic_entries:
            entry.add_files(files, config)
        return files


def make_section(node: Node, config: MkDocsConfig) -> list[StructureItem]:
    result: list[StructureItem] = [Page(title=node.name, file=node.file, config=config)]
    for child in node.children:
        obj: Page | Section
        if len(child.children) == 0:
            obj = Page(title=child.name, file=child.file, config=config)
        else:
            children = make_section(node=child, config=config)
            obj = Section(title=child.name, children=children)
        result.append(obj)
    return result


def find_pydantic_items(
    data: Any, path: Path = Path("."), breadcrumbs: list[int] | None = None
) -> list[PydanticEntry]:
    pydantic_entries = []
    if breadcrumbs is None:
        breadcrumbs = []

    if isinstance(data, list):
        # Recurse into each item in the list
        for idx, item in enumerate(data):
            pydantic_entries.extend(
                find_pydantic_items(item, path, [*breadcrumbs, idx])
            )
    elif isinstance(data, dict):
        # Recurse into each value in the dictionary
        for key, value in data.items():
            pydantic_entries.extend(find_pydantic_items(value, path / key, breadcrumbs))
    elif isinstance(data, str) and data.startswith("pydantic:::"):
        class_path = data[len("pydantic:::") :]
        make_md = MakeMd(class_path)
        model = import_class_from_string(class_path)
        model_file = make_md.extend_files(model, rel_path=path.parent)
        entry = PydanticEntry(
            class_path=class_path, breadcrumbs=breadcrumbs, root=model_file
        )
        pydantic_entries.append(entry)

    return pydantic_entries


def import_class_from_string(fully_qualified_name_str: str) -> type[BaseSettings]:
    """
    Dynamically imports a class given its fully qualified name string.

    Args:
        fully_qualified_name_str (str): The full path to the class,
                                        e.g., "my_package.my_module.MyClass"

    Returns:
        type: The imported class object.
    """
    try:
        module_name, class_name = fully_qualified_name_str.rsplit(".", 1)
    except ValueError:
        raise ValueError(
            f"'{fully_qualified_name_str}' does not appear to be a"
            f" fully qualified class name."
        ) from None

    module = importlib.import_module(module_name)
    class_object = getattr(module, class_name)
    assert issubclass(class_object, BaseSettings)

    # TODO: Why doesn't mypy narrow here?
    return class_object  # type: ignore[no-any-return]
