import json

from .result import AgentResult


class Agent:
    """
    def __init__(
        self,
        model,
        tools,
        tool_functions,
        max_steps=10,
    ):
    """
    def __init__(
            self,
            model,
            tool_registry,
            max_steps = 10,
    ):
        self.model = model
        self.tool_registry = tool_registry
        # self.tool_functions = tool_functions
        self.max_steps = max_steps

    def run(self, user_input):
        messages = [
            {
                "role": "user",
                "content": user_input,
            }
        ]

        tool_call_count = 0

        for step in range(self.max_steps):

            print(f"\n--- Step {step + 1} ---")

            # 1. Ask the model what to do next
            try:
                response = self.model.generate(
                    messages=messages,
                    tools=self.tool_registry.schemas(),
                )
            except Exception as error:
                return AgentResult(
                    status="model_error",
                    content=None,
                    steps=step,
                    tool_calls=tool_call_count,
                    error=str(error),
                )

            message = response.choices[0].message

            # Save the assistant message into the trajectory
            messages.append(
                message.model_dump(exclude_none=True)
            )

            # 2. No tool call means the model has finished the task
            if not message.tool_calls:
                return AgentResult(
                    status="success",
                    content=message.content,
                    steps=step + 1,
                    tool_calls=tool_call_count,
                )

            # 3. Execute every tool call returned in this step
            for tool_call in message.tool_calls:

                tool_call_count += 1

                tool_name = tool_call.function.name
                raw_arguments = tool_call.function.arguments

                # -------------------------------------------------
                # Parse tool arguments
                # -------------------------------------------------
                try:
                    tool_args = json.loads(raw_arguments)

                    # Tool arguments should be a JSON object
                    if not isinstance(tool_args, dict):
                        raise ValueError(
                            "Tool arguments must be a JSON object."
                        )

                except (json.JSONDecodeError, ValueError) as error:
                    result = {
                        "error": "invalid_tool_arguments",
                        "message": str(error),
                    }

                else:
                    print(
                        f"Tool call: "
                        f"{tool_name}({tool_args})"
                    )

                    # ---------------------------------------------
                    # Find the corresponding Python function
                    # ---------------------------------------------
                    tool = self.tool_registry.get(tool_name)

                    if tool is None:
                        result = {
                            "error": "unknown_tool",
                            "message": (
                                f"Tool '{tool_name}' not found."
                            ),
                        }

                    else:
                        # -----------------------------------------
                        # Execute the tool
                        # -----------------------------------------
                        try:
                            result = tool.execute(tool_args)

                        except Exception as error:
                            result = {
                                "error": "tool_execution_error",
                                "message": str(error),
                            }

                print(f"Tool result: {result}")

                # -------------------------------------------------
                # Every tool call MUST receive one tool response
                # -------------------------------------------------
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            result,
                            ensure_ascii=False,
                            default=str,
                        ),
                    }
                )

        # 4. Agent did not finish within max_steps
        return AgentResult(
            status="max_steps",
            content=None,
            steps=self.max_steps,
            tool_calls=tool_call_count,
            error=(
                f"Agent exceeded "
                f"max_steps={self.max_steps}."
            ),
        )