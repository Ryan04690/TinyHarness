import json

from jsonschema import ValidationError

from .result import AgentResult
from .state import AgentState


class Agent:
    def __init__(
        self,
        model,
        tool_registry,
        max_steps=10,
    ):
        self.model = model
        self.tool_registry = tool_registry
        self.max_steps = max_steps

    def run(self, user_input):
        state = AgentState.from_user_input(
            user_input
        )

        for _ in range(self.max_steps):

            print(
                f"\n--- Step "
                f"{state.steps + 1} ---"
            )

            # ---------------------------------------------
            # 1. Ask the model what to do next
            # ---------------------------------------------
            try:
                response = self.model.generate(
                    messages=state.messages,
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