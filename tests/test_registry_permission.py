
import pytest

from tinyharness.security import (
    PermissionAction,
    PermissionDecision,
    PermissionManager,
)
from tinyharness.tools.registry import ToolRegistry
from tinyharness.tools.tool import Tool


def make_registry(
    tool_name,
    permission_manager,
    tool_permissions=None,
):
    """
    Build a registry with a recording tool.

    The tool records whether its function was
    actually executed.
    """
    calls = []

    def operation(path):
        calls.append(path)
        return {"path": path, "executed": True}

    registry = ToolRegistry(
        permission_manager=permission_manager,
        tool_permissions=tool_permissions,
    )

    registry.register(
        Tool(
            name=tool_name,
            description="A test tool that records execution.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
                "additionalProperties": False,
            },
            function=operation,
        )
    )

    return registry, calls


def test_legacy_registry_still_works():
    # Without a PermissionManager, old behavior remains.
    registry, calls = make_registry(
        "write_file",
        permission_manager=None,
    )

    result = registry.execute(
        "write_file",
        {"path": "test.txt"},
    )

    assert result["executed"] is True
    assert calls == ["test.txt"]


def test_read_allowed_by_default():
    registry, calls = make_registry(
        "read_file",
        PermissionManager(),
    )

    result = registry.execute(
        "read_file",
        {"path": "README.md"},
    )

    assert result["executed"] is True
    assert calls == ["README.md"]


def test_write_ask_blocks_without_approval():
    registry, calls = make_registry(
        "write_file",
        PermissionManager(),
    )

    with pytest.raises(PermissionError):
        registry.execute(
            "write_file",
            {"path": "test.txt"},
        )

    # The underlying tool was never executed.
    assert calls == []


def test_write_ask_allows_trusted_approval():
    registry, calls = make_registry(
        "write_file",
        PermissionManager(),
    )

    result = registry.execute(
        "write_file",
        {"path": "test.txt"},
        user_approved=True,
    )

    assert result["executed"] is True
    assert calls == ["test.txt"]


def test_shell_deny_cannot_be_overridden():
    manager = PermissionManager(
        rules={
            PermissionAction.SHELL:
                PermissionDecision.DENY,
        }
    )

    registry, calls = make_registry(
        "run_shell",
        manager,
    )

    with pytest.raises(PermissionError):
        registry.execute(
            "run_shell",
            {"path": "ignored"},
            user_approved=True,
        )

    assert calls == []


def test_unknown_tool_permission_denied():
    registry, calls = make_registry(
        "custom_tool",
        PermissionManager(),
    )

    with pytest.raises(PermissionError):
        registry.execute(
            "custom_tool",
            {"path": "test.txt"},
            user_approved=True,
        )

    assert calls == []


def test_custom_tool_permission_mapping():
    registry, calls = make_registry(
        "custom_tool",
        PermissionManager(),
        tool_permissions={
            "custom_tool": PermissionAction.READ,
        },
    )

    result = registry.execute(
        "custom_tool",
        {"path": "test.txt"},
    )

    assert result["executed"] is True
    assert calls == ["test.txt"]
