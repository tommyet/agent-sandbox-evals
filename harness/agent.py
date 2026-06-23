from dataclasses import dataclass
from typing import Dict, List, Optional

from harness.recorder import RunRecorder
from harness.sandbox import DockerSandbox
from harness.task import TaskSpec


@dataclass
class ParsedAgentResponse:
    kind: str  # "action" or "final" or "invalid"
    content: str


def parse_agent_response(response: str) -> ParsedAgentResponse:
    stripped = response.strip()

    if stripped.startswith("ACTION:"):
        command = stripped[len("ACTION:"):].strip()
        return ParsedAgentResponse(kind="action", content=command)

    if stripped.startswith("FINAL:"):
        final_answer = stripped[len("FINAL:"):].strip()
        return ParsedAgentResponse(kind="final", content=final_answer)

    return ParsedAgentResponse(kind="invalid", content=stripped)


class AgentLoop:
    """
    Runs a simple think-act-observe loop.

    The model receives:
    - the task briefing
    - previous actions
    - observations from the sandbox

    The model must respond with either:

    ACTION:
    <single bash command>

    or:

    FINAL:
    <brief final answer>
    """

    def __init__(
        self,
        model,
        sandbox: DockerSandbox,
        recorder: RunRecorder,
        max_steps: int = 10,
    ):
        self.model = model
        self.sandbox = sandbox
        self.recorder = recorder
        self.max_steps = max_steps

    def run(self, task: TaskSpec) -> Optional[str]:
        messages: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": task.briefing,
            }
        ]

        for step in range(1, self.max_steps + 1):
            response = self.model.complete(messages)
            self.recorder.log_model_event(messages=messages, response=response)

            parsed = parse_agent_response(response)

            print("=" * 80)
            print(f"AGENT STEP {step}")
            print(response)

            if parsed.kind == "final":
                print("=" * 80)
                print("AGENT FINISHED")
                print(parsed.content)
                return parsed.content

            if parsed.kind == "invalid":
                observation = (
                    "Invalid response format. Please respond with either "
                    "ACTION:\\n<single bash command> or FINAL:\\n<brief final answer>."
                )
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": observation})
                continue

            command = parsed.content

            result = self.sandbox.exec(command)
            self.recorder.log_command(result)

            observation = self._format_observation(result)

            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": observation})

        return None

    def _format_observation(self, result) -> str:
        return f"""Observation from running command:

COMMAND:
{result.command}

EXIT CODE:
{result.exit_code}

STDOUT:
{result.stdout}

STDERR:
{result.stderr}
"""