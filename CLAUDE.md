# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

mkdocs-pydantic is an MkDocs plugin that automatically generates documentation pages from Pydantic model classes. Models are referenced in `mkdocs.yaml` nav using `pydantic:::fully.qualified.ClassName` syntax, and the plugin dynamically creates markdown files and navigation entries during the MkDocs build.

## Commands

- **Install (dev):** `uv pip install .[dev]`
- **Lint:** `pre-commit run --all-files -v` (ruff format, ruff lint, codespell, mypy strict)
- **Build docs:** `mkdocs build --strict`
- **Test:** `pytest`
- **Test single file:** `pytest tests/test_make_md.py`
- **Test single class/method:** `pytest tests/test_make_md.py::TestRun::test_flat_model_single_node`
- **Type check only:** `mypy src/`

## Architecture

All source code is in `src/mkdocs_pydantic/`. The plugin hooks into two MkDocs lifecycle events:

1. **`plugin.py`** — `MkdocsPydantic(BasePlugin)` is the entry point (registered via `pyproject.toml` entry-points). It implements:
   - `on_files()`: Parses the nav config for `pydantic:::` entries, dynamically imports the referenced Pydantic models, generates markdown files, and adds them to MkDocs' file collection.
   - `on_nav()`: Patches the navigation tree to include the generated pages using breadcrumb indices to locate the correct position.
   - `find_pydantic_entries()`: Recursively walks the nav config (lists, dicts, strings), resolving aliases (dict keys) and building breadcrumb paths.
   - `import_class_from_string()`: Dynamically imports a class by fully qualified name and asserts it is a BaseModel subclass.

2. **`make_md.py`** — Generates markdown content from Pydantic models. `run()` recursively processes nested BaseModel fields, creating a `Node` tree. Flat models produce a single `ModelName.md` file; models with nested BaseModel fields produce an `index.md` with child pages in a subdirectory. Each field is rendered with its type, description, and default value (multi-line defaults use fenced code blocks via `formatted_default()`).

3. **`structs.py`** — Data structures: `PydanticEntry` (model + nav breadcrumb + root Node) and `Node` (tree of generated pages with name, path, markdown content, and children). `Node.add_files()` writes markdown to disk and registers files with MkDocs. `PydanticEntry.make_nav_object()` produces Page or Section nav items depending on whether children exist.

`src/mkdocs_pydantic_examples/` contains example Pydantic models (single, two-level, three-level nesting) used by the project's own documentation site.

## Code Style

- mypy strict mode is enabled
- Ruff handles formatting and linting with `skip-magic-trailing-comma = true`
- Uses Pydantic v2 APIs (`model_fields`, `model_rebuild()`)
