import subprocess
import locale
import os

from dotenv import load_dotenv
from pathlib import Path
from tinyharness.agent import Agent
from tinyharness.models import OpenAICompatibleProvider
from tinyharness.tools import Tool,ToolRegistry

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    raise ValueError(
        "DEEPSEEK_API_KEY is not set."
    )

def add(a, b):
    return a + b


def multiply(a, b):
    return a * b

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

multiply_tool = Tool(
    name="multiply",
    description="Multiply two numbers together.",
    parameters={
        "type": "object",
        "properties": {
             "a": {
                "type": "number",
                 "description": "The first number to multiply."
            },
            "b": {
                "type": "number",
                "description": "The second number to multiply."
            }
        },
        "required": ["a", "b"]
                },
    function=multiply,
)

registry = ToolRegistry()
registry.register(add_tool)
registry.register(multiply_tool)

model = OpenAICompatibleProvider(
    model="deepseek-flash",
    api_key=api_key,
    base_url="https://api.deepseek.com",
)

agent = Agent(
    model=model,
    tool_registry=registry,
    max_steps=10,
)

print(agent.run("What is 10 plus 20 multiplied by 3?"))