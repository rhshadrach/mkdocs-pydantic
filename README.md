# mkdocs-pydantic

An [MkDocs](https://www.mkdocs.org/) plugin that automatically generates documentation pages from [Pydantic](https://docs.pydantic.dev/) model classes. Fields, types, defaults, and descriptions are rendered into navigable markdown — nested models get their own sub-pages organized into sections.

## Installation

```bash
pip install mkdocs-pydantic
```

## Usage

Add the plugin to your `mkdocs.yaml` and reference your Pydantic models in the nav using the `pydantic:::` prefix:

```yaml
plugins:
  - mkdocs-pydantic

nav:
  - index.md
  - 'pydantic:::mypackage.config.AppSettings'
  - Custom Name: 'pydantic:::mypackage.config.DatabaseSettings'
```

The plugin imports each referenced model, generates markdown from its fields, and injects the pages into the MkDocs build. Dict keys in the nav become display name aliases.

## Documentation

Full documentation and live examples: [rhshadrach.github.io/mkdocs-pydantic](https://rhshadrach.github.io/mkdocs-pydantic/)
