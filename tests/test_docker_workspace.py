from tinyharness.workspace import (
    DockerWorkspace,
)


def test_docker_workspace_create_and_run():

    workspace = DockerWorkspace()


    try:

        workspace.create()


        result = workspace.run(
            "echo hello docker"
        )


        assert result.returncode == 0

        assert (
            "hello docker"
            in result.stdout
        )


    finally:

        workspace.remove()



def test_docker_workspace_file_isolated():

    workspace = DockerWorkspace()


    try:

        workspace.create()


        workspace.write_file(
            "/tmp/test.txt",
            "docker workspace",
        )


        content = workspace.read_file(
            "/tmp/test.txt"
        )


        assert (
            content.strip()
            ==
            "docker workspace"
        )


    finally:

        workspace.remove()