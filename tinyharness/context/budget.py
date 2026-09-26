# tinyharness/context/budget.py

from dataclasses import dataclass

@dataclass(frozen=True)
class BudgetCheck:
    input_tokens: int
    max_input_tokens: int
    remaining_tokens: int
    within_budget: bool
    usage_ratio: float

class ContextBudget:
    def __init__(
        self,
        max_input_tokens: int,
    ):
        if max_input_tokens <= 0:
            raise ValueError(
                "max_input_tokens must be "
                "greater than 0."
            )

        self.max_input_tokens = (
            max_input_tokens
        )

    def check(
        self,
        input_tokens: int,
    ) -> BudgetCheck:
        if input_tokens < 0:
            raise ValueError(
                "input_tokens cannot be negative."
            )

        remaining_tokens = (
            self.max_input_tokens
            - input_tokens
        )

        return BudgetCheck(
            input_tokens=input_tokens,
            max_input_tokens=(
                self.max_input_tokens
            ),
            remaining_tokens=(
                remaining_tokens
            ),
            within_budget=(
                input_tokens
                <= self.max_input_tokens
            ),
            usage_ratio=(
                input_tokens
                / self.max_input_tokens
            ),
        )