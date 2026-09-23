import os
from dotenv import load_dotenv
from openai import OpenAI
from tinyharness.models import OpenAICompatibleProvider
from tinyharness.agent import Agent

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    raise ValueError(
        "DEEPSEEK_API_KEY is not set."
    )

def add(a,b):
    return a + b

def multiply(a,b):
    return a * b

tool_functions = {
    "add": add,
    "multiply": multiply,
}

tools = [
    {
        "type": "function",
        "function":{
            "name": "add",
            "description": "Add two numbers together.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "The first number to add."
                    },
                    "b": {
                        "type": "number",
                        "description": "The second number to add."
                    }
                },
                "required": ["a", "b"]
            }
        }
    },
    {
        "type": "function",
        "function":{
            "name": "multiply",
            "description": "Multiply two numbers together.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "The first number to multiply."
                    },
                    "b": {
                        "type": "number",
                        "description": "The second number to multiply."
                    }
                },
                "required": ["a", "b"]
            }
        }
    }
]

model = OpenAICompatibleProvider(
    model="deepseek-flash",
    api_key=api_key,
    base_url="https://api.deepseek.com",
)

agent = Agent(
    model=model,
    tools=tools,
    tool_functions=tool_functions,
    max_steps=10,
)

result = agent.run("What is 10 plus 20 multiplied by 3? ")
print(result)