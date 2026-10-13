from .base import (
    CommandResult,
    FileEntry,
    Workspace,
)
from .local import LocalWorkspace
from .docker import DockerWorkspace

__all__ = [
    "CommandResult",
    "FileEntry",
    "Workspace",
    "LocalWorkspace",
    "DockerWorkspace",
] # When someone writes 'from yourpackage import *', only the names listed in __all__ will be imported.