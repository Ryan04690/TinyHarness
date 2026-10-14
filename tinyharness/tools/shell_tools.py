from .decorators import tool


def create_shell_tools(workspace):

    @tool()
    def run_shell(
        command:str,
        cwd:str=".",
        timeout:int=10,
    ):

        result = workspace.run(
            command,
            cwd=cwd,
            timeout=timeout,
        )


        return {
            "command":result.command,
            "cwd":result.cwd,
            "returncode":result.returncode,
            "stdout":result.stdout,
            "stderr":result.stderr,
            "timed_out":result.timed_out,
        }


    return [
        run_shell
    ]