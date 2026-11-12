# nakprok - Python with Enforced Static Typing

[![License](https://img.shields.io/pypi/l/nakprok)](LICENSE)
[![Python Compatibility](https://img.shields.io/pypi/pyversions/nakprok)](#installation)
[![PyPI Version](https://img.shields.io/pypi/v/nakprok.svg)](https://pypi.org/project/nakprok/)
[![Ask DeepWiki](https://img.shields.io/badge/Ask-DeepWiki-blue)](https://deepwiki.com/cwt/nakprok)<!-- [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/cwt/nakprok) -->
[![View Code Wiki](https://assets.codewiki.google/readme-badge/static.svg)](https://codewiki.google/github.com/cwt/nakprok?utm_source=badge&utm_medium=github&utm_campaign=github.com/cwt/nakprok)

**Same Python syntax. Explicit type annotations required.**

`nakprok` (นาคปรก) is a subset of Python that enforces static type annotations
everywhere. It's not a new language, but a stricter runtime for the Python you
already know. Code that violates the rules is blocked when run through
`nakprok`.

> **Why the name?** Nakprok is a depiction of the Buddha sheltered by the
> multi-headed serpent Nāga in Thai Buddhist art. Just as the Naga protected the
> Buddha, this project protects your code from untyped or mistyped logic.

## 🚀 Key Concepts

1. **Explicit is Better than Implicit**: If a value's type can't be seen in the
   code, it shouldn't be there.
2. **No per-operation overhead**: Validation happens once at startup. After the
   AST check and `compile()`, validated code runs as ordinary CPython. There is
   still startup cost for the extra parse and AST traversal.
3. **Ecosystem Compatibility**: Imported libraries run unchanged. A script is
   executed with its own directory on `sys.path`, matching `python file.py`.
4. **No New Syntax**: Uses standard Python 3.10+ type hinting syntax.
5. **Checks Before Execution**: `nakprok run` and the direct-execution shorthand
   block execution when type checking fails; nothing is executed.

## 🆚 How is this different from mypy?

`nakprok` is **not** a replacement for `mypy`. They tackle type safety from
different angles and work well together:

|            | **mypy**                         | **nakprok**                                              |
|------------|----------------------------------|----------------------------------------------------------|
| **When**   | Static analysis (separate step)  | AST validation before execution                          |
| **What**   | Deep type inference & checking   | Enforces *explicit* type declarations                    |
| **Scope**  | All valid Python                 | Strict subset (blocks `lambda`, untyped unpacking, etc.) |
| **Result** | Advisory report (can be ignored) | Hard block when run through `nakprok`                    |

Think of it this way:

- **nakprok** ensures every value is *explicitly typed* at the source level.
- **mypy** then verifies those types are *semantically correct* (e.g., protocol
  compliance, generic constraints, `int` where `float` is expected).

You can (and should) run both:

```bash
nakprok check src/     # Enforces explicit typing
mypy .                 # Validates type correctness
```

In this repository, check the source and test directories because
`examples/invalid.py` is intentionally invalid:

```bash
nakprok check nakprok/ tests/
```

## 🛠️ Implemented Rules

The assignment, loop, `with`, `match`, and walrus rules below apply **inside
functions and methods**. Function signatures are checked at every nesting
level, and UPPERCASE reassignment is tracked globally. Module-level variable
annotations are not enforced yet, and module-level class-body assignments are
not validated.

See [docs/overview.md](docs/overview.md) for the full rule and scope reference.

### 1. Function Signatures

- **All parameters must be typed**: `def add(a: int, b: int) -> int` is
  required.
- **Return types are mandatory**: `-> None` or `-> int` must be specified.
- **Exceptions**: `self` and `cls` parameters in methods are exempt.
- **Variadic arguments**: `*args: str` and `**kwargs: Any` must also have
  annotations.

### 2. Variable Declarations

- **Strict Local Typing**: Every local variable must be declared with a type.
  - `x: int = 10` (annotated assignment)
  - `x: int` followed by `x = 10` (declaration then assignment)
- **Re-assignment**: Once a variable is typed in the current function scope, it
  can be re-assigned without repeating the annotation.

```python
def add() -> int:
    x: int = 10
    x = 20
    return x
```

### 3. Control Flow

- **For Loops**: Loop variables must be previously declared.

  ```python
  def loop() -> None:
      i: int
      for i in range(10):
          print(i)
  ```

- **With Statements**: Context manager variables must be previously declared.

  ```python
  from typing import TextIO

  def read_file() -> None:
      f: TextIO
      with open("file.txt") as f:
          print(f.read())
  ```

- **Match Case**: Variable captures via `as` in `match` patterns must be
  pre-declared with a type annotation.

  ```python
  def handle(data: object) -> None:
      val: int
      match data:
          case int() as val:
              print(val)
  ```

  Star patterns (`[*rest]`) follow the same rule:

  ```python
  def handle_items(items: list[int]) -> None:
      rest: list[int]
      match items:
          case [*rest]:
              print(rest)
  ```

  Type-only matches without binding (`case int():`) are always valid.

- **Walrus Operator**: The target of `:=` must be pre-declared with a type
  annotation.

  ```python
  def check(value: int) -> None:
      result: int
      if (result := value) > 0:
          print(result)
  ```

### 4. Global Constants

- **Immutability**: UPPERCASE variables are treated as constants and are
  **immutable** everywhere. Reassigning one through an assignment, loop,
  `with`, `match`, or walrus target, or redefining a function/class with that
  name, is an error.
- **Exemptions**: UPPERCASE assignments are exempt from annotation
  requirements, including local assignments inside functions.
- **Known gap**: UPPERCASE parameters join the constant namespace, but a
  parameter that shadows an existing constant is not reported yet.

### 5. Prohibited Features

- **Lambdas**: Blocked everywhere because Python provides no syntax for
  annotating their parameters or return types.
- **Untyped Unpacking**: `x, y = (1, 2)` is blocked inside functions unless
  `x` and `y` were previously declared. Module-level assignments are not
  checked yet.

## 🔮 Future Roadmap

The project aims to become a complete "strict mode" for Python. Future plans
include:

1. **Module-Level Enforcement**: Extend strict typing to all module-level
   variables (currently only UPPERCASE reassignment is tracked).
2. **Type-Safe Imports**: Validate that imported names are used consistently
   with their types (integration with `mypy` or `pyright` stubs).
3. **Strict Class Attributes**: Enforce that all class attributes are declared
   in the class body with types.
4. **Decorator Validation**: Ensure decorators preserve type information and
   are themselves strictly typed.
5. **Linter Integration**: A dedicated VS Code / PyCharm extension to show
   `nakprok` errors in real time.

## 📦 Installation & Usage

### Installation

**For users** (from PyPI):

```bash
pip install nakprok
```

**For developers** (from a cloned repository):

```bash
poetry install
```

Poetry installs the package in editable mode together with the development
dependencies. There is no `.[dev]` extra. See
[docs/dev/setup.md](docs/dev/setup.md) for setup and test commands.

### Usage

```bash
# Check and run (default)
nakprok file.py

# Check types only (file or directory)
nakprok check file.py
nakprok check src/

# Explicit run
nakprok run file.py
```

`nakprok check` has no exclude or ignore option. Point it at source and test
directories when a tree contains intentionally invalid samples or vendored
Python files.

### Exit Codes

- `0`: success, including help, version, and an empty `check` directory.
- `1`: type errors, missing arguments, a missing path or file, an unknown
  command, or no arguments.
- `2`: an ordinary exception during `run`.
- Other: a `SystemExit` code raised by the executed script propagates.

### Example: `factorial.py`

```python
def factorial(n: int) -> int:
    if n <= 1:
        return 1
    return n * factorial(n - 1)


def main() -> None:
    result: int = factorial(5)
    print(f"5! = {result}")


if __name__ == "__main__":
    main()
```

```bash
$ nakprok factorial.py
5! = 120
```

## 🧪 Testing

```bash
poetry run pytest tests/ -v
poetry run mypy .
poetry run nakprok check nakprok/ tests/
```

## 📚 Documentation

- [Documentation index](docs/index.md)
- [Overview and rules](docs/overview.md)
- [CLI API](docs/api/cli.md)
- [Development setup](docs/dev/setup.md)
- [Changelog](CHANGELOG.md)
