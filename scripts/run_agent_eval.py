from dataclasses import asdict

from harness.agent import AgentLoop
from harness.model import FakeModel
from harness.recorder import RunRecorder
from harness.sandbox import DockerSandbox
from harness.scoring import TaskScorer
from harness.task import load_task_spec


def main():
    task_dir = "tasks/fix_bug_no_peeking"
    task = load_task_spec(task_dir)

    model = FakeModel()
    sandbox = DockerSandbox(image_name=task.image_name)
    recorder = RunRecorder()
    scorer = TaskScorer(task_project_dir=f"{task_dir}/project")

    recorder.log_metadata(
        {
            "task": task.name,
            "image_name": task.image_name,
            "description": task.description,
            "briefing": task.briefing,
            "rules": task.rules,
            "success_criteria": task.success_criteria,
            "model": "FakeModel",
        }
    )

    try:
        sandbox.start()

        agent = AgentLoop(
            model=model,
            sandbox=sandbox,
            recorder=recorder,
            max_steps=10,
        )

        final_answer = agent.run(task)

        score = scorer.score(sandbox=sandbox, recorder=recorder)

        print("=" * 80)
        print("FINAL ANSWER:")
        print(final_answer)

        print("=" * 80)
        print("FINAL SCORE:")
        print(asdict(score))

    finally:
        sandbox.stop()
        recorder.print_location()


if __name__ == "__main__":
    main()