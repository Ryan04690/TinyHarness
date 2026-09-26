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
        context_policy=None, # able to choose different policy
    ):
        self.model = model
        self.tool_registry = tool_registry
        self.max_steps = max_steps
        self.token_counter = (
            token_counter          # can switch to the corresponding DeepSeek or OpenAI methods, and so on.
            or ApproxTokenCounter()
        )
        self.context_budget = context_budget
        self.context_policy = context_policy

    def run(self, user_input):
        state = AgentState.from_user_input(
            user_input
        )

        for _ in range(self.max_steps):

            print(
                f"\n--- Step "
                f"{state.steps + 1} ---"
            )

            tool_schemas = (self.tool_registry.schemas())

            model_messages = state.messages # state.messages keeps the completed history

            estimate = (
                self.token_counter.count_request(
                    messages=model_messages,
                    tools=tool_schemas,
                )
            )

            state.set_estimated_input_tokens(estimate.total)

            print(
                "Context estimate: "
                f"{estimate.total} tokens "
                f"(messages={estimate.messages}, "
                f"tools={estimate.tools})"
            )

            if self.context_budget is not None:

                budget_check = (
                    self.context_budget.check(
                        estimate.total
                    )
                )

                print(
                    "Context budget: "
                    f"{budget_check.input_tokens}/"
                    f"{budget_check.max_input_tokens} "
                    f"tokens "
                    f"({budget_check.usage_ratio:.1%})"
                )

                if (
                    not budget_check.within_budget
                    and self.context_policy
                    is not None
                ):
                    original_count = len(model_messages)

                    model_messages = (
                        self.context_policy.apply(
                            messages=state.messages,
                            tools=tool_schemas,
                            token_counter=self.token_counter,
                            context_budget=self.context_budget,
                        )
                    )

                    dropped_count = (
                        original_count
                        - len(model_messages)
                    )

                    print(
                        "Context policy: "
                        f"{original_count} -> "
                        f"{len(model_messages)} messages"
                    )

                    estimate = (
                        self.token_counter.count_request(
                            messages=model_messages,
                            tools=tool_schemas,
                        )
                    )

                    state.set_estimated_input_tokens(estimate.total)

                    budget_check = (
                        self.context_budget.check(
                            estimate.total
                        )
                    )

                    print(
                        "Context after policy: "
                        f"{estimate.total}/"
                        f"{budget_check.max_input_tokens} "
                        f"tokens "
                        f"({budget_check.usage_ratio:.1%})"
                    )

                if not budget_check.within_budget:
                    return AgentResult(
                        status="context_overflow",
                        content=None,
                        steps=state.steps,
                        tool_calls=state.tool_calls,
                        error=(
                            "Context budget exceeded: "
                            f"{budget_check.input_tokens} "
                            f"> "
                            f"{budget_check.max_input_tokens} "
                            "estimated input tokens."
                        ),
                    )

            # ---------------------------------------------
            # 1. Ask the model what to do next
            # ---------------------------------------------
            try:
                response = self.model.generate(
                    messages=model_messages,
                    tools=self.tool_registry.schemas(),
                )

            except Exception as error:
                return AgentResult(
                    status="model_error",
                    content=None,
                    steps=state.steps,
                    tool_calls=state.tool_calls,
                    error=str(error),
                )

            state.record_step()

            message = response.choices[0].message

            # Save assistant message into state
            state.append_message(
                message.model_dump(
                    exclude_none=True
                )
            )

            # ---------------------------------------------
            # 2. No Tool Call means task is finished
            # ---------------------------------------------
            if not message.tool_calls:
                return AgentResult(
                    status="success",
                    content=message.content,
                    steps=state.steps,
                    tool_calls=state.tool_calls,
                )

            # ---------------------------------------------
            # 3. Execute every Tool Call
            # ---------------------------------------------
            for tool_call in message.tool_calls:

                state.record_tool_call()

                tool_name = (
                    tool_call.function.name
                )

                raw_arguments = (
                    tool_call.function.arguments
                )

                # -----------------------------------------
                # 3.1 Parse arguments
                # -----------------------------------------
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
                        f"{tool_name}({tool_args})"
                    )

                    # -------------------------------------
                    # 3.2 Find Tool
                    # -------------------------------------
                    tool = (
                        self.tool_registry.get(
                            tool_name
                        )
                    )

                    if tool is None:
                        result = {
                            "error": "unknown_tool",
                            "message": (
                                f"Tool '{tool_name}' "
                                "not found."
                            ),
                        }

                    else:
                        # ---------------------------------
                        # 3.3 Validate + execute
                        # ---------------------------------
                        try:
                            result = tool.execute(
                                tool_args
                            )

                        except ValidationError as error:
                            result = {
                                "error": (
                                    "invalid_tool_arguments"
                                ),
                                "message": error.message,
                            }

                        except Exception as error:
                            result = {
                                "error": (
                                    "tool_execution_error"
                                ),
                                "message": str(error),
                            }

                print(
                    f"Tool result: {result}"
                )

                # -----------------------------------------
                # 4. Add Tool observation to state
                # -----------------------------------------
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

        return AgentResult(
            status="max_steps",
            content=None,
            steps=state.steps,
            tool_calls=state.tool_calls,
            error=(
                f"Agent exceeded "
                f"max_steps={self.max_steps}."
            ),
        )

