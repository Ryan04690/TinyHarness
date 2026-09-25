import os

from dotenv import load_dotenv
from tinyharness.models import (
    OpenAICompatibleProvider,
)
from tinyharness.agent import Agent
from pathlib import Path

from tinyharness.tools import (
    ToolRegistry,
    create_file_tools,
    create_search_tools,
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

# result = registry.execute(
#     "search_files",
#     {
#         "query":"agent",
#         "search_type":"name",
#     },
# )

# result = registry.execute(
#     "search_files",
#     {
#         "query": ".py",
#         "search_type": "suffix",
#         "max_results": 20,
#     },
# )

# result = registry.execute(
#     "search_files",
#     {
#         "query": "class Agent",
#         "search_type": "content",
#     },
# )

# result = registry.execute(
#     "search_files",
#     {
#         "query": ".py",
#         "search_type": "suffix",
#         "recursive": False,
#     },
# )

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
        "the Agent class, read that file, "
        "and explain what Agent.run does."
    )
)

print(result)


