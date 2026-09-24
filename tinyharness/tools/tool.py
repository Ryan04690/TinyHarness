from dataclasses import dataclass
from typing import Callable
from jsonschema import validate


@dataclass
class Tool:
    name:str
    description:str
    parameters:str
    function:Callable

    def schema(self):
        return {
            "type":"function",
            "function":{
                "name":self.name,
                "description":self.description,
                "parameters":self.parameters,
            },
        }
    #  Check if the JSON returned by the LLM meets the tool's requirements
    def validata_arguments(self,arguments):
        validate(
            instance=arguments,
            schema=self.parameters,
        )

    def execute(self,arguments):
        self.validata_arguments(arguments)
        return self.function(**arguments)


"""
def add(a, b):
    return a + b

add_tool = Tool(
    name="add",
    description="Add two numbers together.",
    parameters={
        "type": "object",
        "properties": {
            "a": {
                "type": "number",
            },
            "b": {
                "type": "number",
            },
        },
        "required": ["a", "b"],
    },
    function=add,
)
print(add_tool.execute({"a":1,"b":2,}))
"""
