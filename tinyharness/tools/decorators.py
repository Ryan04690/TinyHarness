# Implement a tool decorator
# JSON Schema Type -> Tool Schema

import inspect

from .tool import Tool
from .schema import build_parameters_schema


def tool(
    *,
    name=None,
    description=None,
):
    def decorator(function):

        tool_name = (
            name
            if name is not None
            else function.__name__
        )

        tool_description = (
            description
            if description is not None
            else inspect.getdoc(function)
        )

        if not tool_description:
            tool_description = (
                f"Tool '{tool_name}'."
            )

        parameters = (
            build_parameters_schema(
                function
            )
        )

        return Tool(
            name=tool_name,
            description=tool_description,
            parameters=parameters,
            function=function,
        )

    return decorator



# @tool()
# def add(a: float, b: float):
#     """Add two numbers together."""

#     return a + b

# equals :

# def add(a: float, b: float):
#     """Add two numbers together."""

#     return a + b

# decorator = tool()
# add = decorator(add)

