---
type: api_spec
title: "CLI API — nakprok Command-Line Interface"
description: "Command-line interface for running and checking nakprok-typed Python files."
tags:
  - api
  - cli
  - command-line
  - entry-point
timestamp: "2026-10-26T00:00:00Z"
resource: "nakprok/cli.py"
---

# CLI API — nakprok Command-Line Interface

## Overview

The nakprok CLI checks and runs Python files that must satisfy the strict typing
rules enforced by `nakprok.checker`. It has two explicit commands (`run` and
`check`), a direct-execution shorthand, and `--version`/`--help` flags.

## Module

```python
from nakprok.cli import main
```

`main()` takes no arguments. It reads `sys.argv[1:]` and terminates with
`sys.exit()` in every branch.

## Entry Point

```bash
nakprok [command] <file.py|directory> [arguments]
```

## Commands

### `nakprok run <file.py> [arguments...]`

Check the file's types and execute it if the check passes.

- Type errors are printed to `stderr`, and the process exits `1`.
- If the file does not exist, `run_file()` prints
  `error: file not found: <path>` to `stderr` and the process exits `1`.
- If the script raises an ordinary exception, the runner prints
  `runtime error: <detail>` to `stderr` and the process exits `2`.
- Additional arguments after the filename are forwarded to the script through
  `sys.argv`.
- `SystemExit` and `KeyboardInterrupt` are **not** caught by the runner. A
  script that calls `sys.exit(7)` therefore makes nakprok exit with `7`, not
  `2`.

**Exit codes:**

| Code | Meaning |
| --- | --- |
| `0` | Type check passed and execution succeeded |
| `1` | Type check failed, or the file was not found |
| `2` | Type check passed but execution raised an ordinary exception |
| other | Propagated from the script via `SystemExit` |

### `nakprok check <file.py|directory>`

Check types only and do not execute the code.

- A file argument is checked directly, regardless of its extension.
- A directory argument is scanned recursively for `*.py` files.
- Files are checked in sorted path order, and all errors are reported.
- A nonexistent path prints `error: path not found: <path>` to `stderr` and
  exits `1`.
- A directory with no Python files prints `no Python files found in <path>` to
  `stderr`, then `✓ no type errors` to `stdout`, and exits `0`.
- There is no exclude or ignore option. Point the command at source and test
  directories when a tree contains intentionally invalid samples such as
  `examples/invalid.py`.

**Exit codes:**

| Code | Meaning |
| --- | --- |
| `0` | No type errors (including an empty directory) |
| `1` | One or more type errors, a missing argument, or a nonexistent path |

**Failure output:**

```text
type check failed (1 error):

  file.py:10:5: error: variable 'x' missing type annotation (use: x: Type = value)
```

The count is pluralized (`1 error`, `2 errors`). Each error is indented by two
spaces and printed to `stderr`.

**Success output:**

```text
✓ no type errors
```

This line goes to `stdout`.

### `nakprok --version`

Print the version reported by the installed package metadata:

```text
nakprok 0.3.0
```

Exits `0`.

### `nakprok --help` / `-h` / `help`

Print the help text to `stdout` and exit `0`.

### No arguments

Print the same help text to `stdout` and exit `1`. Invoking `nakprok` with no
arguments is treated as a usage error, not as a request for help.

## Direct File Execution

A `.py` file that exists at the first argument position is run directly, as if
`run` had been used:

```bash
nakprok myfile.py
nakprok myfile.py --flag1 --flag2
```

Arguments after the filename are forwarded to the script.

Any other unrecognized first argument prints:

```text
error: unknown command or file not found: '<argument>'
```

to `stderr`, prints the help text to `stdout`, and exits `1`. A bare filename
without a `.py` suffix is only accepted through the explicit `run` command.

## Argument Passing

With `run` or the direct-execution shorthand, the script sees:

```python
sys.argv == ["<path as given>", "--flag1", "--flag2"]
```

The runner saves the previous `sys.argv`, installs this list for the duration
of the call, and restores the previous contents afterward.

## Streams

| Output | Stream |
| --- | --- |
| Help text | `stdout` |
| `✓ no type errors` | `stdout` |
| Type errors and `type check failed (...)` | `stderr` |
| `runtime error: ...` | `stderr` |
| Missing argument and usage lines | `stderr` |
| Missing path or file | `stderr` |
| Unknown command plus help | Error on `stderr`, help on `stdout` |

## Implementation Details

### File Discovery

`_find_python_files()` yields a path directly when it is a file. For a
directory it uses `Path.rglob("*.py")`. `_check_path()` sorts the result before
checking so output order is stable.

### Argument Handling

- `run` and `check` require at least a second argument; otherwise both print
  `error: missing file argument` followed by a usage line to `stderr` and exit
  `1`.
- Extra arguments after the path are ignored by `check`; for `run` they are
  passed to the script.
- The first argument is matched exactly against `run`, `check`, `--help`,
  `-h`, `help`, and `--version`. Everything else is considered a candidate
  script path.

### Exit Code Summary

- **0**: Success, help, version, or an empty `check` directory.
- **1**: Type errors, missing argument, missing path/file, unknown command, or
  no arguments at all.
- **2**: Runtime exception during `run`.
- **Other**: A `SystemExit` code raised by the executed script propagates
  unchanged.

## Related Documentation

- [Checker API](./checker.md)
- [Runner API](./runner.md)
- [Error Handling & Exit Codes](../dev/error-handling.md)
- [Documentation index](../index.md)
