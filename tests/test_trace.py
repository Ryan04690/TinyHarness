from types import SimpleNamespace

from tinyharness.agent import (
    Agent,
    AgentState,
)
from tinyharness.tools import (
    ToolRegistry,
)
from tinyharness.tracing import (
    ExecutionTrace,
)


class FakeMessage:
    def __init__(
        self,
        content,
        tool_calls=None,
    ):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(
        self,
        exclude_none=True,
    ):
        result = {
            "role": "assistant",
            "content": self.content,
        }

        if self.tool_calls is not None:
            result["tool_calls"] = (
                self.tool_calls
            )

        return result


class FakeModel:
    def __init__(
        self,
        content="Done.",
    ):
        self.content = content
        self.calls = []

    def generate(
        self,
        messages,
        tools=None,
    ):
        self.calls.append(
            {
                "messages": messages,
                "tools": tools,
            }
        )

        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=FakeMessage(
                        content=self.content,
                        tool_calls=None,
                    )
                )
            ]
        )


def test_execution_trace_records_events():
    trace = ExecutionTrace()

    trace.record(
        "run_start",
        step=0,
        user_input="Hello",
    )

    trace.record(
        "context_estimate",
        step=1,
        total_tokens=100,
    )

    assert len(trace) == 2

    assert (
        trace.events[0].event_type
        == "run_start"
    )

    assert trace.events[0].step == 0

    assert (
        trace.events[1].data[
            "total_tokens"
        ]
        == 100
    )


def test_execution_trace_filters_by_type():
    trace = ExecutionTrace()

    trace.record(
        "tool_call",
        step=1,
        tool_name="read_file",
    )

    trace.record(
        "tool_result",
        step=1,
        tool_name="read_file",
    )

    trace.record(
        "tool_call",
        step=2,
        tool_name="search_files",
    )

    tool_calls = trace.by_type(
        "tool_call"
    )

    assert len(tool_calls) == 2

    assert (
        tool_calls[0].data[
            "tool_name"
        ]
        == "read_file"
    )

    assert (
        tool_calls[1].data[
            "tool_name"
        ]
        == "search_files"
    )


def test_execution_trace_to_dict():
    trace = ExecutionTrace()

    trace.record(
        "run_end",
        step=2,
        status="success",
    )

    result = trace.to_dict()

    assert "events" in result

    assert len(
        result["events"]
    ) == 1

    assert (
        result["events"][0][
            "event_type"
        ]
        == "run_end"
    )

    assert (
        result["events"][0][
            "data"
        ]["status"]
        == "success"
    )


def test_agent_states_do_not_share_trace():
    state_a = (
        AgentState.from_user_input(
            "A"
        )
    )

    state_b = (
        AgentState.from_user_input(
            "B"
        )
    )

    state_a.trace.record(
        "test_event",
        step=1,
    )

    assert len(
        state_a.trace
    ) == 1

    assert len(
        state_b.trace
    ) == 0


def test_agent_result_contains_trace():
    model = FakeModel(
        content="Done."
    )

    registry = ToolRegistry()

    agent = Agent(
        model=model,
        tool_registry=registry,
        max_steps=3,
    )

    result = agent.run(
        "Say done."
    )

    assert (
        result.status
        == "success"
    )

    assert result.trace is not None

    event_types = [
        event.event_type
        for event
        in result.trace.events
    ]

    assert "run_start" in event_types

    assert (
        "context_estimate"
        in event_types
    )

    assert (
        "model_call_start"
        in event_types
    )

    assert (
        "model_response"
        in event_types
    )

    assert (
        "final_answer"
        in event_types
    )

    assert "run_end" in event_types