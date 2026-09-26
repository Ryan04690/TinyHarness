# Mostly the same as day13
import os

from dotenv import load_dotenv

from tinyharness.agent import Agent
from tinyharness.models import (
    OpenAICompatibleProvider,
)
from pathlib import Path
from tinyharness.tools import (
    ToolRegistry,
    create_file_tools,
    create_search_tools,
    create_shell_tools,
)

load_dotenv()

api_key = os.getenv(
    "DEEPSEEK_API_KEY"
)

if not api_key:
    raise ValueError(
        "DEEPSEEK_API_KEY is not set."
    )


project_root = Path.cwd()

registry = ToolRegistry()

for tool in create_file_tools(
    project_root
):
    registry.register(tool)

for tool in create_search_tools(
    project_root
):
    registry.register(tool)

for tool in create_shell_tools(
    project_root
):
    registry.register(tool)


print(registry.names())
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
    (
        "Find the Python file that defines "
        "ApproxTokenCounter and explain what fields "
        "it stores."
    )
)

print(result)