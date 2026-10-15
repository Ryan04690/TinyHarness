# Tool Registry

from tinyharness.security import (
    PermissionAction,
    PermissionManager,
)


DEFAULT_TOOL_PERMISSIONS = {
    "list_files": PermissionAction.READ,
    "read_file": PermissionAction.READ,
    "search_files": PermissionAction.READ,
    "write_file": PermissionAction.WRITE,
    "run_shell": PermissionAction.SHELL,
}


class ToolRegistry:
    def __init__(
        self,
        permission_manager: PermissionManager | None = None,
        tool_permissions: dict | None = None,
    ):
        self._tools = {}
        self.permission_manager = permission_manager

        self.tool_permissions = DEFAULT_TOOL_PERMISSIONS.copy()

        if tool_permissions is not None:
            self.tool_permissions.update(tool_permissions)

    def register(self, tool):
        if tool.name in self._tools:
            raise ValueError(
                f"Tool '{tool.name}' is already registered."
            )

        self._tools[tool.name] = tool

    def get(self, name):
        return self._tools.get(name)

    def schemas(self):
        return [
            tool.schema()
            for tool in self._tools.values()
        ]

    def execute(
        self,
        name,
        arguments,
        *,
        user_approved: bool = False,
    ):
        tool = self.get(name)

        if tool is None:
            raise KeyError(
                f"Tool '{name}' not found"
            )

        # Permission check before executing the tool.
        if self.permission_manager is not None:
            action = self.tool_permissions.get(name)

            # Fail closed: an unmapped tool cannot execute.
            if action is None:
                raise PermissionError(
                    f"No permission policy for tool '{name}'."
                )

            self.permission_manager.require(
                action,
                user_approved=user_approved,
            )

        return tool.execute(arguments)

    def __len__(self):
        return len(self._tools)

    def names(self):
        return list(self._tools.keys())
