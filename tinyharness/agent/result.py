from dataclasses import (
    dataclass,
    field,
)

from tinyharness.tracing import (
    ExecutionTrace,
)

@dataclass
class AgentResult:
    status: str
    content: str | None
    steps: int
    tool_calls: int
    error: str | None = None

    trace: ExecutionTrace | None = field(
        default=None,
        repr=False,
    )