from tinyharness.context import (
    ApproxTokenCounter,
)

def test_empty_text_has_zero_tokens():
    counter = ApproxTokenCounter()

    assert counter.count_text("") == 0

def test_text_count_is_positive():
    counter = ApproxTokenCounter()

    result = counter.count_text(
        "Hello TinyHarness"
    )

    assert result > 0

def test_text_count_uses_utf8_bytes():
    counter = ApproxTokenCounter(
        bytes_per_token=4.0
    )

    assert (
        counter.count_text("abcd")
        == 1
    )

    assert (
        counter.count_text("abcde")
        == 2
    )

def test_request_counts_messages_and_tools():
    counter = ApproxTokenCounter()

    messages = [
        {
            "role": "user",
            "content": "Hello",
        }
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "demo",
                "description": "Demo tool",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        }
    ]

    estimate = counter.count_request(
        messages=messages,
        tools=tools,
    )

    assert estimate.messages > 0
    assert estimate.tools > 0
    assert estimate.total > 0

    assert estimate.total >= (
        estimate.messages
    )

    assert estimate.total >= (
        estimate.tools
    )