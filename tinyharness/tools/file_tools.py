from .tool import Tool


def create_file_tools(workspace):  #Deleted resolve_path()  Path security should now belong to workspace

    def list_files(path="."):

        entries = workspace.list_files(path)

        return {
            "path": path,
            "entries": [
                {
                    "name": e.name,
                    "path": e.path,
                    "type": e.type,
                }
                for e in entries
            ],
        }


    def read_file(path):

        content = workspace.read_file(path)

        return {
            "path": path,
            "content": content,
        }


    def write_file(
        path,
        content,
        overwrite=False,
    ):

        if not overwrite:

            try:
                workspace.read_file(path)

                raise FileExistsError(
                    f"File '{path}' already exists."
                )

            except FileNotFoundError:
                pass


        workspace.write_file(
            path,
            content,
        )


        return {
            "path": path,
            "characters_written": len(content),
            "overwritten": overwrite,
        }


    list_files_tool = Tool(
        name="list_files",
        description=(
            "List files and directories inside "
            "the workspace."
        ),
        parameters={
            "type": "object",
            "properties":{
                "path":{
                    "type":"string",
                    "default":".",
                }
            },
            "additionalProperties":False,
        },
        function=list_files,
    )


    read_file_tool = Tool(
        name="read_file",
        description=(
            "Read a text file inside "
            "the workspace."
        ),
        parameters={
            "type":"object",
            "properties":{
                "path":{
                    "type":"string",
                }
            },
            "required":[
                "path"
            ],
            "additionalProperties":False,
        },
        function=read_file,
    )


    write_file_tool = Tool(
        name="write_file",
        description=(
            "Write a text file inside "
            "the workspace."
        ),
        parameters={
            "type":"object",
            "properties":{
                "path":{
                    "type":"string",
                },
                "content":{
                    "type":"string",
                },
                "overwrite":{
                    "type":"boolean",
                    "default":False,
                },
            },
            "required":[
                "path",
                "content",
            ],
            "additionalProperties":False,
        },
        function=write_file,
    )


    return [
        list_files_tool,
        read_file_tool,
        write_file_tool,
    ]