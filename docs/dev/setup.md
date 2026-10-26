---
type: development_setup
title: "Development Environment Setup"
description: "Step-by-step guide for setting up the nakprok development environment."
tags:
  - setup
  - development
  - environment
  - poetry
  - testing
timestamp: "2026-10-26T00:00:00Z"
resource: "https://github.com/cwt/nakprok"
---

# Development Environment Setup

## Prerequisites

- **Python 3.10+** — `pyproject.toml` declares `python = "^3.10"`.
- **Poetry** — Installs dependencies and provides the `nakprok` entry point.
- **Mercurial with `hg-git`** — The working repository is Mercurial, synchronized
  with the Git remote through the `main.git` bookmark. A plain Git clone also
  works if you only need the source.

## Clone the Repository

With Mercurial and `hg-git`:

```bash
hg clone https://github.com/cwt/nakprok.git
cd nakprok
```

Or with Git:

```bash
git clone https://github.com/cwt/nakprok.git
cd nakprok
```

## Install Dependencies

All development dependencies (pytest, coverage, xdist, Black, Ruff, mypy) are in
the Poetry `dev` group, so a single install is enough:

```bash
poetry install
```

There is no `.[dev]` extra. `poetry install` creates the virtual environment,
installs the dev group, and installs the project in editable mode so that
`nakprok` points at the working tree.

`scripts/runtest.sh` additionally runs `pip install -q -e .`, but that is a
special-purpose dependency-refresh workflow, not the normal setup step.

## Verify Installation

Prefix commands with `poetry run` unless the virtual environment is already
active:

```bash
# Version from installed package metadata
poetry run nakprok --version

# Static type checking
poetry run mypy .

# Linting (import order and pyflakes rules)
poetry run ruff check --select=I,F .

# Tests
poetry run pytest tests/ -q
```

The full Ruff selection in `pyproject.toml` includes `E501`. Running
`poetry run ruff check .` currently reports long-line findings in existing
source and test files; the helper script selects only `I` and `F`, which pass.

## Project Structure

```text
nakprok/
├── nakprok/                       # Core package
│   ├── __init__.py                # Version metadata export
│   ├── checker.py                 # AST visitor for type validation
│   ├── cli.py                     # Command-line interface
│   └── runner.py                  # Type-check then execute
├── tests/                         # Test suite
│   ├── test_checker.py            # Core checker tests
│   ├── test_checker_extended.py   # Extended checker coverage
│   ├── test_cli.py                # CLI integration tests
│   └── test_runner.py             # Runner tests
├── examples/                      # Valid and invalid Python samples
├── scripts/                       # Formatting, linting, test helpers
├── docs/                          # OKF documentation
├── pyproject.toml                 # Project metadata and tool config
├── poetry.lock                    # Locked dependency versions
└── README.md                      # Project overview
```

## Running the Test Suite

```bash
# All tests
poetry run pytest tests/ -v

# With coverage
poetry run pytest tests/ -v --cov=nakprok --cov-report=term-missing

# One test file
poetry run pytest tests/test_checker.py -v

# One test by name
poetry run pytest tests/test_cli.py -k version -v

# Parallel execution
poetry run pytest tests/ -v -n auto
```

`pytest` is configured in `pyproject.toml` with `testpaths = ["tests"]`, short
tracebacks, and `test_*.py` / `test_*` discovery.

## Helper Scripts

The `scripts/` directory contains four helpers:

| Script | Purpose |
| --- | --- |
| `type-check.sh` | Run `poetry run mypy .` |
| `lint-check-and-fix.sh` | Run `poetry run ruff check --select=I,F --fix .` |
| `code-format.sh` | Run Black (`-t py310 -l 88`) on every `.py` file and strip trailing whitespace |
| `runtest.sh` | Refresh dependencies, reinstall, regenerate the lockfile, then run the full suite under xdist with coverage |

```bash
bash scripts/type-check.sh
bash scripts/lint-check-and-fix.sh
bash scripts/code-format.sh
bash scripts/runtest.sh
```

> **Caution:** `runtest.sh` is not a quick test command. It removes caches, runs
> `poetry update`, runs `pip install -e .`, deletes and regenerates
> `poetry.lock`, and only then runs pytest. Use `poetry run pytest` for routine
> test runs, and review the lockfile diff before committing after using it.

## Key Configuration Files

- **`pyproject.toml`** — Package metadata, dependencies, the `nakprok` entry
  point, and pytest, mypy, and Ruff configuration.
- **`poetry.lock`** — Locked dependency versions.
- **`.markdownlint.json`** — Markdown lint adjustments for table line length and
  front-matter title recognition.

There are no separate `.ruff.toml` or `.mypy.ini` files; both tools read their
configuration from `pyproject.toml`. Black has no configuration section and is
invoked with explicit flags by `scripts/code-format.sh`.

## Development Workflow

1. Clone the repository.
2. Run `poetry install`.
3. Run the existing suite: `poetry run pytest tests/ -q`.
4. Edit files under `nakprok/`.
5. Format with `bash scripts/code-format.sh`.
6. Re-run tests.
7. Run `poetry run mypy .`.
8. Run `poetry run nakprok check nakprok/ tests/`.
9. Commit with Mercurial (or Git).

Check `nakprok/` and `tests/` rather than the repository root:
`examples/invalid.py` is intentionally invalid, and `nakprok check` has no
exclude option, so `nakprok check .` reports its errors.

## Useful Commands

```bash
# Check a valid sample
poetry run nakprok check examples/valid.py

# Run a valid sample
poetry run nakprok run examples/valid.py

# Show the expected failure for an invalid sample
poetry run nakprok run examples/invalid.py

# Run the checker over project source and tests
poetry run nakprok check nakprok/ tests/

# Apply the formatter
bash scripts/code-format.sh
```

## Version Management

The version lives in `[tool.poetry] version` in `pyproject.toml`
(currently `0.3.0`). `nakprok.__version__` reads the installed distribution
metadata with `importlib.metadata.version("nakprok")`; it does not duplicate the
number in source code.

```bash
# Bump the project version (semantic versioning)
poetry version patch   # or: minor, major, or an explicit version

# Reinstall so metadata reflects the new version
poetry install

# Verify
poetry run nakprok --version
```

A source checkout that has never been installed falls back to `0.0.0`.

## Version Control Notes

- The Mercurial bookmark `main.git` is exported to the Git branch by `hg-git`.
- `hg commit` automatically runs `hg gexport` in this repository.
- Use `hg status` and `hg diff` before committing. There is no `.git` working
  tree here, so `git status` is not available and is not the source of truth.

## Related Documentation

- [Coding Conventions & Style Guide](./conventions.md)
- [Testing Strategy](./testing.md)
- [Documentation index](../index.md)
