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
    response = response.strip()

    has_action = "ACTION:" in response
    has_final = "FINAL:" in response

    if has_action and has_final:
        return ParsedAgentResponse(
            kind="invalid",
            content=(
                "Invalid response: include exactly one of ACTION or FINAL, not both."
            ),
        )

    if response.startswith("ACTION:"):
        command = response[len("ACTION:"):].strip()

        if "```" in command:
            return ParsedAgentResponse(
                kind="invalid",
                content="Invalid response: do not use markdown code fences.",
            )

        if "\n\n" in command:
            return ParsedAgentResponse(
                kind="invalid",
                content="Invalid response: ACTION must contain one raw bash command only.",
            )

        if "old_value" in command or "new_value" in command:
            return ParsedAgentResponse(
                kind="invalid",
                content="Invalid response: do not use placeholder commands.",
            )

        if not command:
            return ParsedAgentResponse(
                kind="invalid",
                content="Invalid response: ACTION command was empty.",
            )

        return ParsedAgentResponse(kind="action", content=command)

    if response.startswith("FINAL:"):
        final = response[len("FINAL:"):].strip()

        if not final:
            return ParsedAgentResponse(
                kind="invalid",
                content="Invalid response: FINAL answer was empty.",
            )

        return ParsedAgentResponse(kind="final", content=final)

    return ParsedAgentResponse(
        kind="invalid",
        content=(
            "Invalid response: you must start with exactly ACTION: or FINAL:."
        ),
    )


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