# TinyHarness

TinyHarness is a minimal, hackable agent harness built from scratch for learning, experimentation, and understanding how tool-using LLM agents work internally.

Instead of relying on large agent frameworks, TinyHarness implements the core runtime step by step:

```text
User
↓
Agent
↓
Model
↓
Tool Call
↓
Tool Execution
↓
Observation
↓
Model
↓
Final Answer
```

The project is intentionally small and transparent so that every component can be understood, modified, tested, and replaced independently.

---

## Why TinyHarness?

Modern agent frameworks often hide important runtime mechanisms behind large abstractions.

TinyHarness takes the opposite approach:

> Build the smallest working agent runtime first, understand every component, then gradually add more advanced capabilities.

The project is developed through build-driven learning:

```text
Problem
↓
Understand
↓
Implement
↓
Test
↓
Experiment
↓
Refactor
```

TinyHarness is not intended to compete with mature agent frameworks.

Its main goal is to make the internal structure of an agent harness explicit.

---

## Current Version

Current milestone:

```text
v0.3.0
```

TinyHarness v0.3 introduces:

- Agent runtime state
- Approximate token estimation
- Context budgets
- Recent-context truncation
- Summary-based context compression
- Structured execution tracing

Current automated test status:

```text
50 passed
```

---

## Current Features

### Agent Runtime

- OpenAI-compatible model providers
- Multi-step Agent Loop
- Structured `AgentState`
- Structured `AgentResult`
- Maximum-step termination
- Recoverable Tool errors
- Model error handling
- Context overflow handling

### Tool System

- Unified `Tool` abstraction
- `ToolRegistry`
- JSON Schema argument validation
- Automatic Tool schema generation
- `@tool()` decorator
- Multiple Tool Calls per model step
- Structured Tool results

### Built-in Tools

```text
list_files
read_file
write_file
search_files
run_shell
```

### Context Management

- Approximate UTF-8 byte-based token estimation
- Configurable input context budgets
- Recent-context truncation
- Summary-based context compression
- Complete execution history retained in `AgentState.messages`
- Temporary model-specific context views

### Execution Tracing

- Structured runtime events
- Model call tracing
- Tool Call / Tool Result tracing
- Context budget tracing
- Context policy tracing
- Summary call tracing
- Run lifecycle tracing

---

## Architecture

TinyHarness currently separates the runtime into several independent layers:

```text
                         User
                          │
                          ▼
                        Agent
                          │
          ┌───────────────┼────────────────┐
          │               │                │
          ▼               ▼                ▼
   ModelProvider      ToolRegistry      AgentState
          │               │                │
          ▼         ┌─────┼─────┐          │
         LLM        │     │     │          │
                    ▼     ▼     ▼          │
                  File  Search Shell       │
                    │     │     │          │
                    └─────┼─────┘          │
                          │                │
                          ▼                │
                     Observation           │
                          │                │
                          └──────► Agent ◄─┘
                                   │
                      ┌────────────┴────────────┐
                      │                         │
                      ▼                         ▼
               Context System            ExecutionTrace
                      │
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
    TokenCounter    Budget      Policy
                                /    \
                               /      \
                          Recent      Summary
```

---

## Agent Runtime

The central Agent loop is:

```text
User Request
↓
Build Model Context
↓
Estimate Context Size
↓
Check Context Budget
↓
Apply Context Policy if needed
↓
Call Model
↓
Tool Calls?
├── No  → Final Answer
└── Yes → Execute Tools
          ↓
       Observations
          ↓
       Next Step
```

A single Agent step means:

> One successfully completed Agent model decision.

One model response may contain multiple Tool Calls.

Auxiliary summarization model calls do not count as Agent steps.

---

## Agent State

`AgentState` stores mutable state for a single Agent run.

Conceptually:

```text
AgentState
├── messages
├── steps
├── tool_calls
├── estimated_input_tokens
└── trace
```

`messages` stores the complete execution trajectory.

The complete trajectory is retained even when a Context Policy produces a smaller temporary context for the next model call.

This creates an important distinction:

```text
AgentState.messages
=
complete runtime history

model_messages
=
temporary context view sent to the model
```

---

## Tool System

Tools expose structured capabilities to the model.

Example:

```python
from tinyharness.tools import tool


@tool()
def add(
    a: float,
    b: float,
):
    """Add two numbers."""

    return a + b
```

