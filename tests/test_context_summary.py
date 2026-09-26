from types import SimpleNamespace

from tinyharness.context import (
    ApproxTokenCounter,
    ContextBudget,
    LLMContextSummarizer,
    SummaryContextPolicy,
)


# =========================================================
# Fake Summarizer
# =========================================================

class FakeSummarizer:
    def __init__(
        self,
        summary="Old context summary.",
    ):
        self.summary = summary
        self.calls = []

    def summarize(
        self,
        messages,
    ):
        self.calls.append(
            list(messages)
        )

        return self.summary


# =========================================================
# Fake Model
# =========================================================

class FakeModel:
    def __init__(
        self,
        content="Compressed history.",
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
                    message=SimpleNamespace(
                        content=self.content
                    )
                )
            ]
        )


# =========================================================
# Test 1
# No overflow -> no summarization
# =========================================================

def test_summary_policy_does_nothing_when_within_budget():
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

    summarizer = FakeSummarizer()

    policy = SummaryContextPolicy(
        summarizer=summarizer
    )

    result = policy.apply(
        messages=messages,
        tools=[],
        token_counter=counter,
        context_budget=budget,
    )

    assert result == messages

    assert summarizer.calls == []


# =========================================================
# Test 2
# Old block should be summarized
# =========================================================

def test_summary_policy_summarizes_old_block():
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
        "content": "x" * 1200,
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
        "content": "important recent result",
    }

    messages = [
        user,
        old_assistant,
        old_tool,
        recent_assistant,
        recent_tool,
    ]

    summary_text = (
        "Old search produced a large result."
    )

    summarizer = FakeSummarizer(
        summary=summary_text
    )

    policy = SummaryContextPolicy(
        summarizer=summarizer
    )

    expected = [
        user,
        {
            "role": "assistant",
            "content": (
                "[Earlier execution summary]\n"
                f"{summary_text}"
            ),
        },
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

    result = policy.apply(
        messages=messages,
        tools=[],
        token_counter=counter,
        context_budget=budget,
    )

    assert result == expected

    assert summarizer.calls


# =========================================================
# Test 3
# Summarizer should receive only old history
# =========================================================

def test_summary_policy_sends_old_history_to_summarizer():
    counter = ApproxTokenCounter()

    user = {
        "role": "user",
        "content": "Task",
    }

    old_assistant = {
        "role": "assistant",
        "tool_calls": [
            {
                "id": "call_1",
            }
        ],
    }

    old_tool = {
        "role": "tool",
        "tool_call_id": "call_1",
        "content": "x" * 1000,
    }

    recent_assistant = {
        "role": "assistant",
        "content": "Recent message",
    }

    messages = [
        user,
        old_assistant,
        old_tool,
        recent_assistant,
    ]

    summarizer = FakeSummarizer(
        summary="summary"
    )

    policy = SummaryContextPolicy(
        summarizer=summarizer
    )

    expected_candidate = [
        user,
        {
            "role": "assistant",
            "content": (
                "[Earlier execution summary]\n"
                "summary"
            ),
        },
        recent_assistant,
    ]

    target_tokens = (
        counter.count_request(
            messages=expected_candidate,
            tools=[],
        ).total
    )

    budget = ContextBudget(
        max_input_tokens=target_tokens
    )

    policy.apply(
        messages=messages,
        tools=[],
        token_counter=counter,
        context_budget=budget,
    )

    assert summarizer.calls

    assert (
        summarizer.calls[0]
        == [
            old_assistant,
            old_tool,
        ]
    )


# =========================================================
# Test 4
# Original full trajectory must not be mutated
# =========================================================

def test_summary_policy_does_not_mutate_original_messages():
    counter = ApproxTokenCounter()

    messages = [
        {
            "role": "user",
            "content": "Task",
        },
        {
            "role": "assistant",
            "content": "x" * 1000,
        },
    ]

    original = list(messages)

    summarizer = FakeSummarizer(
        summary="summary"
    )

    policy = SummaryContextPolicy(
        summarizer=summarizer
    )

    policy.apply(
        messages=messages,
        tools=[],
        token_counter=counter,
        context_budget=ContextBudget(
            max_input_tokens=1
        ),
    )

    assert messages == original


# =========================================================
# Test 5
# LLMContextSummarizer should call model without tools
# =========================================================

def test_llm_context_summarizer():
    model = FakeModel(
        content="Compressed history."
    )

    summarizer = LLMContextSummarizer(
        model=model
    )

    result = summarizer.summarize(
        [
            {
                "role": "tool",
                "content": "large output",
            }
        ]
    )

    assert (
        result
        == "Compressed history."
    )

    assert len(model.calls) == 1

    assert (
        model.calls[0]["tools"]
        is None
    )

    assert len(
        model.calls[0]["messages"]
    ) == 2

    assert (
        model.calls[0]["messages"][0]
        ["role"]
        == "system"
    )

    assert (
        model.calls[0]["messages"][1]
        ["role"]
        == "user"
    )


# =========================================================
# Test 6
# Empty input should not call model
# =========================================================

def test_llm_context_summarizer_empty_messages():
    model = FakeModel()

    summarizer = LLMContextSummarizer(
        model=model
    )

    result = summarizer.summarize(
        []
    )

    assert result == ""

    assert model.calls == []


# =========================================================
# Test 7
# Empty model summary should be rejected
# =========================================================

def test_llm_context_summarizer_rejects_empty_content():
    model = FakeModel(
        content=""
    )

    summarizer = LLMContextSummarizer(
        model=model
    )

    try:
        summarizer.summarize(
            [
                {
                    "role": "assistant",
                    "content": "old context",
                }
            ]
        )

        assert False, (
            "Expected ValueError "
            "for empty summary."
        )

    except ValueError as error:
        assert (
            "empty content"
            in str(error)
        )