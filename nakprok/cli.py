"""
CLI for nakprok - Python with enforced static typing.

Usage:
    nakprok run <file.py>     Check types and run
    nakprok check <file.py>   Check types only
"""

import sys
from pathlib import Path
from typing import Iterable

from .checker import TypeError, check_file
from .runner import run_file


def _find_python_files(path: Path) -> Iterable[Path]:
    """Recursively find all .py files in a directory, or yield the file itself."""
    if path.is_file():
        yield path
    elif path.is_dir():
        yield from path.rglob("*.py")


def _check_path(path: Path) -> list[TypeError]:
    """Check a single file or directory for type errors."""
    py_files: list[Path] = list(_find_python_files(path))
    if not py_files:
        if path.is_dir():
            print(f"no Python files found in {path}", file=sys.stderr)
        return []

    all_errors: list[TypeError] = []
    filepath: Path
    for filepath in sorted(py_files):
        errors: list[TypeError] = check_file(filepath)
        all_errors.extend(errors)

    return all_errors


def main() -> None:
    """Entry point for nakprok CLI."""
    args: list[str] = sys.argv[1:]

    if not args:
        _print_help()
        sys.exit(1)

    command: str = args[0]

    # Check for known commands
    if command == "run":
        if len(args) < 2:
            print("error: missing file argument", file=sys.stderr)
            print("usage: nakprok run <file.py>", file=sys.stderr)
            sys.exit(1)

        filepath_str: str = args[1]
        exit_code: int = run_file(filepath_str, args[2:])
        sys.exit(exit_code)

    elif command == "check":
        if len(args) < 2:
            print("error: missing file argument", file=sys.stderr)
            print("usage: nakprok check <file.py|directory>", file=sys.stderr)
            sys.exit(1)

        path: Path = Path(args[1])
        errors: list[TypeError] = _check_path(path)

        if errors:
            print(
                f"type check failed ({len(errors)} error{'s' if len(errors) != 1 else ''}):\n",
                file=sys.stderr,
            )
            error: TypeError
            for error in errors:
                print(f"  {error}", file=sys.stderr)
            sys.exit(1)
        else:
            print("✓ no type errors")
            sys.exit(0)

    elif command in ("--help", "-h", "help"):
        _print_help()
        sys.exit(0)

    elif command == "--version":
        from . import __version__

        print(f"nakprok {__version__}")
        sys.exit(0)

    # If not a command, check if it's a file to run
    elif Path(command).exists() and command.endswith(".py"):
        exit_code = run_file(command, args[1:])
        sys.exit(exit_code)

    else:
        print(
            f"error: unknown command or file not found: '{command}'",
            file=sys.stderr,
        )
        _print_help()
        sys.exit(1)


def _print_help() -> None:
    """Print help message."""
    print("""nakprok - Python with enforced static typing

usage: nakprok [command] <file.py|directory> [arguments]

commands:
  [run] <file.py>       Check types and execute (default)
  check <file.py|dir>   Check types only, don't run
  --version             Show version
  --help                Show this help

examples:
  nakprok hello.py
  nakprok run hello.py
  nakprok check module.py
  nakprok check src/""")
