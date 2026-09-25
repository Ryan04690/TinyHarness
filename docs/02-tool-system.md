# TinyHarness Tool System

## 1. Overview

TinyHarness uses a structured Tool System to expose executable
capabilities to the language model while keeping actual execution
inside the harness.

The language model itself does not directly execute Python functions,
read files, search source code, or run shell commands.

Instead, the model produces a structured Tool Call containing:

- tool name
- tool arguments

TinyHarness then resolves the requested tool, validates its arguments,
executes it, and sends the result back to the model as an observation.

The current execution flow is:

```text
User
  ↓
Agent
  ↓
Model
  ↓
Tool Call
  ↓
Argument Parsing
  ↓
ToolRegistry
  ↓
Tool Validation
  ↓
Tool Execution
  ↓
Structured Observation
  ↓
Agent
  ↓
Model
```

This design separates model reasoning from environment execution.

The model decides **what action should be taken**, while TinyHarness
controls **how that action is validated and executed**.

---

## 2. Tool Abstraction

The central abstraction of the Tool System is `Tool`.

A Tool contains four core pieces of information:

- `name`
- `description`
- `parameters`
- Python callable

Conceptually:

```text
Tool
├── name
├── description
├── JSON Schema
└── Python function
```

A simplified Tool definition is:

```python
@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    function: Callable
```

The Tool provides two important operations:

```text
schema()
execute(arguments)
```

`schema()` produces the model-facing tool definition.

`execute()` performs runtime validation and invokes the underlying
Python function.

The execution flow is:

```text
arguments
   ↓
validate_arguments()
   ↓
JSON Schema validation
   ↓
function(**arguments)
   ↓
result
```

This means Tool validation cannot accidentally be skipped when tools
are executed through the normal TinyHarness runtime.

---

## 3. Automatic Tool Definition

TinyHarness supports defining tools using the `@tool()` decorator.

Example:

```python
@tool()
def add(
    a: float,
    b: float,
):
    """Add two numbers."""

    return a + b
```

Instead of manually constructing:

```python
Tool(
    name="add",
    description="Add two numbers.",
    parameters={...},
    function=add,
)
```

TinyHarness inspects the Python function and automatically constructs
the Tool.

The decorator extracts:

```text
function.__name__
        ↓
Tool name

function docstring
        ↓
Tool description

function signature
        ↓
parameter names and defaults

type annotations
        ↓
JSON Schema types

original function
        ↓
Tool.function
```

Therefore the Python function becomes the primary source of
information for the Tool definition.

---

## 4. Reflection and Schema Generation

TinyHarness uses Python introspection to inspect Tool functions.

For example:

```python
def greet(
    name: str,
    excited: bool = False,
):
    """Generate a greeting."""
```

`inspect.signature()` exposes the function signature:

```text
(name: str, excited: bool = False)
```

TinyHarness currently maps basic Python types to JSON Schema:

```text
Python        JSON Schema

str      →    string
int      →    integer
float    →    number
bool     →    boolean
```

A parameter without a Python default value is considered required.

For example:

```python
name: str
```

becomes:

```json
{
    "name": {
        "type": "string"
    }
}
```

and is included in:

```json
"required": ["name"]
```

A parameter with a default value:

```python
excited: bool = False
```

becomes:

```json
{
    "excited": {
        "type": "boolean",
        "default": false
    }
}
```

but does not need to appear in `required`.

TinyHarness also generates:

```json
"additionalProperties": false
```

so the model cannot silently pass unexpected arguments.

Unsupported parameter types currently fail immediately during Tool
construction instead of silently generating an incorrect schema.

---

## 5. ToolRegistry

Tools are stored inside `ToolRegistry`.

The registry provides a single place for the Agent to discover and
execute available capabilities.

Current operations include:

```text
register(tool)
get(name)
names()
schemas()
execute(name, arguments)
```

Internally, the registry stores:

```text
tool name
    ↓
Tool object
```

Conceptually:

```text
ToolRegistry
├── list_files   → Tool(...)
├── read_file    → Tool(...)
├── write_file   → Tool(...)
├── search_files → Tool(...)
└── run_shell    → Tool(...)
```

Tool lookup is therefore independent from the Agent itself.

The Agent only needs access to:

```python
self.tool_registry
```

rather than maintaining separate schema lists and Python function
dictionaries.

Duplicate Tool registration is rejected.

