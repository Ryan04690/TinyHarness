"""
the same as day05
aiming to test the AgentResult
"""

import subprocess
import locale
import os

from dotenv import load_dotenv
from pathlib import Path
from tinyharness.agent import Agent
from tinyharness.models import OpenAICompatibleProvider

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("DEEPSEEK_API_KEY is not set.")

project_root = Path.cwd() # This will need to be replaced with Workspace later

def decode_output(data): # fix the issue where subprocess.run returns stdout and stderr as bytes on Windows
    if not data:
        return ""

    encodings = [
        "utf-8",
        locale.getpreferredencoding(False),
        "gb18030",
    ]
    for encoding in encodings:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")

def run_shell(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            timeout=10,
            cwd = project_root
        )

        return {
            "returncode": result.returncode,
            "stdout": decode_output(result.stdout),
            "stderr": decode_output(result.stderr),
        }

    except subprocess.TimeoutExpired:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": "Command timed out.",
        }   

def broken_tool():
    raise RuntimeError(
        "This tool is intentionally broken."
    )

tools = [
    {
        "type": "function",
        "function":{
            "name": "run_shell",
            "description": (
                "Execute a Windows CMD command in the current project "
                "directory. The operating system is Windows. "
                "Use Windows CMD syntax rather than Unix/Linux shell syntax. "
                "Return stdout, stderr, and the process return code."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name": "broken_tool",
            "description": "a tool to test the code."
        }
    }
]

tool_functions = {
    "run_shell": run_shell,
    "broken_tool": broken_tool,
}

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

result = agent.run("Use broken_tool and tell me what happens.")
print(result)
