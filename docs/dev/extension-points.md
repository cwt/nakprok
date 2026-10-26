---
type: architecture_guideline
title: "Extension Points — Adding New Type Rules"
description: "How to add new type-checking rules to the nakprok checker."
tags:
  - architecture
  - extension
  - rules
  - development
  - customization
timestamp: "2026-10-26T00:00:00Z"
resource: "nakprok/checker.py"
---

# Extension Points — Adding New Type Rules

## Overview

`StrictTypeChecker` is an `ast.NodeVisitor`. New rules are added by implementing
`visit_<NodeType>` methods, updating checker state, and recording violations
with `self._error()`. This page describes the current rules, the state model,
and a safe pattern for adding a rule with tests.

## Current Rules

| Rule | Implemented In |
| --- | --- |
| Function parameter and return annotations | `visit_FunctionDef`, `visit_AsyncFunctionDef` via `_validate_function` |
| Local variable annotations | `visit_Assign` via `_check_assign_target`; `visit_AnnAssign` tracks typed names directly |
| UPPERCASE constant immutability | `visit_ClassDef`, `visit_FunctionDef`, `visit_AsyncFunctionDef`, `visit_Assign`, `visit_AnnAssign`, `visit_For`, `visit_With`, `visit_NamedExpr`, `visit_MatchAs`, `visit_MatchStar` |
| `for` target pre-declaration | `visit_For` |
| `with ... as` target pre-declaration | `visit_With` |
| `match` captures and star patterns | `visit_MatchAs`, `visit_MatchStar` |
| Walrus (`:=`) target pre-declaration | `visit_NamedExpr` |
| Lambda prohibition | `visit_Lambda` |

`_validate_function` checks `node.args.args`, `node.args.vararg`, and
`node.args.kwarg`, and skips parameters named `self` or `cls`. It does not
handle positional-only parameters (`node.args.posonlyargs`); adding that check
is a natural small extension.

## Adding a New Rule

### Step 1: Identify the AST Node

List concrete AST classes rather than visitor method names:

```python
import ast

node_names: list[str] = [
    name
    for name in dir(ast)
    if isinstance(getattr(ast, name), type)
    and issubclass(getattr(ast, name), ast.AST)
]
print(sorted(node_names))
```

The visitor method name must be `visit_` plus the class name, such as
`visit_While` for `ast.While`. CPython's `ast.NodeVisitor.visit()` dispatches on
`type(node).__name__`.

Common nodes:

- `FunctionDef`, `AsyncFunctionDef` — function definitions
- `Assign`, `AnnAssign`, `AugAssign` — assignments
- `For`, `While`, `With` — control flow
- `ClassDef` — class definitions
- `If`, `Try`, `Match` — branching
- `Import`, `ImportFrom` — imports

### Step 2: Implement the Visitor Method

A self-contained example that rejects `while` loops:

```python
import ast


class ExampleChecker(ast.NodeVisitor):
    """Illustrative checker; not part of nakprok."""

    def __init__(self) -> None:
        self.errors: list[str] = []

    def visit_While(self, node: ast.While) -> None:
        """Reject while loops (example rule)."""
        self.errors.append("while loops not supported (use for with typed iterator)")
        self.generic_visit(node)
```

Rules:

1. Call `self.generic_visit(node)` unless the method intentionally owns
   traversal of the subtree.
2. Record violations with `self._error(node, message)` in the real checker so
   line and column are captured.
3. Gate rules on `self._in_function` when they should not apply at module level.
4. Return `None`.

### Step 3: Track State if Needed

For rules that depend on previously typed names, use `_typed_vars` and respect
`_in_function`. This example requires an augmented-assignment target to be
declared first:

```python
def visit_AugAssign(self, node: ast.AugAssign) -> None:
    """Require augmented assignment targets to be pre-declared."""
    if isinstance(node.target, ast.Name):
        name: str = node.target.id
        if (
            self._in_function
            and not name.isupper()
            and name not in self._typed_vars
        ):
            self._error(
                node,
                f"variable '{name}' must be pre-declared before augmented assignment",
            )

    self.generic_visit(node)
```

UPPERCASE names are excluded because the checker exempts constants from
annotation requirements and tracks them in `_assigned_constants` instead.

### Step 4: Test Your Rule

Add tests to `tests/test_checker_extended.py` or a focused new file. Keep source
strings at column zero:

```python
from nakprok.checker import TypeError, is_strict


class TestAugmentedAssignmentRule:
    def test_declared_target_is_valid(self) -> None:
        source: str = """def bump() -> None:
    count: int = 0
    count += 1
"""
        valid: bool
        errors: list[TypeError]
        valid, errors = is_strict(source)
        assert valid is True
        assert len(errors) == 0

    def test_undeclared_target_is_invalid(self) -> None:
        source: str = """def bump() -> None:
    count += 1
"""
        valid: bool
        errors: list[TypeError]
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 1
        assert "must be pre-declared" in errors[0].message
```

