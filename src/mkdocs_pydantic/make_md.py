from __future__ import annotations

import importlib
import io
import os
import pprint
from pathlib import Path
from typing import Any, ForwardRef

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File, Files
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from pydantic_settings import BaseSettings

from mkdocs_pydantic.structs import ModelFile, PydanticEntry

HTML_HR = '<hr stype="height:3px;border-width:0;color:gray;background-color:gray">'


def import_class_from_string(fully_qualified_name_str: str) -> type[BaseSettings]:
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
        raise ImportError(
            f"'{fully_qualified_name_str}' does not appear to be a"
            f" fully qualified class name."
        ) from None

    # 2. Import the module
    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        raise ImportError(f"Could not import module '{module_name}': {e}") from None

    # 3. Get the class from the module
    try:
        class_object = getattr(module, class_name)
    except AttributeError as e:
        raise ImportError(
            f"Module '{module_name}' has no class named '{class_name}': {e}"
        ) from None

    if not isinstance(class_object, type):
        raise ImportError(f"'{fully_qualified_name_str}' is not a class.")

    assert issubclass(class_object, BaseSettings)

    return class_object


class MakeMd:
    def __init__(self, fully_qualified_name: str) -> None:
        self.fully_qualified_name = fully_qualified_name
        self.root: type[BaseSettings] = import_class_from_string(fully_qualified_name)

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

    def make_top_level(self) -> str:
        result = f"# {self.root.__name__}\n\n"
        for name, field in self.root.model_fields.items():
            result += (
                '<div class="mkdocs-pydantic-field" markdown>\n\n'
                # TODO: Add \n?
                f"{self.markdown_field(name, field, prefix=self.root.__name__)}"
                "</div>\n\n"
                "---\n\n"
            )
        return result

    def make_sub_level(self, klass: type[BaseSettings], prefix: str) -> str:
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
            result.append((name, field))
        return result

    def extend_files(
        self,
        class_path: str,
        breadcrumbs: list[str],
        int_breadcrumbs: list[int],
        files: Files,
        config: MkDocsConfig,
        rel_path: Path,
    ) -> PydanticEntry:
        model_file = self.extend_files_sub(
            self.root, files, config, rel_path, prefix=self.root.__name__
        )
        result = PydanticEntry(
            class_path=class_path,
            breadcrumbs=breadcrumbs,
            int_breadcrumbs=int_breadcrumbs,
            model_file=model_file,
        )
        return result

    def extend_files_sub(
        self,
        model: type[BaseSettings],
        files: Files,
        config: MkDocsConfig,
        rel_path: Path,
        prefix: str,
    ) -> ModelFile:
        if len(self.sub_models(model)) > 0:
            rel_path /= model.__name__
        name = model.__name__ if len(self.sub_models(model)) == 0 else "index"
        markdown = self.make_sub_level(model, prefix)
        file = File(
            path=str(rel_path / f"{name}.md"),
            src_dir=config["docs_dir"],
            dest_dir=config["site_dir"],
            use_directory_urls=config["use_directory_urls"],
        )
        assert file.abs_src_path is not None
        base_path = Path(file.abs_src_path).parent
        os.makedirs(base_path, exist_ok=True)
        with open(file.abs_src_path, "w") as fh:
            fh.write(markdown)
        files.append(file)
        model_file = ModelFile(name=model.__name__, file=file, children=[])

        for name, field in self.sub_models(model):
            assert field.annotation is not None
            assert issubclass(field.annotation, BaseSettings)
            model_file.children.append(
                self.extend_files_sub(
                    field.annotation, files, config, rel_path, prefix + f".{name}"
                )
            )
        return model_file
