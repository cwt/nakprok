"""Tests for nakprok type checker."""

from nakprok.checker import is_strict


class TestFunctionAnnotations:
    """Test function type annotation enforcement."""

    def test_valid_function(self) -> None:
        source = """
def add(a: int, b: int) -> int:
    return a + b
"""
        valid, errors = is_strict(source)
        assert valid is True
        assert len(errors) == 0

    def test_missing_return_type(self) -> None:
        source = """
def add(a: int, b: int):
    return a + b
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 1
        assert "missing return type" in errors[0].message

    def test_missing_param_type(self) -> None:
        source = """
def add(a, b: int) -> int:
    return a + b
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 1
        assert "'a' missing type annotation" in errors[0].message

    def test_missing_all_annotations(self) -> None:
        source = """
def add(a, b):
    return a + b
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 3  # 2 params + return type

    def test_self_param_skipped(self) -> None:
        source = """
class MyClass:
    def method(self, x: int) -> int:
        return x
"""
        valid, errors = is_strict(source)
        assert valid is True


class TestVariableAnnotations:
    """Test variable type annotation enforcement."""

    def test_annotated_variable(self) -> None:
        source = """
def foo() -> None:
    x: int = 10
"""
        valid, errors = is_strict(source)
        assert valid is True

    def test_untyped_variable_in_function(self) -> None:
        source = """
def foo() -> None:
    x = 10
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 1
        assert "missing type annotation" in errors[0].message

    def test_uppercase_constant_allowed(self) -> None:
        source = """
def foo() -> None:
    MAX_SIZE = 100
"""
        valid, errors = is_strict(source)
        # UPPERCASE constants are allowed
        assert valid is True

    def test_reassignment(self) -> None:
        source = """
def foo() -> None:
    x: int = 10
    x = 20
"""
        valid, errors = is_strict(source)
        # Re-assignment is now allowed if previously typed
        assert valid is True
        assert len(errors) == 0

    def test_untyped_unpacked_assignment(self) -> None:
        source = """
def foo() -> None:
    [x, y] = [1, 2]
"""
        valid, errors = is_strict(source)
        # Unpacked assignment IS now correctly flagged
        assert valid is False
        assert len(errors) == 2
        assert "variable 'x' missing type annotation" in errors[0].message
        assert "variable 'y' missing type annotation" in errors[1].message

    def test_typed_unpacked_assignment(self) -> None:
        source = """
def foo() -> None:
    x: int
    y: int
    [x, y] = [1, 2]
"""
        valid, errors = is_strict(source)
        assert valid is True


class TestComplexCode:
    """Test more complex code patterns."""

    def test_valid_factorial(self) -> None:
        source = """
def factorial(n: int) -> int:
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

def main() -> None:
    result: int = factorial(10)
    print(result)
"""
        valid, errors = is_strict(source)
        assert valid is True

    def test_fibonacci(self) -> None:
        source = """
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    else:
        a: int = fibonacci(n - 1)
        b: int = fibonacci(n - 2)
        return a + b
"""
        valid, errors = is_strict(source)
        assert valid is True

    def test_match_statement(self) -> None:
        source = """
def process(data: int | str) -> str:
    match data:
        case int(val):
            return f"int: {val}"
        case str(val):
            return f"str: {val}"
        case _:
            return "unknown"
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 2
        assert (
            "variable 'val' in match pattern must be pre-declared" in errors[0].message
        )
        assert (
            "variable 'val' in match pattern must be pre-declared" in errors[1].message
        )

    def test_match_valid(self) -> None:
        source = """
def process(data: int | str) -> str:
    match data:
        case int():
            val: int = data
            return f"int: {val}"
        case str():
            val: str = data
            return f"str: {val}"
        case _:
            return "unknown"
"""
        valid, errors = is_strict(source)
        assert valid is True

    def test_match_with_predeclared_binding(self) -> None:
        source = """
def process(data: int | str) -> str:
    val: int | str
    match data:
        case int() as val:
            return f"int: {val}"
        case str() as val:
            return f"str: {val}"
        case _:
            return "unknown"
"""
        valid, errors = is_strict(source)
        assert valid is True

    def test_match_star_pattern_predeclared(self) -> None:
        source = """
def get_rest(items: list[int]) -> list[int]:
    first: int
    rest: list[int]
    match items:
        case [first, *rest]:
            return rest
        case _:
            return []
"""
        valid, errors = is_strict(source)
        assert valid is True

    def test_constant_immutability(self) -> None:
        source = """
MAX_SIZE = 100
MAX_SIZE = 200  # Should be blocked
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert "re-assignment to constant 'MAX_SIZE'" in errors[0].message

    def test_local_constant_immutability(self) -> None:
        source = """
def main() -> None:
    LIMIT = 10
    LIMIT = 20  # Should be blocked
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert "re-assignment to constant 'LIMIT'" in errors[0].message

    def test_constant_shadowing_blocked(self) -> None:
        source = """
GLOBAL_VAL = 1
def main() -> None:
    GLOBAL_VAL = 2  # Should be blocked as re-assignment or shadowing
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert "re-assignment to constant 'GLOBAL_VAL'" in errors[0].message

    def test_local_constants_different_scopes(self) -> None:
        source = """
def foo() -> None:
    X = 1
def bar() -> None:
    X = 2  # Should this be blocked?
"""
        valid, errors = is_strict(source)
        # Based on current implementation, this will be blocked.
        # If we want to allow this, we need scope-aware constants.
        assert valid is False
        assert "re-assignment to constant 'X'" in errors[0].message

    def test_attribute_assignment(self) -> None:
        source = """
class MyClass:
    def __init__(self, x: int) -> None:
        self.x = x
"""
        valid, errors = is_strict(source)
        # Attribute assignment is currently NOT checked
        assert valid is True

    def test_empty_function(self) -> None:
        source = """
def noop() -> None:
    pass
"""
        valid, errors = is_strict(source)
        assert valid is True

    def test_class_without_methods(self) -> None:
        source = """
class Empty:
    pass
"""
        valid, errors = is_strict(source)
        assert valid is True

    def test_syntax_error(self) -> None:
        source = """
def broken(
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 1
        assert "syntax error" in errors[0].message


class TestIntegration:
    """Integration tests with actual files."""

    def test_valid_example_file(self) -> None:
        from pathlib import Path

        examples_dir = Path(__file__).parent.parent / "examples"
        valid_file = examples_dir / "valid.py"

        if valid_file.exists():
            from nakprok.checker import check_file

            errors = check_file(valid_file)
            assert len(errors) == 0

    def test_invalid_example_file(self) -> None:
        from pathlib import Path

        examples_dir = Path(__file__).parent.parent / "examples"
        invalid_file = examples_dir / "invalid.py"

        if invalid_file.exists():
            from nakprok.checker import check_file

            errors = check_file(invalid_file)
            assert len(errors) > 0
