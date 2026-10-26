---
type: api_spec
title: "Checker API — StrictTypeChecker"
description: "AST visitor that enforces strict type annotations in Python code."
tags:
  - api
  - checker
  - ast
  - type-checking
timestamp: "2026-10-26T00:00:00Z"
resource: "nakprok/checker.py"
---

# Checker API — StrictTypeChecker

## Overview

`StrictTypeChecker` is an `ast.NodeVisitor` that traverses Python AST trees and
enforces strict type annotation rules. It rejects code that lacks required type
hints.

Most assignment and control-flow rules are **function-scoped**. Module-level
variable assignments are not checked yet; function signatures, class/function
name tracking, `lambda` expressions, and UPPERCASE constant reassignment are
checked. See [Extension Points](../dev/extension-points.md) for the scope model.

## Module

```python
from nakprok.checker import StrictTypeChecker, check_source, check_file, is_strict
```

## Classes

### TypeError

Represents a type violation in the source code. The name shadows Python's
built-in `TypeError`; alias it if both are needed:

```python
from nakprok.checker import TypeError as NakprokTypeError
```

| Field | Type | Description |
| --- | --- | --- |
| `line` | `int` | Line number where the error occurred |
| `column` | `int` | Column offset where the error occurred |
| `message` | `str` | Human-readable error message |
| `filename` | `str` | Source file name (default: `""`) |

**String representation:**

```text
filename:line:column: error: message
```

If `filename` is empty, the format is:

```text
:line:column: error: message
```

### StrictTypeChecker

AST visitor that enforces strict type annotations.

#### Constructor

```python
def __init__(self, filename: str = "") -> None:
    ...
```

- `filename`: Name of the source file (for error reporting).

#### Attributes and Methods

| Member | Type / Returns | Description |
| --- | --- | --- |
| `errors` | `list[TypeError]` | All type errors found during traversal |
| `filename` | `str` | Filename used when constructing errors |
| `visit(node)` | `Any` | Inherited `ast.NodeVisitor` dispatch method |

#### Internal Methods

| Method | Description |
| --- | --- |
| `_validate_function(node)` | Check function signature for type annotations |
| `_check_assign_target(node)` | Recursively check assignment targets |
| `_check_for_target(node)` | Check for-loop variable targets |
| `_check_with_target(node)` | Check with-statement variable targets |
| `_error(node, message)` | Record a type error |

## Visitor Methods

### Function and Class Definitions

- **`visit_FunctionDef(node)`** — Validate regular function definitions and
  track UPPERCASE function names as constants.
- **`visit_AsyncFunctionDef(node)`** — Same validation for async functions.
- **`visit_ClassDef(node)`** — Track UPPERCASE class names as constants and
  traverse the class body. Module-level class-body assignments are not
  validated; a class defined inside a function inherits the enclosing
  function's scope state.

**Rules enforced:**

- All parameters (except `self`/`cls`) must have type annotations.
- `*args` must have a type annotation.
- `**kwargs` must have a type annotation.
- Return type must be annotated.
- UPPERCASE function/class names participate in the global constant namespace.

### Variable Declarations

- **`visit_Assign(node)`** — Flag untyped variable assignments inside functions.
- **`visit_AnnAssign(node)`** — Track typed variables inside functions and track
  UPPERCASE constants at any level.

**Rules enforced:**

- Every local variable must be typed before or at first assignment.
- Re-assignment after a declaration is allowed.
- Re-assignment of an untyped variable is flagged on each occurrence.
- UPPERCASE variables are treated as constants and are immutable.
- UPPERCASE assignments are exempt from annotation requirements, including
  local ones.

### Control Flow

- **`visit_For(node)`** — Loop variables must be pre-declared inside functions.
- **`visit_With(node)`** — Context manager variables must be pre-declared inside
  functions.
- **`visit_MatchAs(node)`** — Match pattern captures must be pre-declared inside
  functions.
- **`visit_MatchStar(node)`** — Star pattern captures must be pre-declared inside
  functions.
- **`visit_NamedExpr(node)`** — Walrus operator targets must be pre-declared
  inside functions.

**Rules enforced:**

- Loop variables must have type annotations.
- With-statement context manager variables must have type annotations.
- Match pattern `as` bindings must be pre-declared.
- Star patterns (`[*rest]`) must be pre-declared.
- Walrus targets (`:=`) must be pre-declared with a type annotation.

### Prohibited Features

- **`visit_Lambda(node)`** — Lambdas are not supported anywhere, including at
  module level.

## Public Functions

### `check_source(source: str, filename: str = "<string>") -> list[TypeError]`

Check Python source code for type annotation violations.

**Parameters:**

- `source`: Python source code string.
- `filename`: Optional filename for error reporting (default: `"<string>"`).

**Returns:**

- List of `TypeError` objects.

**Syntax errors:** `check_source` catches `SyntaxError` and returns a single
`TypeError` whose message is `syntax error: <detail>` instead of raising.

### `check_file(filepath: str | Path) -> list[TypeError]`

Check a Python file for type annotation violations.

**Parameters:**

- `filepath`: Path to a Python file. The file is read as UTF-8.

**Returns:**

- List of `TypeError` objects.

### `is_strict(source: str) -> tuple[bool, list[TypeError]]`

Check if source code is strictly typed.

**Parameters:**

- `source`: Python source code string.

**Returns:**

- Tuple of `(is_valid: bool, errors: list[TypeError])`.
- `is_valid` is `True` when no type violations are found.

## Scope Management

The checker tracks scope through function entry/exit:

1. On function entry, `self._typed_vars` is reset and parameter names are added.
2. On function exit, the previous scope is restored.
3. `_assigned_constants` is **not** reset; UPPERCASE constants share one global
   namespace across functions, classes, and module level.
4. Module-level assignments are not checked, so `_typed_vars` is not populated
   for module-level annotations.
5. UPPERCASE parameters are added to `_assigned_constants` without a duplicate
   check, so a parameter that shadows an existing constant is not reported.

## Error Messages

Common error messages:

| Error | Example |
| --- | --- |
| Missing return type | `function 'foo' missing return type annotation` |
| Missing param type | `parameter 'x' missing type annotation in 'foo'` |
| Missing *args type | `parameter '*args' missing type annotation in 'foo'` |
| Missing **kwargs type | `parameter '**kwargs' missing type annotation in 'foo'` |
| Untyped variable | `variable 'x' missing type annotation (use: x: Type = value)` |
| Untyped loop variable | `loop variable 'i' needs type annotation (consider using typed iterator)` |
| Untyped with variable | `variable 'f' missing type annotation in 'with' statement` |
| Untyped match binding | `variable 'val' in match pattern must be pre-declared (use: val: Type before match)` |
| Untyped walrus target | `variable 'x' in named expression must be pre-declared (use: x: Type before walrus operator)` |
| Lambda not supported | `lambda functions not supported (use def with type annotations)` |
| Constant re-assignment | `re-assignment to constant 'MAX_SIZE'` |
| Syntax error | `syntax error: <detail>` |

## Related Documentation

- [CLI API](./cli.md)
- [Runner API](./runner.md)
- [Extension Points](../dev/extension-points.md)
- [Documentation index](../index.md)
