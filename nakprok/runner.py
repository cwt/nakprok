"""
Runner for strictly-typed Python code.

Validates type annotations, then executes with standard Python.
"""

import sys
import types
from pathlib import Path

from .checker import TypeError, check_source


def run_file(filepath: str | Path, args: list[str] | None = None) -> int:
    """
    Check and run a strictly-typed Python file.

    Returns:
        0 if successful, 1 if type errors, 2 if execution error
    """
    filepath = Path(filepath)

    if not filepath.exists():
        print(f"error: file not found: {filepath}", file=sys.stderr)
        return 1

    source: str = filepath.read_text(encoding="utf-8")
    filename: str = str(filepath)

    # Type check
    errors: list[TypeError] = check_source(source, filename)
    if errors:
        print(
            f"type check failed ({len(errors)} error{'s' if len(errors) != 1 else ''}):\n",
            file=sys.stderr,
        )
        error: TypeError
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1

    # Execute with standard Python
    try:
        code: types.CodeType = compile(source, filename, "exec")
        sys.argv = [str(filepath)] + (args or [])
        exec(code, {"__name__": "__main__", "__file__": str(filepath)})
        return 0
    except Exception as e:
        print(f"runtime error: {e}", file=sys.stderr)
        return 2


def run_source(source: str, filename: str = "<string>") -> int:
    """
    Check and run Python source code.

    Returns:
        0 if successful, 1 if type errors, 2 if execution error
    """
    # Type check
    errors: list[TypeError] = check_source(source, filename)
    if errors:
        print(
            f"type check failed ({len(errors)} error{'s' if len(errors) != 1 else ''}):\n",
            file=sys.stderr,
        )
        error: TypeError
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1

    # Execute
    try:
        code: types.CodeType = compile(source, filename, "exec")
        exec(code, {"__name__": "__main__", "__file__": filename})
        return 0
    except Exception as e:
        print(f"runtime error: {e}", file=sys.stderr)
        return 2
