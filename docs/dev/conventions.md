---
type: development_rules
title: "Coding Conventions & Style Guide"
description: "Code style, naming conventions, and architectural rules for nakprok development."
tags:
  - conventions
  - style
  - code-quality
  - naming
  - architecture
timestamp: "2026-10-26T00:00:00Z"
resource: "https://github.com/cwt/nakprok"
---

# Coding Conventions & Style Guide

## Language & Tooling

- **Python 3.10+** — Matches `python = "^3.10"` in `pyproject.toml`.
- **Type hints** — Use standard Python 3.10 union syntax such as
  `str | Path`.
- **Linter** — Ruff, configured in `[tool.ruff]` with rules
  `E`, `F`, `I`, `N`, `W`, and `UP`, a line length of 88, and target `py310`.
- **Type checker** — mypy in strict mode, configured in `[tool.mypy]`.
- **Formatter** — Black 26, invoked by `scripts/code-format.sh` with
  `-t py310 -l 88`. Black has no separate configuration file.

These tools enforce the same explicitness that nakprok itself demands: every
function signature, local variable, and container type should be visible in the
source.

## Code Style

### Imports

- Group imports as standard library, third-party, then local.
- Inside the `nakprok` package, use relative imports for sibling modules:
  `from .checker import TypeError, check_source`.
- In tests and external consumers, use absolute imports:
  `from nakprok.checker import is_strict`.
- Let Ruff's `I` rules sort imports; run `bash scripts/lint-check-and-fix.sh`.

```python
# Inside nakprok/cli.py
from .checker import TypeError, check_file
from .runner import run_file
```

```python
# Inside tests/test_checker.py
from nakprok.checker import TypeError, is_strict
```

Avoid wildcard imports and unused imports.

### Naming

- `snake_case` for functions, methods, variables, modules, and files.
- `PascalCase` for classes (`StrictTypeChecker`, `TestCLI`), not `camelCase`.
- `UPPERCASE` for constants.
- Leading underscore for private helpers and attributes (`_check_path`,
  `_typed_vars`).
- Prefix test files with `test_` and test classes with `Test`.

```python
def check_type(node: ast.AST) -> bool:
    return True


class StrictTypeChecker:
    pass


MAX_SIZE: int = 100
```

**Important:** the checker decides that a name is a constant with
`name.isupper()`. Any all-uppercase identifier is therefore immutable and
exempt from annotation requirements. Do not use `UPPERCASE` for a variable that
needs to change.

### Type Annotations

- **All parameters** must have type annotations (except `self` and `cls`).
- **All return types** must be annotated, including `-> None`.
- **`*args` and `**kwargs`** must be annotated.
- Annotate local variables before or at first assignment.
- Prefer concrete types over `Any`; use `Any` only at genuinely dynamic
  boundaries.

```python
# Good
def process(data: list[int]) -> str:
    return ",".join(str(item) for item in data)


# Avoid
def process(data: Any) -> Any:
    ...
```

### Variable Declarations

```python
# Annotated assignment
x: int = 10

# Declaration followed by assignment
result: int
result = compute()
```

Inside functions, a variable must be typed before it is used as an assignment
target, a `for` target, a `with ... as` target, a `match` capture, or a walrus
target. Re-assignment after the declaration is allowed.

### Docstrings

- Use Google-style docstrings for public functions, classes, and modules.
- Describe parameters, return values, and behavior.
- Keep the first line as a one-sentence summary.

```python
def check_file(filepath: str | Path) -> list[TypeError]:
    """Check a Python file for type annotation violations.

    Args:
        filepath: Path to the Python file to check.

    Returns:
        List of type errors found in the file.
    """
    ...
```

### Error Handling

- Use specific exception types where possible.
- Include the file, line, and column when reporting checker errors.
- Distinguish type errors (exit code 1) from runtime exceptions (exit code 2),
  and remember that `SystemExit` and `KeyboardInterrupt` are not caught by the
  runner.
- Never swallow errors silently. `nakprok check` reports a missing path instead
  of treating it as success.

## Naming Conventions

### Files & Directories

- `snake_case` for Python modules and packages.
- `ALL_CAPS` filenames only for conventional constant files such as
  `LICENSE`; project Markdown keeps its established names (`README.md`,
  `CHANGELOG.md`).

### Test Files

- Prefix test files with `test_`.
- Use descriptive test classes: `TestFunctionAnnotations`, `TestCLI`,
  `TestRunFile`.

### Variables

- `snake_case` for local variables and parameters.
- `UPPERCASE` for module-level constants and other immutable names.
- Prefix private attributes with `_`.

## Architectural Rules

### Module Responsibilities

| Module | Responsibility |
| --- | --- |
| `checker.py` | AST parsing, validation, shared function signature checks, class/function name tracking, and error reporting |
| `runner.py` | Type-check then compile/execute pipeline, including `sys.path` and `sys.argv` handling |
| `cli.py` | Argument dispatch, file discovery, output streams, and process exit codes |
| `__init__.py` | Package documentation and version export from installed metadata |

The checker must not import the runner or CLI. The runner may import the
checker, and the CLI may import both. Keep the dependency direction one-way.

### Error Types

- `TypeError` in `checker.py` is the single error type for all violations.
  - Fields: `line`, `column`, `message`, `filename`.
  - `str(error)` produces `filename:line:column: error: message`.
  - The name shadows the built-in; alias it when both are needed.

### Public API

- `check_source(source: str, filename: str = "<string>") -> list[TypeError]`
- `check_file(filepath: str | Path) -> list[TypeError]`
- `is_strict(source: str) -> tuple[bool, list[TypeError]]`
- `run_file(filepath: str | Path, args: list[str] | None = None) -> int`
- `run_source(source: str, filename: str = "<string>") -> int`
- `cli.main() -> None`

## Testing Conventions

- Use pytest with descriptive method names.
- Use `is_strict()` for string-based checker tests and `check_file()` when the
  filesystem matters.
- Use subprocess calls for CLI behavior, including exit codes and stream
  separation.
- Use pytest's `tmp_path` fixture for new file-based tests; it cleans up
  automatically.
- Group tests by feature: `TestFunctionAnnotations`, `TestCLI`, etc.
- Assert exact messages or substrings only where the message is part of the
  contract.

## Commit Messages

- Write an imperative subject line, capitalized, without a trailing period.
- Leave a blank line, then explain why and what changed in bullets when useful.
- Examples from this repository:
  - `Fix path validation, sibling imports, and version reporting`
  - `Update dependencies`
- Conventional-commit prefixes (`feat:`, `fix:`) are not required.

## Documentation

- Documentation uses the Google Open Knowledge Format (OKF) with front matter
  (`type`, `title`, `description`, `tags`, `timestamp`, `resource`).
- Keep `index.md` files as directory maps; put conceptual material in content
  pages such as `overview.md`.
- Use relative links between documents; never use absolute `/` paths.
- Update the relevant `index.md` when adding a page.
- Update `README.md` for public-facing changes.

## Related Documentation

- [Testing Strategy](./testing.md)
- [Error Handling & Exit Codes](./error-handling.md)
- [Documentation index](../index.md)