TinyHarness automatically derives Tool metadata from:

```text
function name
docstring
type annotations
default values
```

The generated Tool is registered through `ToolRegistry`.

Before execution, Tool arguments pass through:

```text
Model Tool Call
↓
JSON parsing
↓
Tool lookup
↓
JSON Schema validation
↓
Tool execution
↓
Structured Tool result
```

Tool failures are returned to the Agent as observations when possible instead of immediately crashing the entire run.

For more details:

```text
docs/02-tool-system.md
```

---

## File Tools

TinyHarness provides structured file operations:

```text
list_files
read_file
write_file
```

File paths are resolved relative to a configured project root.

Structured paths outside the configured project root are rejected.

For example:

```text
../outside.txt
```

cannot be accessed through the structured File Tools.

This boundary is useful for file operations, but it is **not a complete sandbox**.

---

## Search Tool

`search_files` supports repository search by:

```text
name
suffix
content
```

A typical source-inspection trajectory may look like:

```text
search_files
↓
read_file
↓
reason about source code
↓
final answer
```

Search output is structured and can be limited with `max_results`.

---

## Shell Tool

TinyHarness includes a Windows shell Tool.

`run_shell` executes commands using a configured working directory and supports:

- stdout capture
- stderr capture
- return codes
- timeout handling
- configurable working directories
- Windows output decoding fallbacks

Example result:

```python
{
    "command": "...",
    "cwd": "...",
    "returncode": 0,
    "stdout": "...",
    "stderr": "",
    "timed_out": False,
}
```

A non-zero return code is treated as a normal Tool result rather than automatically being treated as a Harness crash.

---

## Context Management

TinyHarness v0.3 introduces a dedicated Context Management layer.

The basic pipeline is:

```text
AgentState.messages
↓
ApproxTokenCounter
↓
ContextBudget
↓
ContextPolicy
↓
model_messages
↓
ModelProvider
```

The Context System controls what part of the complete Agent trajectory is visible to the model on each step.

---

## Approximate Token Counting

`ApproxTokenCounter` provides a lightweight estimate of model input size.

The current heuristic is based on:

```python
math.ceil(
    len(text.encode("utf-8"))
    / bytes_per_token
)
```

The default configuration is:

```text
bytes_per_token = 3.0
```

Structured values such as messages and Tool schemas are serialized to compact JSON before being measured.

This counter is intentionally approximate.

It is:

```text
lightweight
deterministic
dependency-free
```

but it is not:

```text
a model-specific tokenizer
an exact API token count
a guaranteed upper bound
```

Its purpose is pre-call context budgeting.

---

## Context Budget

`ContextBudget` defines an approximate input-token limit.

Example:

```python
ContextBudget(
    max_input_tokens=2000
)
```

Before every Agent model call:

```text
estimate input
↓
check budget
```

If the request fits:

```text
continue
```

If the request exceeds the budget and no Context Policy is configured:

```text
context_overflow
```

The over-budget request is stopped before the Agent model call.

---

## Recent Context Policy

`RecentContextPolicy` removes older execution history until the request fits the configured Context Budget.

It preserves:

- leading system messages
- the initial user request
- the newest interaction blocks that still fit

An assistant Tool Call and its following Tool Results are treated as one interaction block.

For example:

```text
User

Assistant Tool Call
Tool Result

Assistant Tool Call
Tool Result
```

The Policy removes complete old blocks rather than arbitrary individual messages.

This avoids breaking the Tool Calling message structure.

### Trade-off

```text
Advantages
- simple
- cheap
- no additional model calls

Disadvantages
- removed information is completely lost
- aggressive truncation may cause repeated Tool Calls
```

---

## Summary Context Policy

`SummaryContextPolicy` compresses older interaction blocks into semantic summaries.

Conceptually:

```text
old execution blocks
↓
LLMContextSummarizer
↓
summary
+
recent execution blocks
↓
model context
```

The original complete trajectory remains stored in:

```text
AgentState.messages
```

The generated summary is only used inside the temporary model context.

Summary calls:

```text
are real model calls
but
are not Agent decision steps
```

### Trade-off

```text
Advantages
- preserves more semantic information from older history
- can recover from large context growth

Disadvantages
- additional model calls
- additional latency
- additional API cost
- summarization is lossy
```

---

## Execution Trace

