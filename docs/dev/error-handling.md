---
type: development_rules
title: "Error Handling & Exit Codes"
description: "Standardized error handling patterns and exit code semantics for nakprok."
tags:
  - errors
  - exit-codes
  - handling
  - conventions
  - cli
timestamp: "2026-10-26T00:00:00Z"
resource: "nakprok/cli.py"
---

# Error Handling & Exit Codes

## Exit Code Semantics

| Code | Meaning | When Used |
| --- | --- | --- |
| `0` | Success | Type check passed and execution succeeded; `check` found no errors; help or version printed; `check` scanned an empty directory |
| `1` | Failure | Type errors; missing argument; missing path or file; unknown command; no arguments |
| `2` | Runtime error | Type check passed but an ordinary exception escaped during execution |
| other | Propagated | A `SystemExit` code raised by the executed script |

`nakprok` with no arguments prints help and exits `1`. Explicit `--help`,
`-h`, or `help` exits `0`.

## Error Output

Errors go to **stderr**; success messages and help go to **stdout**.

### Type Errors

```text
type check failed (1 error):

  file.py:10:5: error: variable 'x' missing type annotation (use: x: Type = value)
```

The summary line is followed by a blank line. Each error is indented by two
spaces. The count is pluralized (`1 error`, `2 errors`). Both `run` and `check`
use this format.

### Runtime Errors

```text
runtime error: division by zero
```

No traceback is printed. Only `str(exception)` is shown.

### Missing File or Path

```text
error: file not found: missing.py
```

```text
error: path not found: missing/
```

`run_file()` returns `1` for a missing file. The `check` command detects a
missing path in `main()` and exits `1` before scanning.

### Usage Errors

```text
error: missing file argument
usage: nakprok run <file.py>
```

Both lines go to stderr, and the process exits `1`. The `check` variant uses:

```text
usage: nakprok check <file.py|directory>
```

### Unknown Command

```text
error: unknown command or file not found: 'bogus'
```

The error goes to stderr, followed by the full help text on stdout. The exit
code is `1`.

### Empty Directory

```text
no Python files found in empty_dir
```

This goes to stderr, then `✓ no type errors` goes to stdout and the exit code
is `0`. An empty directory is not an error.

## Error Type Hierarchy

There is exactly one public error class:

```python
from dataclasses import dataclass


@dataclass
class TypeError:
    line: int
    column: int
    message: str
    filename: str = ""
```

There are no `MissingAnnotationError`, `ConstantReassignmentError`, or
`ProhibitedFeatureError` subclasses. All violations, including syntax errors,
are `TypeError` instances whose `message` distinguishes the cause. Future
specific types would be an API change and should be documented here.

## Error Message Format

```text
filename:line:column: error: message
```

If `filename` is empty:

```text
:line:column: error: message
```

`check_source()` defaults to `filename="<string>"`, so ordinary string-based
checks show that name. Syntax errors use line `0` or the parser's reported line
and column when available.

## Common Error Messages

| Scenario | Message Template |
| --- | --- |
| Missing return type | `function '{name}' missing return type annotation` |
| Missing param type | `parameter '{name}' missing type annotation in '{func}'` |
| Missing `*args` type | `parameter '*{name}' missing type annotation in '{func}'` |
| Missing `**kwargs` type | `parameter '**{name}' missing type annotation in '{func}'` |
| Untyped variable | `variable '{name}' missing type annotation (use: {name}: Type = value)` |
| Untyped loop variable | `loop variable '{name}' needs type annotation (consider using typed iterator)` |
| Untyped `with` variable | `variable '{name}' missing type annotation in 'with' statement` |
| Untyped match binding | `variable '{name}' in match pattern must be pre-declared (use: {name}: Type before match)` |
| Untyped walrus target | `variable '{name}' in named expression must be pre-declared (use: {name}: Type before walrus operator)` |
| Lambda not supported | `lambda functions not supported (use def with type annotations)` |
| Constant reassignment | `re-assignment to constant '{name}'` |
| Syntax error | `syntax error: {detail}` |

Notes:

- Function and class names that are UPPERCASE enter the constant namespace, so
  redefining one produces `re-assignment to constant`.
- Parameters named in UPPERCASE also enter the constant namespace, but they are
  added without a duplicate check, so shadowing a constant with a parameter is
  not reported.
- Attribute and subscript assignment targets are not checked; the checker
  assumes the owning object is typed.

## CLI Error Handling

### No Arguments

```python
args: list[str] = sys.argv[1:]
if not args:
    _print_help()
    sys.exit(1)
```

### Missing Command Argument

```python
if command == "run" and len(args) < 2:
    print("error: missing file argument", file=sys.stderr)
    print("usage: nakprok run <file.py>", file=sys.stderr)
    sys.exit(1)
```

`check` follows the same pattern with its own usage line.

### Missing `check` Path

```python
path: Path = Path(args[1])
if not path.exists():
    print(f"error: path not found: {path}", file=sys.stderr)
    sys.exit(1)
```

This guard matters: `_check_path()` returns an empty error list for paths that
do not exist, so without it a typo would be reported as success.

### Missing Run File

`run_file()` handles this below the CLI:

```python
if not filepath.exists():
    print(f"error: file not found: {filepath}", file=sys.stderr)
    return 1
```

### Unknown Command Dispatch

```python
else:
    print(f"error: unknown command or file not found: '{command}'", file=sys.stderr)
    _print_help()
    sys.exit(1)
```

## Runtime Error Handling

```python
old_path: list[str] = sys.path.copy()
old_argv: list[str] = sys.argv.copy()
sys.path.insert(0, str(filepath.resolve().parent))

try:
    code: types.CodeType = compile(source, filename, "exec")
    sys.argv = [str(filepath)] + (args or [])
    exec(code, {"__name__": "__main__", "__file__": str(filepath)})
    return 0
except Exception as e:
    print(f"runtime error: {e}", file=sys.stderr)
    return 2
finally:
    sys.path[:] = old_path
    sys.argv[:] = old_argv
```

### Exception Boundary

Only `Exception` is caught. Therefore:

- `SystemExit` propagates. Through the CLI, `sys.exit(7)` in a script exits the
  process with `7`, not `2`.
- `KeyboardInterrupt` propagates and is not reported as a runtime error.
- Errors while reading the file happen before the `try` block and propagate.
- Errors while importing modules during execution are inside the `try` and are
  reported as runtime errors with exit code `2`.

## Testing Error Handling

Tests should verify:

1. **Exact exit code** — `result.returncode == expected_code`.
2. **Correct stream** — errors in `stderr`, success in `stdout`.
3. **Message content** — summary, pluralization, and indentation.
4. **Edge cases** — missing paths, empty directories, syntax errors,
   `SystemExit`, and sibling-import failures.
5. **State restoration** — `sys.path` and `sys.argv` are unchanged after
   `run_file()`.

## Future Improvements

- **Specific error types** — Subclasses for syntax, annotation, and constant
  violations, if the API cost is justified.
- **Error severity levels** — Warn versus error versus fatal.
- **Interactive mode** — Prompt the user to fix errors before retrying.
- **Error suggestions** — Hints for common fixes.
- **Exclude patterns** — Let `check` skip intentionally invalid samples and
  vendored code.

## Related Documentation

- [CLI API](../api/cli.md)
- [Runner API](../api/runner.md)
- [Testing Strategy](./testing.md)
- [Documentation index](../index.md)
