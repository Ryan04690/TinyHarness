import json

from jsonschema import ValidationError

from .result import AgentResult
from .state import AgentState

from tinyharness.context import ApproxTokenCounter


class Agent:
    def __init__(
        self,
        model,
        tool_registry,
        max_steps=10,
        token_counter=None,
        context_budget=None,
        context_policy=None,  # able to choose different policy
    ):
        self.model = model
        self.tool_registry = tool_registry
        self.max_steps = max_steps

        self.token_counter = (
            token_counter
            # can switch to the corresponding
            # DeepSeek or OpenAI methods, and so on.
            or ApproxTokenCounter()
        )

        self.context_budget = context_budget
        self.context_policy = context_policy

    # -----------------------------------------------------
    # Private method, convenient for recording
    # some values when return
    # -----------------------------------------------------
    def _finish(
        self,
        state,
        status,
        content=None,
        error=None,
    ):
        state.trace.record(
            "run_end",
            step=state.steps,
            status=status,
            steps=state.steps,
            tool_calls=state.tool_calls,
            error=error,
        )

        return AgentResult(
            status=status,
            content=content,
            steps=state.steps,
            tool_calls=state.tool_calls,
            error=error,
            trace=state.trace,
        )

    def run(self, user_input):
        # -------------------------------------------------
        # Create per-run AgentState
        # -------------------------------------------------
        state = AgentState.from_user_input(
            user_input
        )

        state.trace.record(
            "run_start",
            step=0,
            user_input=user_input,
        )

        for _ in range(self.max_steps):
            current_step = state.steps + 1

            print(
                f"\n--- Step {current_step} ---"
            )

            # -------------------------------------------------
            # Build the model input
            # -------------------------------------------------
            tool_schemas = (
                self.tool_registry.schemas()
            )

            # state.messages keeps the complete history.
            #
            # model_messages is the context view that will
            # actually be sent to the model. A context policy
            # may later replace it with a compressed view.
            model_messages = state.messages

            # -------------------------------------------------
            # Estimate current context size
            # -------------------------------------------------
            estimate = (
                self.token_counter.count_request(
                    messages=model_messages,
                    tools=tool_schemas,
                )
            )

            state.trace.record(
                "context_estimate",
                step=current_step,
                messages_tokens=(
                    estimate.messages
                ),
                tools_tokens=(
                    estimate.tools
                ),
                total_tokens=(
                    estimate.total
                ),
                message_count=len(
                    model_messages
                ),
            )

            state.set_estimated_input_tokens(
                estimate.total
            )

            print(
                "Context estimate: "
                f"{estimate.total} tokens "
                f"(messages={estimate.messages}, "
                f"tools={estimate.tools})"
            )

            # -------------------------------------------------
            # Check context budget
            # -------------------------------------------------
            if self.context_budget is not None:
                budget_check = (
                    self.context_budget.check(
                        estimate.total
                    )
                )

                state.trace.record(
                    "budget_check",
                    step=current_step,
                    input_tokens=(
                        budget_check.input_tokens
                    ),
                    max_input_tokens=(
                        budget_check.max_input_tokens
                    ),
                    remaining_tokens=(
                        budget_check.remaining_tokens
                    ),
                    usage_ratio=(
                        budget_check.usage_ratio
                    ),
                    within_budget=(
                        budget_check.within_budget
                    ),
                )

                print(
                    "Context budget: "
                    f"{budget_check.input_tokens}/"
                    f"{budget_check.max_input_tokens} "
                    "tokens "
                    f"({budget_check.usage_ratio:.1%})"
                )

                # ---------------------------------------------
                # If context is too large, try Context Policy
                # ---------------------------------------------
                if (
                    not budget_check.within_budget
                    and self.context_policy
                    is not None
                ):
                    original_count = len(
                        model_messages
                    )

                    before_tokens = (
                        estimate.total
                    )

                    model_messages = (
                        self.context_policy.apply(
                            messages=state.messages,
                            tools=tool_schemas,
                            token_counter=(
                                self.token_counter
                            ),
                            context_budget=(
                                self.context_budget
                            ),
                            trace=state.trace,
                            step=current_step,
                        )
                    )

                    # Re-count AFTER the policy has changed
                    # the model context view.
                    estimate = (
                        self.token_counter.count_request(
                            messages=model_messages,
                            tools=tool_schemas,
                        )
                    )

                    state.set_estimated_input_tokens(
                        estimate.total
                    )

                    budget_check = (
                        self.context_budget.check(
                            estimate.total
                        )
                    )

                    state.trace.record(
                        "context_policy",
                        step=current_step,
                        policy=(
                            type(
                                self.context_policy
                            ).__name__
                        ),
                        before_messages=(
                            original_count
                        ),
                        after_messages=(
                            len(model_messages)
                        ),
                        before_tokens=(
                            before_tokens
                        ),
                        after_tokens=(
                            estimate.total
                        ),
                    )

                    print(
                        "Context policy: "
                        f"{original_count} -> "
                        f"{len(model_messages)} "
                        "messages"
                    )

                    print(
                        "Context after policy: "
                        f"{estimate.total}/"
                        f"{budget_check.max_input_tokens} "
                        "tokens "
                        f"({budget_check.usage_ratio:.1%})"
                    )

                # ---------------------------------------------
                # Still too large after Context Policy
                # ---------------------------------------------
                if not budget_check.within_budget:
                    return self._finish(
                        state,
                        status="context_overflow",
                        error=(
                            "Context budget exceeded: "
                            f"{budget_check.input_tokens} "
                            "> "
                            f"{budget_check.max_input_tokens} "
                            "estimated input tokens."
                        ),
                    )

            # -------------------------------------------------
            # 1. Ask the model what to do next
            # -------------------------------------------------
            state.trace.record(
                "model_call_start",
                step=current_step,
                message_count=len(
                    model_messages
                ),
                tool_schema_count=len(
                    tool_schemas
                ),
            )

            try:
                response = self.model.generate(
                    messages=model_messages,
                    tools=tool_schemas,
                )

            except Exception as error:
                state.trace.record(
                    "model_error",
                    step=current_step,
                    error=str(error),
                )

                return self._finish(
                    state,
                    status="model_error",
                    error=str(error),
                )

            # A step means one successfully completed
            # Agent model decision.
            state.record_step()

            message = (
                response.choices[0].message
            )

            state.trace.record(
                "model_response",
                step=current_step,
                has_tool_calls=bool(
                    message.tool_calls
                ),
                tool_call_count=(
                    len(message.tool_calls)
                    if message.tool_calls
                    else 0
                ),
                content=message.content,
            )

            # Save assistant message into state.
            #
            # AgentState keeps the complete execution
            # trajectory even if model_messages was
            # compressed by a Context Policy.
            state.append_message(
                message.model_dump(
                    exclude_none=True
                )
            )

            # -------------------------------------------------
            # 2. No Tool Call means task is finished
            # -------------------------------------------------
            if not message.tool_calls:
                state.trace.record(
                    "final_answer",
                    step=current_step,
                    content=message.content,
                )

                return self._finish(
                    state,
                    status="success",
                    content=message.content,
                )

            # -------------------------------------------------
            # 3. Execute every Tool Call
            # -------------------------------------------------
            for tool_call in message.tool_calls:
                state.record_tool_call()

                tool_name = (
                    tool_call.function.name
                )

                raw_arguments = (
                    tool_call.function.arguments
                )

                # Record the model's raw Tool Call before
                # parsing it. This is useful even when the
                # arguments are invalid JSON.
                state.trace.record(
                    "tool_call",
                    step=current_step,
                    tool_call_id=(
                        tool_call.id
                    ),
                    tool_name=tool_name,
                    raw_arguments=(
                        raw_arguments
                    ),
                )

                # ---------------------------------------------
                # 3.1 Parse JSON arguments
                # ---------------------------------------------
                try:
                    tool_args = json.loads(
                        raw_arguments
                    )

                    if not isinstance(
                        tool_args,
                        dict,
                    ):
                        raise ValueError(
                            "Tool arguments must be "
                            "a JSON object."
                        )

                except (
                    json.JSONDecodeError,
                    ValueError,
                ) as error:
                    result = {
                        "error": (
                            "invalid_tool_arguments"
                        ),
                        "message": str(error),
                    }

                else:
                    print(
                        f"Tool call: "
                        f"{tool_name}"
                        f"({tool_args})"
                    )

                    # -----------------------------------------
                    # 3.2 Find Tool
                    # -----------------------------------------
                    tool = (
                        self.tool_registry.get(
                            tool_name
                        )
                    )

                    if tool is None:
                        result = {
                            "error": (
                                "unknown_tool"
                            ),
                            "message": (
                                f"Tool '{tool_name}' "
                                "not found."
                            ),
                        }

                    else:
                        # -------------------------------------
                        # 3.3 Validate + execute Tool
                        # -------------------------------------
                        try:
                            result = (
                                tool.execute(
                                    tool_args
                                )
                            )

                        except (
                            ValidationError
                        ) as error:
                            result = {
                                "error": (
                                    "invalid_tool_arguments"
                                ),
                                "message": (
                                    error.message
                                ),
                            }

                        except Exception as error:
                            result = {
                                "error": (
                                    "tool_execution_error"
                                ),
                                "message": str(
                                    error
                                ),
                            }

                print(
                    f"Tool result: {result}"
                )

                state.trace.record(
                    "tool_result",
                    step=current_step,
                    tool_call_id=(
                        tool_call.id
                    ),
                    tool_name=tool_name,
                    result=result,
                )

                # ---------------------------------------------
                # 4. Add Tool observation to state
                # ---------------------------------------------
                #
                # Every Tool Call must receive a Tool result,
                # including:
                #
                # - invalid JSON
                # - invalid schema
                # - unknown tool
                # - tool execution error
                # - successful execution
                #
                state.append_message(
                    {
                        "role": "tool",
                        "tool_call_id": (
                            tool_call.id
                        ),
                        "content": json.dumps(
                            result,
                            ensure_ascii=False,
                            default=str,
                        ),
                    }
                )

        # -----------------------------------------------------
        # 5. Agent did not finish within max_steps
        # -----------------------------------------------------
        return self._finish(
            state,
            status="max_steps",
            error=(
                f"Agent exceeded "
                f"max_steps={self.max_steps}."
            ),
        )


# Tool execution pipeline:
#
# Model Return
#     ↓
# Can be parsed
#     ↓
# The tool exists
#     ↓
# Meets the tool schema
#     ↓
# Tool executed successfully