Run the new tests and the full suite:

```bash
poetry run pytest tests/test_checker_extended.py -v
poetry run pytest tests/ -q
poetry run mypy .
```

## Common Patterns

### Track Typed Variables

`_typed_vars` holds names that have been annotated or are function parameters:

```python
# Add a name after a successful annotation
self._typed_vars.add(name)

# Check before using a name as an assignment target
if self._in_function and name not in self._typed_vars:
    self._error(node, f"variable '{name}' missing type annotation")
```

### Track Constants

`_assigned_constants` is a single namespace shared by the module, functions, and
classes:

```python
if name.isupper():
    if name in self._assigned_constants:
        self._error(node, f"re-assignment to constant '{name}'")
    self._assigned_constants.add(name)
```

### Scope Management

`visit_FunctionDef` and `visit_AsyncFunctionDef` save and restore state around
the function body:

```python
old_fn: str = self._function_name
old_in_fn: bool = self._in_function
old_vars: set[str] = self._typed_vars

self._function_name = node.name
self._in_function = True
self._typed_vars = set()

# ... visit parameters and body ...

self._function_name = old_fn
self._in_function = old_in_fn
self._typed_vars = old_vars
```

When adding a new visitor that changes state, either restore it immediately or
wrap the body in `try/finally`, so an unexpected exception cannot leave the
checker in a corrupted state.

### Error Reporting

```python
import ast
from typing import Protocol, cast

from .checker import TypeError


class _HasPosition(Protocol):
    lineno: int
    col_offset: int


def _error(self, node: ast.AST, message: str) -> None:
    """Record a type error with the node's source position."""
    pos: _HasPosition = cast(_HasPosition, node)
    self.errors.append(
        TypeError(
            line=pos.lineno,
            column=pos.col_offset,
            message=message,
            filename=self.filename,
        )
    )
```

## Scope Awareness

The checker is **function-scoped** for assignment and binding rules, but not
module-scoped:

- `_in_function` is `True` only while a function or method body is being
  visited.
- `_typed_vars` is replaced with a fresh set on function entry and restored on
  exit. It does not model branches, loops, or class bodies separately.
- `_assigned_constants` is never reset, so UPPERCASE constants share one global
  namespace. UPPERCASE parameters are added without a duplicate check, so
  shadowing a constant with a parameter is not reported yet.
- Function signatures are checked at every nesting level; class bodies are
  traversed, including their method definitions.
- Lambda rejection and UPPERCASE constant reassignment apply at module level
  too.
- Module-level variable assignments are **not** checked for annotations. Of the
  assignment checks, only the UPPERCASE reassignment check runs there.

Class bodies are traversed by `generic_visit`. At module level, `_in_function`
is `False`, so class-body assignments are not checked. A class defined inside a
function inherits `_in_function = True` and its body assignments are checked
against the enclosing function's `_typed_vars`; this is a known limitation of
the single-scope model.

To add module-level enforcement:

1. Add an explicit module/scope flag instead of relying on `not _in_function`.
2. Reset `_typed_vars` for the module and populate it from module-level
   `AnnAssign` nodes.
3. Decide how class bodies and comprehensions should scope names.
4. Add tests for module-level assignment, re-assignment, and nested classes.

## Testing Checklist

- [ ] Valid code passes with no errors.
- [ ] Invalid code produces exactly the expected error count.
- [ ] The error message contains the expected text.
- [ ] Error line and column point at the right node.
- [ ] Nested functions and classes restore state correctly.
- [ ] UPPERCASE names follow constant rules.
- [ ] Module-level behavior matches the intended scope.
- [ ] The CLI reports the new rule (`nakprok check`).
- [ ] The runner blocks execution (`nakprok run`).
- [ ] `poetry run pytest tests/` and `poetry run mypy .` pass.

## Example: Adding Decorator Validation

Insert this loop into the existing `visit_FunctionDef` before visiting the body.
It is a sketch of a policy rule, not part of the current checker:

```python
for decorator in node.decorator_list:
    if isinstance(decorator, ast.Name) and decorator.id == "untyped":
        self._error(
            decorator,
            "decorator 'untyped' does not preserve type information",
        )
```

Use the same pattern in `visit_AsyncFunctionDef` if the rule should apply to
async functions.

## Example: Rejecting Wildcard Imports

A complete rule that uses only the node and `_error`:

```python
def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
    """Reject wildcard imports (example rule)."""
    alias: ast.alias
    for alias in node.names:
        if alias.name == "*":
            self._error(node, "wildcard imports are not supported")

    self.generic_visit(node)
```

Add the corresponding valid and invalid cases to
`tests/test_checker_extended.py`, and run the full checks listed above.

## Related Documentation

- [Checker API](../api/checker.md)
- [Coding Conventions & Style Guide](./conventions.md)
- [Testing Strategy](./testing.md)
- [Documentation index](../index.md)