For example:

```python
registry.register(add)
registry.register(add)
```

raises an error instead of silently replacing the previous Tool.

This follows a fail-fast design and prevents accidental Tool
configuration conflicts.

---

## 6. Argument Validation

TinyHarness validates Tool arguments before executing the underlying
Python function.

Validation uses JSON Schema through the `jsonschema` package.

For example:

```python
@tool()
def write_file(
    path: str,
    content: str,
    overwrite: bool = False,
):
    ...
```

An invalid call such as:

```json
{
    "path": 123,
    "content": "hello"
}
```

is rejected because `path` must be a string.

TinyHarness currently distinguishes several different failure stages:

```text
Malformed JSON
      ↓
invalid_tool_arguments

Valid JSON but schema mismatch
      ↓
invalid_tool_arguments

Unknown Tool
      ↓
unknown_tool

Tool implementation raises
      ↓
tool_execution_error
```

This distinction is important because:

```text
JSON parsing
≠
schema validation
≠
tool execution
```

A JSON object may be syntactically valid while still violating a Tool
contract.

---

## 7. Semantic Validation

JSON Schema validates structural properties such as:

```text
type
required fields
unexpected fields
```

However, type validation alone cannot enforce every semantic rule.

For example:

```python
search_type: str
```

only guarantees that the value is a string.

It does not guarantee that the value is one of:

```text
name
suffix
content
```

Therefore some Tools perform additional semantic validation inside
their Python implementation.

Example:

```python
valid_search_types = {
    "name",
    "suffix",
    "content",
}

if search_type not in valid_search_types:
    raise ValueError(...)
```

Similarly:

```python
timeout: int
```

requires additional checks such as:

```text
timeout > 0
timeout <= maximum allowed timeout
```

Therefore TinyHarness currently uses two validation layers:

```text
JSON Schema Validation
        ↓
structural correctness

Semantic Validation
        ↓
domain-specific correctness
```

---

## 8. File Tools

TinyHarness currently provides structured file-system capabilities:

```text
list_files
read_file
write_file
```

These Tools operate relative to a project root.

Example:

```python
read_file(
    path="README.md"
)
```

instead of requiring the language model to generate platform-specific
shell commands such as:

```text
type README.md
cat README.md
```

Structured File Tools provide:

```text
stable arguments
structured results
platform-independent semantics
clearer security boundaries
```

File paths are resolved before execution.

TinyHarness verifies that the resolved path remains inside the project
root.

For example:

```text
README.md
```

is allowed.

But:

```text
../outside.txt
```

or an absolute path outside the project root is rejected.

This provides a basic workspace boundary for File Tools.

It is important to note that this is **not a full sandbox**.

---

## 9. Write Safety

`write_file` defaults to:

```python
overwrite=False
```

If the requested file already exists, TinyHarness refuses to replace it
unless the caller explicitly provides:

```python
overwrite=True
```

This follows a safe-default design.

Creating a new file and overwriting an existing file are treated as
different operations because overwriting existing data has greater
potential impact.

---

## 10. Search Tool

TinyHarness provides:

```text
search_files
```

for structured repository search.

Current search modes are:

```text
name
suffix
content
```

### Name Search

Example:

```python
search_files(
    query="agent",
    search_type="name",
)
```

can locate files such as:

```text
tinyharness/agent/agent.py
examples/day04_agent_loop.py
```

### Suffix Search

Example:

```python
search_files(
    query=".py",
    search_type="suffix",
)
```

locates Python files.

### Content Search

Example:

```python
search_files(
    query="class Agent",
    search_type="content",
)
```

returns both matching files and matching lines:

```text
path
line number
matching text
```

A structured content-search result may look like:

```json
{
    "path": "tinyharness/agent/agent.py",
    "matches": [
        {
            "line": 8,
            "text": "class Agent:"
        }
    ]
}
```

Search can be recursive or non-recursive and supports a result limit
through `max_results`.

This prevents very large repositories from producing unlimited Tool
output.

Binary or non-UTF-8 files that cannot be safely decoded as text are
skipped during content search.

---

## 11. Search and Read Workflow

Search and File Tools can be combined by the Agent.

A typical Coding Agent trajectory is:

