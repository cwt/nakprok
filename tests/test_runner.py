"""Tests for nakprok runner."""

import tempfile
from pathlib import Path

from nakprok.runner import run_file, run_source


class TestRunFile:
    """Test run_file function."""

    def test_run_valid_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                'def main() -> None:\n    print("hello")\n\nif __name__ == "__main__":\n    main()\n'
            )
            f.flush()
            filepath = f.name

        exit_code = run_file(filepath)
        assert exit_code == 0

    def test_run_invalid_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def foo(x) -> int:\n    return x\n")
            f.flush()
            filepath = f.name

        exit_code = run_file(filepath)
        assert exit_code == 1

    def test_run_file_not_found(self) -> None:
        exit_code = run_file("/nonexistent/file.py")
        assert exit_code == 1

    def test_run_file_with_runtime_error(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                "def main() -> None:\n    x: int = 1 / 0\n\nif __name__ == '__main__':\n    main()\n"
            )
            f.flush()
            filepath = f.name

        exit_code = run_file(filepath)
        assert exit_code == 2

    def test_run_file_with_args(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                "import sys\n\ndef main() -> None:\n    print(sys.argv)\n\nif __name__ == '__main__':\n    main()\n"
            )
            f.flush()
            filepath = f.name

        exit_code = run_file(filepath, ["--arg1", "--arg2"])
        assert exit_code == 0

    def test_run_file_path_object(self) -> None:
        """Test that run_file accepts Path objects."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def main() -> None:\n    pass\n")
            f.flush()
            filepath = Path(f.name)

        exit_code = run_file(filepath)
        assert exit_code == 0


class TestRunSource:
    """Test run_source function."""

    def test_run_source_valid(self) -> None:
        source = """
def greet(name: str) -> str:
    return f"Hello, {name}"

result: str = greet("World")
"""
        exit_code = run_source(source)
        assert exit_code == 0

    def test_run_source_invalid(self) -> None:
        source = """
def greet(name) -> str:
    return f"Hello, {name}"
"""
        exit_code = run_source(source)
        assert exit_code == 1

    def test_run_source_runtime_error(self) -> None:
        source = """
def crash() -> None:
    x: int = 1 / 0

crash()
"""
        exit_code = run_source(source)
        assert exit_code == 2

    def test_run_source_with_filename(self) -> None:
        source = """
def main() -> None:
    pass
"""
        exit_code = run_source(source, filename="test_module.py")
        assert exit_code == 0

    def test_run_source_print(self) -> None:
        source = 'def main() -> None:\n    print("test output")\n\nmain()\n'
        exit_code = run_source(source)
        assert exit_code == 0
