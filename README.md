# nakprok - Python with Enforced Static Typing

**Same Python syntax. Zero dynamic typing.**

`nakprok` (นาคปรก) is a subset of Python that enforces static type annotations everywhere. It's not a new language, but a stricter runtime for the Python you already know.

> **Why the name?** Nakprok is a depiction of the Buddha sheltered by the multi-headed serpent Nāga in Thai Buddhist art. Just as the Naga protected the Buddha, this project protects your code from untyped or mistyped logic.

## 🚀 Key Concepts

1.  **Explicit is Better than Implicit**: If a value's type can't be seen in the code, it shouldn't be there.
2.  **Zero Runtime Overhead**: Validation happens at the AST level before execution. Once validated, it runs as standard CPython.
3.  **Ecosystem Compatibility**: Works with all existing Python libraries and tools.
4.  **No New Syntax**: Uses standard Python 3.10+ type hinting syntax.

---

## 🛠️ Implemented Rules

`nakprok` currently enforces the following rules inside functions (and classes):

### 1. Function Signatures
- **All parameters must be typed**: `def add(a: int, b: int)` is required.
- **Return types are mandatory**: `-> None` or `-> int` must be specified.
- **Exceptions**: `self` and `cls` parameters in methods are exempt.
- **Variadic arguments**: `*args: str` and `**kwargs: Any` must also have annotations.

### 2. Variable Declarations
- **Strict Local Typing**: Every local variable must be declared with a type.
    - `x: int = 10` (Annotated assignment)
    - `x: int` followed by `x = 10` (Declaration then assignment)
- **Re-assignment**: Once a variable is typed in the current scope, it can be re-assigned without repeating the annotation.
    ```python
    x: int = 10
    x = 20  # Valid
    ```

### 3. Control Flow
- **For Loops**: Loop variables must be previously declared.
    ```python
    i: int
    for i in range(10): ...
    ```
- **With Statements**: Context manager variables must be previously declared.
    ```python
    f: TextIO
    with open("file.txt") as f: ...
    ```
- **Match Case**: Variable captures in `match` patterns (e.g., `case int(val):`) are currently blocked because they don't support standard Python annotations. Use body annotations instead:
    ```python
    match data:
        case int():
            val: int = data
            ...
    ```

### 4. Global Constants
- **Exemptions**: UPPERCASE constants at the module level are exempt from strict typing by convention (e.g., `MAX_SIZE = 100`).

### 5. Prohibited Features
- **Lambdas**: Blocked because Python provides no syntax for annotating their parameters or return types.
- **Untyped Unpacking**: `x, y = (1, 2)` is blocked unless `x` and `y` were previously declared.

---

## 🔮 Future Roadmap

The project aims to become a complete "strict mode" for Python. Future plans include:

1.  **Module-Level Enforcement**: Extend strict typing to all module-level variables (not just UPPERCASE constants).
2.  **Type-Safe Imports**: Validate that imported names are used consistently with their types (integration with `mypy` or `pyright` stubs).
3.  **Match Pattern Enhancement**: Explore custom syntax or clever AST transforms to allow inline typing in `match` patterns.
4.  **Strict Class Attributes**: Enforce that all class attributes are declared in the class body with types.
5.  **Decorator Validation**: Ensure decorators preserve type information and are themselves strictly typed.
6.  **Linter Integration**: A dedicated VS Code / PyCharm extension to show `nakprok` errors in real-time.

---

## 📦 Installation & Usage

### Installation
```bash
pip install -e .
```

### Usage
```bash
# Check and run (default)
nakprok file.py

# Check types only
nakprok check file.py

# Explict run
nakprok run file.py
```

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

---

## 🧪 Testing

We maintain a comprehensive test suite to ensure all rules are correctly enforced.

```bash
pytest tests/ -v
```
