"""AuthorStyle — local-first personal writing style research CLI."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("paladini-authorstyle")
except PackageNotFoundError:  # pragma: no cover - source tree without install
    __version__ = "0.2.2"
