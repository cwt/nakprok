---
type: architecture_guideline
title: "nakprok — Python with Enforced Static Typing"
description: "A strict Python runtime that enforces explicit type annotations at the AST level, blocking untyped code from execution."
tags:
  - type-checking
  - static-typing
  - python
  - runtime-enforcement
  - ast-analysis
timestamp: "2026-10-26T00:00:00Z"
resource: "https://github.com/cwt/nakprok"
---

# nakprok — Python with Enforced Static Typing

## Overview

**nakprok** (นาคปรก) is a subset of Python that enforces static type annotations
everywhere. It is not a new language, but a stricter runtime for the Python you
already know. Code that violates the rules is blocked when it is run through
`nakprok`.

> **Why the name?** Nakprok is a depiction of the Buddha sheltered by the
> multi-headed serpent Nāga in Thai Buddhist art. Just as the Naga protected the
> Buddha, this project protects your code from untyped or mistyped logic.

## Key Concepts

- **Explicit is Better than Implicit**: If a value's type can't be seen in the
  code, it shouldn't be there.
- **No per-operation overhead**: Validation happens once at startup. After the
  AST check and `compile()`, the validated code runs as ordinary CPython. There
  is still startup cost for the extra parse and AST traversal.
- **Ecosystem Compatibility**: Imported libraries run unchanged. A script is
  executed with its own directory on `sys.path`, matching `python file.py`.
- **No New Syntax**: Uses standard Python 3.10+ type hinting syntax.

## Comparison with mypy

| Aspect | **mypy** | **nakprok** |
| --- | --- | --- |
| **When** | Static analysis (separate step) | AST validation before execution |
| **What** | Deep type inference & checking | Enforces *explicit* type declarations |
| **Scope** | All valid Python | Strict subset (blocks `lambda`, untyped unpacking, etc.) |
| **Result** | Advisory report (can be ignored) | Hard block when run through `nakprok` |

**Recommended workflow**:

```bash
nakprok check src/     # Enforces explicit typing
mypy .                 # Validates type correctness
```

In this repository, use the source and test directories because
`examples/invalid.py` is intentionally invalid:

```bash
nakprok check nakprok/ tests/
```

## Implemented Rules

The assignment, loop, `with`, `match`, and walrus checks below apply **inside
functions and methods**. Module-level variable assignments are not checked yet;
function signatures, class/function name tracking, lambdas, and UPPERCASE
constant reassignment are checked. Module-level enforcement is on the roadmap.

### Function Signatures

- All parameters must be typed: `def add(a: int, b: int)` is required.
- Return types are mandatory: `-> None` or `-> int` must be specified.
- Exceptions: `self` and `cls` parameters in methods are exempt.
- Variadic arguments: `*args: str` and `**kwargs: Any` must also have
  annotations.

### Variable Declarations

- **Strict Local Typing**: Every local variable must be declared with a type.
  - `x: int = 10` (annotated assignment)
  - `x: int` followed by `x = 10` (declaration then assignment)
- **Re-assignment**: Once a variable is typed in the current function scope, it
  can be re-assigned without repeating the annotation.

### Control Flow

- **For Loops**: Loop variables must be previously declared with a type.
- **With Statements**: Context manager variables must be previously declared.
- **Match Case**: Variable captures via `as` in `match` patterns must be
  pre-declared with a type annotation. Star patterns (`[*rest]`) follow the same
  rule. Type-only matches without binding (`case int():`) are always valid.
- **Walrus Operator**: The target of `:=` must be pre-declared with a type
  annotation:

  ```python
  def check() -> None:
      x: int
      if (x := 10) > 5:
          print(x)
  ```

### Global Constants

- **Immutability**: `UPPERCASE` variables are treated as constants and are
  immutable everywhere. Once assigned, reassigning one through an assignment,
  loop, `with`, `match`, or walrus target, or redefining a function/class with
  that name, is an error. UPPERCASE parameters join the same namespace, but
  shadowing a constant with a parameter is a known gap.
- **Exemptions**: UPPERCASE assignments are exempt from strict typing, including
  local assignments inside functions (e.g. `MAX_SIZE = 100`). The constant
  namespace is global, not function-scoped.

### Prohibited Features

- **Lambdas**: Blocked everywhere because Python provides no syntax for
  annotating their parameters or return types.
- **Untyped Unpacking**: `x, y = (1, 2)` is blocked inside functions unless `x`
  and `y` were previously declared. Module-level assignments are not checked yet.

## Architecture

```text
nakprok/
├── nakprok/
│   ├── __init__.py        # Package init, version metadata
│   ├── checker.py         # AST visitor for type validation (core logic)
│   ├── cli.py             # Command-line interface (run / check / --version)
│   └── runner.py          # Type-check then execute via compile()/exec()
├── tests/                 # Test suite (checker, cli, runner)
├── examples/              # Valid and invalid Python samples
├── scripts/               # CI/CD helpers
├── docs/                  # OKF documentation
├── pyproject.toml         # Project configuration
└── README.md              # Project overview
```

### Core Components

1. **`checker.py`** — AST visitor that traverses Python source code and
   validates type annotations. Rejects code with violations.
2. **`runner.py`** — Type-checks source via `checker.py`, then executes with
   standard Python `compile()` / `exec()`.
3. **`cli.py`** — CLI entry point with commands:
   - `nakprok run <file.py>` — Check types and execute
   - `nakprok check <file.py|dir>` — Check types only
   - `nakprok --version` / `--help`

## Installation

```bash
# From PyPI
pip install nakprok

# From source
pip install -e .
```

For development setup, see [Development Environment Setup](./dev/setup.md).

## Usage

```bash
# Check and run
nakprok file.py

# Check types only
nakprok check file.py
nakprok check src/

# Explicit run
nakprok run file.py
```

`nakprok check` currently has no exclude mechanism, so target source and test
directories when a tree contains intentionally invalid samples or vendored
Python files.

## Relationship to OKF Documents

- This project serves as an **architecture guideline** for enforced type safety.
- It complements static analysis tools (e.g., mypy) by operating at a different
  layer — runtime enforcement vs. static analysis.

## Roadmap

1. **Module-Level Enforcement**: Extend strict typing to all module-level
   variables (currently only UPPERCASE constants are tracked).
2. **Type-Safe Imports**: Validate imported names are used consistently with
   their types.
3. **Strict Class Attributes**: Enforce class attributes declared with types in
   the class body.
4. **Decorator Validation**: Ensure decorators preserve type information.
5. **Linter Integration**: VS Code / PyCharm extension for real-time error
   display.
