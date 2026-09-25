import pytest

from jsonschema import ValidationError

from tinyharness.tools import tool


@tool()
def add(
    a: float,
    b: float,
):
    """Add two numbers."""

    return a + b


@tool()
def greet(
    name: str,
    excited: bool = False,
):
    """Generate a greeting."""

    if excited:
        return f"Hello, {name}!"

    return f"Hello, {name}."

def test_tool_execute():
    result = add.execute(
        {
            "a": 1,
            "b": 2,
        }
    )

    assert result == 3

def test_tool_schema_generation():
    schema = add.schema()

    function_schema = schema["function"]

    assert function_schema["name"] == "add"

    assert (
        function_schema["description"]
        == "Add two numbers."
    )

    parameters = (
        function_schema["parameters"]
    )

    assert (
        parameters["properties"]["a"]["type"]
        == "number"
    )

    assert (
        parameters["properties"]["b"]["type"]
        == "number"
    )

    assert set(
        parameters["required"]
    ) == {"a", "b"}

def test_optional_parameter_not_required():
    schema = greet.schema()

    parameters = (
        schema["function"]["parameters"]
    )

    assert parameters["required"] == [
        "name"
    ]

    assert (
        parameters["properties"]
        ["excited"]["default"]
        is False
    )

def test_invalid_argument_type():
    with pytest.raises(
        ValidationError
    ):
        add.execute(
            {
                "a": "hello",
                "b": 2,
            }
        )