import os
import json

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY") 

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",
    )

def add(a,b):
    return a + b

def multiply(a,b):
    return a * b    

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
        "role": "user",
        "content": "What is 10 plus 20 multiplied by 3?"
    }
]

response = client.chat.completions.create(
    model="deepseek-flash",
    messages=messages,
    tools=tools,
    stream=False,
    extra_body={
        "thinking": {
            "type":"disabled"
        },
    },
)

message = response.choices[0].message
print(message.tool_calls)

if message.tool_calls:
    messages.append(message)
    tool_args = json.loads(message.tool_calls[0].function.arguments)
    if message.tool_calls[0].function.name == "add":
        result = add(**tool_args)
    elif message.tool_calls[0].function.name == "multiply":
        result = multiply(**tool_args)
    messages.append({
        "role": "tool",
        "tool_call_id": message.tool_calls[0].id,
        "content": str(result)
    })
    second_response = client.chat.completions.create(
    model="deepseek-flash", 
    messages=messages,
    tools=tools,
    stream=False,
    extra_body={
        "thinking": {
            "type":"disabled"
        },
    },
)
    final_message = second_response.choices[0].message
    print(final_message.content)
else:
    print(message.content)