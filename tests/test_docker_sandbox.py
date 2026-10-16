import subprocess
from pathlib import Path


def run_docker(*args):
    return subprocess.run(
        ["docker", *args],
        capture_output=True,
        text=True,
    )


def test_network_isolation():
    result = run_docker(
        "run",
        "--rm",
        "--network",
        "none",
        "ubuntu:latest",
        "bash",
        "-c",
        "timeout 3 bash -c '</dev/tcp/1.1.1.1/80'",
    )

    assert result.returncode != 0
    assert "Network is unreachable" in (
        result.stdout + result.stderr
    )


def test_readonly_mount_blocks_write(tmp_path):
    test_dir = tmp_path / "sandbox"
    test_dir.mkdir()

    secret_file = test_dir / "secret.txt"
    secret_file.write_text(
        "HOST_SECRET",
        encoding="utf-8",
    )

    result = run_docker(
        "run",
        "--rm",
        "--mount",
        f"type=bind,source={test_dir},target=/workspace,readonly",
        "ubuntu:latest",
        "bash",
        "-c",
        "echo HACKED > /workspace/new.txt",
    )

    assert result.returncode != 0
    assert "Read-only file system" in (
        result.stdout + result.stderr
    )


def test_readonly_mount_allows_read(tmp_path):
    test_dir = tmp_path / "sandbox"
    test_dir.mkdir()

    secret_file = test_dir / "secret.txt"
    secret_file.write_text(
        "HOST_SECRET",
        encoding="utf-8",
    )

    result = run_docker(
        "run",
        "--rm",
        "--mount",
        f"type=bind,source={test_dir},target=/workspace,readonly",
        "ubuntu:latest",
        "cat",
        "/workspace/secret.txt",
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "HOST_SECRET"


def test_command_timeout():
    result = run_docker(
        "run",
        "--rm",
        "ubuntu:latest",
        "bash",
        "-c",
        "timeout 2 bash -c 'while true; do :; done'",
    )

    assert result.returncode == 124

from tinyharness.workspace import DockerWorkspace


def test_docker_workspace_command_runs_in_container():
    workspace = DockerWorkspace()

    workspace.create()

    try:
        result = workspace.run(
            "echo TinyHarnessSandbox"
        )

        assert result.returncode == 0
        assert "TinyHarnessSandbox" in result.stdout
    finally:
        workspace.remove()

def test_docker_workspace_network_isolation():
    workspace = DockerWorkspace()

    workspace.create()

    try:
        result = workspace.run(
            "timeout 3 bash -c '</dev/tcp/1.1.1.1/80'"
        )

        assert result.returncode != 0
        assert "Network is unreachable" in (
            result.stdout + result.stderr
        )
    finally:
        workspace.remove()

def test_docker_workspace_timeout():
    workspace = DockerWorkspace()

    workspace.create()

    try:
        result = workspace.run(
            "while true; do :; done",
            timeout=2,
        )

        assert result.timed_out is True
    finally:
        workspace.remove()