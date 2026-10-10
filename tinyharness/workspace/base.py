
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CommandResult:
    """Structured result returned by workspace commands."""

    command: str
    cwd: str
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


@dataclass
class FileEntry:
    """A file or directory entry."""

    name: str
    path: str
    type: str


class Workspace(ABC):
    """
    Abstract execution environment for TinyHarness.

    A Workspace provides basic filesystem and command
    execution capabilities.

    This abstraction does not guarantee sandbox isolation.
    """

    @abstractmethod
    def list_files(
        self,
        path: str = ".",
    ) -> list[FileEntry]:
        """List entries in a directory."""
        raise NotImplementedError

    @abstractmethod
    def read_file(
        self,
        path: str,
    ) -> str:
        """Read a text file."""
        raise NotImplementedError

    @abstractmethod
    def write_file(
        self,
        path: str,
        content: str,
    ) -> None:
        """Write text to a file."""
        raise NotImplementedError

    @abstractmethod
    def run(
        self,
        command: str,
        cwd: str = ".",
        timeout: int = 10,
    ) -> CommandResult:
        """Execute a command in the workspace."""
        raise NotImplementedError
