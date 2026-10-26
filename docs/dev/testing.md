---
type: development_rules
title: "Testing Strategy"
description: "How to write and structure tests for the nakprok project."
tags:
  - testing
  - pytest
  - strategy
  - unit-tests
  - integration-tests
timestamp: "2026-10-26T00:00:00Z"
resource: "tests/"
---

# Testing Strategy

## Test Framework

- **pytest 9** — Primary framework, configured in `[tool.pytest.ini_options]`.
- **pytest-cov** — Coverage reporting.
- **pytest-xdist** — Parallel execution with `-n auto`.
- **coverage** — Pinned by Python version in the dev dependency group.

Run everything through Poetry so the installed entry point and package metadata
match the working tree:

```bash
poetry run pytest tests/ -q
```

## Test Structure

| File | Focus |
| --- | --- |
| `tests/test_checker.py` | Core signature, variable, constant, lambda, `match`, class, and integration tests |
| `tests/test_checker_extended.py` | Extended coverage: async functions, loops, `with`, walrus, file I/O, and `TypeError` formatting |
| `tests/test_cli.py` | Subprocess integration tests for commands, streams, exit codes, version, and path handling |
| `tests/test_runner.py` | `run_file()` / `run_source()` exit codes, arguments, sibling imports, and runtime failures |

### Class Structure

```python
class TestFeatureName:
    """Docstring describing the feature being tested."""

    def test_case_name(self) -> None:
        """Descriptive test name."""
        ...
```

### Naming Convention

- Test classes: `Test<Feature>` (e.g., `TestFunctionAnnotations`, `TestCLI`).
- Test methods: `test_<scenario>` (e.g., `test_missing_return_type`).
- Every test method returns `None` and has no untyped locals, so the test suite
  itself can be checked with `nakprok check tests/`.

## Test Types

### 1. Unit Tests (Checker)

Use `is_strict()` with source strings for fast rule tests:

```python
from nakprok.checker import TypeError, is_strict


class TestNewRule:
    def test_valid_code(self) -> None:
        source: str = """def foo(x: int) -> int:
    return x
"""
        valid: bool
        errors: list[TypeError]
        valid, errors = is_strict(source)
        assert valid is True
        assert len(errors) == 0

    def test_invalid_code(self) -> None:
        source: str = """def foo(x) -> None:
    pass
"""
        valid: bool
        errors: list[TypeError]
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 1
        assert "missing type annotation" in errors[0].message
```

**Key patterns:**

- Keep the Python code inside triple-quoted strings at column zero. Indenting
  it to match the test body produces an `IndentationError`, which the checker
  reports as a syntax error rather than the rule under test.
- Use `is_strict()` for a quick `(valid, errors)` result.
- Use `check_file()` and `tmp_path` when file reading is part of the behavior.
- Assert the number of errors deliberately; a missing return annotation and a
  missing parameter annotation produce two separate errors.

### 2. Integration Tests (CLI)

The active CLI tests use `_run_nakprok_entrypoint(*args)`, which runs
`poetry run nakprok` with a 30-second timeout. It verifies the installed entry
point and package metadata, so it requires `poetry install`.

`tests/test_cli.py` also defines an unused `_run_nakprok(*args)` helper that
builds `python -m nakprok.cli`. `cli.py` has no `if __name__ == "__main__"`
block, so that module invocation imports the module without calling `main()`.
Use the entry point for real CLI tests unless a `__main__` guard is added.

```python
class TestCLI:
    def test_check_missing_path(self) -> None:
        result: subprocess.CompletedProcess[str] = self._run_nakprok_entrypoint(
            "check", "/nonexistent/file.py"
        )
        assert result.returncode == 1
        assert "path not found" in result.stderr
```

**Key patterns:**

- Check `returncode`, `stdout`, and `stderr` separately.
- Type errors and usage errors go to `stderr`; success and help go to `stdout`.
- Test the installed entry point, especially for `--version`; the module
  invocation does not call `main()` because there is no `__main__` guard.
- Keep subprocess tests free of reliance on the developer's current directory
  when possible; use absolute temporary paths.

### 3. Runner Tests

Runner tests exercise the full check-then-execute pipeline. Prefer `tmp_path`
for new tests because pytest removes it automatically:

