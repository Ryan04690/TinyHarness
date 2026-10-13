from .base import (
    CommandResult,
    FileEntry,
    Workspace,
)
from .local import LocalWorkspace

__all__ = [
    "CommandResult",
    "FileEntry",
    "Workspace",
    "LocalWorkspace",
] # When someone writes 'from yourpackage import *', only the names listed in __all__ will be imported.