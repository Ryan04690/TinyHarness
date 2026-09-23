import json

class Agent:
    def __init__(
            self,
            model,
            tools,
            tool_functions,
            max_steps=10,
    ):
        self.model = model
        self.tools = tools
        self.tool_functions = tool_functions
        self.max_steps = max_steps

    def run(self,user_input):
        messages = [
            {
                "role": "user",
                "content": user_input
            }
        ]
        for step in range(self.max_steps):

            print(f"\n--- Step {step + 1} ---")

            response = self.model.generate(messages=messages, tools=self.tools)

            message = response.choices[0].message
            messages.append(message.model_dump(exclude_none=True))

            if not message.tool_calls:
                return message.content


            for tool_call in message.tool_calls:

                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                tool_function = self.tool_functions.get(tool_name)

                if tool_function is None:
                    result = f"Error: Tool '{tool_name}' not found." #这里不要直接raise异常，直接返回错误信息给模型
                else:
                    print(f"Tool call: {tool_name}({tool_args})")

                    result = tool_function(**tool_args)

                    print(f"Tool result: {result}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result),
                    })
        raise Exception("Max steps exceeded without reaching a final answer.")

