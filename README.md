# TinyHarness

TinyHarness is a minimal agent harness built from scratch for learning, experimentation, and understanding how modern tool-using AI agents work internally.

Instead of relying on high-level agent frameworks, TinyHarness implements the core components step by step, including model abstraction, tool calling, agent loops, environment interaction, error handling, and structured execution results.

The project is intentionally small and hackable so that each part of the agent runtime can be understood, modified, and experimented with independently.

---

## Why TinyHarness?

Modern agent frameworks often hide important implementation details behind large abstractions.

TinyHarness takes the opposite approach:

> Build the smallest working agent runtime first, understand every component, and then gradually add more advanced capabilities.

The goal is not to compete with mature frameworks such as OpenHands or SWE-agent, but to provide a lightweight environment for learning and experimenting with the fundamental mechanisms behind them.

---

## Current Features

TinyHarness currently supports:

* OpenAI-compatible model providers
* Multi-step agent execution
* Function / tool calling
* Multiple tool calls in a single model step
* Dynamic Python tool dispatch
* Shell command execution
* Real environment interaction through `subprocess`
* Tool execution timeout
* Windows shell output decoding
* Recoverable tool errors
* Model error handling
* Maximum agent step limits
* Structured `AgentResult`
* Step and tool-call counting

The current version represents the first minimal working agent runtime.

---

## Architecture

The core execution flow is:

```text
User
 │
 ▼
Agent.run()
 │
 ▼
State / Messages
 │
 ▼
ModelProvider
 │
 ▼
LLM
 │
 ├──────────── No tool call ────────────┐
 │                                       │
 ▼                                       ▼
Tool Call                           Final Answer
 │                                       │
 ▼                                       │
Argument Parsing                         │
 │                                       │
 ▼                                       │
Tool Lookup                              │
 │                                       │
 ▼                                       │
Tool Execution                           │
 │                                       │
 ▼                                       │
Environment                              │
 │                                       │
 ▼                                       │
Observation                              │
 │                                       │
 ▼                                       │
Append to Messages                       │
 │                                       │
 └──────────── Next Agent Step ──────────┘
                     │
                     ▼
                AgentResult
```

A simplified view of the system is:

```text
                 ┌─────────────────┐
                 │      User       │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │      Agent      │
                 │                 │
                 │  Loop + State   │
                 └───────┬─────────┘
                         │
               ┌─────────┴──────────┐
               │                    │
               ▼                    ▼
      ┌─────────────────┐    ┌───────────────┐
      │  ModelProvider  │    │     Tools     │
      └────────┬────────┘    └───────┬───────┘
               │                     │
               ▼                     ▼
             LLM                Environment
                                      │
                                      ▼
                                Observation
                                      │
                                      └──────► Agent
```

---

## Core Concepts

### Model Provider

`ModelProvider` defines the interface used by the Agent to communicate with language models.

```python
class ModelProvider(ABC):

    @abstractmethod
    def generate(self, messages, tools=None):
        pass
```

`OpenAICompatibleProvider` implements this interface for OpenAI-compatible APIs.

The Agent therefore does not need to know about API keys, base URLs, or a specific model SDK.

```text
Agent
  │
  ▼
ModelProvider
  │
  ├── DeepSeek
  ├── OpenAI-compatible services
  └── Future local models
```

---

### Agent Loop

The Agent repeatedly asks the model what to do next.

```text
Model
  ↓
Action / Tool Call
  ↓
Tool Execution
  ↓
Observation
  ↓
Model
```

The loop terminates when:

* the model returns a final answer without additional tool calls;
* the maximum number of steps is reached; or
* a fatal model error occurs.

---

### Tools

The model does not execute Python functions directly.

Instead, the model produces a structured tool call containing:

```text
tool name
+
arguments
```

TinyHarness maps the tool name to an actual Python callable:

```python
tool_functions = {
    "run_shell": run_shell,
}
```

The Harness then executes the function and sends its result back to the model as an observation.

---

### Agent State

The current implementation uses the message history as the execution state.

A typical trajectory looks like:

```text
USER
  ↓
ASSISTANT tool call
  ↓
TOOL observation
  ↓
ASSISTANT tool call
  ↓
TOOL observation
  ↓
ASSISTANT final answer
```

