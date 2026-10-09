# Workspace Concepts

## 1. Motivation

TinyHarness v0.3 provides File, Search, and Shell Tools that operate directly on the local operating system.

The v0.4 milestone introduces a Workspace abstraction to separate tools from their execution environments.

The intended architecture is:

```text
Agent
  |
ToolRegistry
  |
Tools
  |
Workspace
  |
  +-- LocalWorkspace
  |
  +-- DockerWorkspace
```

## 2. Project Root

The project root is a directory used as the reference point for structured file paths and command execution.

File and Search Tools currently restrict structured paths to the configured project root.

However, a project root is not a complete security boundary.

## 3. Current Working Directory

The `cwd` parameter of `subprocess.run()` determines where a child process starts.

Example:

```python
subprocess.run(
    command,
    shell=True,
    cwd=project_root,
)
```

The command may still navigate to other directories or access absolute paths.

Therefore:

```text
cwd restriction != filesystem isolation
```

## 4. Workspace

A Workspace is an abstraction representing the execution environment available to an Agent.

It may expose capabilities such as:

- File listing
- File reading
- File writing
- Command execution
- Working-directory management

The Workspace interface allows tools to operate without directly depending on environment-specific implementation details.

## 5. LocalWorkspace

LocalWorkspace executes operations on the host operating system.

It provides a unified execution interface but does not create a sandbox by itself.

## 6. DockerWorkspace

DockerWorkspace will execute supported operations inside a Docker container.

This can provide stronger isolation than direct host execution.

The security guarantees depend on container configuration, privileges, mounted directories, and other controls.

## 7. Workspace vs Permission vs Sandbox

Workspace defines the execution capabilities and environment.

Permission Policy determines which operations the Agent is allowed to request.

Sandbox provides lower-level isolation that restricts the possible effects of executed operations.

These concepts are related but not interchangeable.

## 8. Day 22 Experiment

The experiment is implemented in:

`examples/day22_workspace_concepts.py`

It checks three behaviors:

1. Running a command from the configured project root.
2. Rejecting an invalid structured `cwd` argument.
3. Demonstrating that a CMD command can change directories even when its starting `cwd` is valid.

The experiment demonstrates that a validated working directory does not provide full filesystem isolation.

## 9. Current Limitations

TinyHarness v0.3 does not yet provide:

- A unified Workspace abstraction
- Container-based execution isolation
- A central Permission Policy
- A full sandbox

These capabilities are planned for later development in the v0.4 milestone.

## 10. Next Step

Day 23 will introduce the Workspace interface.

Day 24 will implement LocalWorkspace.

Day 26 will introduce DockerWorkspace.

Day 27 will focus on the Permission System.