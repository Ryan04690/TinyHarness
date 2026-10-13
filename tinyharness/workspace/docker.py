import subprocess
import shlex

from .base import (
    Workspace,
    CommandResult,
    FileEntry,
)


class DockerWorkspace(Workspace):
    """
    Workspace implementation backed by Docker container.

    The workspace interface remains identical to LocalWorkspace,
    but all operations are executed inside a container.
    """

    def __init__(
        self,
        image: str = "ubuntu:latest",
    ):
        self.image = image
        self.container_id = None


    def create(self):
        """
        Create and start a detached container.
        """

        result = subprocess.run(
            [
                "docker",
                "run",
                "-dit",
                self.image,
                "bash",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        self.container_id = result.stdout.strip()


    def remove(self):
        """
        Remove container.
        """

        if self.container_id is None:
            return

        subprocess.run(
            [
                "docker",
                "rm",
                "-f",
                self.container_id,
            ],
            capture_output=True,
            text=True,
        )

        self.container_id = None


    def _ensure_running(self):

        if self.container_id is None:
            raise RuntimeError(
                "Docker container is not created."
            )


    def run(
        self,
        command: str,
        cwd: str = ".",
        timeout: int = 10,
    ) -> CommandResult:

        self._ensure_running()


        docker_command = [
            "docker",
            "exec",
            self.container_id,
            "bash",
            "-c",
            f"cd {shlex.quote(cwd)} && {command}",
        ]


        try:

            result = subprocess.run(
                docker_command,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return CommandResult(
                command=command,
                cwd=cwd,
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )


        except subprocess.TimeoutExpired:

            return CommandResult(
                command=command,
                cwd=cwd,
                returncode=-1,
                stdout="",
                stderr="Command timed out.",
                timed_out=True,
            )


    def write_file(
        self,
        path: str,
        content: str,
    ) -> None:

        self._ensure_running()


        escaped = (
            content
            .replace("\\", "\\\\")
            .replace("'", "'\\''")
        )


        command = (
            f"echo '{escaped}' > {shlex.quote(path)}"
        )


        result = self.run(command)


        if result.returncode != 0:
            raise RuntimeError(
                result.stderr
            )


    def read_file(
        self,
        path: str,
    ) -> str:

        result = self.run(
            f"cat {shlex.quote(path)}"
        )


        if result.returncode != 0:
            raise RuntimeError(
                result.stderr
            )


        return result.stdout


    def list_files(
        self,
        path: str = ".",
    ) -> list[FileEntry]:

        result = self.run(
            f"ls -a {shlex.quote(path)}"
        )


        if result.returncode != 0:
            raise RuntimeError(
                result.stderr
            )


        entries=[]


        for name in result.stdout.splitlines():

            if name in [".", ".."]:
                continue


            entries.append(
                FileEntry(
                    name=name,
                    path=f"{path}/{name}",
                    type="unknown",
                )
            )


        return entries