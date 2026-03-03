# mkdocs-pydantic

**mkdocs-pydantic** is an MkDocs plugin that automatically generates documentation pages from
[Pydantic](https://docs.pydantic.dev/) model classes. Instead of writing and maintaining
documentation for your configuration schemas by hand, you reference your Pydantic models directly
in `mkdocs.yaml` and the plugin generates structured, navigable pages during the build.

## How it works

In your `mkdocs.yaml` nav section, use the `pydantic:::` prefix followed by the fully qualified
class name of a Pydantic model:

```yaml
nav:
  - index.md
  - 'pydantic:::mypackage.config.AppSettings'
```

During the MkDocs build, the plugin:

1. Imports the referenced Pydantic model class.
2. Inspects its fields, types, defaults, and descriptions.
3. Generates markdown pages — one per model, with nested models getting their own sub-pages
   organized into sections.
4. Injects the generated pages into the MkDocs navigation tree.

The result is always in sync with your code because the documentation is derived directly from
your model definitions.

## Features

- **Automatic field documentation** — each field's type, default value, title, and description
  are rendered into clean markdown.
- **Nested model support** — fields that reference other `BaseModel` subclasses are documented
  on their own pages and organized into navigable sections.
- **Nav aliases** — use a dict key in your nav to give a model a custom display name
  (e.g., `SomeAlias: 'pydantic:::mypackage.MyModel'`).
- **Multi-line defaults** — large default values like long lists and dictionaries are rendered
  in fenced code blocks for readability.

## Example models

This documentation site is built using three example Pydantic models that demonstrate the plugin
at different levels of nesting. Each model is a realistic configuration schema with a variety of
field types and verbose descriptions. See the full
[mkdocs.yaml](https://github.com/rhshadrach/mkdocs-pydantic/blob/main/mkdocs.yaml) for how
these models are referenced in practice.

### SingleLevel

A flat server configuration model with no nested sub-models. It showcases a broad range of
Python types including `str`, `int`, `bool`, `float`, `Path`, `Enum`, `Optional`, `tuple`,
`list`, `set`, and `dict`. Several fields have large default values (lists and dictionaries
with 10 entries) that demonstrate multi-line code block rendering. The model is referenced in
the nav as:

```yaml
- 'pydantic:::mkdocs_pydantic_examples.SingleLevel'
```

Because it has no nested models, the plugin generates a single documentation page.

### TwoLevels

A database configuration model with one level of nesting. The top-level `TwoLevels` model
contains scalar fields, a `dict[str, list[str]]` table schema mapping, and a list of database
extensions. It also has a `pool` field of type `ConnectionPool`, which is itself a `BaseModel`
with fields for pool sizing, timeouts, overflow behavior, and per-host connection limits. The
plugin generates an index page for `TwoLevels` and a separate page for `ConnectionPool`,
organized into a navigable section. It is referenced in the nav as:

```yaml
- 'pydantic:::mkdocs_pydantic_examples.TwoLevels'
```

### ThreeLevels

A deployment configuration model with two levels of nesting, demonstrating the deepest
structure the plugin handles. `ThreeLevels` contains service-level settings (replicas,
environment variables, feature flags) and a `networking` field of type `Networking`.
`Networking` in turn contains ingress, TLS, firewall, and DNS settings plus a `monitoring`
field of type `Monitoring`, which defines metrics scraping, tracing, alert thresholds, and
notification channels. The plugin generates a three-level section hierarchy with index pages
at each level. This model also demonstrates nav aliasing — it is referenced with a custom
display name:

```yaml
- Base Directory:
    - SomeAlias: 'pydantic:::mkdocs_pydantic_examples.ThreeLevels'
```

Here, `SomeAlias` becomes the display name in the navigation, and `Base Directory` creates a
parent section.
