from dataclasses import (
    dataclass,
    field,
)


@dataclass
class AgentState:
    messages: list[dict] = field(
        default_factory=list # Every time a new AgentState is created, call list() again.
    )

    steps: int = 0
    tool_calls: int = 0

    @classmethod
    def from_user_input(
        cls,
        user_input: str,
    ):
        return cls( # similar as **return AgentState(...)**
            messages=[
                {
                    "role": "user",
                    "content": user_input,
                }
            ]
        )

    def append_message(
        self,
        message: dict,
    ):
        self.messages.append(message)

    def record_step(self):
        self.steps += 1

    def record_tool_call(self):
        self.tool_calls += 1