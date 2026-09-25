import pytest

from tinyharness.tools import (
    ToolRegistry,
    tool,
)


@tool()
def add(
    a: float,
    b: float,
):
    """Add two numbers."""

    return a + b

def test_registry_register_and_get():
    registry = ToolRegistry()

    registry.register(add)

    assert registry.get("add") is add
    assert registry.names() == ["add"]
    assert len(registry) == 1

def test_registry_execute():
    registry = ToolRegistry()

    registry.register(add)

    result = registry.execute(
        "add",
        {
            "a": 10,
            "b": 20,
        },
    )

    assert result == 30

def test_duplicate_tool_registration():
    registry = ToolRegistry()

    registry.register(add)

    with pytest.raises(ValueError):
        registry.register(add)

def test_unknown_tool():
    registry = ToolRegistry()

    with pytest.raises(KeyError):
        registry.execute(
            "does_not_exist",
            {},
        )