# import json

# from jsonschema import ValidationError
# from .state import AgentState
# from .result import AgentResult


# class Agent:
#     def __init__(
#         self,
#         model,
#         tool_registry,
#         max_steps=10,
#     ):
#         self.model = model
#         self.tool_registry = tool_registry
#         self.max_steps = max_steps

#     def run(self, user_input):
#         # messages = [
#         #     {
#         #         "role": "user",
#         #         "content": user_input,
#         #     }
#         # ]

#         # tool_call_count = 0
#         # Take the state maintenance out of the loop and change it to look like this
        
#         state = AgentState.from_user_input(
#             user_input
#             )
        
#         for _ in range(self.max_steps):

#             print(f"\n--- Step {state.steps + 1} ---")

#             # -------------------------------------------------
#             # 1. Ask the model what to do next
#             # -------------------------------------------------
#             try:
#                 response = self.model.generate(
#                     messages=state.messages,
#                     tools=self.tool_registry.schemas(),
#                 )

#             except Exception as error:
#                 return AgentResult(
#                     status="model_error",
#                     content=None,
#                     steps=state.steps,
#                     tool_calls=state.tool_calls,
#                     error=str(error),
#                 )
#             state.record_step()

#             message = response.choices[0].message

#             # Save the assistant message into the trajectory
#             state.append_message(
#                 message.model_dump(
#                     exclude_none=True
#                 )
#             )

#             # -------------------------------------------------
#             # 2. No tool call means the task is finished
#             # -------------------------------------------------
#             if not message.tool_calls:
#                 return AgentResult(
#                     status="success",
#                     content=message.content,
#                     steps=state.steps,
#                     tool_calls=state.tool_calls,
#                 )

#             # -------------------------------------------------
#             # 3. Execute every tool call returned by the model
#             # -------------------------------------------------
#             for tool_call in message.tool_calls:

#                 state.record_tool_call()

#                 tool_name = tool_call.function.name
#                 raw_arguments = (
#                     tool_call.function.arguments
#                 )

#                 # ---------------------------------------------
#                 # 3.1 Parse JSON arguments
#                 # ---------------------------------------------
#                 try:
#                     tool_args = json.loads(
#                         raw_arguments
#                     )

#                     if not isinstance(tool_args, dict):
#                         raise ValueError(
#                             "Tool arguments must be "
#                             "a JSON object."
#                         )

#                 except (
#                     json.JSONDecodeError,
#                     ValueError,
#                 ) as error:
#                     result = {
#                         "error": (
#                             "invalid_tool_arguments"
#                         ),
#                         "message": str(error),
#                     }

#                 else:
#                     print(
#                         f"Tool call: "
#                         f"{tool_name}({tool_args})"
#                     )

#                     # -----------------------------------------
#                     # 3.2 Find the Tool
#                     # -----------------------------------------
#                     tool = self.tool_registry.get(
#                         tool_name
#                     )

#                     if tool is None:
#                         result = {
#                             "error": "unknown_tool",
#                             "message": (
#                                 f"Tool '{tool_name}' "
#                                 "not found."
#                             ),
#                         }

#                     else:
#                         # -------------------------------------
#                         # 3.3 Validate + execute the Tool
#                         # -------------------------------------
#                         try:
#                             result = tool.execute(
#                                 tool_args
#                             )

#                         except ValidationError as error:
#                             result = {
#                                 "error": (
#                                     "invalid_tool_arguments"
#                                 ),
#                                 "message": error.message,
#                             }

#                         except Exception as error:
#                             result = {
#                                 "error": (
#                                     "tool_execution_error"
#                                 ),
#                                 "message": str(error),
#                             }

#                 print(f"Tool result: {result}")

#                 # ---------------------------------------------
#                 # 4. Every tool call must receive a tool result
#                 # ---------------------------------------------
#                 state.append_message(
#                     {
#                         "role": "tool",
#                         "tool_call_id": tool_call.id,
#                         "content": json.dumps(
#                             result,
#                             ensure_ascii=False,
#                             default=str,
#                         ),
#                     }
#                 )

#         # -----------------------------------------------------
#         # 5. Agent did not finish within max_steps
#         # -----------------------------------------------------
#         return AgentResult(
#             status="max_steps",
#             content=None,
#             steps=self.max_steps,
#             tool_calls=state.tool_calls,
#             error=(
#                 f"Agent exceeded "
#                 f"max_steps={self.max_steps}."
#             ),
#         )

# # Return is valid、Can be parsed、The tool exists、Meets the tool schema、Tool executed successfully