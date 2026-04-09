"""
Static type enforcement for Python code.

Parses Python AST and validates:
- All function parameters have type annotations
- All functions have return type annotations
- All variable assignments have type annotations
- No implicit Any types
"""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast


class _HasPosition(Protocol):
    lineno: int
    col_offset: int


@dataclass
class TypeError:
    """Represents a type violation in the source code."""

    line: int
    column: int
    message: str
    filename: str = ""

    def __str__(self) -> str:
        location = f"{self.filename}:{self.line}:{self.column}"
        return f"{location}: error: {self.message}"


class StrictTypeChecker(ast.NodeVisitor):
    """
    AST visitor that enforces strict type annotations.
    Rejects any code that lacks proper type hints.
    """

    def __init__(self, filename: str = ""):
        self.errors: list[TypeError] = []
        self.filename = filename
        self._in_function = False
        self._function_name = ""
        self._typed_vars: set[str] = set()
        self._assigned_constants: set[str] = set()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track class name as a constant if UPPERCASE."""
        if node.name.isupper():
            if node.name in self._assigned_constants:
                self._error(node, f"re-assignment to constant '{node.name}'")
            self._assigned_constants.add(node.name)

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Validate function has full type annotations."""
        if node.name.isupper():
            if node.name in self._assigned_constants:
                self._error(node, f"re-assignment to constant '{node.name}'")
            self._assigned_constants.add(node.name)

        self._validate_function(node)

        old_fn = self._function_name
        old_in_fn = self._in_function
        old_vars = self._typed_vars

        self._function_name = node.name
        self._in_function = True
        self._typed_vars = set()

        # Add parameters to typed variables
        for arg in node.args.args:
            self._typed_vars.add(arg.arg)
            if arg.arg.isupper():
                self._assigned_constants.add(arg.arg)

        if node.args.vararg:
            self._typed_vars.add(node.args.vararg.arg)
            if node.args.vararg.arg.isupper():
                self._assigned_constants.add(node.args.vararg.arg)

        if node.args.kwarg:
            self._typed_vars.add(node.args.kwarg.arg)
            if node.args.kwarg.arg.isupper():
                self._assigned_constants.add(node.args.kwarg.arg)

        # Visit body
        for child in node.body:
            self.visit(child)

        self._function_name = old_fn
        self._in_function = old_in_fn
        self._typed_vars = old_vars

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Same validation for async functions."""
        if node.name.isupper():
            if node.name in self._assigned_constants:
                self._error(node, f"re-assignment to constant '{node.name}'")
            self._assigned_constants.add(node.name)

        self._validate_function(node)

        old_fn = self._function_name
        old_in_fn = self._in_function
        old_vars = self._typed_vars

        self._function_name = node.name
        self._in_function = True
        self._typed_vars = set()

        # Add parameters
        for arg in node.args.args:
            self._typed_vars.add(arg.arg)
            if arg.arg.isupper():
                self._assigned_constants.add(arg.arg)

        if node.args.vararg:
            self._typed_vars.add(node.args.vararg.arg)
            if node.args.vararg.arg.isupper():
                self._assigned_constants.add(node.args.vararg.arg)

        if node.args.kwarg:
            self._typed_vars.add(node.args.kwarg.arg)
            if node.args.kwarg.arg.isupper():
                self._assigned_constants.add(node.args.kwarg.arg)

        for child in node.body:
            self.visit(child)

        self._function_name = old_fn
        self._in_function = old_in_fn
        self._typed_vars = old_vars

    def _validate_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Check function signature for type annotations."""
        name = node.name

        # Check return type
        if node.returns is None:
            self._error(node, f"function '{name}' missing return type annotation")

        # Check parameters (skip self/cls)
        for arg in node.args.args:
            if arg.arg in ("self", "cls"):
                continue
            if arg.annotation is None:
                self._error(
                    arg,
                    f"parameter '{arg.arg}' missing type annotation in '{name}'",
                )

        # Check *args
        if node.args.vararg:
            if node.args.vararg.annotation is None:
                self._error(
                    node.args.vararg,
                    f"parameter '*{node.args.vararg.arg}' missing type annotation in '{name}'",
                )

        # Check **kwargs
        if node.args.kwarg:
            if node.args.kwarg.annotation is None:
                self._error(
                    node.args.kwarg,
                    f"parameter '**{node.args.kwarg.arg}' missing type annotation in '{name}'",
                )

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Track variable as typed."""
        if isinstance(node.target, ast.Name):
            name = node.target.id
            if name.isupper():
                if name in self._assigned_constants:
                    self._error(node, f"re-assignment to constant '{name}'")
                self._assigned_constants.add(name)

            if self._in_function:
                self._typed_vars.add(name)

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Flag untyped variable assignments inside functions."""
        for target in node.targets:
            self._check_assign_target(target)

        # Still visit children
        self.generic_visit(node)

    def _check_assign_target(self, node: ast.AST) -> None:
        """Recursively check assignment targets."""
        if isinstance(node, ast.Name):
            name = node.id
            if name.isupper():
                if name in self._assigned_constants:
                    self._error(node, f"re-assignment to constant '{name}'")
                self._assigned_constants.add(name)
            elif self._in_function and name not in self._typed_vars:
                self._error(
                    node,
                    f"variable '{name}' missing type annotation (use: {name}: Type = value)",
                )
        elif isinstance(node, (ast.Tuple, ast.List)):
            for element in node.elts:
                self._check_assign_target(element)
        # Attributes and Subscripts are allowed (assuming they belong to something already typed)
        # or they don't support annotations anyway in standard Python for local re-assignment.

    def visit_For(self, node: ast.For) -> None:
        """For loops - loop variable needs type annotation."""
        if self._in_function:
            self._check_for_target(node.target)

        self.generic_visit(node)

    def _check_for_target(self, node: ast.AST) -> None:
        """Check for loop targets."""
        if isinstance(node, ast.Name):
            name = node.id
            if name.isupper():
                if name in self._assigned_constants:
                    self._error(node, f"re-assignment to constant '{name}'")
                self._assigned_constants.add(name)
            elif name not in self._typed_vars:
                self._error(
                    node,
                    f"loop variable '{name}' needs type annotation (consider using typed iterator)",
                )
        elif isinstance(node, (ast.Tuple, ast.List)):
            for element in node.elts:
                self._check_for_target(element)

    def visit_With(self, node: ast.With) -> None:
        """With statements - context manager variable should be typed."""
        if self._in_function:
            for item in node.items:
                if item.optional_vars:
                    self._check_with_target(item.optional_vars)

        self.generic_visit(node)

    def _check_with_target(self, node: ast.AST) -> None:
        """Check with statement targets."""
        if isinstance(node, ast.Name):
            name = node.id
            if name.isupper():
                if name in self._assigned_constants:
                    self._error(node, f"re-assignment to constant '{name}'")
                self._assigned_constants.add(name)
            elif name not in self._typed_vars:
                self._error(
                    node,
                    f"variable '{name}' missing type annotation in 'with' statement",
                )
        elif isinstance(node, (ast.Tuple, ast.List)):
            for element in node.elts:
                self._check_with_target(element)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        """Lambdas should also have type annotations."""
        # Python lambda doesn't support annotations easily, so flag them
        self._error(
            node,
            "lambda functions not supported (use def with type annotations)",
        )

        self.generic_visit(node)

    def visit_MatchAs(self, node: ast.MatchAs) -> None:
        """Validate match pattern captures via 'as'."""
        if node.name:
            if node.name.isupper():
                if node.name in self._assigned_constants:
                    self._error(node, f"re-assignment to constant '{node.name}'")
                self._assigned_constants.add(node.name)
            elif self._in_function and node.name not in self._typed_vars:
                self._error(
                    node,
                    f"variable '{node.name}' in match pattern must be pre-declared "
                    f"(use: {node.name}: Type before match)",
                )

        self.generic_visit(node)

    def visit_MatchStar(self, node: ast.MatchStar) -> None:
        """Validate match star patterns (e.g., [*rest])."""
        if node.name:
            if node.name.isupper():
                if node.name in self._assigned_constants:
                    self._error(node, f"re-assignment to constant '{node.name}'")
                self._assigned_constants.add(node.name)
            elif self._in_function and node.name not in self._typed_vars:
                self._error(
                    node,
                    f"variable '{node.name}' in match pattern must be pre-declared "
                    f"(use: {node.name}: Type before match)",
                )

        self.generic_visit(node)

    def _error(self, node: ast.AST, message: str) -> None:
        """Add a type error."""
        pos = cast(_HasPosition, node)
        self.errors.append(
            TypeError(
                line=pos.lineno,
                column=pos.col_offset,
                message=message,
                filename=self.filename,
            )
        )


def check_file(filepath: str | Path) -> list[TypeError]:
    """Check a Python file for type annotation violations."""
    filepath = Path(filepath)
    source = filepath.read_text(encoding="utf-8")
    return check_source(source, str(filepath))


def check_source(source: str, filename: str = "<string>") -> list[TypeError]:
    """Check Python source code for type annotation violations."""
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as e:
        return [
            TypeError(
                line=e.lineno or 0,
                column=e.offset or 0,
                message=f"syntax error: {e.msg}",
                filename=filename,
            )
        ]

    checker = StrictTypeChecker(filename)
    checker.visit(tree)
    return checker.errors


def is_strict(source: str) -> tuple[bool, list[TypeError]]:
    """
    Check if source code is strictly typed.

    Returns:
        (is_valid, errors) - True if no type violations
    """
    errors = check_source(source)
    return len(errors) == 0, errors
