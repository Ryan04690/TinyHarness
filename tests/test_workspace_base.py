
import pytest

from tinyharness.workspace import (
    CommandResult,
    FileEntry,
    Workspace,
)


def test_workspace_cannot_be_instantiated():
    with pytest.raises(TypeError):
        Workspace()


def test_incomplete_workspace_cannot_be_instantiated():

    class IncompleteWorkspace(Workspace):

        def read_file(self, path: str) -> str:
            return "hello"

    with pytest.raises(TypeError):
        IncompleteWorkspace()


class DummyWorkspace(Workspace):
    """
    In-memory implementation used only for testing.

    This class does not access the real filesystem.
    """

    def __init__(self):
        self.files = {
            "hello.txt": "Hello TinyHarness",
        }

    def list_files(
        self,
        path: str = ".",
    ) -> list[FileEntry]:
        return [
            FileEntry(
                name="hello.txt",
                path="hello.txt",
                type="file",
            )
        ]

    def read_file(
        self,
        path: str,
    ) -> str:
        return self.files[path]

    def write_file(
        self,
        path: str,
        content: str,
    ) -> None:
        self.files[path] = content

    def run(
        self,
        command: str,
        cwd: str = ".",
        timeout: int = 10,
    ) -> CommandResult:
        return CommandResult(
            command=command,
            cwd=cwd,
            returncode=0,
            stdout="mock output",
            stderr="",
            timed_out=False,
        )


def test_dummy_workspace_file_operations():
    workspace = DummyWorkspace()

    entries = workspace.list_files()

    assert len(entries) == 1
    assert entries[0].name == "hello.txt"

    assert workspace.read_file(
        "hello.txt"
    ) == "Hello TinyHarness"

    workspace.write_file(
        "new.txt",
        "New content",
    )

    assert workspace.read_file(
        "new.txt"
    ) == "New content"


def test_dummy_workspace_run():
    workspace = DummyWorkspace()

    result = workspace.run(
        "python --version"
    )

    assert isinstance(
        result,
        CommandResult,
    )

    assert result.command == "python --version"
    assert result.returncode == 0
    assert result.stdout == "mock output"
    assert result.timed_out is False
