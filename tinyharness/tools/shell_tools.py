import locale
import subprocess
from pathlib import Path

from .decorators import tool


def decode_output(data): # fix the issue where subprocess.run returns stdout and stderr as bytes on Windows
    if not data:
        return ""

    encodings = [
        "utf-8",
        locale.getpreferredencoding(False),
        "gb18030",
    ]

    for encoding in encodings:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue

    return data.decode(
        "utf-8",
        errors="replace",
    )


def create_shell_tools(project_root):
    root = Path(project_root).resolve() # This will be replaced with Workspace later

    def resolve_cwd(cwd):
        target = (root / cwd).resolve()

        try:
            target.relative_to(root)

        except ValueError:
            raise ValueError(
                f"Working directory '{cwd}' "
                "is outside the project root."
            )

        if not target.exists():
            raise FileNotFoundError(
                f"Working directory '{cwd}' "
                "does not exist."
            )

        if not target.is_dir():
            raise NotADirectoryError(
                f"Working directory '{cwd}' "
                "is not a directory."
            )

        return target

    @tool()
    def run_shell(
        command: str,
        cwd: str = ".",
        timeout: int = 10,
    ):
        """Execute a Windows shell command inside the project workspace."""

        if timeout <= 0:
            raise ValueError(
                "timeout must be greater than 0."
            )

        if timeout > 60:
            raise ValueError(
                "timeout cannot exceed 60 seconds."
            )

        workdir = resolve_cwd(cwd)

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                timeout=timeout,
                cwd=workdir,
            )

            return {
                "command": command,
                "cwd": str(
                    workdir.relative_to(root)
                ),
                "returncode": (
                    result.returncode
                ),
                "stdout": decode_output(
                    result.stdout
                ),
                "stderr": decode_output(
                    result.stderr
                ),
                "timed_out": False,
            }

        except subprocess.TimeoutExpired as error:
            return {
                "command": command,
                "cwd": str(
                    workdir.relative_to(root)
                ),
                "returncode": None,
                "stdout": decode_output(
                    error.stdout
                ),
                "stderr": decode_output(
                    error.stderr
                ),
                "timed_out": True,
                "message": (
                    f"Command exceeded "
                    f"timeout={timeout} seconds."
                ),
            }

    return [
        run_shell,
    ]