TinyHarness v0.3 includes structured execution tracing.

`ExecutionTrace` records what happened during an Agent run without inserting Trace data into the model context.

Typical events include:

```text
run_start
context_estimate
budget_check
context_summary_start
context_summary_end
context_policy
model_call_start
model_response
tool_call
tool_result
final_answer
run_end
```

Example:

```text
run_start
↓
context_estimate
↓
budget_check
↓
model_call_start
↓
model_response
↓
tool_call
↓
tool_result
↓
...
↓
final_answer
↓
run_end
```

Trace events can be queried programmatically:

```python
tool_calls = result.trace.by_type(
    "tool_call"
)

summary_calls = result.trace.by_type(
    "context_summary_start"
)
```

This provides a structured foundation for later debugging, evaluation, and ablation experiments.

---

## Context Experiment

TinyHarness v0.3 includes a small behavioral experiment comparing three Context configurations under the same approximate input budget.

The experiment compares:

```text
A — No Context Policy
B — RecentContextPolicy
C — SummaryContextPolicy
```

The same repository-inspection task, model configuration, Tool set, Context Budget, and maximum step count are used.

One observed run produced:

| Policy | Status | Steps | Tool Calls | Agent Model Calls | Summary Calls | Policy Calls |
|---|---:|---:|---:|---:|---:|---:|
| No Policy | `context_overflow` | 2 | 4 | 2 | 0 | 0 |
| RecentContextPolicy | `max_steps` | 10 | 25 | 10 | 0 | 8 |
| SummaryContextPolicy | `success` | 6 | 13 | 6 | 14 | 4 |

### Observed behavior

In this experiment:

- **No Policy** terminated when the full context exceeded the configured budget.
- **RecentContextPolicy** repeatedly reduced the context below the budget, but the Agent reacquired previously discarded information and eventually reached `max_steps`.
- **SummaryContextPolicy** performed additional summarization model calls, but retained enough execution information for the Agent to complete the task.

An important observation is:

```text
Context management succeeded
≠
Task execution succeeded
```

`RecentContextPolicy` successfully kept the visible context under budget, but the Agent still failed to complete the task within the configured step limit.

These results describe one behavioral experiment only.

They are **not** a general claim that `SummaryContextPolicy` is always better than `RecentContextPolicy`.

LLM execution is non-deterministic, and broader evaluation is planned for later versions.

Run the experiment with:

```bash
python examples/day21_context_experiment.py
```

---

## Project Structure

```text
TinyHarness/
├── tinyharness/
│   ├── agent/
│   │   ├── agent.py
│   │   ├── result.py
│   │   └── state.py
│   │
│   ├── context/
│   │   ├── budget.py
│   │   ├── policy.py
│   │   ├── summarizer.py
│   │   └── token_counter.py
│   │
│   ├── models/
│   │
│   ├── tools/
│   │   ├── tool.py
│   │   ├── registry.py
│   │   ├── decorators.py
│   │   ├── schema.py
│   │   ├── file_tools.py
│   │   ├── search_tools.py
│   │   └── shell_tools.py
│   │
│   └── tracing/
│       ├── __init__.py
│       └── trace.py
│
├── examples/
├── tests/
├── docs/
├── pyproject.toml
├── README.md
└── .gitignore
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Ryan04690/TinyHarness.git
cd TinyHarness
```

Install in editable mode:

```bash
pip install -e .
```

For development and testing:

```bash
pip install -e ".[dev]"
```

---

## Configuration

The current examples use an OpenAI-compatible DeepSeek endpoint.

Create a `.env` file:

```text
.env
```

Add:

```text
DEEPSEEK_API_KEY=your_api_key_here
```

`.env` should never be committed to Git.

---

## Quick Start

```python
import os

from pathlib import Path
from dotenv import load_dotenv

from tinyharness.agent import Agent
from tinyharness.models import (
    OpenAICompatibleProvider,
)
from tinyharness.tools import (
    ToolRegistry,
    create_file_tools,
    create_search_tools,
    create_shell_tools,
)


load_dotenv()

project_root = Path.cwd()

model = OpenAICompatibleProvider(
    model="deepseek-flash",
    api_key=os.getenv(
        "DEEPSEEK_API_KEY"
    ),
    base_url="https://api.deepseek.com",
)

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

agent = Agent(
    model=model,
    tool_registry=registry,
    max_steps=10,
)

result = agent.run(
    "Find the file that defines Agent "
    "and explain Agent.run."
)

print(result)
```

