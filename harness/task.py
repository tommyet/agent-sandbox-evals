from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml


@dataclass
class TaskSpec:
    name: str
    description: str
    image_name: str
    working_directory: str
    briefing: str
    rules: List[str]
    allowed_to_modify: List[str]
    protected_files: List[str]
    forbidden_to_read: List[str]
    success_criteria: List[str]


def load_task_spec(task_dir: str) -> TaskSpec:
    task_path = Path(task_dir) / "task.yaml"

    if not task_path.exists():
        raise FileNotFoundError(f"Could not find task file: {task_path}")

    with task_path.open("r") as f:
        data = yaml.safe_load(f)

    return TaskSpec(
        name=data["name"],
        description=data["description"],
        image_name=data["image_name"],
        working_directory=data["working_directory"],
        briefing=data["briefing"],
        rules=data["rules"],
        allowed_to_modify=data["allowed_to_modify"],
        protected_files=data["protected_files"],
        forbidden_to_read=data["forbidden_to_read"],
        success_criteria=data["success_criteria"],
    )