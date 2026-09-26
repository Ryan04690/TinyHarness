from dataclasses import dataclass
import json
import math

@dataclass(frozen=True) # immutable measurement result
class TokenEstimate:
    messages: int
    tools: int
    total: int

class ApproxTokenCounter:
    def __init__(
        self,
        bytes_per_token: float = 3.0,
    ):
        if bytes_per_token <= 0:
            raise ValueError(
                "bytes_per_token must be "
                "greater than 0."
            )

        self.bytes_per_token = (
            bytes_per_token
        )

    def count_text(
        self,
        text: str,
    ) -> int:
        if not isinstance(text, str):
            raise TypeError(
                "text must be a string."
            )

        if not text:
            return 0

        byte_count = len(
            text.encode("utf-8")  # Able to give a somewhat reasonable general estimate for English, Chinese, code, and JSON at the same time
        )

        return math.ceil(
            byte_count
            / self.bytes_per_token
        )

    def count_json(
        self,
        value,
    ) -> int:
        serialized = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )

        return self.count_text(
            serialized
        )

    def count_messages(
        self,
        messages,
    ) -> int:
        if not messages:
            return 0

        return self.count_json(
            messages
        )

    def count_tools(
        self,
        tools,
    ) -> int:
        if not tools:
            return 0

        return self.count_json(
            tools
        )

    def count_request(
        self,
        messages,
        tools=None,
    ) -> TokenEstimate:
        message_tokens = (
            self.count_messages(
                messages
            )
        )

        tool_tokens = self.count_tools(
            tools
        )

        payload = {
            "messages": messages,
        }

        if tools:
            payload["tools"] = tools

        total_tokens = self.count_json(
            payload
        )

        return TokenEstimate(
            messages=message_tokens,
            tools=tool_tokens,
            total=total_tokens,
        )