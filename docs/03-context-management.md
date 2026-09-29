# Context Management

TinyHarness provides a small context-management layer for
controlling the amount of execution history sent to the model.

## Architecture

The context pipeline is:

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

`AgentState.messages` remains the full execution trajectory.

`model_messages` is only the current view presented to the model.
Context policies never replace the full trajectory stored by
`AgentState`.

## Token Estimation

`ApproxTokenCounter` estimates request size using UTF-8 byte length.

It is intentionally lightweight and deterministic.

The estimate is only a budgeting heuristic. It is not the exact
token count produced by the model provider's tokenizer.

## Context Budget

`ContextBudget` checks whether the estimated request size exceeds
a configured input-token limit.

If no context policy is configured, an over-budget request ends
with:

`context_overflow`

before the model API is called.

## Recent Context Policy

`RecentContextPolicy` preserves:

- leading system messages,
- the initial user request,
- the newest interaction blocks that fit the budget.

An assistant Tool Call and its following Tool Results are treated
as one interaction block so the model protocol is not broken.

The oldest complete blocks are removed first.

## Summary Context Policy

`SummaryContextPolicy` compresses older interaction blocks into a
short semantic summary.

The summary is inserted into the temporary model context while
the complete execution history remains unchanged in
`AgentState.messages`.

Summary generation is an auxiliary model call and does not count
as an Agent step.

Because summarization itself requires model calls, summary-based
context management trades additional compute, latency, and cost
for better preservation of earlier semantic information.

## Execution Trace

Context behavior is recorded through `ExecutionTrace`.

Important events include:

- `context_estimate`
- `budget_check`
- `context_summary_start`
- `context_summary_end`
- `context_policy`

This makes context compression observable without depending on
terminal output.

## Current Limitations

The current token counter is approximate rather than
model-specific.

Summary generation may require multiple model calls while the
policy searches for a context representation that fits the
budget.

Summary compression is lossy and can cause an agent to repeat
tool calls when detailed evidence is no longer present in the
visible context.

The current implementation is intentionally minimal and serves
as a baseline for later context-management experiments.