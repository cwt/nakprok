"""
nakprok - Python with enforced static typing.
Reuses everything from Python, just requires type annotations everywhere.
"""

from importlib.metadata import PackageNotFoundError, version

__version__: str
try:
    __version__ = version("nakprok")
except PackageNotFoundError:  # pragma: no cover - source checkout without install
    __version__ = "0.0.0"
