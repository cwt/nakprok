---
type: api_spec
title: "Runner API — Type-Check and Execute"
description: "Pipeline that type-checks Python source code and then executes it with standard Python."
tags:
  - api
  - runner
  - execution
  - pipeline
timestamp: "2026-10-26T00:00:00Z"
resource: "nakprok/runner.py"
---

# Runner API — Type-Check and Execute

## Overview

The `runner` module checks source code with `check_source()` and, only when the
check passes, executes it with the standard `compile()` / `exec()` machinery.
There is no custom bytecode or instrumented runtime.

## Module

```python
from nakprok.runner import run_file, run_source
```

## Functions

### `run_file(filepath: str | Path, args: list[str] | None = None) -> int`

Check and run a strictly-typed Python file.

**Parameters:**

- `filepath`: Path to a Python file (string or `Path`).
- `args`: Optional list of command-line arguments for the script.

**Returns:** An exit code: `0` on success, `1` for a missing file or type
errors, `2` for an ordinary runtime exception.

**Behavior:**

1. Convert `filepath` to `Path`.
2. If the path does not exist, print `error: file not found: <path>` to
   `stderr` and return `1`.
3. Read the file as UTF-8 and type-check it with
   `check_source(source, str(filepath))`.
4. If type errors exist, print `type check failed (...)` and each error to
   `stderr`, then return `1`. Nothing is executed.
5. Save the current `sys.path` and `sys.argv`, then insert the resolved
   script's parent directory at the front of `sys.path`. This makes sibling
   imports behave like `python file.py`.
6. Compile with `compile(source, filename, "exec")`.
7. Set `sys.argv` to `[str(filepath)] + args` and execute in a namespace
   containing `__name__ == "__main__"` and `__file__ == str(filepath)`.
8. Return `0` if execution completes.
9. If execution raises an `Exception`, print `runtime error: <detail>` to
   `stderr` and return `2`.
10. In a `finally` block, restore the original `sys.path` and `sys.argv`
    contents in place.

**Exit codes:**

| Code | Meaning |
| --- | --- |
| `0` | Type check passed and execution succeeded |
| `1` | File not found or type check failed |
| `2` | Execution raised an ordinary `Exception` |

### `run_source(source: str, filename: str = "<string>") -> int`

Check and run source code supplied as a string.

**Parameters:**

- `source`: Python source code.
- `filename`: Name used in error messages and in the execution namespace
  (default: `"<string>"`).

**Returns:** The same `0` / `1` / `2` exit codes as `run_file()`.

**Behavior:**

1. Type-check with `check_source(source, filename)`.
2. Print and return `1` on type errors.
3. Compile and execute the code in a namespace containing `__name__` set to
   `"__main__"` and `__file__` set to `filename`.
4. Return `0` on success, or print `runtime error: <detail>` and return `2` on
   an ordinary exception.

`run_source()` does **not** modify `sys.path` or `sys.argv`.

## Exception Boundaries

Both functions catch only `Exception`, not `BaseException`. Consequences:

- `SystemExit` propagates to the caller. Through the CLI, a script calling
  `sys.exit(3)` exits the process with `3`; it is not converted to `2`.
- `KeyboardInterrupt` propagates, so Ctrl-C is not reported as a runtime error.
- Errors raised while reading the file (for example, an unreadable path) occur
  before the `try` block and propagate as normal Python exceptions.

## Output Formats

### Type Errors (return `1`)

```text
type check failed (1 error):

  file.py:10:5: error: variable 'x' missing type annotation (use: x: Type = value)
```

The count is pluralized. All lines go to `stderr`.

### Missing File (return `1`)

```text
error: file not found: missing.py
```

### Runtime Errors (return `2`)

```text
runtime error: division by zero
```

Only the exception's string form is shown; no traceback is printed.

## Implementation Notes

- Execution uses standard `compile()` and `exec()`; there is no per-operation
  interpretation overhead after startup.
- The explicit execution globals are `__name__` and `__file__`; Python adds
  `__builtins__` automatically. The script's imports still use the normal
  import system and `sys.path`.
- `sys.path` insertion matches `python file.py` for sibling modules, but
  `run_source()` intentionally does not alter import paths.
- `sys.path` is restored in place with slice assignment. `sys.argv` is replaced
  for the run and its previous contents are copied back in the `finally` block;
  the original `sys.argv` list object is not reinstalled.

## Relationship to Checker

```python
from nakprok.checker import TypeError, check_source
```

The runner depends on the checker for validation and on the CLI for process
exit-code handling. See [Checker API](./checker.md) and
[CLI API](./cli.md).