```python
from pathlib import Path

from nakprok.runner import run_file


def test_run_file_with_sibling_import(tmp_path: Path) -> None:
    helper: Path = tmp_path / "helper.py"
    helper.write_text("VALUE: int = 42\n")
    script: Path = tmp_path / "main.py"
    script.write_text(
        "import helper\n"
        "\n"
        "def main() -> None:\n"
        "    print(helper.VALUE)\n"
        "\n"
        "if __name__ == \"__main__\":\n"
        "    main()\n"
    )

    assert run_file(script) == 0
```

The older tests use `tempfile.NamedTemporaryFile(..., delete=False)` because
the file must remain readable after the `with` block closes. Those tests do not
explicitly unlink the files. Do not copy that pattern into new tests; use
`tmp_path` instead.

**Key patterns:**

- Assert the exact return code: `0` success, `1` type error or missing file,
  `2` ordinary runtime exception.
- Capture output with `capsys` when testing messages from `run_source()`.
- Test that `sys.path` and `sys.argv` are restored after a run.
- Test sibling imports with a real temporary directory, not by relying on the
  repository layout.
- Remember that `SystemExit` is not caught; in a test, a script calling
  `sys.exit(7)` raises through `run_file()`, and through the CLI the process
  exits `7`.

## Test Coverage

### Coverage Goals

- **Checker**: every visitor method, including `NamedExpr`, `MatchAs`, and
  `MatchStar`.
- **CLI**: every dispatch branch and exit code.
- **Runner**: success, missing file, type errors, runtime errors, argument
  forwarding, and sibling imports.

### Running Coverage Reports

```bash
# Terminal output
poetry run pytest tests/ --cov=nakprok --cov-report=term-missing

# HTML report
poetry run pytest tests/ --cov=nakprok --cov-report=html

# XML report (for CI)
poetry run pytest tests/ --cov=nakprok --cov-report=xml
```

The package name is `nakprok`; a misspelling such as `--cov=nakprek` produces
`module-not-imported` warnings and an empty report while the tests still pass,
so verify the coverage output rather than only the exit code.

## Edge Cases

Test these thoroughly:

1. **Empty input** — Empty source, empty files, and an empty directory passed
   to `nakprok check`.
2. **Syntax errors** — Invalid Python is converted to a single `TypeError` with
   a `syntax error:` prefix.
3. **Missing paths** — `nakprok check` and `nakprok run` must fail instead of
   silently succeeding.
4. **Module-level vs function-level** — Assignment, loop, `with`, `match`, and
   walrus checks apply inside functions; function signature, lambda, and
   constant checks still apply at module level.
5. **Constants** — UPPERCASE names, re-assignment across functions, and the
   annotation exemption.
6. **Nested structures** — Nested functions, classes, loops, and `with` blocks.
7. **Error messages** — Exact format, pluralization, indentation, and stream.
8. **Process semantics** — `SystemExit` propagation, `KeyboardInterrupt`, and
   `sys.path`/`sys.argv` restoration.
9. **File discovery** — Recursive `.py` scanning, sorted order, and
   non-`.py` files passed explicitly.

## Test Isolation

- Each test must be independent; do not rely on ordering or mutable module
  state.
- Use `tmp_path` for files and directories. It is unique per test and cleaned
  up by pytest.
- If you must use `tempfile`, either delete the file in a `finally` block or
  use `tmp_path`; `delete=False` alone does not clean up.
- Avoid changing the process-wide working directory; pass absolute paths.
- Subprocess CLI tests should not depend on repository-relative files unless
  they construct the path from `Path(__file__)`.

## Running Tests

```bash
# All tests
poetry run pytest tests/ -v

# One file
poetry run pytest tests/test_checker.py -v

# One class or test
poetry run pytest tests/test_cli.py::TestCLI::test_version_flag -v

# With coverage
poetry run pytest tests/ -v --cov=nakprok --cov-report=term-missing

# Parallel execution
poetry run pytest tests/ -v -n auto
```

For the dependency-refreshing CI-style run, `scripts/runtest.sh` updates
packages, reinstalls the project, regenerates `poetry.lock`, and then runs
pytest with xdist and coverage. Review its lockfile changes before committing.

## Related Documentation

- [Development Environment Setup](./setup.md)
- [Coding Conventions & Style Guide](./conventions.md)
- [Error Handling & Exit Codes](./error-handling.md)
- [Documentation index](../index.md)
