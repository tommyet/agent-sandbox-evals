import subprocess
import time
import uuid
from dataclasses import dataclass


@dataclass
class CommandResult:
    command: str
    stdout: str
    stderr: str
    exit_code: int
    runtime_seconds: float


class DockerSandbox:
    """
    Small wrapper around Docker.

    It starts a container from an image, runs shell commands inside it,
    captures stdout/stderr/exit code, then stops the container.
    """

    def __init__(self, image_name: str, timeout_seconds: int = 30):
        self.image_name = image_name
        self.timeout_seconds = timeout_seconds
        self.container_name = f"agent-sandbox-{uuid.uuid4().hex[:8]}"
        self.started = False

    def start(self) -> None:
        if self.started:
            raise RuntimeError("Sandbox already started")

        command = [
            "docker",
            "run",
            "-d",                  # run in background
            "--rm",                # delete container after it stops
            "--network",
            "none",                # no internet/network access
            "--name",
            self.container_name,
            self.image_name,
            "sleep",
            "infinity",            # keep container alive
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to start container.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )

        self.started = True

    def exec(self, command: str) -> CommandResult:
        if not self.started:
            raise RuntimeError("Sandbox is not started")

        docker_command = [
            "docker",
            "exec",
            self.container_name,
            "bash",
            "-lc",
            command,
        ]

        start_time = time.time()

        result = subprocess.run(
            docker_command,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )

        runtime = time.time() - start_time

        return CommandResult(
            command=command,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            runtime_seconds=runtime,
        )

    def stop(self) -> None:
        if not self.started:
            return

        subprocess.run(
            ["docker", "stop", self.container_name],
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )

        self.started = False