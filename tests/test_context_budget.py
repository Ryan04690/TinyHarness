import pytest

from tinyharness.context import ContextBudget

def test_context_within_budget():
    budget = ContextBudget(
        max_input_tokens=1000
    )

    result = budget.check(600)

    assert result.input_tokens == 600
    assert result.max_input_tokens == 1000
    assert result.remaining_tokens == 400
    assert result.within_budget is True
    assert result.usage_ratio == 0.6

def test_context_exactly_at_budget():
    budget = ContextBudget(
        max_input_tokens=1000
    )

    result = budget.check(1000)

    assert result.remaining_tokens == 0
    assert result.within_budget is True
    assert result.usage_ratio == 1.0

def test_context_over_budget():
    budget = ContextBudget(
        max_input_tokens=1000
    )

    result = budget.check(1200)

    assert result.remaining_tokens == -200
    assert result.within_budget is False
    assert result.usage_ratio == 1.2

def test_context_budget_must_be_positive():
    with pytest.raises(ValueError):
        ContextBudget(
            max_input_tokens=0
        )