```text
User:
"Find the file that defines Agent and explain Agent.run."

        ↓

search_files(
    query="class Agent",
    search_type="content"
)

        ↓

Locate:
tinyharness/agent/agent.py

        ↓

read_file(
    path="tinyharness/agent/agent.py"
)

        ↓

Model reads source code

        ↓

Final explanation
```

This demonstrates an important Agent pattern:

```text
Locate
↓
Inspect
↓
Reason
```

The workflow is not hard-coded into the Agent.

The language model decides how to combine the capabilities exposed by
the ToolRegistry.

---

## 12. Robust Shell Tool

TinyHarness also provides a general-purpose Shell capability:

```text
run_shell
```

The current implementation targets Windows CMD commands.

Example:

```python
run_shell(
    command="dir",
    cwd=".",
    timeout=10,
)
```

The Tool executes the command using `subprocess`.

It returns a structured result containing:

```text
command
cwd
returncode
stdout
stderr
timed_out
```

Example:

```json
{
    "command": "dir",
    "cwd": ".",
    "returncode": 0,
    "stdout": "...",
    "stderr": "",
    "timed_out": false
}
```

---

## 13. Shell Output Handling

TinyHarness keeps `stdout` and `stderr` separate.

This is important because they represent different process streams.

A process may:

```text
returncode = 0
stderr != ""
```

for example when a program writes warnings to stderr.

Therefore TinyHarness does not assume:

```text
stderr exists
→ command failed
```

The process return code is retained explicitly.

On Windows, shell output encoding may vary.

TinyHarness captures raw bytes and attempts several decoding strategies
instead of relying only on `text=True`.

The current decoding logic attempts encodings such as:

```text
UTF-8
system preferred encoding
GB18030
```

before falling back to replacement decoding.

---

## 14. Command Failure vs Tool Failure

TinyHarness distinguishes command failure from Tool runtime failure.

For example:

```text
returncode = 3
stderr = "failed"
```

does not mean the Tool System itself crashed.

The Shell Tool executed normally and returned a process result.

Conceptually:

```text
Command Failure
→ structured Tool result

Tool Runtime Failure
→ tool_execution_error
```

This allows the model to inspect failed commands and decide what to do
next.

For example:

```text
Shell command
↓
returncode = 1
↓
Agent observes stderr
↓
Agent tries another command
↓
Agent produces final answer
```

A failed command therefore does not automatically terminate the Agent
Loop.

---

## 15. Shell Timeout

Shell execution supports a timeout.

Example:

```python
run_shell(
    command="...",
    timeout=1,
)
```

If the process does not complete in time, TinyHarness returns a
structured result:

```json
{
    "returncode": null,
    "stdout": "",
    "stderr": "",
    "timed_out": true
}
```

A timeout is treated as an expected operational failure rather than an
unhandled Python exception.

This allows the model to observe the timeout and decide how to recover.

---

## 16. Shell Working Directory

`run_shell` accepts a structured `cwd` argument.

Example:

```python
run_shell(
    command="dir",
    cwd="examples",
)
```

The Tool verifies that `cwd` resolves inside the project root.

For example:

```text
cwd="tinyharness/tools"
```

is allowed.

But:

```text
cwd=".."
```

is rejected.

Separating:

```text
command
```

from:

```text
cwd
```

makes the execution environment easier to inspect and will make future
Workspace abstractions easier to implement.

---

## 17. Current Security Limitations

The current Tool System provides some safety boundaries but is not a
sandbox.

File Tools enforce project-root path restrictions.

Search Tools also operate inside the project root.

The Shell Tool restricts the structured `cwd` argument.

However:

```text
cwd restriction
≠
shell isolation
```

A shell command may still contain operations such as:

```text
cd ..
absolute paths
external programs
network commands
file deletion
```

if the operating-system user has permission.

Therefore the current state is:

```text
File Tool workspace boundary     ✓
Search Tool workspace boundary   ✓
Shell cwd restriction            ✓

Shell filesystem isolation       ✗
Permission System                ✗
Container isolation              ✗
Full Sandbox                     ✗
```

Workspace abstraction, permissions, and sandboxing are planned for a
later TinyHarness stage.

---

## 18. Tool System Architecture

The current Tool System can be summarized as:

