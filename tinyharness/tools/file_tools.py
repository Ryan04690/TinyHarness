# File Tools already has its own path boundaries. But not SandBox

from pathlib import Path
from .tool import Tool

def create_file_tools(project_root):
    root = Path(project_root).resolve()

    def resolve_path(path):
        target = (root / path).resolve()

        try:
            target.relative_to(root)
        except ValueError:
            raise ValueError(
                f"Path '{path}' is outside the project root."
            )

        return target
    
    def list_files(path="."):
        target = resolve_path(path)

        if not target.exists():
            raise FileExistsError(
                f"Path '{path}' is not a directory."
            )
        entries = []

        for items in sorted(target.iterdir()):
            entries.append(
                {
                    "name":items.name,
                    "path":str(
                        items.relative_to(root)
                    ),
                    "type":(
                        "directory"
                        if items.is_dir()
                        else "file"
                    ),
                }
            )

        return {
            "path":str(
                target.relative_to(root)
            ),
            "entries":entries,
        }

    def read_file(path):
        target = resolve_path(path)

        if not target.exists():
            raise FileNotFoundError(
                f"File '{path}' does not exist."
            )

        if not target.is_file():
            raise IsADirectoryError(
                f"Path '{path}' is not a file."
            )

        content = target.read_text(
            encoding="utf-8"
        )

        return {
            "path": str(
                target.relative_to(root)
            ),
            "content": content,
        }

    def write_file(
        path,
        content,
        overwrite=False,
    ):
        target = resolve_path(path)

        existed_before = target.exists()

        if existed_before and not overwrite:
            raise FileExistsError(
                f"File '{path}' already exists. "
                "Set overwrite=true to replace it."
            )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        characters_written = target.write_text(
            content,
            encoding="utf-8",
        )

        return {
            "path": str(
                target.relative_to(root)
            ),
            "characters_written": (
                characters_written
            ),
            "overwritten": existed_before,
        }

    list_files_tool = Tool(
        name="list_files",
        description=(
            "List files and directories inside "
            "the project workspace."
        ),
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Directory path relative "
                        "to the project root."
                    ),
                    "default": ".",
                }
            },
        },
        function=list_files,
    )

    read_file_tool = Tool(
        name="read_file",
        description=(
            "Read a UTF-8 text file inside "
            "the project workspace."
        ),
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "File path relative "
                        "to the project root."
                    ),
                }
            },
            "required": ["path"],
        },
        function=read_file,
    )

    write_file_tool = Tool(
        name="write_file",
        description=(
            "Write a UTF-8 text file inside "
            "the project workspace."
        ),
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "File path relative "
                        "to the project root."
                    ),
                },
                "content": {
                    "type": "string",
                    "description": (
                        "Complete text content "
                        "to write to the file."
                    ),
                },
                "overwrite": {
                    "type": "boolean",
                    "description": (
                        "Whether an existing file "
                        "may be overwritten."
                    ),
                    "default": False,
                },
            },
            "required": [
                "path",
                "content",
            ],
        },
        function=write_file,
    )

    return [
        list_files_tool,
        read_file_tool,
        write_file_tool,
    ]