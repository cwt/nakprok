"""Tests for nakprok CLI."""

import subprocess
import sys
import tempfile


class TestCLI:
    """Test nakprok CLI commands."""

    def _run_nakprok(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run nakprok CLI with given arguments."""
        result = subprocess.run(
            [sys.executable, "-m", "nakprok.cli"] + list(args),
            capture_output=True,
            text=True,
        )
        return result

    def _run_nakprok_entrypoint(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run nakprok via the entry point script."""
        result = subprocess.run(
            ["poetry", "run", "nakprok"] + list(args),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result

    def test_no_args_shows_help_and_exits_1(self) -> None:
        result = self._run_nakprok_entrypoint()
        assert result.returncode == 1
        assert "nakprok - Python with enforced static typing" in result.stdout

    def test_help_flag(self) -> None:
        result = self._run_nakprok_entrypoint("--help")
        assert result.returncode == 0
        assert "nakprok - Python with enforced static typing" in result.stdout

    def test_h_flag(self) -> None:
        result = self._run_nakprok_entrypoint("-h")
        assert result.returncode == 0
        assert "nakprok - Python with enforced static typing" in result.stdout

    def test_version_flag(self) -> None:
        result = self._run_nakprok_entrypoint("--version")
        assert result.returncode == 0
        assert "nakprok" in result.stdout

    def test_check_valid_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def foo(x: int) -> int:\n    return x\n")
            f.flush()
            filepath = f.name

        result = self._run_nakprok_entrypoint("check", filepath)
        assert result.returncode == 0
        assert "no type errors" in result.stdout

    def test_check_invalid_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def foo(x) -> int:\n    return x\n")
            f.flush()
            filepath = f.name

        result = self._run_nakprok_entrypoint("check", filepath)
        assert result.returncode == 1
        assert "type check failed" in result.stderr
        assert "missing type annotation" in result.stderr

    def test_check_missing_file_arg(self) -> None:
        result = self._run_nakprok_entrypoint("check")
        assert result.returncode == 1
        assert "missing file argument" in result.stderr

    def test_run_missing_file_arg(self) -> None:
        result = self._run_nakprok_entrypoint("run")
        assert result.returncode == 1
        assert "missing file argument" in result.stderr

    def test_unknown_command(self) -> None:
        result = self._run_nakprok_entrypoint("foobar")
        assert result.returncode == 1
        assert "unknown command" in result.stderr

    def test_run_valid_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                'def main() -> None:\n    print("hello")\n\nif __name__ == "__main__":\n    main()\n'
            )
            f.flush()
            filepath = f.name

        result = self._run_nakprok_entrypoint("run", filepath)
        assert result.returncode == 0
        assert "hello" in result.stdout

    def test_run_invalid_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def foo(x) -> int:\n    return x\n")
            f.flush()
            filepath = f.name

        result = self._run_nakprok_entrypoint("run", filepath)
        assert result.returncode == 1
        assert "type check failed" in result.stderr

    def test_run_file_not_found(self) -> None:
        result = self._run_nakprok_entrypoint("run", "/nonexistent/file.py")
        assert result.returncode == 1
        assert "file not found" in result.stderr

    def test_direct_file_execution(self) -> None:
        """Test running nakprok with just a .py file (no 'run' command)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write('print("direct")\n')
            f.flush()
            filepath = f.name

        result = self._run_nakprok_entrypoint(filepath)
        assert result.returncode == 0
        assert "direct" in result.stdout