```text
                       Agent
                         │
                         ▼
                    ToolRegistry
                         │
          ┌──────────────┼───────────────┐
          │              │               │
          ▼              ▼               ▼
      File Tools     Search Tool      Shell Tool
          │              │               │
          ▼              ▼               ▼
      File System    Repository       subprocess
          │                              │
          │                 ┌────────────┼────────────┐
          │                 │            │            │
          │              stdout       stderr     returncode
          │                                           │
          └──────────── Structured Observation ──────┘
                              │
                              ▼
                            Agent
```

The Tool System exposes both:

```text
Structured Capabilities

list_files
read_file
write_file
search_files
```

and:

```text
General Capability

run_shell
```

Structured tools are more predictable and easier to constrain.

Shell provides broader capabilities but requires stronger future
security controls.

---

## 19. Unit Tests

The Tool System is covered by automated tests using `pytest`.

The current test suite includes:

```text
Tool execution
Tool schema generation
optional/default arguments
argument validation

ToolRegistry registration
ToolRegistry execution
duplicate registration
unknown tools

file read/write
overwrite protection
workspace path boundary

file-name search
content search
invalid search mode

shell success
non-zero return code
timeout
cwd boundary
```

Tests use `pytest` fixtures such as:

```python
tmp_path
```

to create isolated temporary workspaces.

This prevents tests from modifying the real TinyHarness repository.

The current Tool System test suite contains:

```text
18 unit tests
```

All tests pass.

---

## 20. Unit Tests vs Agent Evaluation

TinyHarness distinguishes deterministic unit testing from Agent
evaluation.

Unit tests answer questions such as:

```text
Does Tool validation work?
Does ToolRegistry route correctly?
Does write_file refuse accidental overwrite?
Does search_files return the expected result?
Does run_shell preserve return codes?
```

These tests should be:

```text
fast
cheap
deterministic
repeatable
```

Agent evaluation asks a different question:

```text
Can an LLM successfully use these tools to complete a task?
```

Agent evaluation depends on:

```text
model behavior
prompts
tool selection
multi-step reasoning
API availability
```

and will be handled separately during the Evaluation and Benchmark
stages.

---

## 21. Current Tool Set

TinyHarness v0.2 currently exposes the following core capabilities:

```text
list_files
read_file
write_file
search_files
run_shell
```

Together they provide the minimum repository-interaction capabilities
required for a simple Coding Agent:

```text
Explore
↓
Locate
↓
Inspect
↓
Modify
↓
Execute
```

---

## 22. Design Principles

The current Tool System follows several design principles.

### Structured Actions

Prefer explicit structured tools when an operation has a clear
interface.

For example:

```text
read_file(path)
```

is preferred over forcing the model to generate:

```text
type file
cat file
```

for every file read operation.

### Single Source of Truth

Python function signatures, type annotations, and docstrings are used
to generate Tool metadata where possible.

This reduces duplicated Tool definitions.

### Fail Fast

Invalid Tool definitions, unsupported types, duplicate tools, and
invalid parameters should fail early rather than producing hidden
runtime inconsistencies.

### Safe Defaults

Potentially destructive operations should require explicit intent.

For example:

```text
write_file(..., overwrite=False)
```

is the default.

### Structured Observations

Tools return structured results rather than uncontrolled terminal
output whenever possible.

### Separation of Responsibilities

The language model chooses actions.

The Agent manages the execution loop.

ToolRegistry manages capability lookup.

Tool handles validation and execution.

The environment performs the actual side effect.

---

## 23. Current Limitations

The current Tool System intentionally remains small.

Known limitations include:

```text
Only basic Python types are supported by automatic schema generation.

Parameter semantic descriptions are not automatically generated from
type annotations.

Search uses simple substring matching rather than AST-based symbol
search.

Large Tool outputs are not yet truncated according to context budget.

Shell output is captured after execution rather than streamed live.

Shell commands are not sandboxed.

Sensitive files inside the project root are not protected by a
Permission System yet.

File and Shell Tools still interact directly with the local operating
system rather than a Workspace abstraction.
```

These limitations will be addressed in later TinyHarness stages.

---

## 24. Version

TinyHarness v0.2 represents the completion of the first structured Tool
System.

The progression so far is:

```text
v0.1
LLM
+
Agent Loop
+
basic environment interaction

        ↓

v0.2
Tool abstraction
+
ToolRegistry
+
validation
+
automatic schema
+
File Tools
+
Search Tool
+
Robust Shell
+
unit tests
```

The next development stage will focus on:

```text
Agent State
Context Engineering
Token Budget
Context Compression
Execution Trace
```