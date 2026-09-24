from pathlib import Path

from jsonschema import ValidationError

from tinyharness.tools import (
    ToolRegistry,
    create_file_tools,
)


project_root = Path.cwd()

registry = ToolRegistry()

for tool in create_file_tools(project_root):
    registry.register(tool)

try:
    registry.execute(
        "read_file",
        {
            "path": "README.md",
            "banana": 123,
        },
    )
except ValidationError as error:
    print(error.message)

# result = registry.execute(
#     "read_file",
#     {
#         "path": "README.md",
#     },
# )

# print(result)
