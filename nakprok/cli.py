"""
CLI for nakprok - Python with enforced static typing.

Usage:
    nakprok run <file.py>     Check types and run
    nakprok check <file.py>   Check types only
"""

import sys
from pathlib import Path

from .checker import check_file
from .runner import run_file


def main() -> None:
    """Entry point for nakprok CLI."""
    args = sys.argv[1:]

    if not args:
        _print_help()
        sys.exit(1)

    command = args[0]

    # Check for known commands
    if command == "run":
        if len(args) < 2:
            print("error: missing file argument", file=sys.stderr)
            print("usage: nakprok run <file.py>", file=sys.stderr)
            sys.exit(1)

        filepath = args[1]
        exit_code = run_file(filepath, args[2:])
        sys.exit(exit_code)

    elif command == "check":
        if len(args) < 2:
            print("error: missing file argument", file=sys.stderr)
            print("usage: nakprok check <file.py>", file=sys.stderr)
            sys.exit(1)

        filepath = args[1]
        errors = check_file(filepath)

        if errors:
            print(
                f"type check failed ({len(errors)} error{'s' if len(errors) != 1 else ''}):\n",
                file=sys.stderr,
            )
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

usage: nakprok [command] <file.py> [arguments]

commands:
  [run] <file.py>   Check types and execute (default)
  check <file.py>   Check types only, don't run
  --version         Show version
  --help            Show this help

examples:
  nakprok hello.py
  nakprok run hello.py
  nakprok check module.py""")
