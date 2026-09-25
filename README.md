# TinyHarness

TinyHarness is a minimal agent harness built from scratch for learning,
experimentation, and understanding how tool-using LLM agents work internally.

Instead of relying on large agent frameworks, TinyHarness implements the
core runtime step by step:

```text
LLM
↓
Agent Loop
↓
Tool Call
↓
Tool Execution
↓
Observation
↓
LLM
```

The project is intentionally small and hackable so that every component can
be understood, modified, and tested independently.

---

## Why TinyHarness?

Modern agent frameworks often hide important runtime mechanisms behind large
abstractions.

TinyHarness takes the opposite approach:

> Build the smallest working agent runtime first, understand every component,
> then gradually add more advanced capabilities.

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
Refactor
```

---

## Current Features

TinyHarness v0.2 currently supports:

- OpenAI-compatible model providers
- Multi-step Agent Loop
- Structured Tool Calling
- Unified `Tool` abstraction
- `ToolRegistry`
- JSON Schema argument validation
- Automatic Tool schema generation with `@tool()`
- Structured File Tools
- Repository search
- Robust Windows shell execution
- Recoverable Tool errors
- Structured `AgentResult`
- Automated tests with `pytest`

Current built-in capabilities:

```text
list_files
read_file
write_file
search_files
run_shell
```

Current test status:

```text
18 passed
```

---

## Architecture

```text
                     User
                      │
                      ▼
                    Agent
                      │
              ┌───────┴───────┐
              │               │
              ▼               ▼
       ModelProvider      ToolRegistry
              │               │
              ▼        ┌──────┼───────┐
             LLM       │      │       │
                       ▼      ▼       ▼
                     File   Search   Shell
                       │      │       │
                       └──────┼───────┘
                              │
                              ▼
                         Observation
                              │
                              └──────► Agent
```

A typical Agent trajectory:

```text
User
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

The generated Tool is registered through `ToolRegistry` and validated before
execution.

For the complete Tool System design, see:

```text
docs/02-tool-system.md
```

---

## Project Structure

```text
TinyHarness/
├── tinyharness/
│   ├── agent/
│   ├── models/
│   └── tools/
├── examples/
├── tests/
├── docs/
├── pyproject.toml
├── README.md
└── .gitignore
```

Current Tool modules include:

```text
tool.py
registry.py
decorators.py
schema.py
file_tools.py
search_tools.py
shell_tools.py
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

Create:

```text
.env
```

and add:

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
from tinyharness.models import OpenAICompatibleProvider
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
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

registry = ToolRegistry()

for tool in create_file_tools(project_root):
    registry.register(tool)

for tool in create_search_tools(project_root):
    registry.register(tool)

for tool in create_shell_tools(project_root):
    registry.register(tool)

agent = Agent(
    model=model,
    tool_registry=registry,
    max_steps=10,
)

result = agent.run(
    "Find the file that defines Agent and explain Agent.run."
)

print(result)
```

The Agent may autonomously execute:

```text
search_files
↓
read_file
↓
final answer
```

---

## Testing

Run all tests:

```bash
pytest -v
```

Current v0.2 test coverage includes:

```text
Tool schema generation
argument validation
ToolRegistry
File Tools
Search Tool
Shell execution
timeouts
return codes
workspace boundaries
```

Current result:

```text
18 passed
```

---

## Development Progress

```text
v0.1
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

```text
v0.2
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

Next milestone:

```text
v0.3
Agent State
+
Context Engineering
+
Execution Trace
```

---

## Roadmap

### v0.3 — Context + Trace

- Agent State
- Token counting
- Context budget
- Context truncation
- Context summarization
- Execution Trace

### v0.4 — Workspace + Security

- Workspace abstraction
- LocalWorkspace
- DockerWorkspace
- Permission system
- Sandbox

### v0.5 — Skills + MCP + Evaluation

- Skills
- MCP Client / Server
- Agent evaluation

### v1.0 — Benchmark + Release

- Benchmark tasks
- Tool / Context / Skill ablations
- Documentation
- Packaging
- Release

---

## Security

TinyHarness v0.2 is intended for local learning and experimentation.

File and Search Tools restrict structured paths to the configured project
root.

However, `run_shell` executes real Windows CMD commands using the permissions
of the current operating-system user.

The current system does **not** provide a real sandbox.

```text
File path boundary       ✅
Search path boundary     ✅
Shell cwd restriction    ✅

Shell isolation          ❌
Permission system        ❌
Container isolation      ❌
Full sandbox             ❌
```

Do not run the shell-enabled Agent unattended in environments containing
sensitive files or credentials.

---

## Documentation

Detailed design notes:

```text
docs/02-tool-system.md
```

Future documentation will cover Context Engineering, Workspace/Sandbox,
Skills, MCP, and Evaluation.

---

## Version

Current version:

```text
v0.2.0
```

TinyHarness v0.2.0 represents the completion of the first structured Tool
System.

The next milestone is:

```text
v0.3 — Context Engineering + Execution Trace
```