# For today all file paths must be inside the project root.
# Only implement the first layer of the Workspace Boundary, sandbox features to be developed later
import os
from pathlib import Path

from dotenv import load_dotenv

from tinyharness.agent import Agent
from tinyharness.models import (
    OpenAICompatibleProvider,
)
from tinyharness.tools import (
    ToolRegistry,
    create_file_tools,
)


load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    raise ValueError(
        "DEEPSEEK_API_KEY is not set."
    )

project_root = Path.cwd()

registry = ToolRegistry()
for tool in create_file_tools(project_root):
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
# result = agent.run(
#     (
#         "List the files in the current project, "
#         "read README.md, and tell me what this "
#         "project is about."
#     )
# )

# result = agent.run(
#     (
#         "Create a file named "
#         "'day09_test.txt' in the project root. "
#         "Write exactly 'Hello from TinyHarness' "
#         "into it, then read the file back "
#         "and verify its content."
#     )
# )

result = agent.run("Read C:\Windows\win.ini")

print(result)