import argparse
from dataclasses import asdict

from harness.agent import AgentLoop
from harness.model import FakeModel, OpenAIModel, OllamaModel
from harness.recorder import RunRecorder
from harness.sandbox import DockerSandbox
from harness.scoring import TaskScorer
from harness.task import load_task_spec


def build_model(backend: str, model_name: str):
    if backend == "fake":
        return FakeModel()

    if backend == "openai":
        return OpenAIModel(model_name=model_name)

    if backend == "ollama":
        return OllamaModel(model_name=model_name)

    raise ValueError(f"Unknown backend: {backend}")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--task",
        default="tasks/fix_bug_no_peeking",
        help="Path to task directory.",
    )

    parser.add_argument(
        "--backend",
        choices=["fake", "openai", "ollama"],
        default="fake",
        help="Model backend to use.",
    )

    parser.add_argument(
        "--model",
        default="gpt-4.1-mini",
        help="Model name for OpenAI or Ollama runs.",
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=10,
        help="Maximum number of agent steps.",
    )

    args = parser.parse_args()

    task_dir = args.task
    task = load_task_spec(task_dir)

    model = build_model(backend=args.backend, model_name=args.model)
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
            "backend": args.backend,
            "model": args.model if args.backend in ["openai", "ollama"] else "FakeModel",
            "max_steps": args.max_steps,
        }
    )

    try:
        sandbox.start()

        agent = AgentLoop(
            model=model,
            sandbox=sandbox,
            recorder=recorder,
            max_steps=args.max_steps,
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