from tinyharness.agent import AgentState

def test_state_from_user_input():
    state = AgentState.from_user_input(
        "Hello"
    )

    assert state.messages == [
        {
            "role": "user",
            "content": "Hello",
        }
    ]

    assert state.steps == 0
    assert state.tool_calls == 0

def test_state_append_message():
    state = AgentState.from_user_input(
        "Hello"
    )

    state.append_message(
        {
            "role": "assistant",
            "content": "Hi",
        }
    )

    assert len(state.messages) == 2

    assert (
        state.messages[-1]["content"]
        == "Hi"
    )

def test_state_counters():
    state = AgentState()

    state.record_step()
    state.record_step()

    state.record_tool_call()

    assert state.steps == 2
    assert state.tool_calls == 1

# Test whether the two states are independent
def test_states_do_not_share_messages():
    state_a = AgentState()
    state_b = AgentState()

    state_a.append_message(
        {
            "role": "user",
            "content": "Task A",
        }
    )

    assert len(state_a.messages) == 1
    assert len(state_b.messages) == 0