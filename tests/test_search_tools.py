import pytest

from tinyharness.tools import (
    ToolRegistry,
    create_search_tools,
)


def create_registry(root):
    registry = ToolRegistry()

    for tool in create_search_tools(root):
        registry.register(tool)

    return registry

def test_search_by_name(tmp_path):
    (
        tmp_path
        / "agent.py"
    ).write_text(
        "class Agent:\n    pass\n",
        encoding="utf-8",
    )

    registry = create_registry(
        tmp_path
    )

    result = registry.execute(
        "search_files",
        {
            "query": "agent",
            "search_type": "name",
        },
    )

    assert result["count"] == 1

    assert (
        result["results"][0]["path"]
        == "agent.py"
    )

def test_search_by_content(tmp_path):
    (
        tmp_path
        / "agent.py"
    ).write_text(
        "class Agent:\n    pass\n",
        encoding="utf-8",
    )

    registry = create_registry(
        tmp_path
    )

    result = registry.execute(
        "search_files",
        {
            "query": "class Agent",
            "search_type": "content",
        },
    )

    assert result["count"] == 1

    match = (
        result["results"][0]
        ["matches"][0]
    )

    assert match["line"] == 1
    assert match["text"] == "class Agent:"

def test_invalid_search_type(
    tmp_path,
):
    registry = create_registry(
        tmp_path
    )

    with pytest.raises(ValueError):
        registry.execute(
            "search_files",
            {
                "query": "Agent",
                "search_type": "banana",
            },
        )