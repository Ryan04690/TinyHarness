
from pathlib import Path

from tinyharness.tools import create_shell_tools


def main():
    # Ensure the example uses the repository root
    # even when launched from another directory.
    project_root = Path(__file__).resolve().parent.parent

    shell_tools = create_shell_tools(project_root)

    run_shell = next(
        tool
        for tool in shell_tools
        if tool.name == "run_shell"
    )

    print("Project root:", project_root)

    # Experiment 1:
    # Execute a command from a valid workspace cwd.
    print("\n=== Experiment 1: Normal cwd ===")

    result = run_shell.execute({
        "command": "cd",
        "cwd": ".",
    })

    print(result)

    # Experiment 2:
    # Try to escape using the structured cwd argument.
    print("\n=== Experiment 2: CWD path escape ===")

    try:
        result = run_shell.execute({
            "command": "cd",
            "cwd": "..",
        })
        print(result)
    except Exception as error:
        print(type(error).__name__, str(error))

    # Experiment 3:
    # Use a valid cwd but change directory inside CMD.
    # This is an intentionally harmless read-only demo.
    print("\n=== Experiment 3: CMD directory escape ===")

    result = run_shell.execute({
        "command": "cd .. && cd",
        "cwd": ".",
    })

    print(result)


if __name__ == "__main__":
    main()
