# Python Type → JSON Schema Type
# Reflection

import inspect
from typing import get_type_hints


PYTHON_TO_JSON_TYPE = {
    str: "string", # 
    int: "integer",
    float: "number",
    bool: "boolean",
}


def python_type_to_json_type(
    annotation,
):
    json_type = PYTHON_TO_JSON_TYPE.get(
        annotation
    )

    if json_type is None:
        raise TypeError(
            f"Unsupported parameter type: "
            f"{annotation}"
        )

    return json_type


def build_parameters_schema(function):
    signature = inspect.signature(function)

    type_hints = get_type_hints(function)

    properties = {}
    required = []

    for name, parameter in (
        signature.parameters.items()
    ):

        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            raise TypeError(
                f"Tool function "
                f"'{function.__name__}' "
                "cannot use *args or **kwargs."
            )

        annotation = type_hints.get(name)

        if annotation is None:
            raise TypeError(
                f"Parameter '{name}' in "
                f"'{function.__name__}' "
                "must have a type annotation."
            )

        json_type = (
            python_type_to_json_type(
                annotation
            )
        )

        property_schema = {
            "type": json_type,
        }

        if (
            parameter.default
            is inspect.Parameter.empty
        ):
            required.append(name)

        else:
            property_schema["default"] = (
                parameter.default
            )

        properties[name] = property_schema

    schema = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }

    if required:
        schema["required"] = required

    return schema