Dedicated state and context-management abstractions are planned for later versions.

---

### Error Handling

TinyHarness distinguishes between recoverable execution errors and fatal agent errors.

Recoverable errors include:

```text
invalid tool arguments
unknown tools
tool execution errors
```

These errors are converted into observations and returned to the model so that it can decide how to recover.

Fatal model errors terminate the current agent run.

The final execution state is represented using `AgentResult`.

```python
@dataclass
class AgentResult:
    status: str
    content: str | None
    steps: int
    tool_calls: int
    error: str | None = None
```

Example:

```text
AgentResult(
    status="success",
    content="Task completed.",
    steps=3,
    tool_calls=2,
    error=None
)
```

---

## Project Structure

```text
TinyHarness/
│
├── tinyharness/
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── openai_compatible.py
│   │
│   └── agent/
│       ├── __init__.py
│       ├── agent.py
│       └── result.py
│
├── examples/
│   ├── day01_basic_chat.py
│   ├── day02_tool_calling.py
│   ├── day03_model_provider.py
│   ├── day04_agent_loop.py
│   ├── day05_shell_tool.py
│   └── day06_error_handling.py
│
├── pyproject.toml
├── README.md
├── .gitignore
└── .env
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Ryan04690/TinyHarness.git
cd TinyHarness
```

Create and activate a Python environment, then install the project in editable mode:

```bash
pip install -e .
```

Editable installation allows changes inside the `tinyharness/` package to take effect immediately during development.

---

## Configuration

The current examples use an OpenAI-compatible DeepSeek endpoint.

Create a `.env` file in the project root:

```text
DEEPSEEK_API_KEY=your_api_key_here
```

The `.env` file should never be committed to Git.

---

## Quick Start

Create a model provider:

```python
import os

from dotenv import load_dotenv

from tinyharness.models import OpenAICompatibleProvider

load_dotenv()

model = OpenAICompatibleProvider(
    model="deepseek-flash",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
```

Create an Agent:

```python
from tinyharness.agent import Agent

agent = Agent(
    model=model,
    tools=tools,
    tool_functions=tool_functions,
    max_steps=10,
)
```

Run a task:

```python
result = agent.run(
    "Find all Python files in this project and explain what they do."
)

print(result)
```

A successful run may return:

```text
AgentResult(
    status='success',
    steps=5,
    tool_calls=12,
    content='...',
    error=None
)
```

---

## Learning Progress

The project is being developed incrementally.

| Stage | Topic          | Result                             |
| ----- | -------------- | ---------------------------------- |
| Day 1 | Basic LLM API  | Stateless chat and message history |
| Day 2 | Tool Calling   | Function calling and tool results  |
| Day 3 | Model Provider | Model abstraction                  |
| Day 4 | Agent Loop     | Multi-step autonomous execution    |
| Day 5 | Shell Tool     | Real environment interaction       |
| Day 6 | Error Handling | Structured execution results       |
| Day 7 | v0.1 Review    | First minimal TinyHarness runtime  |

---

## Roadmap

TinyHarness will gradually add:

* Unified Tool abstraction
* Tool Registry
* Argument validation
* Context management
* Agent state abstraction
* Execution tracing
* Token and cost tracking
* Workspace abstraction
* File-system boundaries
* Permission system
* Sandboxed execution
* Skills
* MCP integration
* Agent evaluation
* Benchmarks

The long-term goal is to build a small but complete agent harness while keeping each component easy to inspect and modify.

---

## Security

The current shell tool is intentionally simple and is intended for local experimentation only.

It can execute real shell commands using the permissions of the current operating-system user.

The current `cwd` setting defines the initial working directory but **does not provide filesystem isolation**.

For example, a shell command may still access files outside the project directory if the operating-system user has permission.

Similarly, `.gitignore` prevents files such as `.env` from being committed to Git, but it does not prevent an Agent from reading those files.

Future versions will introduce workspace restrictions, permissions, and sandboxing.

Do not run the current shell-enabled Agent unattended in an environment containing sensitive files or credentials.

---

## Version

Current development version:

```text
v0.1.0
```

TinyHarness v0.1.0 represents the first minimal tool-using agent runtime.

It includes model abstraction, a multi-step Agent Loop, tool execution, shell environment interaction, structured termination, and basic error handling.
