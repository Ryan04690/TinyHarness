# Tool Registry
class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self,tool):
        if tool.name in self._tools:
            raise ValueError(
                f"Tool '{tool.name}' is already registered."
            )
        self._tools[tool.name] = tool

    def get(self,name):
        return self._tools.get(name)

    def schemas(self):
        return [
            tool.schema()
            for tool in self._tools.values()
        ]

    def execute(self,name,arguments):
        tool = self.get(name)

        if tool is None:
            raise KeyError(
                f"Tool '{name}' not found"
            )

        return tool.execute(arguments)

    def __len__(self):
        return len(self._tools)

    def names(self):
        return list(self._tools.keys())
        