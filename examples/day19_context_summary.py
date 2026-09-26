

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

for tool in create_file_tools(
    project_root
):
    registry.register(tool)

for tool in create_search_tools(
    project_root
):
    registry.register(tool)

for tool in create_shell_tools(
    project_root
):
    registry.register(tool)


print(registry.names())
model = OpenAICompatibleProvider(
    model="deepseek-flash",
    api_key=api_key,
    base_url="https://api.deepseek.com",
)

summarizer = (
    LLMContextSummarizer(
        model
    )
)

policy = SummaryContextPolicy(
    summarizer=summarizer
)

budget = ContextBudget(
    max_input_tokens=2000
)

agent = Agent(
    model=model,
    tool_registry=registry,
    max_steps=10,
    context_budget=budget,
    context_policy=policy,
)
result = agent.run(
    (
        "Find the file that defines "
        "ApproxTokenCounter, inspect how it "
        "estimates tokens, and explain both "
        "what state it stores and why UTF-8 "
        "bytes are used."
    )
)

print(result)