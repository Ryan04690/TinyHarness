"""
LocalWorkspace.run() still calls the Windows Shell, and the command itself might access things outside the root directory, so it's still not a secure sandbox.
"""
from pathlib import Path

import pytest

from tinyharness.workspace import (
    CommandResult,
    FileEntry,
    LocalWorkspace,
    Workspace,
)


# Test 1: LocalWorkspace implements Workspace
def test_local_workspace_is_workspace(tmp_path):
    workspace = LocalWorkspace(tmp_path)

    assert isinstance(workspace, Workspace)
    assert workspace.root == tmp_path.resolve()


# Test 2: Read a real file
def test_local_workspace_read_file(tmp_path):
    workspace = LocalWorkspace(tmp_path)

    file_path = tmp_path / "hello.txt"
    file_path.write_text(
        "Hello TinyHarness",
        encoding="utf-8",
    )

    result = workspace.read_file("hello.txt")

    assert result == "Hello TinyHarness"


# Test 3: Write a real file
def test_local_workspace_write_file(tmp_path):
    workspace = LocalWorkspace(tmp_path)

    workspace.write_file(
        "new.txt",
        "New content",
    )

    file_path = tmp_path / "new.txt"

    assert file_path.exists()
    assert file_path.read_text(
        encoding="utf-8"
    ) == "New content"


# Test 4: List directory entries
def test_local_workspace_list_files(tmp_path):
    workspace = LocalWorkspace(tmp_path)

    (tmp_path / "hello.txt").write_text(
        "hello",
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir()

    entries = workspace.list_files(".")

    assert all(
        isinstance(entry, FileEntry)
        for entry in entries
    )

    entry_map = {
        entry.name: entry
        for entry in entries
    }

    assert entry_map["hello.txt"].type == "file"
    assert entry_map["docs"].type == "dir"


# Test 5: Reject parent path traversal
def test_local_workspace_blocks_parent_path(tmp_path):
    workspace = LocalWorkspace(tmp_path)

    with pytest.raises(ValueError):
        workspace.read_file("../outside.txt")


# Test 6: Reject sibling directory with similar prefix
def test_local_workspace_blocks_sibling_path(tmp_path):
    root = tmp_path / "project"
    sibling = tmp_path / "project_backup"

    root.mkdir()
    sibling.mkdir()

    (sibling / "secret.txt").write_text(
        "secret",
        encoding="utf-8",
    )

    workspace = LocalWorkspace(root)

    with pytest.raises(ValueError):
        workspace.read_file(
            "../project_backup/secret.txt"
        )


# Test 7: Execute a real Windows command
def test_local_workspace_run(tmp_path):
    workspace = LocalWorkspace(tmp_path)

    result = workspace.run("echo hello")

    assert isinstance(result, CommandResult)
    assert result.returncode == 0
    assert "hello" in result.stdout.lower()
    assert result.timed_out is False


# Test 8: Reject an invalid command cwd
def test_local_workspace_blocks_parent_cwd(tmp_path):
    workspace = LocalWorkspace(tmp_path)

    with pytest.raises(ValueError):
        workspace.run(
            "echo hello",
            cwd="..",
        )
