"""Extended tests for nakprok type checker - covering previously uncovered code."""

import tempfile

from nakprok.checker import TypeError, check_file, is_strict


class TestTypeError:
    """Test TypeError dataclass."""

    def test_str_format(self) -> None:
        error = TypeError(
            line=10,
            column=5,
            message="missing type annotation",
            filename="test.py",
        )
        assert str(error) == "test.py:10:5: error: missing type annotation"

    def test_str_without_filename(self) -> None:
        error = TypeError(line=1, column=0, message="syntax error")
        assert str(error) == ":1:0: error: syntax error"


class TestAsyncFunctions:
    """Test async function type annotation enforcement."""

    def test_async_function_valid(self) -> None:
        source = """
async def fetch(url: str) -> str:
    return url
"""
        valid, errors = is_strict(source)
        assert valid is True

    def test_async_function_missing_return(self) -> None:
        source = """
async def fetch(url: str):
    return url
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 1
        assert "missing return type" in errors[0].message

    def test_async_function_with_vararg_valid(self) -> None:
        source = """
async def foo(*args: int) -> None:
    pass
"""
        valid, errors = is_strict(source)
        assert valid is True

    def test_async_function_with_vararg_invalid(self) -> None:
        source = """
async def foo(*args) -> None:
    pass
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 1
        assert "missing type annotation" in errors[0].message

    def test_async_function_with_kwarg_valid(self) -> None:
        source = """
async def foo(**kwargs: str) -> None:
    pass
"""
        valid, errors = is_strict(source)
        assert valid is True

    def test_async_function_with_kwarg_invalid(self) -> None:
        source = """
async def foo(**kwargs) -> None:
    pass
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 1
        assert "missing type annotation" in errors[0].message

    def test_async_function_with_body_untyped_var(self) -> None:
        source = """
async def compute(x: int) -> int:
    y = x * 2
    return y
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 1
        assert "'y' missing type annotation" in errors[0].message

    def test_async_function_with_body_typed_var(self) -> None:
        source = """
async def compute(x: int) -> int:
    y: int = x * 2
    return y
"""
        valid, errors = is_strict(source)
        assert valid is True


class TestVarargKwargRegular:
    """Test *args and **kwargs in regular functions."""

    def test_vararg_invalid(self) -> None:
        source = """
def foo(*args) -> None:
    pass
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 1
        assert "missing type annotation" in errors[0].message

    def test_vararg_valid(self) -> None:
        source = """
def foo(*args: int) -> None:
    pass
"""
        valid, errors = is_strict(source)
        assert valid is True

    def test_kwarg_invalid(self) -> None:
        source = """
def foo(**kwargs) -> None:
    pass
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 1
        assert "missing type annotation" in errors[0].message

    def test_kwarg_valid(self) -> None:
        source = """
def foo(**kwargs: str) -> None:
    pass
"""
        valid, errors = is_strict(source)
        assert valid is True

    def test_both_vararg_kwarg_invalid(self) -> None:
        source = """
def foo(*args, **kwargs):
    pass
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 3  # *args + **kwargs + return


class TestForLoops:
    """Test for-loop variable type annotation enforcement."""

    def test_for_loop_untyped_in_function(self) -> None:
        source = """
def process() -> None:
    for i in range(10):
        print(i)
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 1
        assert "loop variable" in errors[0].message

    def test_for_loop_pre_typed(self) -> None:
        source = """
def process() -> None:
    i: int
    for i in range(10):
        print(i)
"""
        valid, errors = is_strict(source)
        assert valid is True

    def test_for_loop_module_level(self) -> None:
        source = """
for i in range(10):
    print(i)
"""
        valid, errors = is_strict(source)
        # Module-level for loops are not checked
        assert valid is True

    def test_for_loop_tuple_unpacking(self) -> None:
        source = """
def process() -> None:
    for a, b in [(1, 2)]:
        print(a, b)
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 2
        assert "loop variable" in errors[0].message
        assert "loop variable" in errors[1].message

    def test_for_loop_tuple_unpacking_pre_typed(self) -> None:
        source = """
