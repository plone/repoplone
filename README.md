# RepoPlone

<div align="center">

[![PyPI](https://img.shields.io/pypi/v/repoplone)](https://pypi.org/project/repoplone/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/repoplone)](https://pypi.org/project/repoplone/)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/repoplone)](https://pypi.org/project/repoplone/)
[![PyPI - License](https://img.shields.io/pypi/l/repoplone)](https://pypi.org/project/repoplone/)
[![PyPI - Status](https://img.shields.io/pypi/status/repoplone)](https://pypi.org/project/repoplone/)


[![Code Quality](https://github.com/plone/repoplone/actions/workflows/main.yml/badge.svg)](https://github.com/plone/repoplone/actions/workflows/main.yml)

[![GitHub contributors](https://img.shields.io/github/contributors/plone/repoplone)](https://github.com/plone/repoplone)
[![GitHub Repo stars](https://img.shields.io/github/stars/plone/repoplone?style=social)](https://github.com/plone/repoplone)

</div>

## Overview

The **RepoPlone** is a tool designed to manage mono repos containing a `repository.toml` configuration file at the repository root.

It provides various commands to streamline repository management, versioning, and release processes.

## Setup

### Installation

To use the latest version of this tool, run the command:

```sh
uvx repoplone
```

### Authentications

#### PyPi

We use `uv` to make the release, please make sure authentication is in place by setting the environment variable `UV_PUBLISH_TOKEN`:

```sh
export UV_PUBLISH_TOKEN=<MYTOKEN>
```

or by using the `uv auth login pypi.org` command, as explained [here](https://docs.astral.sh/uv/concepts/authentication/cli/#the-uv-auth-cli).

#### NPM

```sh
npm whoami
```

#### GitHub

To add releases to GitHub, you should have an environment variable `GITHUB_TOKEN` set -- with a valid token -- before running this tool.

```sh
export GITHUB_TOKEN='<token>'
```

## Usage

### Prepare the repository

Ensure that your monorepo contains a `repository.toml` file. Below is an example of such a configuration:

```toml
[repository]
name = "fake-distribution"
changelog = "CHANGELOG.md"
version = "version.txt"
version_format = "semver"
container_images_prefix = "ghcr.io/collective/fake-distribution"
compose = ["docker-compose.yml"]

[repository.towncrier]
section = "Project"
settings = "towncrier.toml"

[backend.package]
name = "fake.distribution"
path = "backend"
python_version = "3.13"
python_versions = ["3.11", "3.12", "3.13"]
plone_versions = ["6.1", "6.2"]
changelog = "backend/CHANGELOG.md"
towncrier_settings = "backend/pyproject.toml"
base_package = "Products.CMFPlone"
publish = false

[frontend.package]
name = "fake-distribution"
path = "frontend/packages/fake-distribution"
changelog = "frontend/packages/fake-distribution/CHANGELOG.md"
towncrier_settings = "frontend/packages/fake-distribution/towncrier.toml"
publish = false
```

Please refer to [`repository.toml` Specification 1](#repositorytoml-specification-1) for more information, or to [Specification 2](#repositorytoml-specification-2) to declare several packages.

### List Available Commands
To see all available commands, run:

```bash
uvx repoplone
```

### Check Installed Version
To check the installed version of the tool, use:

```bash
uvx repoplone --version
```

## Check repository versions

### Current versions

List current versions for:

- Repository
- Backend package
- Frontend package

```bash
uvx repoplone versions current
```

### Next versions

Report next version of all components of this repository:

- Repository
- Backend package
- Frontend package

```bash
uvx repoplone versions next
```

### Dependencies

Report version information for major dependencies:

- Backend base package
- Frontend base package
- Frontend @plone/volto package

```bash
uvx repoplone versions dependencies
```

## Preview Changelog

To generate and display the draft changelog, run:

```bash
uvx repoplone changelog
```

## Releasing Monorepo Packages

The `release` command creates a new release and accepts the following arguments:

#### `desired_version`

The desired_version argument defines the new version to be used in the release. It can be a specific version number or a version segment.

##### Semantic Versioning

For projects using *Semantic Versioning* -- the default for repoplone --, below is a reference table showing how version segments modify an existing `1.0.0` version:

| Segment | New Version |
|---------|------------|
| `release` | `1.0.0` |
| `major` | `2.0.0` |
| `minor` | `1.1.0` |
| `micro` / `patch` / `fix` | `1.0.1` |
| `a` / `alpha` | `1.0.0a0` |
| `b` / `beta` | `1.0.0b0` |
| `c` / `rc` / `pre` / `preview` | `1.0.0rc0` |
| `r` / `rev` / `post` | `1.0.0.post0` |
| `dev` | `1.0.0.dev0` |

If not provided, you will be prompted to select a version from a list of most probable version options:

```
01/09 Select the next version
    1 - 1.0.1 (micro)
    2 - 1.1.0 (minor)
    3 - 2.0.0 (release)
    Choose from [1/2/3] (1):
```

##### Calendar Versioning

For projects that have the value of `version_format` set as `calver`, the `desired_version`, by default, will compute the next available version.

Examples:
| Current Version | Date | Next Version |
|---------|------------|------------|
| 20250404.1|2026-02-13|20260213.1|
| 20260213.1|2026-02-13|20260213.2|

#### `--dry-run`

Use this flag to simulate the release process without actually publishing the new version.

**Example:**

```bash
uvx repoplone release a
```

This will create an `alpha` release.

### Configuring the release pipeline

By default, repoplone runs a fixed sequence of steps when releasing. Projects
can override that sequence in `repository.toml` under `[repository.release]`.

Built-in step ids: `changelog`, `version`, `repository`, `release_backend`,
`release_frontend`, `git`, `gh_release`, `bye`. The default order matches
that list.

#### Reordering or omitting built-in steps

```toml
[repository.release]
steps = [
    "changelog",
    "version",
    "repository",
    "release_backend",
    "git",
    "bye",
]
```

The example above skips `release_frontend` and `gh_release`.

#### Running a project-local hook

The `local_step` built-in imports a callable from the project root and runs
it under the standard step contract:

```python
def step(step_id, title, settings, state, **kwargs) -> bool: ...
```

Wire it via a registry alias. The alias id is what you put in `steps`:

```toml
[repository.release]
steps = ["changelog", "version", "repository", "notify_slack", "git", "bye"]

[repository.release.registry.notify_slack]
title = "Notify internal Slack"
function = "local_step"
args = { entrypoint = "scripts.notify:hook", channel = "#releases" }
```

Repoplone adds the project root to `sys.path` before resolving the
entrypoint, so a hook at `scripts/notify.py` is reachable as
`scripts.notify:hook`. Any keys in `args` other than `entrypoint` are
forwarded to the hook as keyword arguments.

> **uvx caveat.** Because `uvx repoplone` runs in an isolated environment,
> a local hook may only use the standard library plus packages repoplone
> itself depends on. Third-party packages installed in the project's own
> environment are *not* available to the hook.

`local_step` cannot appear in `steps` directly — it must be wrapped in a
registry alias that supplies `args.entrypoint`.

#### Validating the configuration

Before committing a `[repository.release]` change, validate it:

```bash
uvx repoplone settings sanity-check
```

This loads the settings and resolves every `local_step` entrypoint. It
exits non-zero with a precise message if anything fails.

To inspect the resolved pipeline:

```bash
uvx repoplone settings release-steps          # human-readable table
uvx repoplone settings release-steps --json   # machine-readable
```

---

## Dependencies

### Manage backend's base package

The following commands are available exclusively for projects managed by UV and with a base_package set in the `[backend.package]` section of repository.toml.

#### Report the base package
To check which is the current base package, run:

```bash
uvx repoplone deps info
```

#### Check version
To check the current base package version, run:

```bash
uvx repoplone deps check
```

#### Upgrade version

To upgrade the base package to a specific version, use:

```bash
uvx repoplone deps upgrade backend 6.1.1
```

#### Upgrade a frontend distribution

Repoplone can take care of upgrading a frontend distribution and ensuring that all frontend package versions in the project remain consistent with the distribution.
It reads the base_package set in the `[frontend.package]` section of repository.toml.

```bash
uvx repoplone deps upgrade frontend 3.0.0
```

you can also use `latest` to upgrade to the most recent version of the frontend distribution.

```bash
uvx repoplone deps upgrade frontend latest
```

When you have a project that is based on a distribution, we need to make sure that the versions of the frontend packages in the project are consistent with the versions in the distribution and that these versions are all in sync across all the build.
When creating a distribution, make sure to stamp the Volto version as described in the next section.
Then repoplone can use that stamped Volto version to enforce consistency across all frontend packages in the project.
When the distribution has the `volto_version` field stamped in `package.json`, repoplone also fetches its enforced `dependencies` and `volto_version` from the npm registry and writes them to `frontend/distribution.json`.
That file is consumed by the project's `.pnpmfile.cjs` hook, which overrides those versions across the whole
workspace at install time.
The `@plone/volto` tag in the project's `mrs.developer.json` is aligned to the distribution's `volto_version` as well.

#### Stamp the Volto version when releasing a distribution

The `volto_version` field described above is what identifies a package as a Volto
distribution. When you *release* a distribution, stamp that field from the Volto
core tag checked out via `mrs.developer.json`:

```bash
uvx repoplone deps stamp-volto-version
```

This reads the `@plone/volto` tag from `mrs.developer.json` and writes it verbatim
to the frontend package's `package.json` `volto_version` field. It is typically
wired into a `release-it` hook so the published package advertises the Volto core
it targets. For example, in the distribution package's `.release-it.json`:

```json
{
  "hooks": {
    "after:bump": [
      "uvx repoplone deps stamp-volto-version",
      "git add package.json"
    ]
  }
}
```

The command is cwd-independent inside the repository (it locates `repository.toml`
by walking up), so it works from the package directory where `release-it` runs.

#### Install from a Git branch

To track an unreleased branch of the base package, pass the branch name prefixed
with `@`:

```bash
uvx repoplone deps upgrade backend @main
```

This resolves the constraints from the branch's `pyproject.toml` and pins the
base package to the branch through a `[tool.uv.sources]` entry instead of a
version specifier. The base package must declare repository information to be
installable this way.

## `repository.toml` Specification 1

This section outlines the format and available options for a specification 1 `repository.toml` — a file with no `spec_version` key. Each section is detailed below, along with the available options and their default values.

Specification 1 declares at most one backend and one frontend package. To declare several, or to release a plain Python or Node package, see [Specification 2](#repositorytoml-specification-2).

| Section               | Option                    | Description                                                                                                                     | Example Value                                   | Default Value Source                                                                                                                                         |
|-----------------------|---------------------------|------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `repository`          | `name`                    | Name of the repository.                                                                                                         | `"collective-addon"`                            |                                                                                                                                                              |
|                       | `changelog`               | Path to the changelog file.                                                                                                     | `"CHANGELOG.md"`                                |                                                                                                                                                              |
|                       | `version`                 | Path to the version file of this repository.                                                                                    | `"version.txt"`                                 |                                                                                                                                                              |
|                       | `container_images_prefix` | Prefix for container images. We will add the `-backend` and `-frontend` suffixes to generate the final images.                 | `"ghcr.io/collective/collective-addon"`         |                                                                                                                                                              |
|                       | `compose`                 | List of Docker Compose files.                                                                                                   | `["docker-compose.yml"]`                        |                                                                                                                                                              |
|                       | `version_format`          | Format of the versioning.                                                                                                       | `"semver"` or `"calver"`                        |                                                                                                                                                              |
|                       | `issues_url`              | URL where issues for this repository are tracked.                                                                               | `"https://github.com/plone/repoplone/issues"`   | Empty by default. When unset and the git `origin` points at GitHub, the value is derived as `https://github.com/<owner>/<repo>/issues`.                      |
| `repository.towncrier`| `enabled`                 | Whether a top-level Towncrier is enabled.                                                                                       | `true` or `false`                               | Calculated if a section is present in `repository.toml`                                                                                                      |
|                       | `section`                 | Section name used by Towncrier.                                                                                                 | `"Project"`                                     |                                                                                                                                                              |
|                       | `settings`                | Path to Towncrier settings.                                                                                                     | `"towncrier.toml"`                              |                                                                                                                                                              |
| `backend.package`     | `enabled`                 | Whether the backend package is enabled.                                                                                         | `true` or `false`                               | Calculated if a section is present in `repository.toml`                                                                                                      |
|                       | `name`                    | Name of the backend package.                                                                                                    | `"collective.addon"`                            |                                                                                                                                                              |
|                       | `path`                    | Path to the backend package.                                                                                                    | `"backend"`                                     |                                                                                                                                                              |
|                       | `python_version`          | Base Python version for the package. (Used in tests)                                                                            | `"3.11"`                                        | If value is not present in `repository.toml`, repoplone will inspect `pyproject.toml` `project.classifiers` and return the first supported Python version.  |
|                       | `python_versions`         | List of supported Python versions.                                                                                              | `["3.10", "3.11", "3.12"]`                      | If value is not present in `repository.toml`, repoplone will inspect `pyproject.toml` `project.classifiers` and return all supported Python versions.       |
|                       | `plone_versions`          | List of supported Plone versions.                                                                                               | `["6.0", "6.1"]`                                | If value is not present in `repository.toml`, repoplone will inspect `pyproject.toml` `project.classifiers` and return all supported Plone versions.        |
|                       | `changelog`               | Path to the changelog for the backend.                                                                                          | `"backend/CHANGELOG.md"`                        |                                                                                                                                                              |
|                       | `code_path`               | Path to the source code.                                                                                                        | `"src/collective/addon"`                        |                                                                                                                                                              |
|                       | `towncrier_settings`      | Path to Towncrier settings for backend.                                                                                         | `"backend/pyproject.toml"`                      |                                                                                                                                                              |
|                       | `publish`                 | Whether to publish the backend package to PyPI.                                                                                 | `true` or `false`                               |                                                                                                                                                              |
| `frontend.package`    | `enabled`                 | Whether the frontend package is enabled.                                                                                        | `true` or `false`                               | Calculated if a section is present in `repository.toml`                                                                                                      |
|                       | `name`                    | Name of the frontend package.                                                                                                   | `"@plone-collective/volto-addon"`               |                                                                                                                                                              |
|                       | `path`                    | Path to the frontend package.                                                                                                   | `"frontend/packages/volto-addon"`               |                                                                                                                                                              |
|                       | `code_path`               | Path to the source code.                                                                                                        | `"src"`                                         |                                                                                                                                                              |
|                       | `changelog`               | Path to the changelog for the frontend.                                                                                         | `"frontend/CHANGELOG.md"`                       |                                                                                                                                                              |
|                       | `towncrier_settings`      | Path to Towncrier settings for frontend.                                                                                        | `"frontend/packages/volto-addon/towncrier.toml"`|                                                                                                                                                              |
|                       | `publish`                 | Whether to publish the frontend package to npm.                                                                                 | `true` or `false`                               |                                                                                                                                                              |
|                       | `base_package`            | Name of the frontend base package (e.g. a Volto distribution).                                                                  | `"@kitconcept/intranet"`                        | Defaults to `"@plone/volto"`.                                                                                                                                 |


## `repository.toml` Specification 2

Specification 2 lets a repository declare **several packages**, of several kinds. It is selected by a top-level `spec_version` key:

```toml
spec_version = "2"
```

A file without that key is a specification 1 file and keeps behaving exactly as before. Run [`repoplone settings migrate`](#migrating-from-specification-1) to convert one.

### The `[[package]]` array

Specification 2 replaces the `[backend.package]` and `[frontend.package]` tables with a single array of packages. Note the double brackets: each `[[package]]` adds an entry.

```toml
spec_version = "2"

[repository]
name = "acme-site"
changelog = "CHANGELOG.md"
version = "version.txt"
compose = ["docker-compose.yml"]

[repository.towncrier]
section = "Project"
settings = "towncrier.toml"

[[package]]
type = "python-plone"
primary = true
name = "acme.core"
path = "backend"
changelog = "backend/CHANGELOG.md"
towncrier_settings = "backend/pyproject.toml"
base_package = "Products.CMFPlone"
publish = true

[[package]]
type = "python-plone"
name = "acme.theme"
path = "backend/sources/acme.theme"
changelog = "backend/sources/acme.theme/CHANGELOG.md"
towncrier_settings = "backend/sources/acme.theme/pyproject.toml"
publish = true

[[package]]
type = "node-volto"
primary = true
name = "@acme/volto-core"
path = "frontend/packages/volto-core"
changelog = "frontend/packages/volto-core/CHANGELOG.md"
towncrier_settings = "frontend/packages/volto-core/towncrier.toml"
publish = true

[[package]]
type = "node-volto"
name = "@acme/volto-theme"
path = "frontend/packages/volto-theme"
changelog = "frontend/packages/volto-theme/CHANGELOG.md"
towncrier_settings = "frontend/packages/volto-theme/towncrier.toml"
publish = true
```

A repository that releases a single Python package living at its own root needs no frontend at all:

```toml
spec_version = "2"

[repository]
name = "acme-tool"
changelog = "CHANGELOG.md"
version = "version.txt"

[[package]]
type = "python"
name = "acme-tool"
path = "."
code_path = "src/acme_tool"
changelog = "CHANGELOG.md"
towncrier_settings = "pyproject.toml"
publish = true
```

### Package types

`type` is required. It encodes two things: the **language prefix** decides how a package is built, versioned and published, and the **ecosystem suffix** decides which extra options apply.

| `type`         | Family   | Built and published with | Extra options                                                                 |
|----------------|----------|--------------------------|-------------------------------------------------------------------------------|
| `python-plone` | `python` | uv, PyPI, PEP 440        | `base_package` (default `Products.CMFPlone`), `python_version`, `python_versions`, `plone_versions` |
| `python`       | `python` | uv, PyPI, PEP 440        | `python_version`, `python_versions`                                            |
| `node-volto`   | `node`   | release-it, npm, semver  | `base_package` (default `@plone/volto`)                                        |
| `node-aurora`  | `node`   | release-it, npm, semver  | `base_package` (default `@plone/aurora`)                                      |
| `node`         | `node`   | release-it, npm, semver  | none                                                                           |

Using an option on a type that does not support it — `plone_versions` on a `node-volto` package, say — is an error rather than a silently ignored key.

### Families and the primary package

Packages group into two families by their language prefix. Each family has one **primary** package, which owns the settings that belong to the component rather than to a single package: the base package and its constraints, `pyproject.toml` resolution, `mrs.developer.json`, the lockfiles.

Mark it with `primary = true`. When a family marks none, the first one in the file is primary — which is what a family with a single package has always meant.

`settings.backend` and `settings.frontend` still answer, with the primary package of the `python` and `node` families, so project release hooks keep working.

### Per-package options

| Option               | Description                                                                 |
|----------------------|-----------------------------------------------------------------------------|
| `type`               | **Required.** One of the types above.                                        |
| `name`               | Package name, as published to PyPI or npm.                                   |
| `path`               | Path to the package, relative to the repository root. Use `"."` for a package that *is* the repository. |
| `changelog`          | Path to the package changelog.                                               |
| `towncrier_settings` | Path to the package Towncrier settings.                                      |
| `code_path`          | Path to the source code, relative to `path`.                                 |
| `publish`            | Whether to publish this package to its registry.                             |
| `primary`            | Marks the primary package of its family.                                     |
| `section`            | Heading for this package in the repository changelog. Defaults to its name.  |
| `base_package`       | Package this one builds on. Only meaningful on a family's primary package.   |

### What changed from specification 1

| Specification 1                                    | Specification 2                                        |
|----------------------------------------------------|--------------------------------------------------------|
| `[backend.package]` / `[frontend.package]` tables  | a flat `[[package]]` array, each entry with a `type`    |
| `compose` as a string or a list                    | a list                                                  |
| `repository.managed_by_uv`, `backend.path`, `frontend.path` | removed                                        |
| release steps `release_backend`, `release_frontend`| `release_python`, `release_node`                        |
| changelog sections titled `Backend` / `Frontend`   | titled with the package name, unless `section` says otherwise |

The release step ids are user-facing, so the rename is gradual: a specification 1 file accepts either spelling, a specification 2 file accepts only the new ones, and `--start-step` always accepts both.

Changelog headings only change when a file moves to specification 2. Upgrading RepoPlone never rewrites the headings of an existing project.

### JSON Schemas

Both specifications are described by JSON Schemas, shipped in `repoplone/schemas/` and published through [pytest-jsonschema](https://github.com/collective/pytest-jsonschema) as `repository-v1` and `repository-v2`. They validate the shape of a file: which tables and options exist, and their types. Rules that span the whole document — duplicate package names, one primary per family, paths existing on disk — are checked by RepoPlone when it reads the file.

### Migrating from specification 1

```shell
repoplone settings migrate
```

The command rewrites `repository.toml` in place, preserving comments and formatting, and validates the result against the specification 2 schema before writing it. It:

- adds `spec_version = "2"`
- turns each component's package table into a `[[package]]` entry, with its `type` and `primary = true`
- normalizes `compose` to a list
- removes the deprecated `repository.managed_by_uv`, `backend.path` and `frontend.path`
- renames the release step ids
- leaves tables it does not own, such as `[cookieplone]`, alone

Every change is reported. Use `--dry-run` to print the result without writing it, and `--path` to migrate a file other than the detected one.

The command does **not** add `section` options to keep the old `Backend` / `Frontend` changelog headings — migrating is the deliberate moment those become package names. It says so, and adding `section = "Backend"` to a package restores the old heading.

## Contribute 🤝

We welcome contributions to RepoPlone.

You can create an issue in the issue tracker, or contact a maintainer.

- [Issue Tracker](https://github.com/plone/repoplone/issues)
- [Source Code](https://github.com/plone/repoplone/)

### Development requirements

- [uv](https://docs.astral.sh/uv/)

### Setup

Clone this repository:

```sh
git clone git@github.com:plone/repoplone.git
```

Install `UV`, and create a local virtual environment with the following command.

```shell
make install
```

### Run the checked out branch of RepoPlone

```shell
uv run repoplone
```

### Check and format the codebase

```shell
make check
```

### Run tests

[`pytest`](https://docs.pytest.org/) is this package's test runner.

Run all tests with the following command.

```shell
make test
```

Run all tests, but stop on the first error and open a `pdb` session with the following command.

```shell
uv run pytest -x --pdb
```

Run only tests that match `test_release_backend` with the following command.

```shell
uv run pytest -k test_release_backend
```

Run only tests that match `test_release_backend`, but stop on the first error and open a `pdb` session with the following command.

```shell
uv run pytest -k test_release_backend -x --pdb
```

### Run type checker

We use [`mypy`](https://www.mypy-lang.org/) to run static type checking for this codebase.

Run the checker with the following command.

```shell
uv run mypy src
```


## Support 📢

For support, questions, or more detailed documentation, visit the [official RepoPlone repository](https://github.com/plone/repoplone).


## This project is supported by

<p align="left">
    <a href="https://plone.org/foundation/">
      <img alt="Plone Foundation Logo" width="200px" src="https://raw.githubusercontent.com/plone/.github/main/plone-foundation.png">
    </a>
</p>

## License

The project is released under the [MIT License](./LICENSE).
