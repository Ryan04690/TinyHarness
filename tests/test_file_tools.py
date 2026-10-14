from tinyharness.tools import (
    ToolRegistry,
    create_file_tools,
)

from tinyharness.workspace import LocalWorkspace

def create_registry(workspace):
    registry = ToolRegistry()

    for tool in create_file_tools(workspace):
        registry.register(tool)

    return registry

def test_write_and_read_file(tmp_path):
    workspace = LocalWorkspace(
        tmp_path
    )

    registry = create_registry(
        workspace
    )
    write_result = registry.execute(
        "write_file",
        {
            "path": "hello.txt",
            "content": "Hello TinyHarness",
        },
    )

    assert (
        write_result["characters_written"]
        == len("Hello TinyHarness")
    )

    read_result = registry.execute(
        "read_file",
        {
            "path": "hello.txt",
        },
    )

    assert (
        read_result["content"]
        == "Hello TinyHarness"
    )

import pytest


def test_write_file_refuses_overwrite(
    tmp_path,
):
    workspace = LocalWorkspace(
        tmp_path
    )

    registry = create_registry(
        workspace
    )

    registry.execute(
        "write_file",
        {
            "path": "hello.txt",
            "content": "first",
        },
    )

    with pytest.raises(
        FileExistsError
    ):
        registry.execute(
            "write_file",
            {
                "path": "hello.txt",
                "content": "second",
            },
        )

def test_file_tool_blocks_parent_path(
    tmp_path,
):
    workspace = LocalWorkspace(
        tmp_path
    )

    registry = create_registry(
        workspace
    )

    with pytest.raises(ValueError):
        registry.execute(
            "read_file",
            {
                "path": "../outside.txt",
            },
        )