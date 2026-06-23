import json
import time
import uuid
from dataclasses import asdict
from pathlib import Path

from harness.sandbox import CommandResult


class RunRecorder:
    """
    Records what happens during an eval run.

    For now, it logs every shell command as one JSON line.
    Later, we can also log model prompts, model outputs, scores, and metadata.
    """

    def __init__(self, runs_dir: str = "runs"):
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        run_id = f"{timestamp}_{uuid.uuid4().hex[:8]}"

        self.run_dir = Path(runs_dir) / run_id
        self.run_dir.mkdir(parents=True, exist_ok=False)

        self.commands_path = self.run_dir / "commands.jsonl"
        self.step = 0

    def log_command(self, result: CommandResult) -> None:
        self.step += 1

        record = {
            "step": self.step,
            **asdict(result),
        }

        with self.commands_path.open("a") as f:
            f.write(json.dumps(record) + "\n")

    def log_metadata(self, metadata: dict) -> None:
        metadata_path = self.run_dir / "metadata.json"

        with metadata_path.open("w") as f:
            json.dump(metadata, f, indent=2)

    def print_location(self) -> None:
        print(f"Run logs saved to: {self.run_dir}")

    def log_score(self, score: dict) -> None:
        score_path = self.run_dir / "score.json"

        with score_path.open("w") as f:
            json.dump(score, f, indent=2)