A possible Agent trajectory is:

```text
search_files
↓
read_file
↓
final answer
```

---

## Context-Aware Agent Example

```python
from tinyharness.context import (
    ContextBudget,
    LLMContextSummarizer,
    SummaryContextPolicy,
)


summarizer = LLMContextSummarizer(
    model=model
)

policy = SummaryContextPolicy(
    summarizer=summarizer
)

agent = Agent(
    model=model,
    tool_registry=registry,
    max_steps=10,
    context_budget=ContextBudget(
        max_input_tokens=2000
    ),
    context_policy=policy,
)
```

When the complete trajectory exceeds the configured Context Budget:

```text
Full AgentState.messages
↓
SummaryContextPolicy
↓
Summary + recent context
↓
Budget re-check
↓
Model
```

---

## Testing

Run all tests:

```bash
pytest -v
```

Current v0.3 test coverage includes:

```text
AgentState
AgentResult
Tool schema generation
argument validation
ToolRegistry
File Tools
Search Tools
Shell execution
timeouts
return codes
project-root boundaries
token estimation
ContextBudget
RecentContextPolicy
SummaryContextPolicy
LLMContextSummarizer
ExecutionTrace
```

Current result:

```text
50 passed
```

---

## Development Progress

### v0.1 — Minimal Agent Runtime

```text
LLM API
+
ModelProvider
+
Agent Loop
+
basic Shell interaction
+
structured errors
```

### v0.2 — Tool System

```text
Tool abstraction
+
ToolRegistry
+
argument validation
+
automatic schema generation
+
File / Search / Shell Tools
+
unit tests
```

### v0.3 — State + Context + Trace

```text
AgentState
+
ApproxTokenCounter
+
ContextBudget
+
RecentContextPolicy
+
SummaryContextPolicy
+
LLMContextSummarizer
+
ExecutionTrace
+
Context experiment
```

---

## Roadmap

### v0.4 — Workspace + Security

Planned:

- Workspace concepts
- Workspace abstraction
- `LocalWorkspace`
- Docker basics
- `DockerWorkspace`
- Permission System
- Security tests

### v0.5 — Skills + MCP + Evaluation

Planned:

- Skills
- `SkillLoader`
- Skill experiments
- MCP principles
- MCP Server
- MCP Client
- Agent Evaluation

### v1.0 — Benchmark + Release

Planned:

- Benchmark tasks
- Baseline experiments
- Tool ablation
- Context ablation
- Harness ablation
- Documentation
- Packaging
- Release

---

## Security

TinyHarness v0.3 is intended for local learning and experimentation.

Structured File and Search Tools restrict resolved paths to the configured project root.

However:

```text
File path boundary       ✅
Search path boundary     ✅
Shell cwd restriction    ✅

Shell isolation          ❌
Permission system        ❌
Container isolation      ❌
Full sandbox             ❌
```

`run_shell` executes real commands using the permissions of the current operating-system user.

A project-root `cwd` restriction does **not** prevent a shell command from explicitly accessing paths outside the project root.

Do not run the shell-enabled Agent unattended in environments containing sensitive files or credentials.

A stronger Workspace and Permission layer is planned for v0.4.

---

## Documentation

Current design documents:

```text
docs/02-tool-system.md
docs/03-context-management.md
```

`docs/02-tool-system.md` covers the Tool System.

`docs/03-context-management.md` covers:

```text
Token estimation
Context budgets
RecentContextPolicy
SummaryContextPolicy
ExecutionTrace integration
```

Future documentation will cover:

```text
Workspace
Sandboxing
Permissions
Skills
MCP
Evaluation
```

---

## Philosophy

TinyHarness intentionally avoids hiding important Agent mechanisms behind large abstractions.

The project prefers:

```text
small components
explicit control flow
structured state
observable execution
testable boundaries
```

over:

```text
large opaque orchestration layers
```

The goal is not merely to make an Agent work.

The goal is to understand why it works.

---

## Version

Current version:

```text
v0.3.0
```

TinyHarness v0.3.0 marks the completion of the first:

```text
Agent State
+
Context Management
+
Execution Trace
```

milestone.

The next milestone is:

```text
v0.4 — Workspace + Security
```