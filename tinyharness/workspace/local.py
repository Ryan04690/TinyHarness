from pathlib import Path
import subprocess

from .base import Workspace, CommandResult, FileEntry

"""
LocalWorkspace.run() still calls the Windows Shell, and the command itself might access things outside the root directory, so it's still not a secure sandbox.
"""

class LocalWorkspace(Workspace):

    def __init__(
        self,
        root: Path,
    ):
        self.root = root.resolve()


    def _resolve_path(self, path: str) -> Path:
        target = (self.root / path).resolve()

        if not target.is_relative_to(self.root):
            raise ValueError(
                "Path escapes workspace root"
            )

        return target


    def read_file(
        self,
        path: str,
    ) -> str:

        target = self._resolve_path(path)

        return target.read_text(
            encoding="utf-8"
        )


    def write_file(
        self,
        path: str,
        content: str,
    ):

        target = self._resolve_path(path)

        target.write_text(
            content,
            encoding="utf-8"
        )


    def list_files(
    self,
    path: str = ".",
) -> list[FileEntry]:

        directory = self._resolve_path(path)

        if not directory.is_dir():
            raise NotADirectoryError(
                f"Not a directory: {path}"
            )

        return [
            FileEntry(
                name=item.name,
                path=item.relative_to(self.root).as_posix(),
                type="dir" if item.is_dir() else "file",
            )
            for item in sorted(directory.iterdir())
        ]


    def run(
        self,
        command: str,
        cwd: str = ".",
        timeout: int = 10,
    ):

        workdir = self._resolve_path(cwd)


        result = subprocess.run(
            command,
            shell=True,
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )


        return CommandResult(
            command=command,
            cwd=str(workdir),
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=False,
        )