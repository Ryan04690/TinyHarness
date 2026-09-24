from dataclasses import dataclass

@dataclass
class AgentResult:
    status: str
    tool_calls: int
    steps: int
    content: str
    error: str | None = None