def process() -> None:
    a: int
    b: int
    for a, b in [(1, 2)]:
        print(a, b)
"""
        valid, errors = is_strict(source)
        assert valid is True

    def test_for_loop_nested_tuple(self) -> None:
        source = """
def process() -> None:
    for x, y in []:
        pass
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 2


class TestWithStatements:
    """Test with-statement variable type annotation enforcement."""

    def test_with_untyped_in_function(self) -> None:
        source = """
def read() -> None:
    with open("f.txt") as f:
        pass
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 1
        assert "'f' missing type annotation" in errors[0].message

    def test_with_pre_typed(self) -> None:
        source = """
def read() -> None:
    f: str
    with open("f.txt") as f:
        pass
"""
        valid, errors = is_strict(source)
        assert valid is True

    def test_with_module_level(self) -> None:
        source = """
with open("f.txt") as f:
    pass
"""
        valid, errors = is_strict(source)
        # Module-level with is not checked
        assert valid is True

    def test_with_tuple_unpacking(self) -> None:
        source = """
def process() -> None:
    with context() as (a, b):
        pass
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 2
        assert "'a' missing type annotation" in errors[0].message
        assert "'b' missing type annotation" in errors[1].message

    def test_with_tuple_pre_typed(self) -> None:
        source = """
def process() -> None:
    a: int
    b: int
    with context() as (a, b):
        pass
"""
        valid, errors = is_strict(source)
        assert valid is True


class TestLambdaExpressions:
    """Test lambda expressions are flagged as unsupported."""

    def test_lambda_in_assignment(self) -> None:
        source = """
def foo() -> int:
    f = lambda x: x + 1
    return f(1)
"""
        valid, errors = is_strict(source)
        assert valid is False
        # 2 errors: untyped variable 'f' + lambda not supported
        assert len(errors) == 2
        assert "lambda functions not supported" in errors[1].message

    def test_lambda_as_argument(self) -> None:
        source = """
def foo() -> int:
    return list(map(lambda x: x * 2, [1, 2]))
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 1
        assert "lambda functions not supported" in errors[0].message

    def test_multiple_lambdas(self) -> None:
        source = """
def foo() -> int:
    a: int
    a = lambda x: x
    b: int
    b = lambda y: y
    return a(b(1))
"""
        valid, errors = is_strict(source)
        assert valid is False
        assert len(errors) == 2


class TestCheckFile:
    """Test check_file function."""

    def test_check_file_valid(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def foo(x: int) -> int:\n    return x\n")
            f.flush()
            filepath = f.name

        errors = check_file(filepath)
        assert len(errors) == 0

    def test_check_file_invalid(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def foo(x) -> int:\n    return x\n")
            f.flush()
            filepath = f.name

        errors = check_file(filepath)
        assert len(errors) == 1
        assert "'x' missing type annotation" in errors[0].message

    def test_check_file_syntax_error(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def broken(\n")
            f.flush()
            filepath = f.name

        errors = check_file(filepath)
        assert len(errors) == 1
        assert "syntax error" in errors[0].message

    def test_check_file_empty(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("")
            f.flush()
            filepath = f.name

        errors = check_file(filepath)
        assert len(errors) == 0


class TestCheckSourceEdgeCases:
    """Test edge cases in check_source."""

    def test_empty_source(self) -> None:
        valid, errors = is_strict("")
        assert valid is True
        assert len(errors) == 0

    def test_only_comments(self) -> None:
        source = """
# This is a comment
# Another comment
"""
        valid, errors = is_strict(source)
        assert valid is True
        assert len(errors) == 0

    def test_only_imports(self) -> None:
        source = """
import os
from pathlib import Path
"""
        valid, errors = is_strict(source)
        assert valid is True
        assert len(errors) == 0
