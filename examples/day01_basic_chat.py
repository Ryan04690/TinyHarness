import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY") # 无状态的api 后面可以注意一下历史信息

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",
    )

messages = [
    {
        "role": "system",
        "content": "You are a helpful AI assistant."
    },
    {
        "role": "user",
        "content": "My favorite color is blue.",
    },
]

response = client.chat.completions.create(
    model="deepseek-flash",
    messages=messages,
    stream=False,
    extra_body={
        "thinking": {
            "type":"disabled"
        },
    },
)

print(response.choices[0].message.content)
# print(response)

messages.append({
    "role": "assistant", 
    "content": response.choices[0].message.content
    }
    )

messages.append({
        "role": "user",
        "content": "What is my favorite color?"
    }
)
response = client.chat.completions.create(
    model="deepseek-flash", 
    messages=messages,
    stream=False,
    extra_body={
        "thinking": {
            "type":"disabled"
        },
    },
)

print(response.choices[0].message.content)

