import sys

from tinyharness.tools import (
    ToolRegistry,
    create_shell_tools,
)


def create_registry(root):
    registry = ToolRegistry()

    for tool in create_shell_tools(root):
        registry.register(tool)

    return registry

def test_shell_success(tmp_path):
    registry = create_registry(
        tmp_path
    )

    result = registry.execute(
        "run_shell",
        {
            "command": "echo Hello",
        },
    )

    assert result["returncode"] == 0
    assert "Hello" in result["stdout"]
    assert result["timed_out"] is False

def test_shell_nonzero_returncode(
    tmp_path,
):
    registry = create_registry(
        tmp_path
    )

    command = (
        f'"{sys.executable}" '
        '-c "import sys; '
        'sys.exit(3)"'
    )

    result = registry.execute(
        "run_shell",
        {
            "command": command,
        },
    )

    assert result["returncode"] == 3
    assert result["timed_out"] is False

def test_shell_timeout(tmp_path):
    registry = create_registry(
        tmp_path
    )

    command = (
        f'"{sys.executable}" '
        '-c "import time; '
        'time.sleep(2)"'
    )

    result = registry.execute(
        "run_shell",
        {
            "command": command,
            "timeout": 1,
        },
    )

    assert result["timed_out"] is True
    assert result["returncode"] is None

import pytest


def test_shell_blocks_parent_cwd(
    tmp_path,
):
    registry = create_registry(
        tmp_path
    )

    with pytest.raises(ValueError):
        registry.execute(
            "run_shell",
            {
                "command": "dir",
                "cwd": "..",
            },
        )