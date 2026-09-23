import os
from dotenv import load_dotenv
from tinyharness.models import OpenAICompatibleProvider

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    raise ValueError(
        "DEEPSEEK_API_KEY is not set."
    )

model = OpenAICompatibleProvider(
    model="deepseek-flash",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# tools JSON Schema
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

messages = [
    {
        "role":"user",
        "content":"what is 1 + 2 ?",
    }
]
response = model.generate(messages=messages,tools=tools)
print(response.choices[0].message.tool_calls) # None