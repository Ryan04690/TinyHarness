# mostly the same as day19

import os

from dotenv import load_dotenv

from tinyharness.agent import Agent
from tinyharness.models import (
    OpenAICompatibleProvider,
)
from pathlib import Path
from tinyharness.tools import (
    ToolRegistry,
    create_file_tools,
    create_search_tools,
    create_shell_tools,
)
from tinyharness.context import (
    ContextBudget,
    LLMContextSummarizer,
    RecentContextPolicy,
    SummaryContextPolicy,
)

load_dotenv()

api_key = os.getenv(
    "DEEPSEEK_API_KEY"
)

if not api_key:
    raise ValueError(
        "DEEPSEEK_API_KEY is not set."
    )


project_root = Path.cwd()

registry = ToolRegistry()

for tool in create_file_tools(project_root):
    registry.register(tool)

for tool in create_search_tools(project_root):
    registry.register(tool)

for tool in create_shell_tools(project_root):
    registry.register(tool)


print(registry.names())
model = OpenAICompatibleProvider(
    model="deepseek-flash",
    api_key=api_key,
    base_url="https://api.deepseek.com",
)

BUDGET = 2000
MAX_STEPS = 10

PROMPT = (
    "Inspect the current TinyHarness repository "
    "using the available tools. "
    "You must perform repository inspection before "
    "giving the final answer. "
    "Use search_files to locate ApproxTokenCounter. "
    "Then use read_file to read "
    "tinyharness/context/token_counter.py and "
    "tests/test_token_counter.py. "
    "Only after inspecting those files, explain "
    "how ApproxTokenCounter estimates tokens, "
    "what state it stores, and why UTF-8 bytes "
    "are used. "
    "Do not answer without using the tools."
)

def analyze_trace(
    name,
    result,
):
    trace = result.trace

    model_calls = len(trace.by_type("model_call_start"))

    summary_calls = len(trace.by_type("context_summary_start"))

    policy_events = trace.by_type("context_policy")

    overflow_checks = [
        event
        for event in trace.by_type("budget_check")
        if not event.data["within_budget"]
    ]

    context_estimates = (trace.by_type("context_estimate"))

    peak_context = 0

    if context_estimates:
        peak_context = max(
            event.data["total_tokens"]
            for event
            in context_estimates
        )

    print(
        "\n"
        "================================"
    )

    print(
        f"Experiment: {name}"
    )

    print(
        "================================"
    )

    print(
        f"status: {result.status}"
    )

    print(
        f"steps: {result.steps}"
    )

    print(
        f"tool_calls: "
        f"{result.tool_calls}"
    )

    print(
        f"model_calls: "
        f"{model_calls}"
    )

    print(
        f"summary_calls: "
        f"{summary_calls}"
    )

    print(
        f"context_policy_calls: "
        f"{len(policy_events)}"
    )

    print(
        f"over_budget_checks: "
        f"{len(overflow_checks)}"
    )

    print(
        f"peak_raw_context: " # If the strategy isn't executed, the model's actual input
        f"{peak_context}"
    )

    if policy_events:
        print(
            "\nContext compression:"
        )

        for event in policy_events:
            print(
                f"  step={event.step}: "
                f"{event.data['before_tokens']} "
                "-> "
                f"{event.data['after_tokens']} "
                "tokens, "
                f"{event.data['before_messages']} "
                "-> "
                f"{event.data['after_messages']} "
                "messages"
            )

no_policy_agent = Agent(
    model=model,
    tool_registry=registry,
    max_steps=MAX_STEPS,
    context_budget=ContextBudget(
        max_input_tokens=BUDGET
    ),
    context_policy=None,
)

print(
    "\n\n"
    "################################"
)
print(
    "# Experiment A: No Policy"
)
print(
    "################################"
)

result_no_policy = (
    no_policy_agent.run(
        PROMPT
    )
)

analyze_trace(
    "No Policy",
    result_no_policy,
)

recent_agent = Agent(
    model=model,
    tool_registry=registry,
    max_steps=MAX_STEPS,
    context_budget=ContextBudget(
        max_input_tokens=BUDGET
    ),
    context_policy=(
        RecentContextPolicy()
    ),
)

print(
    "\n\n"
    "################################"
)
print(
    "# Experiment B: Recent Policy"
)
print(
    "################################"
)

result_recent = recent_agent.run(
    PROMPT
)

analyze_trace(
    "Recent Context Policy",
    result_recent,
)

summarizer = (
    LLMContextSummarizer(
        model=model
    )
)

summary_agent = Agent(
    model=model,
    tool_registry=registry,
    max_steps=MAX_STEPS,
    context_budget=ContextBudget(
        max_input_tokens=BUDGET
    ),
    context_policy=(
        SummaryContextPolicy(
            summarizer=summarizer
        )
    ),
)

print(
    "\n\n"
    "################################"
)
print(
    "# Experiment C: Summary Policy"
)
print(
    "################################"
)

result_summary = (summary_agent.run(PROMPT))

analyze_trace(
    "Summary Context Policy",
    result_summary,
)

def summary_row(
    name,
    result,
):
    trace = result.trace

    return {
        "name": name,
        "status": result.status,
        "steps": result.steps,
        "tool_calls": (result.tool_calls),
        "model_calls": len(trace.by_type("model_call_start")),
        "summary_calls": len(trace.by_type("context_summary_start")),
        "policy_calls": len(trace.by_type("context_policy")),
    }


rows = [
    summary_row(
        "No Policy",
        result_no_policy,
    ),
    summary_row(
        "Recent",
        result_recent,
    ),
    summary_row(
        "Summary",
        result_summary,
    ),
]


print(
    "\n\n"
    "================================"
)
print(
    "Final Comparison"
)
print(
    "================================"
)

for row in rows:
    print(
        f"{row['name']:<12} "
        f"status={row['status']:<18} "
        f"steps={row['steps']:<3} "
        f"tools={row['tool_calls']:<3} "
        f"models={row['model_calls']:<3} "
        f"summaries={row['summary_calls']:<3} "
        f"policies={row['policy_calls']}"
    )