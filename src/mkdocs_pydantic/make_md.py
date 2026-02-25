from __future__ import annotations

from typing import Any, ForwardRef
import io
import importlib
import pprint
from pathlib import Path
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from pydantic_settings import BaseSettings
from mkdocs.structure.files import File
from mkdocs.structure.files import Files
from mkdocs.config.defaults import MkDocsConfig
import os


HTML_HR = '<hr stype="height:3px;border-width:0;color:gray;background-color:gray">'

def import_class_from_string(fully_qualified_name_str):
    """
    Dynamically imports a class given its fully qualified name string.

    Args:
        fully_qualified_name_str (str): The full path to the class,
                                        e.g., "my_package.my_module.MyClass"

    Returns:
        type: The imported class object.
    """
    # 1. Split the string into module name and class name
    try:
        module_name, class_name = fully_qualified_name_str.rsplit(".", 1)
    except ValueError:
        raise ImportError(f"'{fully_qualified_name_str}' does not appear to be a fully qualified class name.")

    # 2. Import the module
    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        raise ImportError(f"Could not import module '{module_name}': {e}")

    # 3. Get the class from the module
    try:
        class_object = getattr(module, class_name)
    except AttributeError as e:
        raise ImportError(f"Module '{module_name}' has no class named '{class_name}': {e}")

    if not isinstance(class_object, type):
        raise ImportError(f"'{fully_qualified_name_str}' is not a class.")

    return class_object

class MakeMd:
    def __init__(self, fully_qualified_name: str) -> None:
        self.fully_qualified_name = fully_qualified_name
        self.root = import_class_from_string(fully_qualified_name)

    @staticmethod
    def formatted_default(obj: Any) -> str:
        buf = io.StringIO()
        pprint.pprint(obj, stream=buf)
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

    def markdown_field(self, name: str, field: FieldInfo, prefix: str = "settings", level: int = 3) -> str:
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

    def make_top_level(self) -> str:
        result = f"# {self.root.__name__}\n\n"
        for name, field in self.root.model_fields.items():
            result += (
                '<div class="mkdocs-pydantic-field" markdown>\n\n'
                f"{self.markdown_field(name, field)}"  # TODO: Add \n?
                "</div>\n\n"
                "---\n\n"
            )
        return result

    def make_sub_level(self, klass: type[BaseSettings], attr: str) -> str:
        name = klass.__name__
        # TODO: Get title from klass?
        title = name
        result = f"# {title}\n\n"
        for name, field in klass.model_fields.items():
            if isinstance(field.default, BaseSettings):
                result += (
                    f"## {name}\n\n"
                    f"{field.title}\n\n"
                    f"{HTML_HR}\n\n"
                )
                for subname, subfield in field.default.model_fields.items():
                    result += (
                        '<div class="mkdocs-pydantic-field" markdown>\n\n'
                        f"{self.markdown_field(subname, subfield, prefix=f'settings.{attr}.{name}')}"
                        "---\n\n"
                        "</div>\n\n"
                    )
            else:
                result += (
                    f"{self.markdown_field(name, field, prefix=f'settings.{attr}', level=2)}"
                    f"---\n\n"
                )
        return result

    def extend_files(self, files: Files, config: MkDocsConfig, rel_path: Path):
        result: list[File] = []

        idx = 0
        top_level_markdown = self.make_top_level()
        top_level_file = File(
            path=str(rel_path / f"index.md"),
            src_dir=config['docs_dir'],
            dest_dir=config['site_dir'],
            use_directory_urls=config['use_directory_urls']
        )
        idx += 1

        base_path = Path(top_level_file.abs_src_path).parent
        os.makedirs(base_path, exist_ok=True)
        with open(top_level_file.abs_src_path, 'w') as fh:
            fh.write(top_level_markdown)
        files.append(top_level_file)
        result.append((self.root.__name__, top_level_file))

        for name, field in self.root.model_fields.items():
            if isinstance(field.annotation, ForwardRef):
                # TODO: Add test for this case.
                raise ValueError(
                    f"{self.root.__name__} contains a ForwardRef on the field {name}."
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

            markdown = self.make_sub_level(field.annotation, name)
            file = File(
                path=str(rel_path / f"{idx:02}_{name}.md"),
                src_dir=config['docs_dir'],
                dest_dir=config['site_dir'],
                use_directory_urls=config['use_directory_urls']
            )
            idx += 1
            with open(file.abs_src_path, 'w') as fh:
                fh.write(markdown)
            files.append(file)
            result.append((field.annotation.__name__, file))
        return result
