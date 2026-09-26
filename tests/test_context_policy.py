from tinyharness.context import (
    ApproxTokenCounter,
    ContextBudget,
    RecentContextPolicy,
)

def test_policy_keeps_messages_when_within_budget():
    counter = ApproxTokenCounter()

    messages = [
        {
            "role": "user",
            "content": "Hello",
        },
        {
            "role": "assistant",
            "content": "Hi",
        },
    ]

    full_tokens = (
        counter.count_request(
            messages=messages,
            tools=[],
        ).total
    )

    budget = ContextBudget(
        max_input_tokens=full_tokens
    )

    policy = RecentContextPolicy()

    result = policy.apply(
        messages=messages,
        tools=[],
        token_counter=counter,
        context_budget=budget,
    )

    assert result == messages

def test_policy_drops_oldest_block():
    counter = ApproxTokenCounter()

    user = {
        "role": "user",
        "content": "Do the task.",
    }

    old_assistant = {
        "role": "assistant",
        "tool_calls": [
            {
                "id": "call_old",
            }
        ],
    }

    old_tool = {
        "role": "tool",
        "tool_call_id": "call_old",
        "content": "x" * 1000,
    }

    recent_assistant = {
        "role": "assistant",
        "tool_calls": [
            {
                "id": "call_recent",
            }
        ],
    }

    recent_tool = {
        "role": "tool",
        "tool_call_id": "call_recent",
        "content": "recent result",
    }

    messages = [
        user,
        old_assistant,
        old_tool,
        recent_assistant,
        recent_tool,
    ]

    expected = [
        user,
        recent_assistant,
        recent_tool,
    ]

    target_tokens = (
        counter.count_request(
            messages=expected,
            tools=[],
        ).total
    )

    budget = ContextBudget(
        max_input_tokens=target_tokens
    )

    policy = RecentContextPolicy()

    result = policy.apply(
        messages=messages,
        tools=[],
        token_counter=counter,
        context_budget=budget,
    )

    assert result == expected

def test_policy_preserves_tool_pair():
    counter = ApproxTokenCounter()

    messages = [
        {
            "role": "user",
            "content": "Task",
        },
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_1",
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "content": "result",
        },
    ]

    tokens = (
        counter.count_request(
            messages=messages,
            tools=[],
        ).total
    )

    policy = RecentContextPolicy()

    result = policy.apply(
        messages=messages,
        tools=[],
        token_counter=counter,
        context_budget=(
            ContextBudget(tokens)
        ),
    )

    assert (
        result[1]["role"]
        == "assistant"
    )

    assert result[2]["role"] == "tool"

    assert (
        result[2]["tool_call_id"]
        == "call_1"
    )

def test_policy_keeps_multi_tool_block_together():
    counter = ApproxTokenCounter()

    user = {
        "role": "user",
        "content": "Task",
    }

    assistant = {
        "role": "assistant",
        "tool_calls": [
            {"id": "call_1"},
            {"id": "call_2"},
        ],
    }

    tool_1 = {
        "role": "tool",
        "tool_call_id": "call_1",
        "content": "result 1",
    }

    tool_2 = {
        "role": "tool",
        "tool_call_id": "call_2",
        "content": "result 2",
    }

    messages = [
        user,
        assistant,
        tool_1,
        tool_2,
    ]

    tokens = (
        counter.count_request(
            messages=messages,
            tools=[],
        ).total
    )

    result = RecentContextPolicy().apply(
        messages=messages,
        tools=[],
        token_counter=counter,
        context_budget=(
            ContextBudget(tokens)
        ),
    )

    assert result == messages

def test_policy_returns_prefix_when_nothing_else_fits():
    counter = ApproxTokenCounter()

    user = {
        "role": "user",
        "content": "x" * 1000,
    }

    messages = [
        user,
        {
            "role": "assistant",
            "content": "old message",
        },
    ]

    policy = RecentContextPolicy()

    result = policy.apply(
        messages=messages,
        tools=[],
        token_counter=counter,
        context_budget=(
            ContextBudget(
                max_input_tokens=1
            )
        ),
    )

    assert result == [user]

    estimate = (
        counter.count_request(
            messages=result,
            tools=[],
        )
    )

    assert (
        ContextBudget(1)
        .check(estimate.total)
        .within_budget
        is False
    )

