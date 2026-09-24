import os

from dotenv import load_dotenv

from tinyharness.agent import Agent
from tinyharness.models import (
    OpenAICompatibleProvider,
)
from tinyharness.tools import (
    ToolRegistry,
    tool,
)


load_dotenv()

api_key = os.getenv(
    "DEEPSEEK_API_KEY"
)

if not api_key:
    raise ValueError(
        "DEEPSEEK_API_KEY is not set."
    )

@tool()
def add(
    a:float,
    b:float,
):
    """Add two numbers together."""
    return a + b

@tool()
def multiply(
    a: float,
    b: float,
):
    """Multiply two numbers together."""

    return a * b

registry = ToolRegistry()
registry.register(add)
registry.register(multiply)

print("Registered tools:")
print(registry.names())

print("\nAdd schema:")
print(add.schema())

@tool()
def greet(
    name: str,
    excited: bool = False,
):
    """Generate a greeting."""

    if excited:
        return f"Hello, {name}!"

    return f"Hello, {name}."

print(greet.schema())

# print(add(1,2))

# @tool()
# def bad_tool(name):
#     """Bad tool."""

#     return name

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

result = agent.run(
    "What is 10 plus 20 multiplied by 3?"
)

print(result)